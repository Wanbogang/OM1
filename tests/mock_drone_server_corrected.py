#!/usr/bin/env python3
"""Mock drone server dengan format MAVLink yang benar."""
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
    # HEARTBEAT: type, autopilot, base_mode, custom_mode, system_status, mavlink_version
    heartbeat_data = struct.pack("<IBBBBB", 0, 3, 4, 0, 0, 3)  # Fixed: 6 items
    heartbeat_msg = create_mavlink_message(0, heartbeat_data)
    sock.sendto(heartbeat_msg, target_addr)
    print(f"💓 HEARTBEAT to {target_addr}")

def send_global_position_int(sock, target_addr):
    """Kirim GLOBAL_POSITION_INT message (ID 33)."""
    lat = int(-6.200000 * 1e7)  # Jakarta
    lon = int(106.816666 * 1e7)
    alt = 50000
    relative_alt = 50000
    
    # time_boot_ms, lat, lon, alt, relative_alt, vx, vy, vz, hdg
    position_data = struct.pack("<IiiiihhH", 
        int(time.time() * 1000) % (2**32),
        lat, lon, alt, relative_alt, 0, 0, 0, 0
    )
    position_msg = create_mavlink_message(33, position_data)
    sock.sendto(position_msg, target_addr)
    print(f"📍 POSITION to {target_addr}")

def send_sys_status(sock, target_addr):
    """Kirim SYS_STATUS message (ID 1) dengan format yang benar."""
    # SYS_STATUS: onboard_control_sensors_present, enabled, health, load, voltage_battery, current_battery, battery_remaining, drop_rate_comm, errors_comm, errors_count1, errors_count2, errors_count3, errors_count4
    sys_status_data = struct.pack("<IIIhHhbHHHHHH", 
        0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0
    )
    sys_status_msg = create_mavlink_message(1, sys_status_data)
    sock.sendto(sys_status_msg, target_addr)
    print(f"🔋 SYS_STATUS to {target_addr}")

def send_gps_raw_int(sock, target_addr):
    """Kirim GPS_RAW_INT message (ID 24) - lebih sederhana."""
    # time_usec, fix_type, lat, lon, alt, eph, epv, vel, cog, satellites_visible
    gps_data = struct.pack("<QBiiiIHHHB", 
        int(time.time() * 1e6),  # time_usec
        3,                      # 3D fix
        int(-6.200000 * 1e7),   # lat
        int(106.816666 * 1e7),  # lon
        50000,                  # alt in mm
        100, 100, 0, 0, 10     # other params
    )
    gps_msg = create_mavlink_message(24, gps_data)
    sock.sendto(gps_msg, target_addr)
    print(f"🛰️ GPS_RAW_INT to {target_addr}")

def broadcast_messages():
    """Broadcast messages ke multiple ports."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    targets = [
        ("127.0.0.1", 14540),
        ("127.0.0.1", 14541),
        ("127.0.0.1", 14550),
    ]
    
    print("🚁 Mock Drone Broadcasting (format diperbaiki)...")
    print("Targets: 14540, 14541, 14550")
    
    message_count = 0
    while True:
        try:
            for target in targets:
                send_heartbeat(sock, target)
                send_sys_status(sock, target)
                send_global_position_int(sock, target)
                send_gps_raw_int(sock, target)
            
            message_count += 1
            print(f"📦 Broadcast cycle {message_count} selesai")
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
