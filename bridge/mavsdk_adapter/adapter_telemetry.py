import asyncio
from mavsdk import System

async def run():
    """Baca data telemetry dari drone."""
    drone = System()
    
    print("🔌 Connecting to drone...")
    
    try:
        await drone.connect(system_address="udp://:14540")
        
        # Tunggu koneksi
        print("⏳ Waiting for connection...")
        async for state in drone.core.connection_state():
            if state.is_connected:
                print("✅ CONNECTED to drone!")
                break
        
        # Baca berbagai data telemetry
        print("\n📡 Reading telemetry data...")
        
        # Task untuk membaca berbagai telemetry
        async def read_position():
            print("📍 Waiting for position data...")
            async for position in drone.telemetry.position():
                print(f"📍 Position: Lat={position.latitude_deg:.6f}, Lon={position.longitude_deg:.6f}, Alt={position.relative_altitude_m:.1f}m")
        
        async def read_health():
            print("🏥 Waiting for health data...")
            async for health in drone.telemetry.health():
                print(f"🏥 Health: GPS_ok={health.is_global_position_ok}, Home_ok={health.is_home_position_ok}")
        
        async def read_battery():
            print("🔋 Waiting for battery data...")
            async for battery in drone.telemetry.battery():
                print(f"🔋 Battery: {battery.remaining_percent:.1%}")
        
        async def read_attitude():
            print("📐 Waiting for attitude data...")
            async for attitude in drone.telemetry.attitude_euler():
                print(f"📐 Attitude: Roll={attitude.roll_deg:.1f}°, Pitch={attitude.pitch_deg:.1f}°, Yaw={attitude.yaw_deg:.1f}°")
        
        # Jalankan semua task selama 10 detik
        tasks = [
            asyncio.create_task(read_position()),
            asyncio.create_task(read_health()),
            asyncio.create_task(read_battery()),
            asyncio.create_task(read_attitude())
        ]
        
        await asyncio.sleep(10)
        
        # Cancel semua task
        for task in tasks:
            task.cancel()
            
        print("\n✅ Telemetry test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
