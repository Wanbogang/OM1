#!/usr/bin/env python3
# Stream ASR (root-JSON) — CHUNK PERTAMA menyertakan language & audio params.
# Python 3.10+, websockets>=10

import os, sys, json, base64, asyncio, wave, contextlib
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

async def reader(ws):
    try:
        async for m in ws:
            print("[<-]", m)
    except websockets.ConnectionClosedOK:
        pass
async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_stream_root_langfirst.py <wav_path> <language>")
        print("Example: python -u ws_asr_stream_root_langfirst.py tools/asr-eval/en/001.wav en-US")
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()

    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))
    tail_s   = float(os.getenv("ASR_READ_TAIL", "8"))

    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        sr = wf.getframerate(); ch = wf.getnchannels(); sw = wf.getsampwidth()
        assert sr == 16000 and ch == 1 and sw == 2, "WAV harus 16kHz, mono, 16-bit (LINEAR16)."

        frames_per_chunk = sr * chunk_ms // 1000

        print(f"ASR_WS_URL  = {url[:40]}****")
        print(f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit)")
        print(f"Language    = {language}")
        print(f"CHUNK_MS    = {chunk_ms} ms, MODE=root-json (lang in first chunk)\n")

        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
            rtask = asyncio.create_task(reader(ws))

            seq = 0
            first = True
            while True:
                buf = wf.readframes(frames_per_chunk)
                if not buf:
                    break
                b64 = base64.b64encode(buf).decode("ascii")

                if first:
                    msg = {
                        "audio": b64,
                        "language": language,
                        "sample_rate": 16000,
                        "channels": 1,
                        "encoding": "LINEAR16"
                    }
                    first = False
                else:
                    msg = {"audio": b64}

                await ws.send(json.dumps(msg))
                print(f"[->] audio#{seq} frames+={len(buf)//(2*1)}")
                seq += 1

                # pace near real-time supaya tidak timeout
                await asyncio.sleep(max(0.0, chunk_ms / 1000.0))

            end_msg = {"end": True}
            print("[->] end", end_msg)
            await ws.send(json.dumps(end_msg))

            await asyncio.sleep(tail_s)
            rtask.cancel()
            try:
                await rtask
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(main())
