# ws_asr_stream_root.py
# Stream WAV 16k/mono/16-bit ke OpenMind ASR (Google) pakai JSON root frames:
#   { "audio": "<base64>", ... } dikirim berkala; tanpa "type"/"start"/"end".

import os, sys, json, base64, wave, contextlib, asyncio
import websockets

CHUNK_MS = int(os.getenv("ASR_CHUNK_MS", "20"))   # 20–30ms ideal (boleh 50)
READ_TAIL_SECS = float(os.getenv("ASR_READ_TAIL", "2.0"))  # tunggu hasil di akhir

def build_ws_url() -> str:
    url = os.getenv("ASR_WS_URL", "").strip()
    if url:
        return url
    endpoint = os.getenv("OM1_ASR_ENDPOINT", "").strip()
    api_key  = os.getenv("OM_API_KEY", "").strip()
    if not endpoint:
        raise RuntimeError("OM1_ASR_ENDPOINT kosong. Contoh: wss://api.openmind.org/api/core/google/asr")
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
        sw = wf.getsampwidth()
        if (sr, ch, sw) != (16000, 1, 2):
            print(f"[!] Warning: ideal 16kHz/mono/16-bit. Sekarang: {sr}Hz, ch={ch}, {8*sw}bit")

        bytes_per_frame  = ch * sw
        bytes_per_ms     = sr * bytes_per_frame // 1000
        chunk_bytes      = max(bytes_per_ms * CHUNK_MS, 1)

        seq = 0
        total_frames = 0
        while True:
            buf = wf.readframes(chunk_bytes // bytes_per_frame)
            if not buf:
                break
            b64 = base64.b64encode(buf).decode("ascii")
            msg = {"audio": b64}
            if seq == 0:
                # metadata di CHUNK PERTAMA saja
                msg.update({
                    "language": language,
                    "sample_rate": sr,
                    "channels": ch,
                    "format": "s16le",
                    "encoding": "LINEAR16",
                    # beberapa server tidak perlu ini, tapi aman untuk ikutkan
                    "contentType": f"audio/pcm;bit={8*sw};rate={sr};channels={ch}",
                })
            await ws.send(json.dumps(msg))
            sent = len(buf) // bytes_per_frame
            total_frames += sent
            print(f"[->] audio#{seq} frames+={sent} (total={total_frames})")
            seq += 1
            # kirim realtime-ish
            await asyncio.sleep(CHUNK_MS / 1000.0)

async def run(wav_path: str, language: str):
    url = build_ws_url()
    print(f"ASR_WS_URL  = {url.split('api_key=')[0]}api_key=****")
    print(f"WAV         = {wav_path}")
    print(f"Language    = {language}")
    print(f"CHUNK_MS    = {CHUNK_MS} ms, MODE=json_root (tanpa type)\n")

    async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=None) as ws:
        async def reader():
            try:
                async for msg in ws:
                    print("[<-]", msg)
                    try:
                        obj = json.loads(msg)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("type") == "error":
                        # bubble up supaya program berhenti & kelihatan pesannya
                        raise RuntimeError(obj.get("message", "ASR error"))
                    # Cetak kemungkinan field hasil
                    for k in ("transcript", "result", "text"):
                        if k in obj:
                            print(f"{k.upper()}:", obj[k])
                    if "alternatives" in obj and obj["alternatives"]:
                        alt = obj["alternatives"][0]
                        print("ALT:", alt.get("transcript") or alt.get("text"))
            except Exception as e:
                print(f"[reader] stop: {e}")

        reader_task = asyncio.create_task(reader())
        try:
            await stream_root(ws, wav_path, language)
            # beri waktu server menyelesaikan decoding
            await asyncio.sleep(READ_TAIL_SECS)
        finally:
            # tutup reader dengan timeout kecil
            try:
                await asyncio.wait_for(reader_task, timeout=5.0)
            except asyncio.TimeoutError:
                pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -u ws_asr_stream_root.py <wav_path> <language>")
        sys.exit(2)
    asyncio.run(run(sys.argv[1], sys.argv[2]))
