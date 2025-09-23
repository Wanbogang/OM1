# ASR Quick Notes & Pitfalls (Beta)

- **Gunakan WebSocket**, bukan HTTP. Contoh:

wss://api.openmind.org/api/core/google/asr?api_key=<YOUR_API_KEY>
Simpan base URL di `.env` (tanpa `api_key`), lalu tambahkan `api_key` sebagai query saat runtime.

- **Format payload** bisa bervariasi. Jika koneksi ditutup/empty:
- `{"audio":"<base64>","rate":16000,"language":"id-ID"}`
- `{"audio":"<base64>","rate":16000}`
- `{"audio":"<base64>"}`

- **Audio pendek** (≤10s), WAV 16 kHz mono.

- **Keamanan**: `OM_API_KEY` hanya di `.env`.  
Jangan taruh kredensial di README, PR, issue, atau log.
