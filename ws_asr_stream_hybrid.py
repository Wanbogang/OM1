# ws_asr_typed_stream.py
# Minimal & robust WebSocket ASR client (typed JSON) untuk endpoint OpenMind Google ASR
# Python 3.10+, websockets>=10

import os, sys, json, base64, asyncio, wave, contextlib, math, time
from typing import Optional
import websockets

# ---------- Konfigurasi dari ENV ----------
CHUNK_MS = int(os.getenv("ASR_CHUNK_MS", "30"))          # 20–40 ms disarankan
READ_TAIL = float(os.getenv("ASR_READ_TAIL", "10"))      # durasi nunggu hasil setelah "end"
DEBUG = os.getenv("ASR_DEBUG", "false").lower() == "true"

def mask(s: str) -> str:
    if not s:
        return s
    return s[:4] + "..." + s[-4:]

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    endpoint = os.getenv("OM1_ASR_ENDPOINT", "").strip() or os.getenv("OM1_ASR_ENDPOINT".replace("OM1_","OM_"), "").strip()
    if not endpoint:
        endpoint = os.getenv("OM1_ASR_ENDPOINT".replace("1_","_"), "").strip()
    if not endpoint:
        endpoint = os.getenv("OM_ASR_ENDPOINT", "").strip()

    api_key = os.getenv("OM_API_KEY", "").strip()
    if not endpoint:
        raise RuntimeError("Env OM1_ASR_ENDPOINT kosong. Contoh: wss://api.openmind.org/api/core/google/asr")
    if not api_key:
        raise RuntimeError("Env OM_API_KEY kosong (API key).")

    sep = "&" if "?" in endpoint else "?"
    return f"{endpoint}{sep}api_key={api_key}"

@contextlib.contextmanager
def open_wav(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    wf = wave.open(path, "rb")
    try:
        yield wf
    finally:
        wf.close()

async def reader(ws):
    """
    Terus baca pesan dari server dan cetak apapun yang datang.
    Akan berakhir sendiri saat server menutup koneksi.
    """
    try:
        while True:
            msg = await ws.recv()
            try:
                data = json.loads(msg)
            except Exception:
                data = msg
            print(f"[<-] {data}")
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except websockets.exceptions.ConnectionClosedError:
        pass

async def sender_stream(ws, wav_path: str, language: str):
    """
    Kirim:
      1) {"type":"start", ...}
      2) berulang: {"type":"audio","audio":"<base64>"}
      3) {"type":"end"}
    dengan pacing real-time CHUNK_MS.
    """
    with open_wav(wav_path) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        nframes = wf.getnframes()

        if sr != 16000 or ch != 1 or sw != 2:
            print(f"[!] Peringatan: WAV ideal = 16kHz mono 16-bit. Sekarang: {sr} Hz, {ch} ch, {8*sw} bit.")

        # 1) START
        start = {
            "type": "start",
            "language": language,
            "sample_rate": sr,
            "channels": ch,
            "format": "s16le",
            "encoding": "LINEAR16",
            "contentType": f"audio/pcm;bit={8*sw};rate={sr};channels={ch}",
            "frame_ms": CHUNK_MS,
        }
        if DEBUG:
            print("[->] start", start)
        await ws.send(json.dumps(start))

        # 2) AUDIO CHUNKS
        frames_per_chunk = int(sr * CHUNK_MS / 1000)
        seq = 0
        t0 = time.perf_counter()
        sent_frames = 0

        while True:
            buf = wf.readframes(frames_per_chunk)
            if not buf:
                break
            b64 = base64.b64encode(buf).decode("ascii")

            msg = {
                "type":  "audio",   # WAJIB
                "seq":   seq,
                "audio": b64,       # WAJIB (server cari key 'audio')
                "data":  b64        # opsional (kompatibilitas server yg cari 'data')
            }

            if DEBUG:
                print(f"[->] audio seq={seq} frames+={len(buf)//sw} (total={sent_frames + len(buf)//sw})")

            await ws.send(json.dumps(msg))
            sent_frames += len(buf)//sw
            seq += 1

            # pacing real-time-ish
            await asyncio.sleep(max(0, CHUNK_MS / 1000))

        # 3) END
        if DEBUG:
            print("[->] end")
        await ws.send(json.dumps({"type": "end"}))

        # setelah end, kasih waktu server memproses
        if READ_TAIL > 0:
            await asyncio.sleep(READ_TAIL)

async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_typed_stream.py <wav_path> <language>")
        print("Contoh: python -u ws_asr_typed_stream.py tools/asr-eval/en/001.wav en-US")
        sys.exit(2)

    wav_path = sys.argv[1]
    language = sys.argv[2]
    url = build_ws_url()

    # Info awal
    with open_wav(wav_path) as wf:
        sr, ch, sw, nframes = wf.getframerate(), wf.getnchannels(), wf.getsampwidth(), wf.getnframes()
    api_key = os.getenv("OM_API_KEY","")
    print(f"ASR_WS_URL  = {url.replace(api_key, '****') if api_key else url}")
    print(f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit, {nframes} frames)")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {CHUNK_MS} ms, MODE=typed-json\n")

    # Koneksi WS
    async with websockets.connect(
        url,
        ping_interval=20,
        ping_timeout=20,
        max_size=None,
    ) as ws:
        # jalanin reader & sender bareng
        reader_task = asyncio.create_task(reader(ws))
        try:
            await sender_stream(ws, wav_path, language)
        finally:
            # tutup koneksi dengan rapi
            try:
                await ws.close()
            except Exception:
                pass
            # beri kesempatan reader menghabiskan pesan yang tersisa
            await asyncio.sleep(0.2)
            if not reader_task.done():
                reader_task.cancel()
                try:
                    await reader_task
                except Exception:
                    pass

if __name__ == "__main__":
    asyncio.run(main())
