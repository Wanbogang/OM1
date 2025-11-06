# agents/perception_agent/simulate_swarm.py (VERSION WITH RESET & LOCATION UPDATE)

import time
import random
import string
import asyncio
import datetime
from prisma import Prisma
from socketio import Client
from dotenv import load_dotenv

load_dotenv()

# Initialize database and socket clients
prisma = Prisma()
sio = Client()

# Function to generate a simple unique ID
def generate_id(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def run_simulation():
    print("🚀 Starting Swarm Simulator...")

    try:
        sio.connect('http://localhost:5001')
        print("✅ Connected to backend Socket.IO server.")
    except Exception as e:
        print(f"❌ Could not connect to backend. Is the server running? Error: {e}")
        return

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
                        'started_at': datetime.datetime.utcnow().isoformat() + 'Z',
                    })

                    # --- FIX: Update drone location to the zone's coordinates ---
                    coord_str = zone.coordinates
                    first_point_str = coord_str.split(';')[0]
                    lat_str, lng_str = first_point_str.split(',')
                    target_lat = float(lat_str)
                    target_lng = float(lng_str)

                    # Update drone and zone status
                    await prisma.drone.update(where={'id': drone.id}, data={
                        'status': 'FLYING',
                        'assignedZoneId': zone.id,
                        'battery_level': drone.battery_level - random.randint(5, 15),
                        'current_latitude': target_lat,
                        'current_longitude': target_lng
                    })
                    await prisma.zone.update(where={'id': zone.id}, data={
                        'status': 'IN_PROGRESS'
                    })

                    print(f"🔥 Assigned {drone.name} to {zone.name}. Task ID: {task.id}. Location updated.")
                    sio.emit('swarm_update', {'message': f'{drone.name} assigned to {zone.name}'})

                else:
                    # --- CYCLE RESET LOGIC ---
                    print("🔄 All zones are completed or no idle drones. Resetting cycle...")

                    # Reset all zones to UNASSIGNED
                    await prisma.zone.update_many(
                        where={},
                        data={'status': 'UNASSIGNED'}
                    )

                    # Reset all drones that might be stuck back to IDLE
                    await prisma.drone.update_many(
                        where={'status': {'in': ['FLYING', 'ASSIGNED', 'RETURNING']}},
                        data={'status': 'IDLE', 'assignedZoneId': None, 'current_latitude': None, 'current_longitude': None}
                    )

                    print("✅ Cycle reset complete. Ready for new assignments.")
                    sio.emit('swarm_update', {'message': 'Simulation cycle has been reset.'})

                # Simulate task completion
                in_progress_tasks = await prisma.task.find_many(where={'status': 'IN_PROGRESS'})
                if in_progress_tasks:
                    task_to_complete = random.choice(in_progress_tasks)

                    await prisma.task.update(where={'id': task_to_complete.id}, data={
                        'status': 'COMPLETED',
                        'completed_at': datetime.datetime.utcnow().isoformat() + 'Z',
                    })

                    drone = await prisma.drone.find_unique(where={'id': task_to_complete.droneId})
                    zone = await prisma.zone.find_unique(where={'id': task_to_complete.zoneId})

                    if drone and zone:
                        # --- FIX: Reset drone location when task is complete ---
                        await prisma.drone.update(where={'id': drone.id}, data={
                            'status': 'IDLE',
                            'assignedZoneId': None,
                            'battery_level': drone.battery_level - random.randint(5, 15),
                            'current_latitude': None,
                            'current_longitude': None
                        })
                        await prisma.zone.update(where={'id': zone.id}, data={
                            'status': 'COMPLETED'
                        })
                        print(f"✅ Task {task_to_complete.id} completed by {drone.name}. Location reset.")
                        sio.emit('swarm_update', {'message': f'Task in {zone.name} completed.'})

            except Exception as e:
                print(f"An error occurred during simulation loop: {e}")

            await asyncio.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped by user.")
    finally:
        print("🔌 Disconnecting from database and socket...")
        if prisma.is_connected():
            await prisma.disconnect()
        if sio.connected:
            sio.disconnect()
        print("✅ Cleanup complete.")

if __name__ == '__main__':
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        print("\n🛑 Simulator stopped by user.")
