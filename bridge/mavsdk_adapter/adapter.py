"""
MAVSDK adapter skeleton (stub).
This is a minimal, non-blocking placeholder showing where MAVSDK code will live.
Install real dependency with: pip install mavsdk
"""
import asyncio

try:
    from mavsdk import System
except Exception:
    System = None  # MAVSDK not installed in CI; keep this file safe to import.

async def run_mavsdk_example():
    if System is None:
        print("MAVSDK not installed - adapter is a stub.")
        return
    drone = System()
    await drone.connect(system_address="udp://:14540")  # typical SITL
    print("Connected (stub)")

if __name__ == "__main__":
    asyncio.run(run_mavsdk_example())
