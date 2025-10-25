import asyncio
from mavsdk import System

async def run():
    """Debug adapter dengan lebih banyak info."""
    drone = System()
    
    print("🔌 Connecting to drone...")
    
    try:
        await drone.connect(system_address="udp://:14540")
        
        print("⏳ Waiting for connection...")
        async for state in drone.core.connection_state():
            print(f"📡 Connection: {state}")
            if state.is_connected:
                print("✅ CONNECTED!")
                break
        
        print("\n🔍 Debug Info:")
        
        # Check telemetry available
        print("1. Checking telemetry availability...")
        try:
            async for health in drone.telemetry.health():
                print(f"   Health: {health}")
                break
        except Exception as e:
            print(f"   Health error: {e}")
        
        # Check position with detailed info
        print("2. Checking position stream...")
        position_count = 0
        start_time = asyncio.get_event_loop().time()
        
        async for position in drone.telemetry.position():
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"   Position #{position_count}: Lat={position.latitude_deg}, Lon={position.longitude_deg}, Alt={position.relative_altitude_m}")
            position_count += 1
            
            if position_count >= 5 or elapsed > 10:
                break
            await asyncio.sleep(1)
        
        if position_count == 0:
            print("   ❌ No position data received")
        else:
            print(f"   ✅ Received {position_count} position updates")
            
        print("\n🎯 Test completed!")
        
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
