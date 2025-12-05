import asyncio
import base64
import json
import os
import uuid
import wave

import websockets

URL = os.getenv("ASR_WS_URL") or (
    os.getenv("OM1_ASR_ENDPOINT", "wss://api.openmind.org/api/core/google/asr")
    + "?api_key="
    + os.getenv("OM_API_KEY", "")
)
WAV = "tools/asr-eval/en/001.wav"
CHUNK_MS = 10  # streaming cepat (hindari timeout)
RECV_TIMEOUT = 20


def open_wav(path):
    w = wave.open(path, "rb")
    sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    assert (
        sr == 16000 and ch == 1 and sw == 2
    ), f"WAV must be 16kHz/mono/16-bit; got {sr}Hz/{ch}ch/{sw * 8}bit"
    return w, sr


def pcm_chunks(w, sr, chunk_ms):
    frames_per_chunk = max(1, int(sr * chunk_ms / 1000))
    while True:
        raw = w.readframes(frames_per_chunk)
        if not raw:
            break
        yield raw


def b64(x):
    return base64.b64encode(x).decode("ascii")


def looks_good(msg: str) -> bool:
    msg_low = msg.lower()
    return any(
        k in msg_low
        for k in [
            "asr_reply",
            "transcript",
            "result",
            "results",
            "final",
            "partial",
            "alternatives",
        ]
    )


def is_format_error(msg: str) -> bool:
    msg_low = msg.lower()
    return ("invalid message format" in msg_low) or ("'audio' field missing" in msg_low)


def is_timeout(msg: str) -> bool:
    return "audio timeout" in msg.lower()


def variants(sr):
    rid = "probe-" + uuid.uuid4().hex[:8]
    cfg = {
        "languageCode": "en-US",
        "encoding": "LINEAR16",
        "sampleRateHertz": sr,
        "channels": 1,
        "bitsPerSample": 16,
    }
    return [
        # 1) config+audio (LINEAR16) — audio = PCM b64
        (
            "config+audio (LINEAR16)",
            lambda first: {"config": cfg, "audio": b64(first)},
            lambda raw, seq: {"audio": b64(raw)},
            lambda last_seq: {"audio": "", "end": True},
        ),
        # 2) audio+rate (docs-ish)
        (
            "audio+rate",
            lambda first: {"audio": b64(first), "rate": sr},
            lambda raw, seq: {"audio": b64(raw)},
            lambda last_seq: {"audio": "", "end": True},
        ),
        # 3) root start+audio+config
        (
            "root start+audio+config",
            lambda first: {"start": True, "audio": b64(first), "config": cfg},
            lambda raw, seq: {"audio": b64(raw)},
            lambda last_seq: {"end": True, "stop": True, "audio": ""},
        ),
        # 4) type:start + audio
        (
            "type:start + audio",
            lambda first: {
                "type": "start",
                "requestId": rid,
                "audio": b64(first),
                "config": cfg,
            },
            lambda raw, seq: {"type": "audio", "seq": seq, "audio": b64(raw)},
            lambda last_seq: {
                "type": "end",
                "stop": True,
                "seq": last_seq,
                "audio": "",
            },
        ),
        # 5) type:start + chunk
        (
            "type:start + chunk",
            lambda first: {
                "type": "start",
                "requestId": rid,
                "chunk": b64(first),
                "config": cfg,
            },
            lambda raw, seq: {"type": "audio", "seq": seq, "chunk": b64(raw)},
            lambda last_seq: {
                "type": "end",
                "stop": True,
                "seq": last_seq,
                "chunk": "",
            },
        ),
        # 6) type:start + data
        (
            "type:start + data",
            lambda first: {
                "type": "start",
                "requestId": rid,
                "data": b64(first),
                "config": cfg,
            },
            lambda raw, seq: {"type": "audio", "seq": seq, "data": b64(raw)},
            lambda last_seq: {"type": "end", "stop": True, "seq": last_seq, "data": ""},
        ),
        # 7) type:start + audioContent
        (
            "type:start + audioContent",
            lambda first: {
                "type": "start",
                "requestId": rid,
                "audioContent": b64(first),
                "config": cfg,
            },
            lambda raw, seq: {"type": "audio", "seq": seq, "audioContent": b64(raw)},
            lambda last_seq: {
                "type": "end",
                "stop": True,
                "seq": last_seq,
                "audioContent": "",
            },
        ),
        # 8) type:start + audio_base64
        (
            "type:start + audio_base64",
            lambda first: {
                "type": "start",
                "requestId": rid,
                "audio_base64": b64(first),
                "config": cfg,
            },
            lambda raw, seq: {"type": "audio", "seq": seq, "audio_base64": b64(raw)},
            lambda last_seq: {
                "type": "end",
                "stop": True,
                "seq": last_seq,
                "audio_base64": "",
            },
        ),
        # 9) root start+config+audio
        (
            "root start+config+audio",
            lambda first: {"start": True, "config": cfg, "audio": b64(first)},
            lambda raw, seq: {"audio": b64(raw)},
            lambda last_seq: {"end": True, "stop": True, "audio": ""},
        ),
        # 10) google-ish config+audio
        (
            "google-ish config+audio",
            lambda first: {"config": cfg, "audio": b64(first)},
            lambda raw, seq: {"audio": b64(raw)},
            lambda last_seq: {"audio": "", "stop": True},
        ),
        # 11) type:start minimal + audio
        (
            "type:start minimal + audio",
            lambda first: {"type": "start", "audio": b64(first), "config": cfg},
            lambda raw, seq: {"type": "audio", "seq": seq, "audio": b64(raw)},
            lambda last_seq: {
                "type": "end",
                "stop": True,
                "seq": last_seq,
                "audio": "",
            },
        ),
        # 12) message:start + audio
        (
            "message:start + audio",
            lambda first: {"message": "start", "audio": b64(first), "config": cfg},
            lambda raw, seq: {"audio": b64(raw)},
            lambda last_seq: {"message": "end", "stop": True, "audio": ""},
        ),
    ]


async def try_one(name, build_first, build_next, build_last, sr):
    print(f"\n[TRY] {name}")
    async with websockets.connect(URL, max_size=None) as ws:
        w, _sr = open_wav(WAV)
        gen = pcm_chunks(w, sr, CHUNK_MS)
        first = next(gen, b"")
        await ws.send(json.dumps(build_first(first)))
        seq = 2
        for raw in gen:
            await ws.send(json.dumps(build_next(raw, seq)))
            seq += 1
        await ws.send(json.dumps(build_last(seq)))
        good = False
        try:
            for _ in range(6):
                msg = await asyncio.wait_for(ws.recv(), timeout=RECV_TIMEOUT)
                print("[<-]", msg)
                if looks_good(msg):
                    good = True
                    break
                if is_format_error(msg):
                    return False
                if is_timeout(msg):
                    break
        except asyncio.TimeoutError:
            pass
        return good


async def main():
    print("ASR_WS_URL =", URL.split("api_key=")[0] + "api_key=****")
    w, sr = open_wav(WAV)
    w.close()
    for name, b1, bn, bl in variants(sr):
        try:
            ok = await try_one(name, b1, bn, bl, sr)
        except websockets.exceptions.ConnectionClosedOK as e:
            print(f"[CLOSE] {name}: {e}")
            ok = False
        except Exception as e:
            print(f"[ERR] {name}: {e.__class__.__name__}: {e}")
            ok = False
        if ok:
            print(f"\n[✓] SCHEMA WORKS: {name}\n")
            return
    print(
        "\n[!] All schemas failed or timed out. Need one sample payload from the server or their official client to finish this.\n"
    )


asyncio.run(main())
