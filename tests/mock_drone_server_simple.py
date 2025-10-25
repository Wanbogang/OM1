#!/usr/bin/env python3
"""Mock drone server sederhana tanpa SYS_STATUS."""
import socket
import time
import struct

def create_mavlink_message(msg_id, data, system_id=1, component_id=1):
    """Buat MAVLink message v1.0."""
    header = struct.pack("<BBBBBB", 0xFE, len(data), 0, system_id, component_id, msg_id)
    
    # Simplified CRC
    crc = 0xFFFF
    crc_data = header[1:] + data
    for byte in crc_data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    
    crc_bytes = struct.pack("<H", crc)
    return header + data + crc_bytes

def send_heartbeat(sock, target_addr):
    """Kirim HEARTBEAT message (ID 0)."""
    heartbeat_data = struct.pack("<IBBBBB", 0, 3, 4, 0, 0, 3)
    heartbeat_msg = create_mavlink_message(0, heartbeat_data)
    sock.sendto(heartbeat_msg, target_addr)
    print(f"💓 HEARTBEAT to {target_addr}")

def send_global_position_int(sock, target_addr):
    """Kirim GLOBAL_POSITION_INT message (ID 33)."""
    lat = int(-6.200000 * 1e7)
    lon = int(106.816666 * 1e7)
    alt = 50000
    relative_alt = 50000
    
    position_data = struct.pack("<IiiiihhH", 
        int(time.time() * 1000) % (2**32),
        lat, lon, alt, relative_alt, 0, 0, 0, 0
    )
    position_msg = create_mavlink_message(33, position_data)
    sock.sendto(position_msg, target_addr)
    print(f"📍 POSITION to {target_addr}")

def send_gps_raw_int(sock, target_addr):
    """Kirim GPS_RAW_INT message (ID 24)."""
    gps_data = struct.pack("<QBiiiIHHHB", 
        int(time.time() * 1e6),
        3,
        int(-6.200000 * 1e7),
        int(106.816666 * 1e7),
        50000,
        100, 100, 0, 0, 10
    )
    gps_msg = create_mavlink_message(24, gps_data)
    sock.sendto(gps_msg, target_addr)
    print(f"🛰️ GPS to {target_addr}")

def broadcast_messages():
    """Broadcast messages tanpa SYS_STATUS."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    targets = [("127.0.0.1", 14540)]
    
    print("🚁 Mock Drone Simple Broadcasting...")
    print("Hanya HEARTBEAT dan POSITION saja")
    
    while True:
        try:
            for target in targets:
                send_heartbeat(sock, target)
                send_global_position_int(sock, target)
                send_gps_raw_int(sock, target)
            
            print("📦 Data terkirim")
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n🛑 Mock drone dihentikan")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
    
    sock.close()

if __name__ == "__main__":
    broadcast_messages()
