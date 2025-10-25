import asyncio
from mavsdk import System

async def run():
    """Mencoba terhubung ke drone dengan konfigurasi port yang benar."""
    drone = System()
    
    print("🔌 Mencoba terhubung ke drone...")
    
    # Gunakan udpin untuk LISTEN, udpout untuk SEND
    # Mock server di 14540, MAVSDK listen di 14541
    connection_strings = [
        "udpin://0.0.0.0:14541",    # MAVSDK listen di port 14541
        "udp://127.0.0.1:14540",    # Langsung connect ke mock server
    ]
    
    connected = False
    
    for conn_str in connection_strings:
        try:
            print(f"🔄 Mencoba: {conn_str}")
            await drone.connect(system_address=conn_str)
            
            # Tunggu koneksi dengan timeout
            print("⏳ Menunggu koneksi drone...")
            connection_timeout = 10  # seconds
            start_time = asyncio.get_event_loop().time()
            
            async for state in drone.core.connection_state():
                if state.is_connected:
                    print(f"✅ TERHUBUNG via {conn_str}!")
                    connected = True
                    break
                
                # Timeout check
                if asyncio.get_event_loop().time() - start_time > connection_timeout:
                    print("❌ Timeout menunggu koneksi")
                    break
                    
            if connected:
                # Berikan waktu untuk sistem stabil
                await asyncio.sleep(2)
                
                # Coba ambil telemetry
                print("📡 Mencoba membaca telemetry...")
                try:
                    position_count = 0
                    async for position in drone.telemetry.position():
                        if position.latitude_deg != 0.0 or position.longitude_deg != 0.0:
                            print(f"📍 Position {position_count + 1}: Lat={position.latitude_deg:.6f}, Lon={position.longitude_deg:.6f}, Alt={position.relative_altitude_m:.1f}m")
                            position_count += 1
                            
                        if position_count >= 3:  # Ambil 3 data lalu keluar
                            break
                        await asyncio.sleep(1)
                        
                    if position_count == 0:
                        print("⚠️ Tidak ada data position yang valid")
                        
                except Exception as e:
                    print(f"❌ Error membaca telemetry: {e}")
                
                # Coba baca status lain
                try:
                    async for health in drone.telemetry.health():
                        print(f"🏥 Health: GPS_ok={health.is_global_position_ok}, Home_ok={health.is_home_position_ok}")
                        break
                except Exception as e:
                    print(f"⚠️ Tidak bisa baca health: {e}")
                    
                break  # Keluar dari loop connection strings
            else:
                # Jika tidak connected, coba disconnect dulu
                try:
                    await asyncio.sleep(1)
                except:
                    pass
                
        except Exception as e:
            print(f"❌ Gagal dengan {conn_str}: {e}")
            continue
    
    if not connected:
        print("💥 Tidak bisa terhubung ke drone dengan semua metode")
    else:
        print("✅ Test selesai dengan sukses!")

if __name__ == "__main__":
    asyncio.run(run())
