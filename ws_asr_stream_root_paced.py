# ws_asr_stream_root_paced.py
# Stream ASR via WebSocket (root JSON mode) dengan pacing real-time.
# Tested dengan websockets>=10, Python 3.10+

import asyncio
import base64
import contextlib
import json
import os
import sys
import wave

import websockets


def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    key = os.getenv("OM_API_KEY", "").strip()
    if not ep:
        raise SystemExit("OM1_ASR_ENDPOINT belum diset.")
    if not key:
        raise SystemExit("OM_API_KEY belum diset.")
    join = "&" if "?" in ep else "?"
    return f"{ep}{join}api_key={key}"


def read_wav_bytes(path: str):
    if not os.path.exists(path):
        raise SystemExit(f"File tidak ditemukan: {path}")
    with contextlib.closing(wave.open(path, "rb")) as wf:
        ch = wf.getnchannels()
        sr = wf.getframerate()
        sw = wf.getsampwidth()
        n = wf.getnframes()
        data = wf.readframes(n)
    return data, sr, ch, sw, n


async def receiver(ws: websockets.WebSocketClientProtocol, tail_s: float):
    """
    Baca pesan server sampai timeout tail_s tercapai setelah terakhir pesan.
    Cetak semua pesan yang datang (biar kelihatan hasil/transkrip).
    """
    last = asyncio.get_event_loop().time()
    while True:
        timeout = max(0.1, (last + tail_s) - asyncio.get_event_loop().time())
        if timeout <= 0:
            print("[i] tail selesai, stop listen")
            return
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
        except asyncio.TimeoutError:
            print("[i] tail timeout tanpa pesan baru")
            return
        except websockets.ConnectionClosedOK:
            print("[i] server tutup (1000 OK)")
            return
        except websockets.ConnectionClosedError as e:
            print(f"[!] koneksi tutup error: {e}")
            return
        last = asyncio.get_event_loop().time()
        try:
            print("[<-]", msg if isinstance(msg, str) else f"<binary {len(msg)}B>")
        except Exception:
            print("[<-] <unprintable>")


async def sender_stream(ws, wav_path: str, language: str, chunk_ms: int):
    raw, sr, ch, sw, n = read_wav_bytes(wav_path)
    if not (sr == 16000 and ch == 1 and sw == 2):
        print(
            f"[!] WAV bukan 16kHz mono 16-bit (sr={sr}, ch={ch}, sw={8 * sw}b). Tetap dicoba."
        )
    # hitung bytes per chunk (PCM 16-bit mono: 2 byte/sampel)
    bytes_per_ms = sr * ch * (sw) // 1000  # 16000 * 1 * 2 / 1000 = 32
    chunk_bytes = bytes_per_ms * chunk_ms  # 30ms -> 960 byte
    total = len(raw)
    off = 0
    seq = 0

    # kecilkan burst: tunggu “connection” dulu, tapi jangan blocking lama
    # receiver di main akan print “connection”, kita kasih sedikit jeda ringan
    await asyncio.sleep(0.05)

    while off < total:
        end = min(off + chunk_bytes, total)
        piece = raw[off:end]
        b64 = base64.b64encode(piece).decode("ascii")
        if seq == 0:
            payload = {"audio": b64, "language": language}
        else:
            payload = {"audio": b64}
        await ws.send(json.dumps(payload))
        print(f"[->] audio seq={seq} bytes={len(piece)}")
        off = end
        seq += 1
        # pacing real-time
        await asyncio.sleep(chunk_ms / 1000.0)

    # flush: kirim frame kosong untuk menandai akhir
    await ws.send(json.dumps({"audio": ""}))
    print("[->] flush {'audio': ''}")


async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_stream_root_paced.py <wav_path> <language>")
        sys.exit(2)
    wav_path = sys.argv[1]
    language = sys.argv[2]

    url = build_ws_url()
    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))
    tail = float(os.getenv("ASR_READ_TAIL", "10"))

    print(f"ASR_WS_URL  = {url[:32]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {chunk_ms} ms, MODE=root JSON paced")
    # penting: jangan disable ping; biarkan default (keepalive ok)
    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:
        # Jalankan receiver dan sender paralel:
        recv_task = asyncio.create_task(receiver(ws, tail))
        await sender_stream(ws, wav_path, language, chunk_ms)
        # biarkan receiver terus hidup sampai tail habis / server close
        await recv_task


if __name__ == "__main__":
    asyncio.run(main())
