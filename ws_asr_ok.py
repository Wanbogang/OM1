# ws_asr_ok.py — kirim {"audio": "<base64>", "language": "..."} dan tunggu hasil
import os, sys, json, base64, wave, contextlib, asyncio
import websockets

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    endpoint = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    api_key  = os.getenv("OM_API_KEY", "").strip()
    if not endpoint:
        raise RuntimeError("OM1_ASR_ENDPOINT kosong. Contoh: wss://api.openmind.org/api/core/google/asr")
    if not api_key:
        raise RuntimeError("OM_API_KEY kosong.")
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

def read_wav_b64(path: str) -> str:
    with open_wav(path) as wf:
        sr, ch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
        if sr != 16000 or ch != 1 or sw != 2:
            print(f"Warning: WAV ideal 16kHz/mono/16-bit. Sekarang: {sr}Hz, ch={ch}, {8*sw}bit", flush=True)
        raw = wf.readframes(wf.getnframes())
    return base64.b64encode(raw).decode("ascii")

async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_ok.py <wav_path> <language>")
        sys.exit(2)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()
    audio_b64 = read_wav_b64(wav_path)

    print(f"ASR_WS_URL  = {url.split('api_key=')[0]}api_key=****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print("Mode        = root JSON {audio, language}\n", flush=True)

    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        # kirim audio
        await ws.send(json.dumps({"audio": audio_b64, "language": language}))

        deadline = asyncio.get_event_loop().time() + 30.0  # tunggu sampai 30 dtk
        sent_end = False
        got_any  = False

        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=max(0.1, remaining))
            except asyncio.TimeoutError:
                # beberapa server butuh sinyal "end" eksplisit
                if not sent_end:
                    try:
                        await ws.send(json.dumps({"type": "end"}))
                        sent_end = True
                        deadline += 5.0
                        print("[->] {\"type\":\"end\"}")
                        continue
                    except Exception:
                        break
                else:
                    break
            got_any = True
            if isinstance(msg, bytes):
                print(f"[<-] <{len(msg)} bytes>")
                continue
            print("[<-]", msg)
            try:
                obj = json.loads(msg)
                # cetak transkrip kalau ada
                if "transcript" in obj:
                    print("TRANSCRIPT:", obj["transcript"])
                elif "result" in obj:
                    print("RESULT:", obj["result"])
                elif "alternatives" in obj and isinstance(obj["alternatives"], list) and obj["alternatives"]:
                    alt = obj["alternatives"][0]
                    print("ALT:", alt.get("transcript") or alt.get("text"))
                elif "text" in obj:
                    print("TEXT:", obj["text"])
            except Exception:
                pass

        if not got_any:
            print("Tidak ada respons selain handshake. Coba durasi lebih lama atau cek log server.")

if __name__ == "__main__":
    asyncio.run(main())
