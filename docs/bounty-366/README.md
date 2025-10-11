# Bounty #366 — OM1 ↔ Home Assistant (MQTT) Bridge

Komponen `tools/om1-ha-bridge/` menghubungkan OM1 ke Home Assistant via **MQTT Discovery**.
MVP: kontrol lampu (on/off, brightness, HS color).

## Jalankan
```bash
cd tools/om1-ha-bridge
cp -n .env.example .env || cp -n env.sample .env
./run.sh

API test:

POST /light/on

POST /light/off

POST /light/brightness body: {"value": 200}

POST /light/color body: {"hs": [120.0, 80.0]}

### Thermostat (Climate) test

```bash
# set mode
curl -s -X POST http://127.0.0.1:8086/climate/mode   -H 'Content-Type: application/json' -d '{"value":"heat"}'
# set target temperature
curl -s -X POST http://127.0.0.1:8086/climate/target -H 'Content-Type: application/json' -d '{"value":24.5}'
# update current temperature (optional)
curl -s -X POST http://127.0.0.1:8086/climate/current -H 'Content-Type: application/json' -d '{"value":26.0}'


## Demo (short)
Asciinema: https://asciinema.org/a/z8ltqVJ4BjP06HwEFpWv4pXiE
