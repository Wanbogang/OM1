import asyncio
import sys
from mavsdk import System

async def run():
    """Mencoba terhubung ke drone dan cetak telemetry dasar dengan timeout."""
    drone = System()
    
    print("🔌 Mencoba terhubung ke drone...")
    
    # Coba beberapa format connection string
    connection_strings = [
        "udp://:14540",           # Listen pada port 14540
        "udp://0.0.0.0:14540",    # Listen pada semua interface
        "udpin://0.0.0.0:14540",  # MAVSDK style input
    ]
    
    connected = False
    
    for conn_str in connection_strings:
        try:
            print(f"🔄 Mencoba: {conn_str}")
            await drone.connect(system_address=conn_str)
            
            # Tunggu koneksi dengan timeout
            print("⏳ Menunggu koneksi drone...")
            try:
                async for state in drone.core.connection_state():
                    if state.is_connected:
                        print(f"✅ TERHUBUNG via {conn_str}!")
                        connected = True
                        break
                    # Timeout setelah 5 detik
                    await asyncio.sleep(5)
                    print("❌ Timeout menunggu koneksi")
                    break
            except asyncio.TimeoutError:
                print("❌ Timeout menunggu connection state")
                continue
                
            if connected:
                # Coba ambil telemetry
                print("📡 Mencoba membaca telemetry...")
                try:
                    async for position in drone.telemetry.position():
                        print(f"📍 Position: Lat={position.latitude_deg:.6f}, Lon={position.longitude_deg:.6f}, Alt={position.relative_altitude_m:.1f}m")
                        # Ambil beberapa data lalu keluar
                        await asyncio.sleep(2)
                        break
                        
                except Exception as e:
                    print(f"❌ Error membaca telemetry: {e}")
                
                # Coba baca status baterai juga
                try:
                    async for battery in drone.telemetry.battery():
                        print(f"🔋 Battery: {battery.remaining_percent:.1%}")
                        break
                except Exception as e:
                    print(f"⚠️ Tidak bisa baca battery: {e}")
                    
                break  # Keluar dari loop connection strings
                
        except Exception as e:
            print(f"❌ Gagal dengan {conn_str}: {e}")
            continue
    
    if not connected:
        print("💥 Tidak bisa terhubung ke drone dengan semua metode")
        return
    
    print("✅ Test selesai!")

if __name__ == "__main__":
    asyncio.run(run())
