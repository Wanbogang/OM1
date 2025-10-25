import asyncio
from mavsdk import System

async def run():
    """Test final dengan semua telemetry."""
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
        
        print("\n📡 Starting telemetry streams...")
        
        # Baca position dengan timeout
        print("📍 Waiting for position data (timeout: 15s)...")
        position_received = False
        start_time = asyncio.get_event_loop().time()
        
        async for position in drone.telemetry.position():
            if position.latitude_deg != 0.0 or position.longitude_deg != 0.0:
                print(f"🎉 POSITION RECEIVED: Lat={position.latitude_deg:.6f}, Lon={position.longitude_deg:.6f}, Alt={position.relative_altitude_m:.1f}m")
                position_received = True
                break
            
            # Timeout setelah 15 detik
            if asyncio.get_event_loop().time() - start_time > 15:
                print("⏰ Timeout: No position data received")
                break
            await asyncio.sleep(0.1)
        
        # Baca health status
        print("\n🏥 Reading health status...")
        async for health in drone.telemetry.health():
            print(f"Health: GPS_ok={health.is_global_position_ok}, Home_ok={health.is_home_position_ok}")
            break
        
        if position_received:
            print("\n✅ SUCCESS! MAVSDK can read drone telemetry!")
        else:
            print("\n❌ FAILED! No position data received")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
