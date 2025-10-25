#!/usr/bin/env python3
"""Mock drone server dengan format struct yang benar."""
import socket
import time
import struct

def create_mavlink_message(msg_id, data, system_id=1, component_id=1):
    """Buat MAVLink message v1.0."""
    header = struct.pack("<BBBBBB", 0xFE, len(data), 0, system_id, component_id, msg_id)
    
    # CRC sederhana
    crc = 0xFFFF
    for byte in header[1:] + data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    
    return header + data + struct.pack("<H", crc)

def send_heartbeat(sock, target_addr):
    """Kirim HEARTBEAT message (ID 0)."""
    # HEARTBEAT format: type, autopilot, base_mode, custom_mode, system_status, mavlink_version
    # Perbaikan: gunakan format yang tepat
    heartbeat_data = struct.pack("<IBBBBB", 
        0,    # type
        3,    # autopilot  
        4,    # base_mode
        0,    # custom_mode
        0,    # system_status
        3     # mavlink_version
    )
    heartbeat_msg = create_mavlink_message(0, heartbeat_data)
    sock.sendto(heartbeat_msg, target_addr)
    print(f"💓 HEARTBEAT sent")

def send_simple_position(sock, target_addr):
    """Kirim POSITION sederhana."""
    try:
        # Buat data posisi sederhana
        lat = -6.200000
        lon = 106.816666
        alt = 50.0
        
        # Format sederhana untuk testing
        position_str = f"POS:{lat},{lon},{alt}"
        sock.sendto(position_str.encode(), target_addr)
        print(f"📍 SIMPLE POSITION sent: {position_str}")
    except Exception as e:
        print(f"Position error: {e}")

def send_raw_mavlink(sock, target_addr):
    """Kirim raw MAVLink heartbeat minimal."""
    try:
        # HEARTBEAT message paling minimal
        # magic, len, seq, sysid, compid, msgid, data
        raw_msg = struct.pack("<BBBBBBIBBBBBH",
            0xFE,           # magic
            9,              # length
            0,              # sequence
            1,              # system ID
            1,              # component ID  
            0,              # message ID (HEARTBEAT)
            0,              # custom mode
            3,              # type
            4,              # autopilot
            0,              # base mode
            0,              # system status
            3,              # mavlink version
            0xFFFF          # crc (dummy)
        )
        sock.sendto(raw_msg, target_addr)
        print(f"📨 RAW MAVLINK sent")
    except Exception as e:
        print(f"Raw mavlink error: {e}")

def broadcast_messages():
    """Broadcast messages."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    target = ("127.0.0.1", 14540)
    
    print("🚁 Mock Drone - Minimal Version")
    print("Mengirim heartbeat sederhana...")
    
    count = 0
    while True:
        try:
            send_heartbeat(sock, target)
            send_simple_position(sock, target)
            send_raw_mavlink(sock, target)
            
            count += 1
            print(f"📦 Cycle {count} completed")
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n🛑 Mock drone stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
    
    sock.close()

if __name__ == "__main__":
    broadcast_messages()
