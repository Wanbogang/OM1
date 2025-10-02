# --- START ws_asr_min.py ---
# Minimal WebSocket ASR client: kirim satu JSON {"audio": "<base64>"}.
# Python 3.10+, websockets>=10

import os, sys, json, base64, wave, contextlib, asyncio
import websockets

def mask_key(s: str) -> str:
    return s[:4] + "..." + s[-4:] if s else s

def build_ws_url() -> str:
    # Pakai ASR_WS_URL kalau ada; kalau tidak, bangun dari OM1_ASR_ENDPOINT + OM_API_KEY
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    endpoint = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    api_key  = os.getenv("OM_API_KEY", "").strip()
    if not endpoint:
        raise RuntimeError("OM1_ASR_ENDPOINT kosong. Contoh: wss://api.openmind.org/api/core/google/asr")
    if not api_key:
        raise RuntimeError("OM_API_KEY kosong (API key).")
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

def read_wav(path: str):
    with open_wav(path) as wf:
        sr, ch, sw, n = wf.getframerate(), wf.getnchannels(), wf.getsampwidth(), wf.getnframes()
        raw = wf.readframes(n)
    return sr, ch, sw, n, raw

async def run(url: str, wav_path: str, language: str):
    sr, ch, sw, n, raw = read_wav(wav_path)
    audio_b64 = base64.b64encode(raw).decode("ascii")

    url_print = url
    if "api_key=" in url_print:
        before, after = url_print.split("api_key=", 1)
        url_print = before + "api_key=" + mask_key(after)

    print(f"ASR_WS_URL      = {url_print}")
    print(f"WAV             = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit, {n} frames, {len(raw)} bytes)")
    print(f"Language        = {language}")
    print("Mode            = single JSON: {'audio': '<base64>'}\n")

    payload = {
        "audio": audio_b64,                 # <— kunci: server minta field 'audio'
        "language": language,
        "sample_rate": sr,
        "channels": ch,
        "format": "s16le" if sw == 2 else f"pcm_{8*sw}",
        "encoding": "LINEAR16" if sw == 2 else f"PCM_{8*sw}",
        "contentType": f"audio/pcm;bit={8*sw};rate={sr};channels={ch}",
    }

    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
            await ws.send(json.dumps(payload))
            # beberapa server gak butuh ini; aman diabaikan
            try:
                await ws.send(json.dumps({"end": True}))
            except Exception:
                pass

            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=8.0)
                    print("[<-] ", msg)
            except asyncio.TimeoutError:
                print("(timeout menunggu balasan lanjutan)")
    except Exception as e:
        print("!! Gagal:", e)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_min.py <wav_path> <language>")
        print("Example: python -u ws_asr_min.py tools/asr-eval/en/001.wav en-US")
        sys.exit(2)
    ws_url = build_ws_url()
    asyncio.run(run(ws_url, sys.argv[1], sys.argv[2]))
# --- END ws_asr_min.py ---
