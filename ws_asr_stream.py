# ws_asr_stream.py
# Stream WAV 16k/mono/16-bit ke OpenMind ASR (Google) via WebSocket
# Format: kirim {"type":"start", ...} -> berulang {"type":"audio","seq", "audio"} -> {"type":"end"}

import os, sys, json, base64, wave, contextlib, asyncio
import websockets

CHUNK_MS = int(os.getenv("ASR_CHUNK_MS", "30"))   # 20–50 ms ideal
END_TYPE = os.getenv("ASR_END_TYPE", "end")       # "end" atau "stop"

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

async def stream_file(ws, wav_path: str, language: str):
    with open_wav(wav_path) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        if (sr, ch, sw) != (16000, 1, 2):
            print(f"[!] Warning: ideal 16kHz/mono/16-bit. Sekarang: {sr}Hz, ch={ch}, {8*sw}bit")

        start_msg = {
            "type": "start",
            "language": language,
            "sample_rate": sr,
            "channels": ch,
            "format": "s16le",
            "encoding": "LINEAR16",
            "contentType": f"audio/pcm;bit={8*sw};rate={sr};channels={ch}",
            "frame_ms": CHUNK_MS,
        }
        await ws.send(json.dumps(start_msg))
        print(f"[->] start {start_msg}")

        bytes_per_frame  = ch * sw
        bytes_per_ms     = sr * bytes_per_frame // 1000
        chunk_bytes      = max(bytes_per_ms * CHUNK_MS, 1)

        seq = 0
        total_frames = 0
        while True:
            buf = wf.readframes(chunk_bytes // bytes_per_frame)
            if not buf:
                break
            b64 = base64.b64encode(buf).decode("ascii")
            payload = {"type": "audio", "seq": seq, "audio": b64}
            await ws.send(json.dumps(payload))
            sent = len(buf) // bytes_per_frame
            total_frames += sent
            seq += 1
            print(f"[->] audio seq={seq-1} frames+={sent} (total={total_frames})")
            await asyncio.sleep(CHUNK_MS / 1000.0)

        await ws.send(json.dumps({"type": END_TYPE}))
        print(f'[->] {{"type": "{END_TYPE}"}}')

async def run(wav_path: str, language: str):
    url = build_ws_url()
    print(f"ASR_WS_URL  = {url.split('api_key=')[0]}api_key=****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {CHUNK_MS} ms, MODE=typed-json\n")

    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        async def reader():
            try:
                async for msg in ws:
                    print("[<-]", msg if isinstance(msg, str) else f"<{len(msg)} bytes>")
                    if isinstance(msg, str):
                        try:
                            obj = json.loads(msg)
                            if obj.get("type") == "error":
                                raise RuntimeError(obj.get("message", "ASR error"))
                            if "transcript" in obj:
                                print("TRANSCRIPT:", obj["transcript"])
                            elif "result" in obj:
                                print("RESULT:", obj["result"])
                            elif "alternatives" in obj and obj["alternatives"]:
                                print("ALT:", obj["alternatives"][0].get("transcript") or obj["alternatives"][0].get("text"))
                            elif "text" in obj:
                                print("TEXT:", obj["text"])
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                print(f"[reader] stop: {e}")

        reader_task = asyncio.create_task(reader())
        try:
            await stream_file(ws, wav_path, language)
        finally:
            try:
                await asyncio.wait_for(reader_task, timeout=10.0)
            except asyncio.TimeoutError:
                print("[i] Done waiting for final messages.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_stream.py <wav_path> <language>")
        sys.exit(2)
    asyncio.run(run(sys.argv[1], sys.argv[2]))
