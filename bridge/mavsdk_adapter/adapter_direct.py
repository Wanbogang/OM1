import asyncio
from mavsdk import System

async def run():
    """Koneksi langsung ke mock server."""
    drone = System()
    
    print("🔌 Connecting to mock drone...")
    
    # Coba koneksi langsung ke mock server
    try:
        # MAVSDK sebagai client yang connect ke server
        await drone.connect(system_address="udp://127.0.0.1:14540")
        print("✅ Connected to drone")
        
        # Tunggu sampai connected
        print("⏳ Waiting for connection state...")
        async for state in drone.core.connection_state():
            if state.is_connected:
                print("🎉 Drone is connected!")
                break
            await asyncio.sleep(0.1)
        
        # Baca telemetry
        print("📡 Reading telemetry...")
        async for position in drone.telemetry.position():
            print(f"📍 Position: Lat={position.latitude_deg:.6f}, Lon={position.longitude_deg:.6f}, Alt={position.relative_altitude_m:.1f}m")
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
