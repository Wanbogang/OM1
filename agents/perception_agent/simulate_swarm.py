# agents/perception_agent/simulate_swarm.py (VERSION WITH MQTT INTEGRATION - FIXED)
import paho.mqtt.client as mqtt
import json
import time
import random
import threading
import string
import asyncio
import datetime
from prisma import Prisma
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# --- Konfigurasi MQTT ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Initialize database client
prisma = Prisma()

# --- Fungsi Baru: Mempublikasikan Update Drone ke MQTT ---
def publish_drone_update_to_mqtt(drone_id, drone_name, status, battery_level, lat, lon):
    """
    Mempublikasikan status dan lokasi drone ke topik MQTT terpisah.
    Fungsi ini berjalan di thread terpisah agar tidak blocking loop utama.
    """
    def mqtt_publisher():
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1) # Perbaiki warning
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)

            # Topik untuk status umum (baterai, status)
            status_topic = f"smartfarm/drone/{drone_id}/status"
            status_payload = {
                "id": drone_id,
                "name": drone_name,
                "status": status,
                "battery": battery_level
            }
            client.publish(status_topic, json.dumps(status_payload))
            print(f"📡 Status update for {drone_name} (Battery: {battery_level}%) published to MQTT.")

            # Topik untuk lokasi GPS (jika ada)
            if lat is not None and lon is not None:
                location_topic = f"smartfarm/drone/{drone_id}/location"
                location_payload = {
                    "id": drone_id,
                    "lat": lat,
                    "lon": lon
                }
                client.publish(location_topic, json.dumps(location_payload))
                print(f"📍 Location update for {drone_name} published to MQTT.")

            client.disconnect()

        except Exception as e:
            print(f"❌ Gagal mempublikasikan update untuk drone {drone_id}: {e}")

    # Jalankan publisher di thread terpisah agar tidak menghentikan simulator
    thread = threading.Thread(target=mqtt_publisher)
    thread.daemon = True
    thread.start()


# Function to generate a simple unique ID
def generate_id(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def run_simulation():
    print("🚀 Starting Swarm Simulator with MQTT Integration...")

    await prisma.connect()

    try:
        # 1. Initialize data if it doesn't exist
        if await prisma.drone.count() == 0:
            print("📦 Initializing drones...")
            for i in range(3):
                await prisma.drone.create(data={
                    'id': f'drone-{i+1}',
                    'name': f'Drone Alpha {i+1}',
                    'status': 'IDLE',
                    'battery_level': random.randint(80, 100)
                })

        if await prisma.zone.count() == 0:
            print("📍 Initializing zones...")
            zone_names = ["Sector A", "Sector B", "Sector C", "Sector D"]
            for name in zone_names:
                await prisma.zone.create(data={
                    'id': generate_id(),
                    'name': name,
                    'coordinates': f"{random.uniform(-6.3, -6.2)},{random.uniform(106.8, 106.9)};{random.uniform(-6.3, -6.2)},{random.uniform(106.8, 106.9)}"
                })

        # 2. Main simulation loop
        while True:
            try:
                # Simple simulation logic
                idle_drones = await prisma.drone.find_many(where={'status': 'IDLE'})
                unassigned_zones = await prisma.zone.find_many(where={'status': 'UNASSIGNED'})

                if idle_drones and unassigned_zones:
                    drone = random.choice(idle_drones)
                    zone = random.choice(unassigned_zones)

                    # Create a new task
                    task = await prisma.task.create(data={
                        'id': generate_id(),
                        'droneId': drone.id,
                        'zoneId': zone.id,
                        'status': 'IN_PROGRESS',
                        'started_at': datetime.utcnow().isoformat() + 'Z',
                    })

                    # --- Update drone location to the zone's coordinates ---
                    coord_str = zone.coordinates
                    first_point_str = coord_str.split(';')[0]
                    lat_str, lng_str = first_point_str.split(',')
                    target_lat = float(lat_str)
                    target_lng = float(lng_str)

                    # --- PERBAIKAN: Hitung baterai baru dan pastikan tidak kurang dari 0 ---
                    new_battery = max(0, drone.battery_level - random.randint(5, 15))

                    # Update drone and zone status
                    await prisma.drone.update(where={'id': drone.id}, data={
                        'status': 'FLYING',
                        'assignedZoneId': zone.id,
                        'battery_level': new_battery,
                        'current_latitude': target_lat,
                        'current_longitude': target_lng
                    })
                    await prisma.zone.update(where={'id': zone.id}, data={
                        'status': 'IN_PROGRESS'
                    })

                    print(f"🔥 Assigned {drone.name} to {zone.name}. Task ID: {task.id}. Location updated.")
                    
                    # --- KIRIM UPDATE KE MQTT (menggunakan nilai yang sudah dihitung) ---
                    publish_drone_update_to_mqtt(drone.id, drone.name, 'FLYING', new_battery, target_lat, target_lng)

                else:
                    # --- CYCLE RESET LOGIC ---
                    print("🔄 All zones are completed or no idle drones. Resetting cycle...")

                    # Reset all zones to UNASSIGNED
                    await prisma.zone.update_many(
                        where={},
                        data={'status': 'UNASSIGNED'}
                    )

                    # Reset all drones that might be stuck back to IDLE
                    # --- PERBAIKAN: Simpan hasil update_many ke variabel ---
                    reset_result = await prisma.drone.update_many(
                        where={'status': {'in': ['FLYING', 'ASSIGNED', 'RETURNING']}},
                        data={'status': 'IDLE', 'assignedZoneId': None, 'current_latitude': None, 'current_longitude': None}
                    )
                    # --- PERBAIKAN: Gunakan variabel hasilnya, bukan .count ---
                    print(f"✅ Cycle reset complete. {reset_result} drones reset to IDLE.")

                # Simulate task completion
                in_progress_tasks = await prisma.task.find_many(where={'status': 'IN_PROGRESS'})
                if in_progress_tasks:
                    task_to_complete = random.choice(in_progress_tasks)

                    await prisma.task.update(where={'id': task_to_complete.id}, data={
                        'status': 'COMPLETED',
                        'completed_at': datetime.utcnow().isoformat() + 'Z',
                    })

                    drone = await prisma.drone.find_unique(where={'id': task_to_complete.droneId})
                    zone = await prisma.zone.find_unique(where={'id': task_to_complete.zoneId})

                    if drone and zone:
                        # --- PERBAIKAN: Hitung baterai baru dan pastikan tidak kurang dari 0 ---
                        new_battery = max(0, drone.battery_level - random.randint(5, 15))
                        # --- Reset drone location when task is complete ---
                        await prisma.drone.update(where={'id': drone.id}, data={
                            'status': 'IDLE',
                            'assignedZoneId': None,
                            'battery_level': new_battery,
                            'current_latitude': None,
                            'current_longitude': None
                        })
                        await prisma.zone.update(where={'id': zone.id}, data={
                            'status': 'COMPLETED'
                        })
                        print(f"✅ Task {task_to_complete.id} completed by {drone.name}. Location reset.")
                        
                        # --- KIRIM UPDATE KE MQTT (menggunakan nilai yang sudah dihitung) ---
                        publish_drone_update_to_mqtt(drone.id, drone.name, 'IDLE', new_battery, None, None)

            except Exception as e:
                print(f"An error occurred during simulation loop: {e}")

            await asyncio.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped by user.")
    finally:
        print("🔌 Disconnecting from database...")
        if prisma.is_connected():
            await prisma.disconnect()
        print("✅ Cleanup complete.")

if __name__ == '__main__':
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped by user.")
