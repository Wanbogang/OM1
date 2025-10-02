# ws_asr_stream_typed_ok.py
# Streaming ASR (typed JSON):
#   1) {"type":"start", ...}
#   2) berulang: {"type":"audio", "audio":"<base64>"}   # Wajib ada field "audio"
#   3) {"type":"end"}

import os, sys, json, base64, wave, contextlib, asyncio
import websockets

CHUNK_MS       = int(os.getenv("ASR_CHUNK_MS", "30"))     # 20–40ms ideal
READ_TAIL_SECS = float(os.getenv("ASR_READ_TAIL", "8"))   # tunggu hasil setelah end
DEBUG          = os.getenv("ASR_DEBUG", "false").lower() in ("1","true","yes")
AUDIO_FIELD    = os.getenv("ASR_AUDIO_FIELD", "audio")    # default "audio"
DUAL_KEY       = os.getenv("ASR_DUAL_KEY", "true").lower() in ("1","true","yes")  # juga kirim "data" utk kompatibilitas

def build_ws_url() -> str:
    url = (os.getenv("ASR_WS_URL") or "").strip()
    if url:
        return url
    ep  = (os.getenv("OM1_ASR_ENDPOINT") or "").strip()
    key = (os.getenv("OM_API_KEY") or "").strip()
    if not ep:
        raise RuntimeError("OM1_ASR_ENDPOINT kosong. Contoh: wss://api.openmind.org/api/core/google/asr")
    if not key:
        raise RuntimeError("OM_API_KEY kosong.")
    sep = "&" if "?" in ep else "?"
    return f"{ep}{sep}api_key={key}"

@contextlib.contextmanager
def open_wav(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    wf = wave.open(path, "rb")
    try:
        yield wf
    finally:
        wf.close()

def wav_info(path: str):
    with open_wav(path) as wf:
        return wf.getframerate(), wf.getnchannels(), wf.getsampwidth(), wf.getnframes()

async def reader(ws):
    try:
        async for raw in ws:
            print("[<-]", raw)
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if isinstance(msg, dict):
                if msg.get("type") == "error":
                    raise RuntimeError(msg.get("message", "ASR error"))

                # berbagai kemungkinan bentuk hasil
                if "transcript" in msg and msg["transcript"]:
                    print("TRANSCRIPT:", msg["transcript"])
                if "text" in msg and msg["text"]:
                    print("TEXT:", msg["text"])
                if "results" in msg:
                    for r in msg.get("results", []):
                        alts = r.get("alternatives") or []
                        if alts:
                            t = alts[0].get("transcript") or alts[0].get("text")
                            if t:
                                print(("FINAL:" if r.get("isFinal") else "PARTIAL:"), t)
                if "alternatives" in msg:
                    alts = msg.get("alternatives") or []
                    if alts:
                        t = alts[0].get("transcript") or alts[0].get("text")
                        if t:
                            print("ALT:", t)
    except Exception as e:
        print("[reader] stop:", e)

async def stream(ws, wav_path: str, language: str):
    with open_wav(wav_path) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        if (sr, ch, sw) != (16000, 1, 2):
            print(f"[!] Warning: ideal 16kHz/mono/16-bit. Sekarang: {sr}Hz, ch={ch}, {8*sw}bit")

        # 1) START
        start_msg = {
            "type": "start",
            "language": language,
            "sample_rate": sr,
            "channels": ch,
            "format": "s16le",
            "encoding": "LINEAR16",
            "contentType": "audio/pcm;bit=16;rate=16000;channels=1",
            "frame_ms": CHUNK_MS,
        }
        if DEBUG:
            print("[->] start", start_msg)
        await ws.send(json.dumps(start_msg))

        # kalkulasi chunk
        bpf = ch * sw
        bytes_per_ms = int(sr * bpf / 1000)
        chunk_bytes  = max(bytes_per_ms * CHUNK_MS, 1)

        seq = 0
        total = 0
        while True:
            buf = wf.readframes(chunk_bytes // bpf)
            if not buf:
                break
            b64 = base64.b64encode(buf).decode("ascii")

            # 2) AUDIO (penting: ada "type":"audio" + field "audio")
            msg = {"type": "audio", AUDIO_FIELD: b64}
            if DUAL_KEY and AUDIO_FIELD != "data":
                msg["data"] = b64  # kompatibilitas server yg cek "audio" tapi pakai "data"
            await ws.send(json.dumps(msg))

            frames = len(buf) // bpf
            total += frames
            if DEBUG:
                print(f"[->] audio seq={seq} frames+={frames} (total={total})")
            seq += 1

            # pacing real-time-ish
            await asyncio.sleep(CHUNK_MS / 1000.0)

        # 3) END
        end_msg = {"type": "end"}
        if DEBUG:
            print("[->] end", end_msg)
        await ws.send(json.dumps(end_msg))

async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_stream_typed_ok.py <wav_path> <language>")
        sys.exit(2)

    wav_path = sys.argv[1]
    language = sys.argv[2]
    url = build_ws_url()

    sr, ch, sw, nframes = wav_info(wav_path)
    safe_url = url.split("api_key=")[0] + "api_key=****"
    print(f"ASR_WS_URL  = {safe_url}")
    print(f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit, {nframes} frames)")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {CHUNK_MS} ms, MODE=typed-json\n")

    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        r = asyncio.create_task(reader(ws))
        await stream(ws, wav_path, language)
        await asyncio.sleep(READ_TAIL_SECS)
        try:
            await asyncio.wait_for(r, timeout=1.0)
        except asyncio.TimeoutError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
