#!/usr/bin/env python3
# WS ASR client: "typed start" -> wait ready -> stream root-JSON audio -> "typed end"
# websockets>=10, Python 3.10+

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

class ReadyWatcher:
    def __init__(self):
        self.ready = asyncio.Event()
        self.last_msg = None
    def feed(self, raw: str):
        self.last_msg = raw
        try:
            obj = json.loads(raw)
        except Exception:
            return
        t = obj.get("type", "")
        # Anggap 'connection' sebagai tanda siap (beberapa gateway pakai 'ready')
        if t in ("connection", "ready"):
            self.ready.set()

async def reader(ws, watcher: ReadyWatcher):
    try:
        async for m in ws:
            print("[<-]", m)
            watcher.feed(m)
    except websockets.ConnectionClosed:
        pass

async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_waitready_root.py <wav_path> <language>")
        print("Example: python -u ws_asr_waitready_root.py tools/asr-eval/en/001.wav en-US")
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()

    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))
    tail_s   = float(os.getenv("ASR_READ_TAIL", "10"))
    wait_ready_timeout = float(os.getenv("ASR_WAIT_READY", "2.0"))  # detik

    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        sr = wf.getframerate(); ch = wf.getnchannels(); sw = wf.getsampwidth()
        if not (sr == 16000 and ch == 1 and sw == 2):
            raise SystemExit("WAV harus LINEAR16: 16kHz, mono, 16-bit")

        frames_per_chunk = sr * chunk_ms // 1000
        print(f"ASR_WS_URL  = {url[:40]}****")
        print(f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit)")
        print(f"Language    = {language}")
        print(f"CHUNK_MS    = {chunk_ms} ms, MODE=typed-start + wait-ready + root-audio + typed-end\n")

        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
            watcher = ReadyWatcher()
            rtask = asyncio.create_task(reader(ws, watcher))

            # 1) HANDSHAKE (typed) — audio kosong tetap ada
            start_msg = {
                "type": "start",
                "language": language,
                "sample_rate": 16000,
                "channels": 1,
                "format": "s16le",
                "encoding": "LINEAR16",
                "contentType": "audio/pcm;bit=16;rate=16000;channels=1",
                "frame_ms": chunk_ms,
                "audio": ""   # penting
            }
            print("[->] start", {k:v for k,v in start_msg.items() if k!="audio"})
            await ws.send(json.dumps(start_msg))

            # 2) TUNGGU "ready/connection" sebelum kirim audio
            try:
                await asyncio.wait_for(watcher.ready.wait(), timeout=wait_ready_timeout)
            except asyncio.TimeoutError:
                print(f"[i] Tidak ada 'connection/ready' dalam {wait_ready_timeout}s — lanjut tetap kirim (fallback).")

            # 3) STREAM: root JSON audio (pertama 2 chunk sertakan meta)
            seq = 0
            meta_left = 2
            t0 = time.monotonic()
            period = chunk_ms / 1000.0

            while True:
                buf = wf.readframes(frames_per_chunk)
                if not buf:
                    break
                b64 = base64.b64encode(buf).decode("ascii")

                if meta_left > 0:
                    msg = {
                        "audio": b64,
                        "language": language,
                        "sample_rate": 16000,
                        "channels": 1,
                        "encoding": "LINEAR16",
                    }
                    meta_left -= 1
                else:
                    msg = {"audio": b64}

                await ws.send(json.dumps(msg))
                print(f"[->] audio seq={seq} frames+={len(buf)//2}")
                seq += 1

                # pace real-time pakai jadwal (kurangin drift)
                next_t = t0 + seq * period
                sleep_s = max(0.0, next_t - time.monotonic())
                if sleep_s:
                    await asyncio.sleep(sleep_s)

            # 4) FLUSH kosong
            flush_msg = {"audio": ""}
            print("[->] flush", flush_msg)
            await ws.send(json.dumps(flush_msg))

            # 5) END (typed) — dengan audio kosong
            end_msg = {"type": "end", "audio": ""}
            print("[->] end", {k:v for k,v in end_msg.items() if k!="audio"})
            await ws.send(json.dumps(end_msg))

            # beri waktu server kirim hasil
            await asyncio.sleep(tail_s)

            await ws.close()
            rtask.cancel()
            try:
                await rtask
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(main())
