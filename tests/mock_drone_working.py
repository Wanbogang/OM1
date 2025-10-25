#!/usr/bin/env python3
"""Mock drone yang benar-benar bekerja."""
import socket
import time
import struct

# MAVLink message IDs
MAVLINK_MSG_ID_HEARTBEAT = 0
MAVLINK_MSG_ID_GLOBAL_POSITION_INT = 33

def create_mavlink_message(msg_id, data, seq=0, sys_id=1, comp_id=1):
    """Create MAVLink v1.0 message."""
    header = struct.pack("<BBBBBB", 0xFE, len(data), seq, sys_id, comp_id, msg_id)
    
    # Simple CRC
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

def send_heartbeat(sock, target_addr, seq):
    """Send HEARTBEAT message dengan format yang benar."""
    # Perbaikan: format yang tepat untuk HEARTBEAT
    # custom_mode, type, autopilot, base_mode, system_status, mavlink_version
    heartbeat_data = struct.pack("<IBBBBB", 
        0,    # custom_mode
        0,    # type
        3,    # autopilot  
        81,   # base_mode
        4,    # system_status
        3     # mavlink_version
    )
    msg = create_mavlink_message(MAVLINK_MSG_ID_HEARTBEAT, heartbeat_data, seq)
    sock.sendto(msg, target_addr)
    print(f"💓 HEARTBEAT {seq}")

def send_global_position_int(sock, target_addr, seq):
    """Send GLOBAL_POSITION_INT message."""
    lat = int(-6.200000 * 1e7)   # Degrees * 1e7
    lon = int(106.816666 * 1e7)  # Degrees * 1e7
    alt = 50000                  # Altitude in millimeters
    relative_alt = 50000         # Relative altitude in millimeters
    
    position_data = struct.pack("<IiiiihhH", 
        int(time.time() * 1000),  # time_boot_ms
        lat, lon, alt, relative_alt,  # position
        0, 0, 0,                   # velocity (vx, vy, vz) in cm/s
        0                          # heading in centidegrees
    )
    msg = create_mavlink_message(MAVLINK_MSG_ID_GLOBAL_POSITION_INT, position_data, seq)
    sock.sendto(msg, target_addr)
    print(f"📍 POSITION {seq}: Lat={-6.200000}, Lon={106.816666}")

def send_gps_raw_int(sock, target_addr, seq):
    """Send GPS_RAW_INT message."""
    gps_data = struct.pack("<QBiiiIHHHB", 
        int(time.time() * 1e6),  # time_usec
        3,                       # fix_type
        int(-6.200000 * 1e7),    # lat
        int(106.816666 * 1e7),   # lon
        50000,                   # alt
        100, 100, 0, 0, 10      # other params
    )
    msg = create_mavlink_message(24, gps_data, seq)
    sock.sendto(msg, target_addr)
    print(f"🛰️ GPS {seq}")

def run_mock_drone():
    """Run working mock drone."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = ("127.0.0.1", 14540)
    
    print("🚁 Working Mock Drone Started")
    print("Sending proper MAVLink messages...")
    
    seq = 0
    while True:
        try:
            send_heartbeat(sock, target, seq)
            send_global_position_int(sock, target, seq)
            send_gps_raw_int(sock, target, seq)
            
            seq += 1
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n🛑 Mock drone stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
    
    sock.close()

if __name__ == "__main__":
    run_mock_drone()
