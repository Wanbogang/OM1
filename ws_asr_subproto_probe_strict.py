import asyncio
import base64
import json
import os
import wave

import websockets

URL = os.getenv("ASR_WS_URL") or (
    os.getenv("OM1_ASR_ENDPOINT", "wss://api.openmind.org/api/core/google/asr")
    + "?api_key="
    + os.getenv("OM_API_KEY", "")
)
WAV = "tools/asr-eval/en/001.wav"
SUBPROTOS = [
    None,
    "om1-asr",
    "asr",
    "google-asr",
    "speech",
    "asr.v1",
    "om1.v1",
    "v1",
    "json",
]


def open_wav(p):
    w = wave.open(p, "rb")
    sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    assert (sr, ch, sw) == (
        16000,
        1,
        2,
    ), f"Need 16k/mono/16-bit, got {sr}/{ch}/{sw * 8}"
    return w, sr


def b64(x):
    return base64.b64encode(x).decode("ascii")


def is_result(msg: str) -> bool:
    m = msg.lower()
    if "error" in m:
        return False
    return any(
        k in m
        for k in [
            "asr_reply",
            "result",
            "results",
            "final",
            "transcript",
            "alternatives",
        ]
    )


async def try_one(proto):
    label = proto or "(none)"
    print(f"\n[PROTO] {label}")
    try:
        async with websockets.connect(
            URL, max_size=None, subprotocols=[proto] if proto else None
        ) as ws:
            w, sr = open_wav(WAV)
            frames = w.readframes(w.getnframes())
            w.close()
            payload = {
                "config": {
                    "languageCode": "en-US",
                    "encoding": "LINEAR16",
                    "sampleRateHertz": sr,
                    "channels": 1,
                    "bitsPerSample": 16,
                },
                "audio": b64(frames),
            }
            await ws.send(json.dumps(payload))
            try:
                # baca beberapa balasan
                for _ in range(10):
                    msg = await asyncio.wait_for(ws.recv(), timeout=10)
                    print("[<-]", msg)
                    if is_result(msg):
                        return True
                return False
            except asyncio.TimeoutError:
                return False
    except Exception as e:
        print("[ERR]", type(e).__name__, e)
        return False


async def main():
    for proto in SUBPROTOS:
        if await try_one(proto):
            print(f"\n[✓] REAL WORKS with subprotocol: {proto or '(none)'}\n")
            return
    print(
        "\n[!] No subprotocol produced a real ASR result. All paths now point to needing the exact server schema.\n"
    )


asyncio.run(main())
