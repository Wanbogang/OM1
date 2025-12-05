# ws_asr_typed_start_audio.py
# WebSocket ASR (typed JSON) — setiap pesan menyertakan "audio".
# Python 3.10+, websockets>=10

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
        raise SystemExit("OM1_ASR_ENDPOINT belum diset")
    if not key:
        raise SystemExit("OM_API_KEY belum diset")
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
        raw = wf.readframes(n)
    return raw, sr, ch, sw, n


async def receiver(ws, tail_s: float):
    """Baca semua pesan server sampai tail timeout/hubungan ditutup."""
    last = asyncio.get_event_loop().time()
    while True:
        timeout = max(0.1, (last + tail_s) - asyncio.get_event_loop().time())
        if timeout <= 0:
            print("[i] tail selesai")
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
        print("[<-]", msg if isinstance(msg, str) else f"<binary {len(msg)}B>")


async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_typed_start_audio.py <wav_path> <language>")
        sys.exit(2)

    wav_path = sys.argv[1]
    language = sys.argv[2]
    url = build_ws_url()
    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))
    tail = float(os.getenv("ASR_READ_TAIL", "10"))

    # baca WAV
    raw, sr, ch, sw, n = read_wav_bytes(wav_path)
    if not (sr == 16000 and ch == 1 and sw == 2):
        print(
            f"[!] WAV bukan 16kHz mono 16-bit (sr={sr}, ch={ch}, sw={8 * sw}b). Tetap dicoba."
        )

    bytes_per_ms = sr * ch * sw // 1000  # 16000*1*2/1000 = 32
    chunk_bytes = bytes_per_ms * chunk_ms

    print(f"ASR_WS_URL  = {url[:32]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(
        f"CHUNK_MS    = {chunk_ms} ms, MODE=typed JSON (start+audio, audio..., end+flush)"
    )

    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:
        # 1) Tunggu ACK "connection" dulu biar gateway siap
        try:
            ack = await asyncio.wait_for(ws.recv(), timeout=1.0)
            print("[<-]", ack)
        except asyncio.TimeoutError:
            print("[i] tidak ada ACK awal, lanjutkan streaming")

        # 2) kirim start+audio (potongan pertama)
        off = 0
        first_end = min(chunk_bytes, len(raw))
        first_piece = raw[off:first_end]
        off = first_end
        first_b64 = base64.b64encode(first_piece).decode("ascii")
        start_msg = {
            "type": "start",
            "language": language,
            "sample_rate": sr,
            "channels": ch,
            "format": "s16le",
            "encoding": "LINEAR16",
            "contentType": "audio/pcm;bit=16;rate=16000;channels=1",
            "frame_ms": chunk_ms,
            "audio": first_b64,  # <- penting: start juga bawa audio
        }
        await ws.send(json.dumps(start_msg))
        print(f"[->] start+audio bytes={len(first_piece)}")

        # 3) kirim sisa chunk sebagai type=audio (tetap bawa 'audio')
        while off < len(raw):
            end = min(off + chunk_bytes, len(raw))
            piece = raw[off:end]
            off = end
            b64 = base64.b64encode(piece).decode("ascii")
            msg = {"type": "audio", "audio": b64, "language": language}
            await ws.send(json.dumps(msg))
            print(f"[->] audio bytes={len(piece)}")
            await asyncio.sleep(chunk_ms / 1000.0)  # pacing realtime

        # 4) kirim end+flush (end wajib tetap ada field audio)
        end_msg = {"type": "end", "audio": ""}  # <- penting
        await ws.send(json.dumps(end_msg))
        print("[->] end+flush")

        # 5) dengarkan hasil selama tail detik
        await receiver(ws, tail)


if __name__ == "__main__":
    asyncio.run(main())
