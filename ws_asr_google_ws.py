# ws_asr_google_ws.py
# WebSocket ASR client (Google-style): kirim config lalu audioContent base64 per chunk.
# Fallback: di setiap chunk ikut kirim "audio" & "data" (dual/triple-key) biar kompatibel.
# Bisa juga mode SINGLE message (gabung semua audio dalam satu pesan) via env ASR_SINGLE=1.

import asyncio
import base64
import contextlib
import json
import os
import sys
import wave

import websockets

# ---------- Env & defaults ----------
CHUNK_MS = int(os.getenv("ASR_CHUNK_MS", "30"))  # 20–40 ms bagus, mulai 30
READ_TAIL_SECS = float(os.getenv("ASR_READ_TAIL", "8"))  # nunggu hasil
DEBUG = os.getenv("ASR_DEBUG", "false").lower() in ("1", "true", "yes")
SINGLE = os.getenv("ASR_SINGLE", "0").lower() in ("1", "true", "yes")  # sekali kirim


def build_ws_url() -> str:
    # Prioritas: ASR_WS_URL; kalau kosong pakai OM1_ASR_ENDPOINT + OM_API_KEY
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


async def send_config(ws, language: str, sr: int, ch: int, sw: int):
    # Kirim “config” ala Google STT
    cfg = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": sr,
            "languageCode": language,
            "audioChannelCount": ch,
            "enableAutomaticPunctuation": True,
        }
    }
    if DEBUG:
        print("[->] config", cfg)
    await ws.send(json.dumps(cfg))


async def stream_chunks(ws, wav_path: str, language: str):
    with open_wav(wav_path) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()  # bytes/sample
        if (sr, ch, sw) != (16000, 1, 2):
            print(
                f"[!] Warning: ideal 16kHz/mono/16-bit. Sekarang: {sr}Hz, ch={ch}, {8 * sw}bit"
            )
        bpf = ch * sw
        bytes_per_ms = int(sr * bpf / 1000)
        chunk_bytes = max(bytes_per_ms * CHUNK_MS, 1)

        seq = 0
        total = 0
        while True:
            buf = wf.readframes(chunk_bytes // bpf)
            if not buf:
                break
            b64 = base64.b64encode(buf).decode("ascii")
            # Kirim triple-key agar lolos variasi server
            msg = {
                "audioContent": b64,
                "audio": b64,
                "data": b64,
                # beberapa server suka simpan meta di chunk
                "languageCode": language,
                "language": language,
                "sampleRateHertz": sr,
                "sample_rate": sr,
                "channels": ch,
                "encoding": "LINEAR16",
                "seq": seq,
                "frame_ms": CHUNK_MS,
            }
            await ws.send(json.dumps(msg))
            sent_frames = len(buf) // bpf
            total += sent_frames
            print(f"[->] audio#{seq} frames+={sent_frames} (total={total})")
            seq += 1
            await asyncio.sleep(CHUNK_MS / 1000.0)

    # finalize (variasi aman)
    for i, payload in enumerate(
        (
            {"audioContent": ""},
            {"audio": ""},
            {"data": ""},
            {"type": "end"},
            {"type": "stop"},
        ),
        start=1,
    ):
        try:
            if DEBUG:
                print(f"[->] flush#{i}", payload)
            await ws.send(json.dumps(payload))
            await asyncio.sleep(0.3)
        except Exception as e:
            if DEBUG:
                print(f"[flush#{i}] err:", e)


async def send_single(ws, wav_path: str, language: str):
    with open_wav(wav_path) as wf:
        pcm = wf.readframes(wf.getnframes())
        sr, ch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
    if (sr, ch, sw) != (16000, 1, 2):
        print(
            f"[!] Warning: ideal 16kHz/mono/16-bit. Sekarang: {sr}Hz, ch={ch}, {8 * sw}bit"
        )
    b64 = base64.b64encode(pcm).decode("ascii")
    # Satu pesan besar: audioContent (+fallback keys)
    msg = {
        "config": {
            "encoding": "LINEAR16",
            "sampleRateHertz": sr,
            "languageCode": language,
            "audioChannelCount": ch,
            "enableAutomaticPunctuation": True,
        },
        "audioContent": b64,
        "audio": b64,
        "data": b64,
        "languageCode": language,
        "language": language,
    }
    if DEBUG:
        print(
            "[->] single",
            {"config": msg["config"], "audioContent": f"<base64:{len(b64)}>"},
        )
    await ws.send(json.dumps(msg))
    # finalize ringan
    for payload in ({"type": "stop"}, {"type": "end"}):
        try:
            await ws.send(json.dumps(payload))
            await asyncio.sleep(0.2)
        except Exception:
            pass


async def run(wav_path: str, language: str):
    url = build_ws_url()
    sr, ch, sw, nframes = wav_info(wav_path)
    safe = url.split("api_key=")[0] + "api_key=****"
    print(f"ASR_WS_URL  = {safe}")
    print(
        f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8 * sw} bit, {nframes} frames)"
    )
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {CHUNK_MS} ms, MODE={'SINGLE' if SINGLE else 'STREAM'}\n")

    got_any = False

    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:

        async def reader():
            nonlocal got_any
            try:
                async for raw in ws:
                    print("[<-]", raw)
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if msg.get("type") == "error":
                        raise RuntimeError(msg.get("message", "ASR error"))

                    # Deteksi hasil umum
                    for k in ("transcript", "text", "result"):
                        if k in msg and msg[k]:
                            got_any = True
                            print(k.upper() + ":", msg[k])

                    # Google-style: results[].alternatives[].transcript
                    if "results" in msg:
                        for r in msg["results"]:
                            alts = r.get("alternatives") or []
                            if alts:
                                t = alts[0].get("transcript")
                                if t:
                                    got_any = True
                                    print(
                                        ("FINAL:" if r.get("isFinal") else "PARTIAL:"),
                                        t,
                                    )

                    # OpenAI/OpenMind variants: alternatives at root
                    if "alternatives" in msg:
                        alts = msg["alternatives"] or []
                        if alts:
                            t = alts[0].get("transcript") or alts[0].get("text")
                            if t:
                                got_any = True
                                print("ALT:", t)
            except Exception as e:
                print("[reader] stop:", e)

        rtask = asyncio.create_task(reader())

        # kirim config dulu
        await send_config(ws, language, sr, ch, sw)

        if SINGLE:
            await send_single(ws, wav_path, language)
        else:
            await stream_chunks(ws, wav_path, language)

        await asyncio.sleep(READ_TAIL_SECS)
        try:
            await asyncio.wait_for(rtask, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    if not got_any:
        print("\n[!] Belum ada hasil. Coba:")
        print("    - export ASR_CHUNK_MS=40      # tambah pacing")
        print("    - export ASR_READ_TAIL=12     # tunggu hasil lebih lama")
        print("    - export ASR_SINGLE=1         # kirim 1 pesan besar (single)")
        print("    - export ASR_DEBUG=true       # debug log")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_google_ws.py <wav_path> <language>")
        print("Example: python -u ws_asr_google_ws.py tools/asr-eval/en/001.wav en-US")
        sys.exit(2)
    asyncio.run(run(sys.argv[1], sys.argv[2]))
