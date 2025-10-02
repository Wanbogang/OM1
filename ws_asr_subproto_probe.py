import os, json, base64, asyncio, wave, websockets

URL = os.getenv("ASR_WS_URL") or (os.getenv("OM1_ASR_ENDPOINT","wss://api.openmind.org/api/core/google/asr")+"?api_key="+os.getenv("OM_API_KEY",""))
WAV = "tools/asr-eval/en/001.wav"
SUBPROTOS = ["om1-asr", "asr", "google-asr", "speech", "asr.v1", "om1.v1", "v1", "json"]

def open_wav(p):
    w = wave.open(p,"rb")
    sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    assert sr==16000 and ch==1 and sw==2, f"Need 16k/mono/16bit, got {sr}/{ch}/{sw*8}"
    return w, sr

def b64(x): return base64.b64encode(x).decode("ascii")

async def try_one(proto):
    print(f"\n[PROTO] {proto or '(none)'}")
    try:
        async with websockets.connect(URL, max_size=None, subprotocols=[proto] if proto else None) as ws:
            w, sr = open_wav(WAV); frames = w.readframes(w.getnframes()); w.close()
            first = {"config":{"languageCode":"en-US","encoding":"LINEAR16","sampleRateHertz":sr,"channels":1,"bitsPerSample":16},
                     "audio": b64(frames)}
            await ws.send(json.dumps(first))
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10)
                    print("[<-]", msg)
                    if "asr" in msg.lower() or "result" in msg.lower() or "final" in msg.lower():
                        return True
            except asyncio.TimeoutError:
                return False
    except Exception as e:
        print("[ERR]", type(e).__name__, e)
        return False

async def main():
    # juga coba tanpa subprotocol
    for proto in [None] + SUBPROTOS:
        ok = await try_one(proto)
        if ok:
            print(f"\n[✓] WORKS with subprotocol: {proto}\n"); return
    print("\n[!] No subprotocol worked. Need 1 contoh payload/handshake dari server resmi.\n")

asyncio.run(main())
