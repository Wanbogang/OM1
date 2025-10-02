#!/usr/bin/env python3
# WebSocket ASR client — "typed start" + root-JSON audio + "typed end".
# Tiap pesan WAJIB punya field "audio" (walau kosong).
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
    except websockets.ConnectionClosed:
        pass

async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_handshake_root.py <wav_path> <language>")
        print("Example: python -u ws_asr_handshake_root.py tools/asr-eval/en/001.wav en-US")
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()

    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))
    tail_s   = float(os.getenv("ASR_READ_TAIL", "10"))

    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        sr = wf.getframerate(); ch = wf.getnchannels(); sw = wf.getsampwidth()
        assert sr == 16000 and ch == 1 and sw == 2, "WAV harus 16kHz, mono, 16-bit (LINEAR16)."
        frames_per_chunk = sr * chunk_ms // 1000

        print(f"ASR_WS_URL  = {url[:40]}****")
        print(f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit)")
        print(f"Language    = {language}")
        print(f"CHUNK_MS    = {chunk_ms} ms, MODE=typed-start + root-audio + typed-end\n")

        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
            rtask = asyncio.create_task(reader(ws))

            # 1) HANDSHAKE: typed "start" (tetap sertakan audio kosong!)
            start_msg = {
                "type": "start",
                "language": language,
                "sample_rate": 16000,
                "channels": 1,
                "format": "s16le",
                "encoding": "LINEAR16",
                "contentType": "audio/pcm;bit=16;rate=16000;channels=1",
                "frame_ms": chunk_ms,
                "audio": ""   # penting: tetap ada field audio
            }
            print("[->] start", {k:v for k,v in start_msg.items() if k!="audio"})
            await ws.send(json.dumps(start_msg))

            # 2) STREAM: root JSON audio
            seq = 0
            meta_repeats = 2  # dua chunk pertama kirim metadata tambahan
            while True:
                buf = wf.readframes(frames_per_chunk)
                if not buf:
                    break
                b64 = base64.b64encode(buf).decode("ascii")

                if meta_repeats > 0:
                    msg = {
                        "audio": b64,
                        "language": language,
                        "sample_rate": 16000,
                        "channels": 1,
                        "encoding": "LINEAR16"
                    }
                    meta_repeats -= 1
                else:
                    msg = {"audio": b64}

                await ws.send(json.dumps(msg))
                print(f"[->] audio seq={seq} frames+={len(buf)//2}")
                seq += 1
                await asyncio.sleep(max(0.0, chunk_ms/1000.0))  # pacing real-time

            # 3) FLUSH kosong (root JSON)
            flush_msg = {"audio": ""}
            print("[->] flush", flush_msg)
            await ws.send(json.dumps(flush_msg))

            # 4) END (typed) — tetap sertakan audio kosong
            end_msg = {"type": "end", "audio": ""}
            print("[->] end", {k:v for k,v in end_msg.items() if k!="audio"})
            await ws.send(json.dumps(end_msg))

            # beri waktu server mengirim hasil
            await asyncio.sleep(tail_s)

            await ws.close()
            rtask.cancel()
            try:
                await rtask
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(main())
