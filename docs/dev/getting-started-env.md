# Environment & Credential Hygiene (OM1)

## .env (jangan di-commit)
Buat file `.env` di root project:

OM_API_KEY=om1_live_xxx
OM1_ASR_ENDPOINT=wss://api.openmind.org/api/core/google/asr

**Jangan** commit `.env`. Tambahkan ke `.gitignore`:

.env
tools/asr-eval/.wav
tools/asr-eval//*.wav

## Rotasi kunci
Jika perlu rotasi, hapus key di portal, buat yang baru, lalu update `.env`.  
Jangan taruh key di kode, PR, issue, atau log.
