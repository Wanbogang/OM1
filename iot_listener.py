import paho.mqtt.client as mqtt
import json
import asyncio
import threading
from prisma import Prisma
from prisma.models import SensorData

# --- Konfigurasi MQTT ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "smartfarm/sensor/+"

# --- Inisialisasi Prisma Client dan Event Loop ---
prisma = Prisma()
loop = asyncio.new_event_loop()

# --- Fungsi Callback saat Koneksi Berhasil ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Berhasil terhubung ke MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        print(f"👂 Mendengarkan pesan di topik: {MQTT_TOPIC}")
    else:
        print(f"❌ Gagal terhubung, kode error: {rc}")

# --- Fungsi Callback saat Menerima Pesan ---
def on_message(client, userdata, msg):
    print(f"\n📩 Pesan diterima dari topik: {msg.topic}")
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
        print(f"   Data: {data}")

        # Jalankan fungsi async untuk menyimpan ke database
        asyncio.run_coroutine_threadsafe(save_to_db(data), loop)

    except json.JSONDecodeError:
        print(f"   ❌ Error: Payload bukan format JSON yang valid.")
    except Exception as e:
        print(f"   ❌ Error saat memproses pesan: {e}")

# --- Fungsi Async untuk Menyimpan ke Database ---
async def save_to_db(data):
    try:
        sensor_data = await prisma.sensordata.create(
            data={
                'sensorId': data.get('sensorId'),
                'type': data.get('type'),
                'value': data.get('value'),
                'unit': data.get('unit'),
            }
        )
        print(f"✅ Data berhasil disimpan ke database dengan ID: {sensor_data.id}")
    except Exception as e:
        print(f"   ❌ Gagal menyimpan ke database: {e}")

# --- Program Utama ---
if __name__ == "__main__":
    # Hubungkan ke database
    try:
        loop.run_until_complete(prisma.connect())
        print("🗄️ Berhasil terhubung ke database.")
    except Exception as e:
        print(f"❌ Gagal terhubung ke database: {e}")
        exit()

    # Setup MQTT Client
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ Tidak dapat terhubung ke broker: {e}")
        loop.run_until_complete(prisma.disconnect())
        exit()

    # Jalankan MQTT loop di thread terpisah agar tidak blocking
    mqtt_thread = threading.Thread(target=client.loop_forever)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    print("🚀 Listener MQTT berjalan. Tekan Ctrl+C untuk berhenti.")
    
    try:
        # Jalankan event loop forever agar bisa mengerjakan task async
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n👋 Listener dihentikan.")
    finally:
        client.disconnect()
        # Tutup loop dan disconnect dari database
        loop.run_until_complete(prisma.disconnect())
        print("🗄️ Koneksi ke database ditutup.")
