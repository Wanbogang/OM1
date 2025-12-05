import asyncio
import base64
import json
import os
import uuid
import wave

import websockets

# ====== KONFIG ======
WAV = "tools/asr-eval/en/001.wav"
LANG = "en-US"
RATE = 16000
CHANNELS = 1
BITS = 16
CHUNK_MS = 20  # ukuran potong; kirim secepatnya (tanpa sleep)
RECV_TIMEOUT = 30  # waktu nunggu balasan
# ====================


def assert_wav_ok(path):
    with wave.open(path, "rb") as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        if (sr, ch, sw * 8) != (RATE, CHANNELS, BITS):
            raise SystemExit(
                f"WAV must be {RATE}Hz/{CHANNELS}ch/{BITS}bit; got {sr}Hz/{ch}ch/{sw * 8}bit"
            )


def b64(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")


def build_url():
    base = os.getenv("ASR_WS_URL") or (
        os.getenv("OM1_ASR_ENDPOINT", "wss://api.openmind.org/api/core/google/asr")
        + "?api_key="
        + os.getenv("OM_API_KEY", "")
    )
    # ikutkan param di query (aman kalau diabaikan server)
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}encoding=LINEAR16&rate={RATE}&languageCode={LANG}"


async def main():
    url = build_url()
    print("ASR_WS_URL =", url.split("api_key=")[0] + "api_key=****")
    assert_wav_ok(WAV)

    request_id = "req-" + uuid.uuid4().hex[:8]

    async with websockets.connect(
        url, max_size=None, ping_interval=20, ping_timeout=20
    ) as ws:
        w = wave.open(WAV, "rb")
        frames_per_chunk = max(1, int(RATE * CHUNK_MS / 1000))

        # === Frame 1: config + audio + seq ===
        first_pcm = w.readframes(frames_per_chunk)
        if not first_pcm:
            # file kosong → kirim frame minimum
            first_pcm = b"\x00" * int(RATE * CHANNELS * (BITS // 8) * CHUNK_MS / 1000)

        first = {
            "requestId": request_id,
            "seq": 1,
            "config": {
                "languageCode": LANG,
                "encoding": "LINEAR16",
                "sampleRateHertz": RATE,
                "channels": CHANNELS,
                "bitsPerSample": BITS,
            },
            "audio": b64(first_pcm),
        }
        await ws.send(json.dumps(first))

        # === Frames berikutnya: selalu ada 'audio' + seq naik (tanpa sleep) ===
        seq = 2
        last_b64 = None
        while True:
            raw = w.readframes(frames_per_chunk)
            if not raw:
                break
            last_b64 = b64(raw)
            await ws.send(
                json.dumps({"requestId": request_id, "seq": seq, "audio": last_b64})
            )
            seq += 1

        # === Frame terakhir: tetap ada 'audio' + end ===
        if last_b64 is None:
            last_b64 = ""  # aman: tetap ada key 'audio'
        await ws.send(
            json.dumps(
                {"requestId": request_id, "seq": seq, "audio": last_b64, "end": True}
            )
        )

        # === Terima hasil ===
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=RECV_TIMEOUT)
                print("[<-]", msg)
        except asyncio.TimeoutError:
            pass
        finally:
            w.close()


if __name__ == "__main__":
    asyncio.run(main())
