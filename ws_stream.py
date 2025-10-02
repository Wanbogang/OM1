#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio, base64, json, math, os, sys, wave
import websockets

def getenv_bool(name: str, default=False):
    v = os.getenv(name)
    return default if v is None else str(v).strip().lower() in ("1","true","yes","y","on")

def read_wav_pcm16(path: str):
    with wave.open(path, "rb") as wf:
        nch = wf.getnchannels()
        sw  = wf.getsampwidth()  # bytes per sample (2 untuk 16-bit)
        sr  = wf.getframerate()
        n   = wf.getnframes()
        raw = wf.readframes(n)
    return raw, sr, nch, sw

async def printer(ws):
    try:
        async for message in ws:
            try:
                obj = json.loads(message)
                print(f"[<-] {json.dumps(obj)}")
                for k in ("partial","text","transcript","result"):
                    if isinstance(obj.get(k), str):
                        print(f"[TRANSCRIPT] {obj[k]}")
            except Exception:
                if isinstance(message, (bytes, bytearray)):
                    print(f"[<-] (binary {len(message)} bytes)")
                else:
                    preview = str(message)
                    print(f"[<-] (non-JSON) {preview[:200]}")
    except websockets.ConnectionClosedOK:
        print("### Server closed (1000 OK).")
    except websockets.ConnectionClosedError as e:
        print(f"### Server closed with error: {e}")

async def send_json_root(ws, raw, chunk_bytes, end_type, chunk_ms, lang=None):
    # Tanpa pesan 'start'. Server sering minta langsung 'audio' di root.
    total = len(raw)
    n_chunks = (total + chunk_bytes - 1)//chunk_bytes
    for i in range(n_chunks):
        buf = raw[i*chunk_bytes:(i+1)*chunk_bytes]
        payload = {"seq": i, "audio": base64.b64encode(buf).decode("ascii")}
        if i == 0 and lang:
            # jika server mau, sisipkan language di chunk pertama (tidak wajib)
            payload["language"] = lang
        await ws.send(json.dumps(payload))
        await asyncio.sleep(chunk_ms/1000.0)
    await ws.send(json.dumps({"type": ("stop" if end_type=="stop" else "end")}))

async def send_binary_no_start(ws, raw, chunk_bytes, end_type, chunk_ms):
    # Kirim WS binary frames langsung, tanpa 'start'
    total = len(raw)
    n_chunks = (total + chunk_bytes - 1)//chunk_bytes
    for i in range(n_chunks):
        await ws.send(raw[i*chunk_bytes:(i+1)*chunk_bytes])
        await asyncio.sleep(chunk_ms/1000.0)
    # Banyak server menerima tanda akhir sebagai JSON kecil
    try:
        await ws.send(json.dumps({"type": ("stop" if end_type=="stop" else "end")}))
    except Exception:
        pass

async def send_typed(ws, raw, chunk_bytes, end_type, chunk_ms, sr, ch, sw, lang):
    # Protokol bertipe (punya 'start' & 'type': 'audio')
    start_msg = {
        "type": "start",
        "language": lang,
        "sample_rate": sr,
        "channels": ch,
        "format": "s16le" if sw == 2 else f"s{sw*8}le",
        "encoding": "LINEAR16",
        "contentType": f"audio/pcm;bit={sw*8};rate={sr};channels={ch}",
        "frame_ms": chunk_ms,
    }
    await ws.send(json.dumps(start_msg))
    total = len(raw)
    n_chunks = (total + chunk_bytes - 1)//chunk_bytes
    for i in range(n_chunks):
        b64 = base64.b64encode(raw[i*chunk_bytes:(i+1)*chunk_bytes]).decode("ascii")
        await ws.send(json.dumps({"type": "audio", "seq": i, "audio": b64}))
        await asyncio.sleep(chunk_ms/1000.0)
    await ws.send(json.dumps({"type": ("stop" if end_type=="stop" else "end")}))

async def stream_once(uri: str, wav_path: str, language: str, mode_hint: str):
    raw, sr, ch, sw = read_wav_pcm16(wav_path)
    chunk_ms      = int(os.getenv("ASR_CHUNK_MS", "30"))
    bytes_per_ms  = int(sr * sw * ch / 1000)
    chunk_bytes   = max(bytes_per_ms * max(1, chunk_ms), 1)
    end_type      = os.getenv("ASR_END_TYPE", "end").strip().lower()
    verbose_audio = getenv_bool("ASR_VERBOSE_AUDIO", False)

    print(f"ASR_WS_URL        = {uri}")
    print(f"ASR_AUDIO_MODE    = {mode_hint}")
    print(f"ASR_END_TYPE      = {end_type}")
    print(f"ASR_CHUNK_MS      = {chunk_ms} ms")
    print(f"ASR_VERBOSE_AUDIO = {verbose_audio}")

    # Urutan fallback: json_root -> binary -> typed (kecuali user override)
    order = []
    mh = (mode_hint or "auto").lower()
    if mh in ("json","json_root"):
        order = ["json_root","binary","typed"]
    elif mh in ("binary", "bin", "binary_nostart"):
        order = ["binary","json_root","typed"]
    elif mh in ("typed", "json_typed"):
        order = ["typed","json_root","binary"]
    else:
        order = ["json_root","binary","typed"]

    last_err = None
    for mode in order:
        print(f"\n=== Trying protocol: {mode} ===")
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=20, max_size=None) as ws:
                reader_task = asyncio.create_task(printer(ws))
                if mode == "json_root":
                    await send_json_root(ws, raw, chunk_bytes, end_type, chunk_ms, lang=language)
                elif mode == "binary":
                    await send_binary_no_start(ws, raw, chunk_bytes, end_type, chunk_ms)
                else:
                    await send_typed(ws, raw, chunk_bytes, end_type, chunk_ms, sr, ch, sw, language)

                # kasih waktu 2.5 detik buat final result
                try:
                    await asyncio.wait_for(reader_task, timeout=2.5)
                except asyncio.TimeoutError:
                    reader_task.cancel()
            print(f"=== Protocol {mode} done ===")
            return
        except Exception as e:
            last_err = e
            print(f"!!! Protocol {mode} failed: {e}")

    if last_err:
        raise last_err

def usage():
    print(f"Usage: {sys.argv[0]} <wav_path> <languageCode>", file=sys.stderr)
    print(f"Example: {sys.argv[0]} tools/asr-eval/en/001.wav en-US", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage(); sys.exit(2)
    wav_path, language = sys.argv[1], sys.argv[2]
    ws_url = os.getenv("ASR_WS_URL") or os.getenv("OM1_ASR_ENDPOINT")
    if not ws_url:
        print("[!] Please set ASR_WS_URL.", file=sys.stderr); sys.exit(1)

    # Hint mode dari env (opsional). Nilai: json | json_root | binary | typed | auto
    hint = os.getenv("ASR_AUDIO_MODE", "auto")

    try:
        asyncio.run(stream_once(ws_url, wav_path, language, hint))
    except KeyboardInterrupt:
        pass
