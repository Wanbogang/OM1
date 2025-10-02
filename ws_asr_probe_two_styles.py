#!/usr/bin/env python3
# ws_asr_probe_two_styles.py
# Mencoba 2 format paling umum utk gateway Google STT di WebSocket:
#  1) Google-REST style: {"config": {...}, "audio": {"content": "<b64 WAV>"}}
#  2) Root-audio style:  {"audio": "<b64 PCM>", "language": "..."} lalu {"type":"end"}

import os, sys, json, base64, asyncio, wave, contextlib, time
from typing import Optional
import websockets

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    endpoint = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    api_key  = os.getenv("OM_API_KEY", "").strip()
    if not endpoint:
        raise RuntimeError("OM1_ASR_ENDPOINT belum diset")
    if not api_key:
        raise RuntimeError("OM_API_KEY belum diset")
    sep = "&" if "?" in endpoint else "?"
    return f"{endpoint}{sep}api_key={api_key}"

def mask(s: str) -> str:
    return s if not s else (s[:4] + "..." + s[-4:])

@contextlib.contextmanager
def open_wav(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    wf = wave.open(path, "rb")
    try:
        yield wf
    finally:
        wf.close()

def read_wav_full_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def read_wav_pcm_and_meta(path: str):
    with open_wav(path) as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()  # bytes per sample
        nframes = wf.getnframes()
        pcm = wf.readframes(nframes)
    return pcm, sr, ch, sw, nframes

async def recv_drain(ws, tail_s: float = 10.0) -> list[dict]:
    """Tarik semua pesan selama tail_s detik atau sampai koneksi ditutup."""
    end_at = time.time() + max(0.1, tail_s)
    msgs = []
    while time.time() < end_at:
        timeout = end_at - time.time()
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        except asyncio.TimeoutError:
            break
        except websockets.exceptions.ConnectionClosed as e:
            print(f"[x] closed: {e.code}")
            break
        try:
            obj = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        except Exception:
            print(f"[<-] (non-JSON) {raw!r}")
            continue
        msgs.append(obj)
        print(f"[<-] {obj}")
    return msgs

async def try_google_rest(ws, wav_path: str, language: str, tail_s: float) -> bool:
    """Kirim 1 pesan bergaya Google REST: {config, audio:{content}}"""
    wav_bytes = read_wav_full_bytes(wav_path)
    b64 = base64.b64encode(wav_bytes).decode("ascii")

    payload = {
        "config": {
            "languageCode": language,
            # untuk WAV, encoding sebenarnya bisa diabaikan, tapi kita set aman:
            "encoding": "LINEAR16",
            "enableAutomaticPunctuation": True,
        },
        "audio": {"content": b64},
    }

    print("[->] send GOOGLE_REST single")
    await ws.send(json.dumps(payload))
    msgs = await recv_drain(ws, tail_s)
    # anggap sukses jika ada pesan selain 'connection'/'error'
    ok = any(m.get("type") not in ("connection", "error") for m in msgs if isinstance(m, dict))
    return ok

async def try_root_audio_then_end(ws, wav_path: str, language: str, tail_s: float) -> bool:
    """Kirim 2 pesan: {audio, language} lalu {type:'end'}"""
    pcm, sr, ch, sw, nframes = read_wav_pcm_and_meta(wav_path)
    b64 = base64.b64encode(pcm).decode("ascii")

    root = {
        "audio": b64,
        "language": language,
        "sample_rate": sr,
        "channels": ch,
        "encoding": "LINEAR16",
        "contentType": f"audio/pcm;bit={8*sw};rate={sr};channels={ch}",
    }
    print("[->] send ROOT_AUDIO single")
    await ws.send(json.dumps(root))

    print("[->] send END")
    await ws.send(json.dumps({"type": "end"}))

    msgs = await recv_drain(ws, tail_s)
    ok = any(m.get("type") not in ("connection", "error") for m in msgs if isinstance(m, dict))
    return ok

async def main():
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_probe_two_styles.py <wav_path> <language>")
        sys.exit(2)
    wav_path = sys.argv[1]
    language = sys.argv[2]

    url = build_ws_url()
    tail_s = float(os.getenv("ASR_READ_TAIL", "10"))

    # info file
    pcm, sr, ch, sw, nframes = read_wav_pcm_and_meta(wav_path)
    print(f"ASR_WS_URL  = {url.replace(os.getenv('OM_API_KEY',''), '****')}")
    print(f"WAV         = {wav_path}  ({sr} Hz, {ch} ch, {8*sw} bit, {nframes} frames)")
    print(f"Language    = {language}")
    print(f"TAIL        = {tail_s}s\n")

    # 1) GOOGLE_REST
    print("=== TRY: GOOGLE_REST (single {config,audio:{content}}) ===")
    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
            ok = await try_google_rest(ws, wav_path, language, tail_s)
            print(f"=== GOOGLE_REST done (ok={ok}) ===\n")
            if ok:
                return
    except Exception as e:
        print(f"[!] google_rest failed: {e}\n")

    # 2) ROOT_AUDIO + END
    print("=== TRY: ROOT_AUDIO + END (single root audio, lalu end) ===")
    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
            ok = await try_root_audio_then_end(ws, wav_path, language, tail_s)
            print(f"=== ROOT_AUDIO done (ok={ok}) ===\n")
            if ok:
                return
    except Exception as e:
        print(f"[!] root_audio failed: {e}\n")

    print("[X] Keduanya belum menerima hasil. Dari log yang kamu kirim sebelumnya, ini memang terjadi jika gateway tidak mengenali bentuk payload audio.")
    print("    Jika masih begitu, langkah berikutnya:")
    print("    - Coba WAV full (tanpa dipecah): skrip ini sudah pakai itu di mode GOOGLE_REST.")
    print("    - Jika gateway mengharuskan field lain (mis. 'seq' atau 'requestId'), itu harus diketahui dari dokumen server.")

if __name__ == "__main__":
    asyncio.run(main())

