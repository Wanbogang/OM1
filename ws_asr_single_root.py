#!/usr/bin/env python3
import os, sys, json, base64, asyncio, wave, contextlib, time
import websockets

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep  = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    key = os.getenv("OM_API_KEY", "").strip()
    if not ep:  raise SystemExit("Env OM1_ASR_ENDPOINT kosong (contoh: wss://api.openmind.org/api/core/google/asr)")
    if not key: raise SystemExit("Env OM_API_KEY kosong")
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

async def send_once(url: str, payload: dict, label: str, read_tail: float = 8.0):
    print(f"\n=== TRY {label} ===")
    print("[->]", payload if len(str(payload)) < 200 else {k: (v if k!='audio' and k!='data' and k!='audioContent' else '<base64>') for k,v in payload.items()})
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        await ws.send(json.dumps(payload))
        got_any = False
        t0 = time.time()
        try:
            while True:
                timeout = max(0.1, read_tail - (time.time() - t0))
                if timeout <= 0:
                    break
                msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
                got_any = True
                print("[<-]", msg)
        except asyncio.TimeoutError:
            pass
        except websockets.ConnectionClosed as e:
            print(f"[x] closed: {e.code} {e.reason}")
        return got_any
async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_single_root.py <wav_path> <language>")
        print("Example: python -u ws_asr_single_root.py tools/asr-eval/en/001.wav en-US")
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()
    audio = read_wav_bytes(wav_path)
    b64   = base64.b64encode(audio).decode("ascii")

    # Tampilkan info singkat
    print(f"ASR_WS_URL  = {url[:40]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")

    # Coba beberapa pola (urut yang paling mungkin diterima gateway kamu)
    variants = [
        ("root_audio",         {"audio": b64, "language": language}),
        ("typed_audio",        {"type": "audio", "audio": b64, "language": language}),
        ("root_data",          {"data": b64, "language": language}),
        ("root_audioContent",  {"audioContent": b64, "languageCode": language}),
    ]

    # Jika user override nama field:
    override = os.getenv("ASR_AUDIO_FIELD", "").strip()
    if override and override not in ("audio", "data", "audioContent"):
        variants.insert(0, (f"root_{override}", {override: b64, "language": language}))

    # Jalankan satu-satu sampai ada respon (bukan error format/doang)
    ok_any = False
    for label, payload in variants:
        got = await send_once(url, payload, label, read_tail=float(os.getenv("ASR_READ_TAIL", "8")))
        ok_any = ok_any or got

    if not ok_any:
        print("\n[!] Tidak ada respon berguna. Biasanya karena server menolak format.")
        print("    Coba urutan berikut:")
        print("    1) root_audio        -> {'audio': '<base64>', 'language': 'en-US'}")
        print("    2) typed_audio       -> {'type':'audio','audio':'<base64>','language':'en-US'}")
        print("    3) root_data         -> {'data': '<base64>', 'language': 'en-US'}")
        print("    4) root_audioContent -> {'audioContent': '<base64>', 'languageCode': 'en-US'}")
        print("   Tips:")
        print("   - export ASR_AUDIO_FIELD=data          # jika gateway minta 'data'")
        print("   - export ASR_READ_TAIL=12              # tunggu balasan lebih lama")
        print("   - pastikan file WAV 16kHz mono 16-bit")

if __name__ == "__main__":
    asyncio.run(main())
