#!/usr/bin/env python3
import os, sys, asyncio, wave, contextlib, json, time
import websockets

def build_ws_url(language: str) -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if not url:
        ep  = os.getenv("OM1_ASR_ENDPOINT", "").strip()
        key = os.getenv("OM_API_KEY", "").strip()
        if not ep:
            raise SystemExit("OM1_ASR_ENDPOINT kosong (contoh: wss://api.openmind.org/api/core/google/asr)")
        if not key:
            raise SystemExit("OM_API_KEY kosong")
        sep = "&" if "?" in ep else "?"
        # Kirim semua param di URL (tanpa JSON control)
        url = (
            f"{ep}{sep}"
            f"api_key={key}"
            f"&language={language}"
            f"&sample_rate=16000&channels=1"
            f"&format=s16le&encoding=LINEAR16"
        )
    return url

def open_wav_checked(path: str):
    if not os.path.exists(path):
        raise SystemExit(f"File tidak ditemukan: {path}")
    wf = wave.open(path, "rb")
    sr, ch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
    if not (sr == 16000 and ch == 1 and sw == 2):
        wf.close()
        raise SystemExit("WAV harus LINEAR16: 16kHz, mono, 16-bit (16k/mono/16-bit).")
    return wf  # jangan ditutup di sini

async def receiver(ws: websockets.WebSocketClientProtocol):
    try:
        async for msg in ws:
            # Server biasanya kirim JSON; tampilkan apa adanya
            print("[<-]", msg)
    except websockets.ConnectionClosedOK:
        pass
    except websockets.ConnectionClosedError as e:
        print(f"[reader] closed with error: {e}")

async def sender_binary(ws: websockets.WebSocketClientProtocol, wav_path: str, chunk_ms: int):
    with contextlib.closing(open_wav_checked(wav_path)) as wf:
        sr = wf.getframerate()
        frames_per_chunk = max(1, sr * chunk_ms // 1000)  # 480 untuk 30ms @16k
        bytes_per_frame = wf.getsampwidth() * wf.getnchannels()  # 2 * 1 = 2
        sleep_s = chunk_ms / 1000.0

        total_frames = wf.getnframes()
        sent_frames = 0
        seq = 0

        while sent_frames < total_frames:
            # baca N frames -> bytes biner
            frames = wf.readframes(frames_per_chunk)
            if not frames:
                break
            await ws.send(frames)  # <- penting: KIRIM BINER (type=bytes), BUKAN JSON
            sent_frames += len(frames) // bytes_per_frame
            print(f"[->] audio seq={seq} frames+={len(frames)//bytes_per_frame} (total~{sent_frames})")
            seq += 1
            await asyncio.sleep(sleep_s)

async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_binary_only.py <wav_path> <language>")
        print("Example: python -u ws_asr_binary_only.py tools/asr-eval/en/001.wav en-US")
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url(language)
    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))
    read_tail = float(os.getenv("ASR_READ_TAIL", "8"))  # waktu tunggu setelah close

    print(f"ASR_WS_URL  = {url[:40]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {chunk_ms} ms, MODE=BINARY ONLY (no JSON)\n")

    # Koneksi WebSocket
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        # Jalankan receiver paralel
        recv_task = asyncio.create_task(receiver(ws))

        # KIRIM BINER SAJA, TANPA start/end/flush/config
        await sender_binary(ws, wav_path, chunk_ms)

        # Selesai kirim -> TUTUP koneksi agar server tahu EOF (ini kuncinya)
        print("[*] closing socket to signal EOF")
        await ws.close()  # kirim close frame; server akan menyelesaikan

        # beri waktu sedikit untuk menyelesaikan loop receiver (kalau masih ada pesan)
        try:
            await asyncio.wait_for(recv_task, timeout=read_tail)
        except asyncio.TimeoutError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
