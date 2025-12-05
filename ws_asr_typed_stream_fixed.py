#!/usr/bin/env python3
# Minimal typed-JSON ASR client (wajib kirim {"type":"audio","audio":"<base64>"})
# Python 3.10+, websockets>=10

import asyncio
import base64
import contextlib
import json
import os
import sys
import wave

import websockets


def build_url() -> str:
    # Pakai ASR_WS_URL kalau ada, kalau tidak rakit dari OM1_ASR_ENDPOINT + OM_API_KEY
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    key = os.getenv("OM_API_KEY", "").strip()
    if not ep or not key:
        raise SystemExit("Env OM1_ASR_ENDPOINT / OM_API_KEY kosong.")
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
        print("Usage: python -u ws_asr_typed_stream_fixed.py <wav_path> <language>")
        print(
            "Example: python -u ws_asr_typed_stream_fixed.py tools/asr-eval/en/001.wav en-US"
        )
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_url()
    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))
    tail_s = float(os.getenv("ASR_READ_TAIL", "8"))

    with contextlib.closing(wave.open(wav_path, "rb")) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        assert (
            sr == 16000 and ch == 1 and sw == 2
        ), "WAV harus 16kHz mono 16-bit (LINEAR16)."
        frames_per_chunk = sr * chunk_ms // 1000

        print(f"ASR_WS_URL  = {url[:40]}****")
        print(f"WAV         = {wav_path}")
        print(f"Language    = {language}")
        print(f"CHUNK_MS    = {chunk_ms} ms, MODE=typed-json\n")

        async with websockets.connect(
            url, ping_interval=20, ping_timeout=20, max_size=None
        ) as ws:
            rtask = asyncio.create_task(reader(ws))

            start = {
                "type": "start",
                "language": language,
                "sample_rate": sr,
                "channels": ch,
                "format": "s16le",
                "encoding": "LINEAR16",
                "contentType": f"audio/pcm;bit=16;rate={sr};channels={ch}",
                "frame_ms": chunk_ms,
            }
            print("[->] start", start)
            await ws.send(json.dumps(start))
            seq = 0
            while True:
                buf = wf.readframes(frames_per_chunk)
                if not buf:
                    break
                b64 = base64.b64encode(buf).decode("ascii")
                # PENTING: wajib field 'audio' (bukan 'data', 'audioContent', dll)
                msg = {"type": "audio", "audio": b64}
                await ws.send(json.dumps(msg))
                print(
                    f"[->] audio seq={seq} frames+={len(buf) // (2 * ch)} (total ~{(seq + 1) * frames_per_chunk})"
                )
                seq += 1
                # Kirim mendekati real-time agar tidak timeout
                await asyncio.sleep(max(0.0, chunk_ms / 1000.0))

            end = {"type": "end"}
            print("[->] end", end)
            await ws.send(json.dumps(end))

            # beri waktu server kirim hasil
            await asyncio.sleep(tail_s)
            rtask.cancel()
            try:
                await rtask
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    asyncio.run(main())
