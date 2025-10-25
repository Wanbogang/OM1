#!/usr/bin/env python3
"""Mock drone dengan MAVLink message yang proper."""
import socket
import time
import struct

# MAVLink message IDs
MAVLINK_MSG_ID_HEARTBEAT = 0
MAVLINK_MSG_ID_GLOBAL_POSITION_INT = 33

def create_mavlink_v1_message(msg_id, data, seq=0, sys_id=1, comp_id=1):
    """Create proper MAVLink v1.0 message."""
    # Header: start sign, payload length, packet sequence, system ID, component ID, message ID
    header = struct.pack("<BBBBBB", 0xFE, len(data), seq, sys_id, comp_id, msg_id)
    
    # Calculate CRC (simplified)
    crc_extra = 0
    if msg_id == MAVLINK_MSG_ID_HEARTBEAT:
        crc_extra = 50
    elif msg_id == MAVLINK_MSG_ID_GLOBAL_POSITION_INT:
        crc_extra = 104
    
    # Simple CRC calculation
    crc = 0xFFFF
    for byte in header[1:] + data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
        crc &= 0xFFFF
    
    crc ^= crc_extra
    return header + data + struct.pack("<H", crc)

def send_heartbeat(sock, target_addr, seq):
    """Send proper HEARTBEAT message."""
    # type, autopilot, base_mode, custom_mode, system_status
    heartbeat_data = struct.pack("<IBBBBB", 
        0,      # type: Generic MAV
        3,      # autopilot: ArduPilot
        81,     # base_mode: MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, MAV_MODE_FLAG_SAFETY_ARMED
        0,      # custom_mode
        4,      # system_status: MAV_STATE_ACTIVE
        3       # mavlink_version
    )
    msg = create_mavlink_v1_message(MAVLINK_MSG_ID_HEARTBEAT, heartbeat_data, seq)
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
    msg = create_mavlink_v1_message(MAVLINK_MSG_ID_GLOBAL_POSITION_INT, position_data, seq)
    sock.sendto(msg, target_addr)
    print(f"📍 POSITION {seq}: Lat={-6.200000}, Lon={106.816666}")

def run_mock_drone():
    """Run proper mock drone."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = ("127.0.0.1", 14540)
    
    print("🚁 Proper Mock Drone Started")
    print("Sending MAVLink messages to 127.0.0.1:14540")
    
    seq = 0
    while True:
        try:
            send_heartbeat(sock, target, seq)
            send_global_position_int(sock, target, seq)
            
            seq += 1
            time.sleep(1)  # Send every 1 second
            
        except KeyboardInterrupt:
            print("\n🛑 Mock drone stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
    
    sock.close()

if __name__ == "__main__":
    run_mock_drone()
