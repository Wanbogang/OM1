# ws_asr_stream_root_flush.py
# Stream WAV 16k/mono/16-bit via JSON ROOT frames:
#   kirim berkala: { "audio": "<base64>", ...(hanya di frame#0 metadata) }
#   TANPA "type": "start". Di akhir, coba beberapa "flush" supaya server finalize.

import asyncio
import base64
import contextlib
import json
import os
import sys
import wave

import websockets

CHUNK_MS = int(os.getenv("ASR_CHUNK_MS", "20"))  # 20–30ms ideal
READ_TAIL_SECS = float(
    os.getenv("ASR_READ_TAIL", "6.0")
)  # waktu tunggu setelah kirim terakhir
DEBUG = os.getenv("ASR_DEBUG", "false").lower() in ("1", "true", "yes")


def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    endpoint = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    api_key = os.getenv("OM_API_KEY", "").strip()
    if not endpoint:
        raise RuntimeError(
            "OM1_ASR_ENDPOINT kosong. Contoh: wss://api.openmind.org/api/core/google/asr"
        )
    if not api_key:
        raise RuntimeError("OM_API_KEY kosong.")
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


async def stream_root(ws, wav_path: str, language: str):
    with open_wav(wav_path) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()  # bytes per sample
        if (sr, ch, sw) != (16000, 1, 2):
            print(
                f"[!] Warning: ideal 16kHz/mono/16-bit. Sekarang: {sr}Hz, ch={ch}, {8 * sw}bit"
            )

        bytes_per_frame = ch * sw
        bytes_per_ms = (sr * bytes_per_frame) // 1000
        chunk_bytes = max(bytes_per_ms * CHUNK_MS, 1)

        seq = 0
        total_frames = 0
        while True:
            buf = wf.readframes(chunk_bytes // bytes_per_frame)
            if not buf:
                break

            b64 = base64.b64encode(buf).decode("ascii")
            msg = {"audio": b64}
            if seq == 0:
                msg.update(
                    {
                        "language": language,
                        "sample_rate": sr,
                        "channels": ch,
                        "format": "s16le",
                        "encoding": "LINEAR16",
                        "contentType": f"audio/pcm;bit={8 * sw};rate={sr};channels={ch}",
                    }
                )

            await ws.send(json.dumps(msg))
            sent = len(buf) // bytes_per_frame
            total_frames += sent
            print(f"[->] audio#{seq} frames+={sent} (total={total_frames})")
            seq += 1

            # real-time pacing
            await asyncio.sleep(CHUNK_MS / 1000.0)


async def try_flushes(ws):
    """
    Beberapa server perlu sinyal akhir. Kita coba beberapa variasi aman.
    Urutan:
      1) {"audio": ""}                 # kosongkan audio
      2) {"type":"end","audio": ""}    # jika server butuh 'type' tapi tetap minta 'audio'
      3) {"type":"stop","audio": ""}   # alternatif
    Antar percobaan beri jeda sebentar agar sempat diproses.
    """
    candidates = [
        {"audio": ""},
        {"type": "end", "audio": ""},
        {"type": "stop", "audio": ""},
    ]
    for i, payload in enumerate(candidates, 1):
        try:
            await ws.send(json.dumps(payload))
            if DEBUG:
                print(f"[->] flush#{i} {payload}")
            await asyncio.sleep(0.4)
        except Exception as e:
            print(f"[flush#{i}] error: {e}")


async def run(wav_path: str, language: str):
    url = build_ws_url()
    safe_url = url.split("api_key=")[0] + "api_key=****"
    print(f"ASR_WS_URL  = {safe_url}")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {CHUNK_MS} ms, MODE=json_root\n")

    got_any_result = False

    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:

        async def reader():
            nonlocal got_any_result
            try:
                async for msg in ws:
                    print("[<-]", msg)
                    try:
                        obj = json.loads(msg)
                    except json.JSONDecodeError:
                        continue

                    if obj.get("type") == "error":
                        raise RuntimeError(obj.get("message", "ASR error"))

                    # Tanda ada hasil
                    for k in ("transcript", "result", "text"):
                        if k in obj and obj[k]:
                            got_any_result = True
                            print(f"{k.upper()}:", obj[k])

                    if "alternatives" in obj and obj["alternatives"]:
                        alt = obj["alternatives"][0]
                        txt = alt.get("transcript") or alt.get("text")
                        if txt:
                            got_any_result = True
                            print("ALT:", txt)
            except Exception as e:
                print(f"[reader] stop: {e}")

        reader_task = asyncio.create_task(reader())

        # 1) stream audio real-time
        await stream_root(ws, wav_path, language)

        # 2) coba beberapa "flush" untuk finalize
        await try_flushes(ws)

        # 3) beri waktu untuk hasil akhir
        await asyncio.sleep(READ_TAIL_SECS)

        # 4) tutup reader rapi
        try:
            await asyncio.wait_for(reader_task, timeout=2.0)
        except asyncio.TimeoutError:
            pass

    if not got_any_result:
        print("\n[!] Belum ada hasil dari server.")
        print("    Coba lagi dengan salah satu ini:")
        print("      - export ASR_CHUNK_MS=30   # pacing sedikit lebih santai")
        print("      - export ASR_READ_TAIL=8   # tunggu hasil lebih lama")
        print("      - export ASR_DEBUG=true    # lihat log flush")
        print("    Kalau tetap kosong, kirim balik log [<-] yang keluar.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_stream_root_flush.py <wav_path> <language>")
        sys.exit(2)
    asyncio.run(run(sys.argv[1], sys.argv[2]))
