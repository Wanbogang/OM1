#!/usr/bin/env python3
# WS ASR client — typed JSON only:
#  start -> wait "connection/ready" -> {type:audio, audio:<b64>} ... -> {type:end}
# Requires: Python 3.10+, websockets>=10

import os, sys, json, base64, asyncio, wave, contextlib, time
import websockets

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep  = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    key = os.getenv("OM_API_KEY", "").strip()
    if not ep or not key:
        raise SystemExit("Set OM1_ASR_ENDPOINT dan OM_API_KEY dulu.")
    sep = "&" if "?" in ep else "?"
    return f"{ep}{sep}api_key={key}"

class ReadyFlag:
    def __init__(self):
        self.ev = asyncio.Event()
        self.last = None
    def feed(self, s: str):
        self.last = s
        try:
            obj = json.loads(s)
        except Exception:
            return
        if obj.get("type") in ("connection", "ready"):
            self.ev.set()

async def reader(ws, flag: ReadyFlag):
    try:
        async for m in ws:
            print("[<-]", m)
            flag.feed(m)
    except websockets.ConnectionClosed:
        pass

async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_waitready_typed.py <wav_path> <language>")
        print("Example: python -u ws_asr_waitready_typed.py tools/asr-eval/en/001.wav en-US")
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()

    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))     # 20–40ms oke
    tail_s   = float(os.getenv("ASR_READ_TAIL", "10"))  # waktu tunggu hasil
    wait_ready_timeout = float(os.getenv("ASR_WAIT_READY", "2.0"))

    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        sr = wf.getframerate(); ch = wf.getnchannels(); sw = wf.getsampwidth()
        if not (sr == 16000 and ch == 1 and sw == 2):
            raise SystemExit("WAV harus LINEAR16: 16kHz, mono, 16-bit")

        frames_per_chunk = sr * chunk_ms // 1000
        print(f"ASR_WS_URL  = {url[:40]}****")
        print(f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit)")
        print(f"Language    = {language}")
        print(f"CHUNK_MS    = {chunk_ms} ms, MODE=typed JSON only\n")

        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
            flag = ReadyFlag()
            rtask = asyncio.create_task(reader(ws, flag))

            # 1) START (typed) — audio tidak dikirim di sini
            start_msg = {
                "type": "start",
                "language": language,
                "sample_rate": 16000,
                "channels": 1,
                "format": "s16le",
                "encoding": "LINEAR16",
                "contentType": "audio/pcm;bit=16;rate=16000;channels=1",
                "frame_ms": chunk_ms
            }
            print("[->] start", start_msg)
            await ws.send(json.dumps(start_msg))

            # 2) tunggu server siap
            try:
                await asyncio.wait_for(flag.ev.wait(), timeout=wait_ready_timeout)
            except asyncio.TimeoutError:
                print(f"[i] Tidak ada 'connection/ready' dalam {wait_ready_timeout}s — lanjut kirim audio (fallback).")

            # 3) STREAM: strictly typed audio messages
            seq = 0
            t0 = time.monotonic()
            period = chunk_ms / 1000.0

            while True:
                buf = wf.readframes(frames_per_chunk)
                if not buf:
                    break
                b64 = base64.b64encode(buf).decode("ascii")
                msg = {"type": "audio", "audio": b64}
                await ws.send(json.dumps(msg))
                print(f"[->] audio seq={seq} frames+={len(buf)//2}")
                seq += 1

                # pace real-time
                next_t = t0 + seq * period
                sleep_s = max(0.0, next_t - time.monotonic())
                if sleep_s:
                    await asyncio.sleep(sleep_s)

            # 4) END (typed)
            end_msg = {"type": "end"}
            print("[->] end", end_msg)
            await ws.send(json.dumps(end_msg))

            # 5) beri waktu server kirim hasil
            await asyncio.sleep(tail_s)

            await ws.close()
            rtask.cancel()
            try:
                await rtask
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(main())
