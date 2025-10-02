# --- START ws_asr_auto.py ---
# Autoprobe WebSocket ASR client: coba beberapa format sampai cocok.
# Python 3.10+, websockets>=10

import os, sys, json, base64, wave, contextlib, asyncio
import websockets

# ---------- utils ----------
def mask_key(s: str) -> str:
    return s[:4] + "..." + s[-4:] if s else s

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    endpoint = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    api_key  = os.getenv("OM_API_KEY", "").strip()
    if not endpoint:
        raise RuntimeError("OM1_ASR_ENDPOINT kosong. Contoh: wss://api.openmind.org/api/core/google/asr")
    if not api_key:
        raise RuntimeError("OM_API_KEY kosong (API key).")
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

def read_wav(path: str):
    with open_wav(path) as wf:
        sr, ch, sw, n = wf.getframerate(), wf.getnchannels(), wf.getsampwidth(), wf.getnframes()
        raw = wf.readframes(n)
    return sr, ch, sw, n, raw

async def recv_until(ws, timeout=6.0):
    """
    Baca beberapa pesan selama 'timeout' detik.
    Kembalikan (ok, last_text). ok=True jika tidak ketemu error fatal.
    """
    ok = True
    last = ""
    end_at = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end_at:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=max(0.1, end_at - asyncio.get_event_loop().time()))
        except asyncio.TimeoutError:
            break
        except Exception as e:
            ok = False
            last = f"(recv error: {e})"
            break
        last = msg if isinstance(msg, str) else f"<{len(msg)} bytes>"
        print("[<-]", last)
        # heuristik: kalau bukan pesan error, anggap ok
        try:
            obj = json.loads(msg) if isinstance(msg, str) else {}
            if isinstance(obj, dict):
                if obj.get("type") == "error":
                    ok = False
                # ada hasil transkrip?
                if any(k in obj for k in ("transcript","result","final","alternatives","text","message")):
                    ok = True
                    break
        except Exception:
            pass
    return ok, last

# ---------- protocol senders ----------
async def proto_root_audio(url, audio_b64, meta):
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        payload = {"audio": audio_b64, "language": meta["language"]}
        print("[-> root] keys:", list(payload.keys()))
        await ws.send(json.dumps(payload))
        return await recv_until(ws)

async def proto_typed_start_audio_end(url, audio_b64, meta):
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        start = {
            "type":"start",
            "language": meta["language"],
            "sample_rate": meta["sr"],
            "channels": meta["ch"],
            "format": meta["fmt"],
            "encoding": meta["enc"],
            "contentType": meta["ct"],
            "frame_ms": 50,
        }
        audio = {"type":"audio", "audio": audio_b64}
        end   = {"type":"end"}
        print("[-> typed] start")
        await ws.send(json.dumps(start))
        print("[-> typed] audio")
        await ws.send(json.dumps(audio))
        print("[-> typed] end")
        await ws.send(json.dumps(end))
        return await recv_until(ws)

async def proto_root_data(url, audio_b64, meta):
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        payload = {"data": audio_b64, "language": meta["language"]}
        print("[-> data] keys:", list(payload.keys()))
        await ws.send(json.dumps(payload))
        return await recv_until(ws)

async def proto_google_style(url, audio_b64, meta):
    # Beberapa gateway minta "config" + "audioContent" (gaya Google)
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        cfg = {
            "config": {
                "encoding": meta["enc"],
                "sampleRateHertz": meta["sr"],
                "languageCode": meta["language"],
                "audioChannelCount": meta["ch"],
            }
        }
        audio = {"audioContent": audio_b64}
        print("[-> gcfg] config")
        await ws.send(json.dumps(cfg))
        print("[-> gcfg] audioContent")
        await ws.send(json.dumps(audio))
        return await recv_until(ws)

# ---------- main ----------
async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_auto.py <wav_path> <language>")
        print("Example: python -u ws_asr_auto.py tools/asr-eval/en/001.wav en-US")
        sys.exit(2)

    wav_path = sys.argv[1]
    language = sys.argv[2]
    url = build_ws_url()

    sr, ch, sw, n, raw = read_wav(wav_path)
    audio_b64 = base64.b64encode(raw).decode("ascii")
    fmt = "s16le" if sw == 2 else f"pcm_{8*sw}"
    enc = "LINEAR16" if sw == 2 else f"PCM_{8*sw}"
    ct  = f"audio/pcm;bit={8*sw};rate={sr};channels={ch}"

    url_print = url
    if "api_key=" in url_print:
        before, after = url_print.split("api_key=", 1)
        url_print = before + "api_key=" + mask_key(after)

    print(f"ASR_WS_URL      = {url_print}")
    print(f"WAV             = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit, {n} frames, {len(raw)} bytes)")
    print(f"Language        = {language}\n")

    meta = {"language": language, "sr": sr, "ch": ch, "fmt": fmt, "enc": enc, "ct": ct}

    candidates = [
        ("root_audio", proto_root_audio),
        ("typed_start_audio_end", proto_typed_start_audio_end),
        ("root_data", proto_root_data),
        ("google_style", proto_google_style),
    ]

    any_ok = False
    for name, sender in candidates:
        print(f"=== Trying protocol: {name} ===")
        try:
            ok, last = await sender(url, audio_b64, meta)
            print(f"=== Protocol {name} done (ok={ok}) ===\n")
            if ok:
                any_ok = True
                break
        except Exception as e:
            print(f"!!! Protocol {name} error: {e}\n")

    if not any_ok:
        print("Semua protokol gagal. Periksa kembali format pesan yang diharapkan server (kunci 'audio' vs 'data' "
              "atau perlu 'start'/'end'). Coba kirim log di atas.")
        
if __name__ == "__main__":
    asyncio.run(main())
# --- END ws_asr_auto.py ---
