import asyncio
from mavsdk import System

async def run():
    """Test koneksi sederhana."""
    drone = System()
    
    print("🔌 Testing connection...")
    
    try:
        # Coba multiple connection methods
        methods = [
            "udp://:14540",
            "udp://127.0.0.1:14540", 
            "udpin://0.0.0.0:14540"
        ]
        
        for method in methods:
            try:
                print(f"🔄 Trying: {method}")
                await drone.connect(system_address=method)
                
                # Check connection state
                print("⏳ Checking connection...")
                async for state in drone.core.connection_state():
                    print(f"📡 Connection state: {state}")
                    if state.is_connected:
                        print("✅ CONNECTED!")
                        return
                    break
                    
            except Exception as e:
                print(f"❌ Failed with {method}: {e}")
                continue
                
        print("💥 All methods failed")
        
    except Exception as e:
        print(f"💥 Overall error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
