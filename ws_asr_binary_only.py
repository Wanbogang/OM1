#!/usr/bin/env python3
import os, sys, asyncio, wave, contextlib
import websockets

def build_ws_url(language: str) -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep  = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    key = os.getenv("OM_API_KEY", "").strip()
    if not ep:
        raise SystemExit("OM1_ASR_ENDPOINT kosong (mis. wss://api.openmind.org/api/core/google/asr)")
    if not key:
        raise SystemExit("OM_API_KEY kosong")
    sep = "&" if "?" in ep else "?"
    # Semua metadata di query string; TANPA JSON control
    return (
        f"{ep}{sep}api_key={key}"
        f"&language={language}"
        f"&sample_rate=16000&channels=1"
        f"&format=s16le&encoding=LINEAR16"
    )

def open_wav_checked(path: str):
    if not os.path.exists(path):
        raise SystemExit(f"File tidak ditemukan: {path}")
    wf = wave.open(path, "rb")
    sr, ch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
    if not (sr == 16000 and ch == 1 and sw == 2):
        wf.close()
        raise SystemExit("WAV harus LINEAR16: 16kHz, mono, 16-bit.")
    return wf

async def receiver(ws: websockets.WebSocketClientProtocol):
    try:
        async for msg in ws:
            print("[<-]", msg)
    except websockets.ConnectionClosedOK:
        pass
    except websockets.ConnectionClosedError as e:
        print(f"[reader] closed with error: {e}")

async def sender_binary(ws: websockets.WebSocketClientProtocol, wav_path: str, chunk_ms: int):
    with contextlib.closing(open_wav_checked(wav_path)) as wf:
        sr = wf.getframerate()
        frames_per_chunk = max(1, sr * chunk_ms // 1000)       # 30ms @16k => 480 frames
        bpf = wf.getsampwidth() * wf.getnchannels()             # bytes per frame (2)
        sleep_s = chunk_ms / 1000.0

        total_frames = wf.getnframes()
        sent_frames = 0
        seq = 0
        while sent_frames < total_frames:
            data = wf.readframes(frames_per_chunk)
            if not data:
                break
            # PENTING: kirim bytes (binary WS frame), BUKAN JSON
            await ws.send(data)
            sent_frames += len(data) // bpf
            print(f"[->] audio seq={seq} frames+={len(data)//bpf} (total~{sent_frames})")
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
    read_tail = float(os.getenv("ASR_READ_TAIL", "8"))

    print(f"ASR_WS_URL  = {url[:40]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {chunk_ms} ms, MODE=BINARY ONLY (no JSON)\n")

    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        recv_task = asyncio.create_task(receiver(ws))
        await sender_binary(ws, wav_path, chunk_ms)

        # Selesai kirim -> close untuk signal EOF (kunci menghindari 'Audio Timeout')
        print("[*] closing socket to signal EOF")
        await ws.close()

        # beri waktu untuk pesan tail
        try:
            await asyncio.wait_for(recv_task, timeout=read_tail)
        except asyncio.TimeoutError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
