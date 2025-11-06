import paho.mqtt.client as mqtt
import json
import threading
from socketio import Client

# --- Konfigurasi MQTT & Socket.IO ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
FLASK_SOCKETIO_URL = "http://localhost:5001"

# --- Inisialisasi Klien Socket.IO ---
# Klien ini akan bertindak sebagai klien yang menghubungkan ke server Flask
sio_client = Client()

# --- Fungsi Callback saat Koneksi ke MQTT Berhasil ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Drone MQTT Listener berhasil terhubung ke MQTT Broker!")
        # Berlangganan ke semua topik status dan lokasi drone
        client.subscribe("smartfarm/drone/+/status")
        client.subscribe("smartfarm/drone/+/location")
        print("👂 Mendengarkan update status dan lokasi drone...")
    else:
        print(f"❌ Gagal terhubung ke MQTT Broker, kode error: {rc}")

# --- Fungsi Callback saat Menerima Pesan dari Drone ---
def on_message(client, userdata, msg):
    print(f"📩 Menerima update drone dari topik: {msg.topic}")
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
        print(f"   Data: {data}")

        # --- Siarkan Ulang ke Frontend via WebSocket ---
        # Kita menggunakan event 'swarm_update' yang sudah dikenali oleh frontend /swarm
        sio_client.emit('swarm_update', data)
        print(f"📡 Data berhasil disiarkan ke frontend via WebSocket.")

    except json.JSONDecodeError:
        print(f"   ❌ Error: Payload bukan format JSON yang valid.")
    except Exception as e:
        print(f"   ❌ Error saat memproses pesan atau mengirim ke WebSocket: {e}")

# --- Program Utama ---
if __name__ == "__main__":
    # 1. Hubungkan ke server Socket.IO Flask
    try:
        sio_client.connect(FLASK_SOCKETIO_URL)
        print("✅ Berhasil terhubung ke server Socket.IO Flask.")
    except Exception as e:
        print(f"❌ Tidak dapat terhubung ke server Socket.IO. Pastikan backend Flask berjalan. Error: {e}")
        exit()

    # 2. Buat instance MQTT client
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # 3. Coba terhubung ke broker MQTT
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ Tidak dapat terhubung ke MQTT Broker: {e}")
        sio_client.disconnect()
        exit()

    # 4. Jalankan MQTT loop di thread terpisah
    mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    print("🚀 Drone MQTT Listener berjalan. Tekan Ctrl+C untuk berhenti.")
    
    try:
        # Biarkan program utama berjalan agar koneksi Socket.IO tetap hidup
        while True:
            pass
    except KeyboardInterrupt:
        print("\n👋 Listener dihentikan.")
    finally:
        mqtt_client.disconnect()
        sio_client.disconnect()
        print("🔌 Semua koneksi ditutup.")
