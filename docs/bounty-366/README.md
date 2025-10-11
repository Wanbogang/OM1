# Bounty #366 — OM1 ↔ Home Assistant (MQTT) Bridge

Komponen `tools/om1-ha-bridge/` menghubungkan OM1 ke Home Assistant via **MQTT Discovery**.
MVP: kontrol lampu (on/off, brightness, HS color).

## Jalankan
```bash
cd tools/om1-ha-bridge
cp -n .env.example .env || cp -n env.sample .env || cp -n env.sample .env
./run.sh

API test:

POST /light/on

POST /light/off

POST /light/brightness body: {"value": 200}

POST /light/color body: {"hs": [120.0, 80.0]}
