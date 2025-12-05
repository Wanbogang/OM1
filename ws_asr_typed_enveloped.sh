cat > ws_asr_single_root.py <<'PY'
#!/usr/bin/env python3
import os, sys, json, base64, asyncio, wave, contextlib
import websockets

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep  = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    key = os.getenv("OM_API_KEY", "").strip()
    if not ep:
        raise SystemExit("Env OM1_ASR_ENDPOINT kosong (contoh: wss://api.openmind.org/api/core/google/asr)")
    if not key:
        raise SystemExit("Env OM_API_KEY kosong")
    sep = "&" if "?" in ep else "?"
    return f"{ep}{sep}api_key={key}"

def read_wav_bytes(path: str) -> bytes:
    if not os.path.exists(path):
        raise SystemExit(f"File tidak ditemukan: {path}")
    with contextlib.closing(wave.open(path, "rb")) as wf:
        sr, ch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
        if not (sr == 16000 and ch == 1 and sw == 2):
            raise SystemExit("WAV harus LINEAR16: 16kHz, mono, 16-bit")
        return wf.readframes(wf.getnframes())

async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_single_root.py <wav_path> <language>")
        print("Example: python -u ws_asr_single_root.py tools/asr-eval/en/001.wav en-US")
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()
    audio = read_wav_bytes(wav_path)
    b64   = base64.b64encode(audio).decode("ascii")
    audio_field = os.getenv("ASR_AUDIO_FIELD", "audio")  # ganti ke 'data' kalau gateway minta

    print(f"ASR_WS_URL  = {url[:40]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"MODE        = single JSON {{{audio_field}, language}}")
    print()

    payload = {audio_field: b64, "language": language}

    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        print("[->] single root JSON (audio + language)")
        await ws.send(json.dumps(payload))
        try:
            async for msg in ws:
                print("[<-]", msg)
        except websockets.ConnectionClosedOK:
            pass

if __name__ == "__main__":
    asyncio.run(main())
