# ws_asr_typed_start_audio_v2.py
# WebSocket ASR (typed JSON).
# Tiap pesan SELALU menyertakan "audio".
# Start membawa audio + config (languageCode), diakhiri end+stop (dua-duanya flush).

import os, sys, json, base64, asyncio, wave, contextlib
import websockets

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    ep  = os.getenv("OM1_ASR_ENDPOINT", "").strip()
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
        n  = wf.getnframes()
        raw = wf.readframes(n)
    return raw, sr, ch, sw, n

async def receiver(ws, tail_s: float):
    """Baca pesan server sampai tail timeout/hubungan tutup."""
    loop = asyncio.get_event_loop()
    last = loop.time()
    while True:
        timeout = max(0.1, (last + tail_s) - loop.time())
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
        last = loop.time()
        print("[<-]", msg if isinstance(msg, str) else f"<binary {len(msg)}B>")

async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_typed_start_audio_v2.py <wav_path> <language>")
        sys.exit(2)

    wav_path = sys.argv[1]
    language = sys.argv[2]
    url      = build_ws_url()

    chunk_ms = int(os.getenv("ASR_CHUNK_MS", "30"))  # 20–40 oke
    tail     = float(os.getenv("ASR_READ_TAIL", "15"))

    raw, sr, ch, sw, n = read_wav_bytes(wav_path)
    if not (sr == 16000 and ch == 1 and sw == 2):
        print(f"[!] WAV bukan 16kHz mono 16-bit (sr={sr}, ch={ch}, sw={8*sw}b). Tetap dicoba.")

    bytes_per_ms = sr * ch * sw // 1000   # 32 B per ms utk 16k/mono/16-bit
    chunk_bytes  = max(1, bytes_per_ms * chunk_ms)

    print(f"ASR_WS_URL  = {url[:32]}****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {chunk_ms} ms, MODE=typed JSON (start+audio+config → audio* → end+stop)")

    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        # (opsional) baca ACK connection dulu (kalau ada)
        try:
            ack = await asyncio.wait_for(ws.recv(), timeout=1.0)
            print("[<-]", ack)
        except asyncio.TimeoutError:
            pass

        # CHUNK 1 — start + audio + config (dengan languageCode di dalam config)
        off = 0
        end = min(chunk_bytes, len(raw))
        first = raw[off:end]
        off = end
        first_b64 = base64.b64encode(first).decode("ascii")
        start_msg = {
            "type": "start",
            "audio": first_b64,                # <- WAJIB ada
            "language": language,              # untuk gateway
            "languageCode": language,          # untuk engine Google
            "sample_rate": sr,
            "channels": ch,
            "format": "s16le",
            "encoding": "LINEAR16",
            "contentType": "audio/pcm;bit=16;rate=16000;channels=1",
            "frame_ms": chunk_ms,
            # config ala Google (ikutkan juga di start)
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": sr,
                "languageCode": language,
                "audioChannelCount": ch,
                "enableAutomaticPunctuation": True,
                "interimResults": True
            }
        }
        await ws.send(json.dumps(start_msg))
        print(f"[->] start+config+audio bytes={len(first)}")

        # CHUNK 2..N — audio beruntun (tetap bawa 'audio' & language)
        while off < len(raw):
            end = min(off + chunk_bytes, len(raw))
            piece = raw[off:end]
            off = end
            b64 = base64.b64encode(piece).decode("ascii")
            msg = {"type": "audio", "audio": b64, "language": language, "languageCode": language}
            await ws.send(json.dumps(msg))
            print(f"[->] audio bytes={len(piece)}")
            await asyncio.sleep(chunk_ms / 1000.0)

        # END — kirim end+flush kemudian stop+flush (keduanya tetap punya 'audio')
        end_msg  = {"type": "end",  "audio": "", "language": language, "languageCode": language}
        stop_msg = {"type": "stop", "audio": "", "language": language, "languageCode": language}
        await ws.send(json.dumps(end_msg))
        print("[->] end+flush")
        await ws.send(json.dumps(stop_msg))
        print("[->] stop+flush")

        # Baca hasil
        await receiver(ws, tail)

if __name__ == "__main__":
    asyncio.run(main())
