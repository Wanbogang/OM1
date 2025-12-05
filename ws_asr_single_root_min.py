#!/usr/bin/env python3
import asyncio
import base64
import json
import os
import sys
import wave

import websockets


def build_ws_url():
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    key = os.getenv("OM_API_KEY", "").strip()
    if not ep:
        raise SystemExit(
            "OM1_ASR_ENDPOINT kosong (mis. wss://api.openmind.org/api/core/google/asr)"
        )
    if not key:
        raise SystemExit("OM_API_KEY kosong")
    sep = "&" if "?" in ep else "?"
    return f"{ep}{sep}api_key={key}"


def load_wav_b64(path: str) -> str:
    if not os.path.exists(path):
        raise SystemExit(f"File tidak ditemukan: {path}")
    with wave.open(path, "rb") as wf:
        sr, ch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
        if not (sr == 16000 and ch == 1 and sw == 2):
            raise SystemExit("WAV harus LINEAR16: 16 kHz, mono, 16-bit.")
        raw = wf.readframes(wf.getnframes())
    return base64.b64encode(raw).decode("ascii")


async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_single_root_min.py <wav_path> <language>")
        print(
            "Example: python -u ws_asr_single_root_min.py tools/asr-eval/en/001.wav en-US"
        )
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()
    read_tail = float(os.getenv("ASR_READ_TAIL", "10"))

    audio_b64 = load_wav_b64(wav_path)
    payload = {"audio": audio_b64, "language": language}  # <— kunci: root JSON tunggal

    print(f"ASR_WS_URL  = {url[:40]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print("Mode        = SINGLE root JSON {audio, language}\n")

    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:
        # kirim satu pesan JSON saja
        await ws.send(json.dumps(payload))
        print("[->] sent single root JSON (audio+language)")

        # baca balasan hingga server close atau timeout pasif
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=read_tail)
            except asyncio.TimeoutError:
                print("[i] no more messages (tail timeout).")
                break
            except websockets.ConnectionClosedOK:
                print("[i] server closed normally.")
                break
            except websockets.ConnectionClosedError as e:
                print(f"[i] closed with error: {e}")
                break
            else:
                print("[<-]", msg)


if __name__ == "__main__":
    asyncio.run(main())
