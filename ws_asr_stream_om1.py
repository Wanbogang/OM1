import asyncio
import json
import os
import wave

import websockets

# ====== KONFIG ======
WAV = "tools/asr-eval/en/001.wav"
LANG = "en-US"
RATE = 16000
CHANNELS = 1
BITS = 16
# Kirim super-cepat (tanpa sleep) supaya tidak timeout
CHUNK_MS = 5  # ukuran potong (~5ms)
RECV_TIMEOUT = 30  # waktu nunggu balasan
# ====================


def build_url():
    base = os.getenv("ASR_WS_URL") or (
        os.getenv("OM1_ASR_ENDPOINT", "wss://api.openmind.org/api/core/google/asr")
        + "?api_key="
        + os.getenv("OM_API_KEY", "")
    )
    # kalau gateway baca param dari query, ikutkan juga (tak merugikan)
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}encoding=LINEAR16&rate={RATE}&languageCode={LANG}"


def assert_wav_16k_mono_16bit(path):
    with wave.open(path, "rb") as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        if sr != RATE or ch != CHANNELS or sw * 8 != BITS:
            raise SystemExit(
                f"WAV mismatch. Need {RATE}Hz/{CHANNELS}ch/{BITS}bit, got {sr}Hz/{ch}ch/{sw * 8}bit"
            )


async def main():
    url = build_url()
    print("ASR_WS_URL =", url.split("api_key=")[0] + "api_key=****")
    assert_wav_16k_mono_16bit(WAV)

    async with websockets.connect(
        url, max_size=None, ping_interval=20, ping_timeout=20
    ) as ws:
        # 1) HANDSHAKE TEKS MINIMAL (TANPA audio, TANPA type/start)
        config = {
            "config": {
                "languageCode": LANG,
                "encoding": "LINEAR16",
                "sampleRateHertz": RATE,
                "channels": CHANNELS,
                "bitsPerSample": BITS,
            }
        }
        await ws.send(json.dumps(config))

        # 2) STREAM AUDIO **BINER** SUPER CEPAT (tanpa sleep)
        with wave.open(WAV, "rb") as w:
            frames_per_chunk = max(1, int(w.getframerate() * CHUNK_MS / 1000))
            while True:
                raw = w.readframes(frames_per_chunk)
                if not raw:
                    break
                await ws.send(raw)  # <— penting: FRAME BINER, bukan JSON

        # 3) TUNGGU BALASAN
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=RECV_TIMEOUT)
                print("[<-]", msg)
        except asyncio.TimeoutError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
