import json
import os
import threading
import time
from typing import List

from dotenv import load_dotenv
from fastapi import Body, FastAPI
from paho.mqtt import client as mqtt

load_dotenv()
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER") or None
MQTT_PASS = os.getenv("MQTT_PASS") or None
PREFIX = os.getenv("HA_DISCOVERY_PREFIX", "homeassistant")
DEVICE_ID = os.getenv("DEVICE_ID", "om1_light_1")
DEVICE_NAME = os.getenv("DEVICE_NAME", "OM1 Light 1")

STATE_TOPIC = f"{PREFIX}/light/{DEVICE_ID}/state"
CMD_TOPIC = f"{PREFIX}/light/{DEVICE_ID}/set"
BRI_STATE_TOPIC = f"{PREFIX}/light/{DEVICE_ID}/brightness_state"
BRI_CMD_TOPIC = f"{PREFIX}/light/{DEVICE_ID}/brightness"
HS_STATE_TOPIC = f"{PREFIX}/light/{DEVICE_ID}/hs_state"
HS_CMD_TOPIC = f"{PREFIX}/light/{DEVICE_ID}/hs"
CONFIG_TOPIC = f"{PREFIX}/light/{DEVICE_ID}/config"

app = FastAPI(title="om1-ha-bridge")

_mqtt = mqtt.Client()
if MQTT_USER:
    _mqtt.username_pw_set(MQTT_USER, MQTT_PASS)


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] connected rc={rc}")
    client.subscribe(
        [
            (STATE_TOPIC, 0),
            (BRI_STATE_TOPIC, 0),
            (HS_STATE_TOPIC, 0),
        ]
    )


def on_message(client, userdata, msg):
    try:
        print(f"[STATE] {msg.topic}: {msg.payload.decode('utf-8')}")
        # TODO: relay ke OM1 event bus bila diperlukan (lanjutan)
    except Exception as e:
        print(f"[STATE_ERR] {e}")


_mqtt.on_connect = on_connect
_mqtt.on_message = on_message


def mqtt_loop():
    _mqtt.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    _mqtt.loop_forever()


def publish_discovery():
    payload = {
        "name": DEVICE_NAME,
        "uniq_id": DEVICE_ID,
        "cmd_t": CMD_TOPIC,
        "stat_t": STATE_TOPIC,
        "bri_cmd_t": BRI_CMD_TOPIC,
        "bri_stat_t": BRI_STATE_TOPIC,
        "hs_cmd_t": HS_CMD_TOPIC,
        "hs_stat_t": HS_STATE_TOPIC,
        "schema": "json",
        "device": {
            "identifiers": [DEVICE_ID],
            "manufacturer": "OM1",
            "model": "OM1-HA-Bridge",
            "name": DEVICE_NAME,
        },
        "supported_color_modes": ["hs"],
        "brightness": True,
    }
    _mqtt.publish(CONFIG_TOPIC, json.dumps(payload), retain=True)
    print(f"[DISCOVERY] published {CONFIG_TOPIC}")


@app.on_event("startup")
def _startup():
    threading.Thread(target=mqtt_loop, daemon=True).start()
    time.sleep(0.8)  # beri waktu konek
    publish_discovery()


def _onoff_payload(on: bool):
    return json.dumps({"state": "ON" if on else "OFF"})


@app.post("/light/on")
def api_on():
    _mqtt.publish(CMD_TOPIC, _onoff_payload(True))
    return {"ok": True}


@app.post("/light/off")
def api_off():
    _mqtt.publish(CMD_TOPIC, _onoff_payload(False))
    return {"ok": True}


@app.post("/light/brightness")
def api_brightness(value: int = Body(..., embed=True)):
    v = max(0, min(255, int(value)))
    _mqtt.publish(BRI_CMD_TOPIC, json.dumps({"brightness": v}))
    return {"ok": True, "brightness": v}


@app.post("/light/color")
def api_color(hs: List[float] = Body(..., embed=True)):
    try:
        H = float(hs[0])
        S = float(hs[1])
    except Exception:
        return {"ok": False, "error": "bad hs"}
    H = max(0.0, min(360.0, H))
    S = max(0.0, min(100.0, S))
    _mqtt.publish(HS_CMD_TOPIC, json.dumps({"hs_color": [H, S]}))
    return {"ok": True, "hs": [H, S]}


# ====== Thermostat (Climate) ======
# Note: we only publish discovery and provide HTTP endpoints that publish MQTT commands.
# Subscriptions for state are optional for this bounty and can be added later.

try:
    THERMO_DEVICE_ID = os.getenv("THERMO_DEVICE_ID", "om1_thermo_1")
    THERMO_DEVICE_NAME = os.getenv("THERMO_DEVICE_NAME", "OM1 Thermostat 1")
    MIN_TEMP = float(os.getenv("MIN_TEMP", "16"))
    MAX_TEMP = float(os.getenv("MAX_TEMP", "30"))
    TEMP_STEP = float(os.getenv("TEMP_STEP", "0.5"))
except Exception:
    THERMO_DEVICE_ID, THERMO_DEVICE_NAME = "om1_thermo_1", "OM1 Thermostat 1"
    MIN_TEMP, MAX_TEMP, TEMP_STEP = 16.0, 30.0, 0.5

_CLIMATE_PREFIX = f"{PREFIX}/climate/{THERMO_DEVICE_ID}"
_MODE_STAT_TOPIC = f"{_CLIMATE_PREFIX}/mode"
_MODE_CMD_TOPIC = f"{_CLIMATE_PREFIX}/mode/set"
_TARGET_STAT_TOPIC = f"{_CLIMATE_PREFIX}/target_temp"
_TARGET_CMD_TOPIC = f"{_CLIMATE_PREFIX}/target_temp/set"
_CURR_TEMP_TOPIC = f"{_CLIMATE_PREFIX}/current_temp"
_CLIMATE_CONFIG_TOPIC = f"{PREFIX}/climate/{THERMO_DEVICE_ID}/config"


def publish_climate_discovery():
    payload = {
        "name": THERMO_DEVICE_NAME,
        "uniq_id": THERMO_DEVICE_ID,
        "mode_cmd_t": _MODE_CMD_TOPIC,
        "mode_stat_t": _MODE_STAT_TOPIC,
        "temp_cmd_t": _TARGET_CMD_TOPIC,
        "temp_stat_t": _TARGET_STAT_TOPIC,
        "curr_temp_t": _CURR_TEMP_TOPIC,
        "modes": ["off", "heat", "cool", "auto"],
        "min_temp": MIN_TEMP,
        "max_temp": MAX_TEMP,
        "temp_step": TEMP_STEP,
        "schema": "json",
        "device": {
            "identifiers": [THERMO_DEVICE_ID],
            "manufacturer": "OM1",
            "model": "OM1-HA-Bridge",
            "name": THERMO_DEVICE_NAME,
        },
    }
    _mqtt.publish(_CLIMATE_CONFIG_TOPIC, json.dumps(payload), retain=True)
    print(f"[DISCOVERY] published {_CLIMATE_CONFIG_TOPIC}")


@app.on_event("startup")
def _startup_climate():
    # publish discovery for climate on startup as a separate handler
    publish_climate_discovery()


@app.post("/climate/mode")
def api_climate_mode(value: str = Body(..., embed=True)):
    value = str(value).lower()
    if value not in {"off", "heat", "cool", "auto"}:
        return {"ok": False, "error": "bad mode"}
    _mqtt.publish(_MODE_CMD_TOPIC, json.dumps({"mode": value}))
    return {"ok": True, "mode": value}


@app.post("/climate/target")
def api_climate_target(value: float = Body(..., embed=True)):
    try:
        t = float(value)
    except Exception:
        return {"ok": False, "error": "bad temperature"}
    t = max(MIN_TEMP, min(MAX_TEMP, t))
    _mqtt.publish(_TARGET_CMD_TOPIC, json.dumps({"temperature": t}))
    return {"ok": True, "target": t}


@app.post("/climate/current")
def api_climate_current(value: float = Body(..., embed=True)):
    try:
        t = float(value)
    except Exception:
        return {"ok": False, "error": "bad temperature"}
    _mqtt.publish(_CURR_TEMP_TOPIC, json.dumps({"temperature": t}))
    return {"ok": True, "current": t}
