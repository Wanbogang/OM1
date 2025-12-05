#!/usr/bin/env python3
import asyncio
import base64
import json
import os
import sys
import wave

import websockets


def build_ws_url():
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    key = os.getenv("OM_API_KEY", "").strip()
    if not ep:
        raise SystemExit(
            "OM1_ASR_ENDPOINT kosong (mis. wss://api.openmind.org/api/core/google/asr)"
        )
    if not key:
        raise SystemExit("OM_API_KEY kosong")
    sep = "&" if "?" in ep else "?"
    return f"{ep}{sep}api_key={key}"


def load_wav(path):
    if not os.path.exists(path):
        raise SystemExit(f"File tidak ditemukan: {path}")
    wf = wave.open(path, "rb")
    sr, ch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
    if not (sr == 16000 and ch == 1 and sw == 2):
        wf.close()
        raise SystemExit("WAV harus LINEAR16: 16kHz, mono, 16-bit.")
    n = wf.getnframes()
    raw = wf.readframes(n)
    wf.close()
    return raw


async def reader(ws, on_connected: asyncio.Event):
    try:
        async for msg in ws:
            # semua pesan dari server diasumsikan text JSON
            print("[<-]", msg)
            try:
                obj = json.loads(msg)
                if obj.get("type") == "connection":
                    on_connected.set()
                # kalau server mengirim “final”/“result”, akan kelihatan di sini
            except Exception:
                # kalau bukan JSON valid, tetap cetak mentah
                pass
    except websockets.ConnectionClosed:
        print("[i] server closed connection (reader).")


async def main():
    if len(sys.argv) != 3:
        print("Usage: python -u ws_asr_stream_root_readyclose.py <wav_path> <language>")
        sys.exit(1)

    wav_path, language = sys.argv[1], sys.argv[2]
    url = build_ws_url()
    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))
    tail = float(os.getenv("ASR_READ_TAIL", "10"))

    raw = load_wav(wav_path)
    frame_bytes = int(16000 * 2 * chunk_ms / 1000)  # 16k * 2 bytes * ms/1000
    print(f"ASR_WS_URL  = {url[:40]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {chunk_ms} ms, MODE=root JSON streaming + close\n")

    async with websockets.connect(
        url, ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:
        on_connected = asyncio.Event()
        task = asyncio.create_task(reader(ws, on_connected))

        # 1) WAJIB: tunggu 'connection' dari server
        try:
            await asyncio.wait_for(on_connected.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            print(
                "[!] Tidak ada 'connection' ack dalam 3 detik, lanjut tetap coba stream."
            )

        # 2) kirim chunk berkala (pesan root JSON)
        offset = 0
        seq = 0
        while offset < len(raw):
            chunk = raw[offset : offset + frame_bytes]
            if not chunk:
                break
            b64 = base64.b64encode(chunk).decode("ascii")
            if seq == 0:
                payload = {"audio": b64, "language": language}
            else:
                payload = {"audio": b64}
            await ws.send(json.dumps(payload))
            print(f"[->] audio#{seq} bytes={len(chunk)}")
            seq += 1
            offset += len(chunk)
            await asyncio.sleep(chunk_ms / 1000.0)

        # 3) end-of-stream: JANGAN kirim 'end' / 'flush' —> cukup tutup ws
        await ws.close(code=1000)
        print("[->] closed socket (1000)")

        # 4) beri waktu baca tail (kalau server masih kirim sisa pesan sebelum close)
        try:
            await asyncio.wait_for(task, timeout=tail)
        except asyncio.TimeoutError:
            print("[i] tail timeout selesai.")


if __name__ == "__main__":
    asyncio.run(main())
