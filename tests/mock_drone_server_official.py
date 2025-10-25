#!/usr/bin/env python3
"""Mock drone yang lebih pintar menggunakan library mavsdk itu sendiri."""
import asyncio
from mavsdk import System

async def run_mock_drone():
    """Jalankan mock drone yang berperilaku seperti drone sungguhan."""
    drone = System()
    print("🚁 Mock Drone (Official) berjalan...")
    
    # Gunakan port yang berbeda untuk menghindari konflik
    await drone.connect(system_address="udpin://127.0.0.1:14540")
    print("✅ Mock Drone siap dan menunggu koneksi dari adapter di port 14540.")

    # Terus berjalan agar tidak mati
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_mock_drone())
