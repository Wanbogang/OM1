# ws_asr_stream_root_plus.py
# Stream WS ASR: setiap pesan = root JSON berisi {audio, language, sample_rate, ...}
# Tanpa "type:start". Akhiri dengan beberapa flush {audio:""} dan {audio:"", end:true}.
# Python 3.10+, websockets>=10

import asyncio
import base64
import contextlib
import json
import os
import sys
import wave

import websockets

CHUNK_MS = int(os.getenv("ASR_CHUNK_MS", "30"))  # 20–40ms ok
READ_TAIL_SECS = float(os.getenv("ASR_READ_TAIL", "10"))  # nunggu hasil setelah kirim
DEBUG = os.getenv("ASR_DEBUG", "false").lower() in ("1", "true", "yes")


def ws_url() -> str:
    url = (os.getenv("ASR_WS_URL") or "").strip()
    if url:
        return url
    ep = (os.getenv("OM1_ASR_ENDPOINT") or "").strip()
    key = (os.getenv("OM_API_KEY") or "").strip()
    if not ep:
        raise RuntimeError(
            "OM1_ASR_ENDPOINT kosong (contoh: wss://api.openmind.org/api/core/google/asr)"
        )
    if not key:
        raise RuntimeError("OM_API_KEY kosong")
    sep = "&" if "?" in ep else "?"
    return f"{ep}{sep}api_key={key}"


@contextlib.contextmanager
def open_wav(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    wf = wave.open(path, "rb")
    try:
        yield wf
    finally:
        wf.close()


def wav_info(path: str):
    with open_wav(path) as wf:
        return wf.getframerate(), wf.getnchannels(), wf.getsampwidth(), wf.getnframes()


async def reader_task(ws):
    """Cetak semua pesan dari server; tangkap potensi transcript di berbagai format."""
    try:
        async for raw in ws:
            print("[<-]", raw)
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            # Beberapa kemungkinan format hasil:
            if isinstance(msg, dict):
                if msg.get("transcript"):  # {transcript: "..."}
                    print("TRANSCRIPT:", msg["transcript"])
                if msg.get("text"):
                    print("TEXT:", msg["text"])
                if "alternatives" in msg and msg["alternatives"]:
                    alt = msg["alternatives"][0]
                    t = alt.get("transcript") or alt.get("text")
                    if t:
                        print("ALT:", t)
                if "results" in msg:
                    for r in msg["results"]:
                        alts = r.get("alternatives") or []
                        if alts:
                            t = alts[0].get("transcript")
                            if t:
                                print(("FINAL:" if r.get("isFinal") else "PARTIAL:"), t)
                if msg.get("type") == "error":
                    # Naikkan sebagai exception supaya program berhenti rapi
                    raise RuntimeError(msg.get("message", "ASR error"))
    except Exception as e:
        print("[reader] stop:", e)


async def stream(ws, wav_path: str, language: str):
    """Kirim chunk root JSON; setiap pesan menyertakan audio + meta minimal."""
    with open_wav(wav_path) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        if (sr, ch, sw) != (16000, 1, 2):
            print(
                f"[!] Warning: ideal 16kHz/mono/16-bit. Sekarang: {sr}Hz, ch={ch}, {8 * sw}bit"
            )

        bpf = ch * sw  # bytes per frame
        bytes_per_ms = int(sr * bpf / 1000)
        chunk_bytes = max(bytes_per_ms * CHUNK_MS, 1)

        seq = 0
        total = 0
        while True:
            buf = wf.readframes(chunk_bytes // bpf)
            if not buf:
                break

            b64 = base64.b64encode(buf).decode("ascii")
            msg = {
                "audio": b64,  # <- WAJIB: root 'audio'
                # meta minimal ikut setiap pesan (beberapa server perlu ini di tiap frame)
                "language": language,
                "sample_rate": sr,
                "channels": ch,
                "encoding": "LINEAR16",
                # varian nama field (server tertentu sensitif)
                "languageCode": language,
                "sampleRateHertz": sr,
                "contentType": "audio/pcm;bit=16;rate=16000;channels=1",
                "seq": seq,
                "frame_ms": CHUNK_MS,
            }
            await ws.send(json.dumps(msg))
            sent = len(buf) // bpf
            total += sent
            if DEBUG:
                print(f"[->] audio#{seq} frames+={sent} (total={total})")
            seq += 1
            await asyncio.sleep(CHUNK_MS / 1000.0)

    # flush akhiran (jangan pakai "type", cukup root fields)
    for i, payload in enumerate(
        (
            {"audio": ""},  # kosongkan menandai akhir buffer
            {"audio": "", "end": True},  # end flag
            {"audio": ""},  # jaga-jaga
        ),
        start=1,
    ):
        if DEBUG:
            print(f"[->] flush#{i}", payload)
        try:
            await ws.send(json.dumps(payload))
            await asyncio.sleep(0.25)
        except Exception as e:
            if DEBUG:
                print(f"[flush#{i}] err:", e)


async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_stream_root_plus.py <wav_path> <language>")
        print(
            "Example: python -u ws_asr_stream_root_plus.py tools/asr-eval/en/001.wav en-US"
        )
        sys.exit(2)

    wav_path = sys.argv[1]
    language = sys.argv[2]
    url = ws_url()
    sr, ch, sw, nframes = wav_info(wav_path)

    safe = url.split("api_key=")[0] + "api_key=****"
    print(f"ASR_WS_URL  = {safe}")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {CHUNK_MS} ms, MODE=json_root_plus\n")

    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:
        r = asyncio.create_task(reader_task(ws))
        await stream(ws, wav_path, language)
        await asyncio.sleep(READ_TAIL_SECS)
        try:
            await asyncio.wait_for(r, timeout=1.0)
        except asyncio.TimeoutError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
