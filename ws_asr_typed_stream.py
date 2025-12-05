# ws_asr_typed_stream.py
# WebSocket ASR client (typed JSON): start -> audio chunks -> end
# Python 3.10+, websockets>=10

import asyncio
import base64
import contextlib
import json
import os
import sys
import wave

import websockets

# ---------- ENV config ----------
CHUNK_MS = int(os.getenv("ASR_CHUNK_MS", "30"))  # 20–40 ms disarankan
READ_TAIL = float(os.getenv("ASR_READ_TAIL", "10"))  # tunggu hasil setelah "end"
DEBUG = os.getenv("ASR_DEBUG", "false").lower() == "true"


def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    endpoint = (
        os.getenv("OM1_ASR_ENDPOINT", "").strip()
        or os.getenv("OM_ASR_ENDPOINT", "").strip()
    )
    api_key = os.getenv("OM_API_KEY", "").strip()
    if not endpoint:
        raise RuntimeError(
            "Env OM1_ASR_ENDPOINT kosong. Contoh: wss://api.openmind.org/api/core/google/asr"
        )
    if not api_key:
        raise RuntimeError("Env OM_API_KEY kosong (API key).")
    sep = "&" if "?" in endpoint else "?"
    return f"{endpoint}{sep}api_key={api_key}"


@contextlib.contextmanager
def open_wav(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    wf = wave.open(path, "rb")
    try:
        yield wf
    finally:
        wf.close()


async def reader(ws):
    """Terima semua pesan dari server & tampilkan."""
    try:
        while True:
            msg = await ws.recv()
            try:
                data = json.loads(msg)
            except Exception:
                data = msg
            print(f"[<-] {data}")
    except (
        websockets.exceptions.ConnectionClosedOK,
        websockets.exceptions.ConnectionClosedError,
    ):
        pass


async def sender_stream(ws, wav_path: str, language: str):
    """Kirim start -> potongan audio (typed JSON) -> end, dengan pacing real-time."""
    with open_wav(wav_path) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        _nframes = wf.getnframes()  # noqa: F841

        if sr != 16000 or ch != 1 or sw != 2:
            print(
                f"[!] Peringatan: WAV ideal = 16kHz mono 16-bit. Sekarang: {sr} Hz, {ch} ch, {8 * sw} bit."
            )

        start = {
            "type": "start",
            "language": language,
            "sample_rate": sr,
            "channels": ch,
            "format": "s16le",
            "encoding": "LINEAR16",
            "contentType": f"audio/pcm;bit={8 * sw};rate={sr};channels={ch}",
            "frame_ms": CHUNK_MS,
        }
        if DEBUG:
            print("[->] start", start)
        await ws.send(json.dumps(start))

        frames_per_chunk = max(1, int(sr * CHUNK_MS / 1000))
        seq = 0
        sent_frames = 0

        while True:
            buf = wf.readframes(frames_per_chunk)
            if not buf:
                break
            b64 = base64.b64encode(buf).decode("ascii")

            # KUNCI: type=audio + field 'audio'
            msg = {
                "type": "audio",
                "seq": seq,
                "audio": b64,
                # tambahan kompat: beberapa server juga menerima 'data'
                "data": b64,
            }
            if DEBUG:
                print(
                    f"[->] audio seq={seq} frames+={len(buf) // sw} (total={sent_frames + len(buf) // sw})"
                )
            await ws.send(json.dumps(msg))

            sent_frames += len(buf) // sw
            seq += 1

            # pacing real-time-ish
            await asyncio.sleep(CHUNK_MS / 1000)

        if DEBUG:
            print("[->] end")
        await ws.send(json.dumps({"type": "end"}))

        if READ_TAIL > 0:
            await asyncio.sleep(READ_TAIL)


async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_typed_stream.py <wav_path> <language>")
        print(
            "Contoh: python -u ws_asr_typed_stream.py tools/asr-eval/en/001.wav en-US"
        )
        sys.exit(2)

    wav_path = sys.argv[1]
    language = sys.argv[2]
    url = build_ws_url()

    # Info awal
    with open_wav(wav_path) as wf:
        sr, ch, sw, nframes = (
            wf.getframerate(),
            wf.getnchannels(),
            wf.getsampwidth(),
            wf.getnframes(),
        )
    api_key = os.getenv("OM_API_KEY", "")
    url_print = url.replace(api_key, "****") if api_key else url
    print(f"ASR_WS_URL  = {url_print}")
    print(
        f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8 * sw} bit, {nframes} frames)"
    )
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {CHUNK_MS} ms, MODE=typed-json\n")

    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:
        reader_task = asyncio.create_task(reader(ws))
        try:
            await sender_stream(ws, wav_path, language)
        finally:
            try:
                await ws.close()
            except Exception:
                pass
            await asyncio.sleep(0.2)
            if not reader_task.done():
                reader_task.cancel()
                try:
                    await reader_task
                except Exception:
                    pass


if __name__ == "__main__":
    asyncio.run(main())
