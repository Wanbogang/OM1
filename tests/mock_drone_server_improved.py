#!/usr/bin/env python3
"""Mock drone server dengan MAVLink message yang lebih lengkap dan benar."""
import socket
import time
import struct
import threading

# MAVLink 1.0 packet format
def create_mavlink_message(msg_id, data, system_id=1, component_id=1):
    """Buat MAVLink message v1.0 yang benar."""
    # MAVLink 1.0 header: magic, length, seq, sysid, compid, msgid
    header = struct.pack("<BBBBBB", 0xFE, len(data), 0, system_id, component_id, msg_id)
    
    # Calculate CRC (disederhanakan untuk demo)
    crc = 0xFFFF
    crc_data = header[1:] + data  # Exclude magic byte
    for byte in crc_data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    
    # Pack CRC little endian
    crc_bytes = struct.pack("<H", crc)
    
    return header + data + crc_bytes

def send_heartbeat(sock, target_addr):
    """Kirim HEARTBEAT message (ID 0)."""
    # HEARTBEAT data: type, autopilot, base_mode, custom_mode, system_status
    heartbeat_data = struct.pack("<IBBBBB", 0, 3, 4, 0, 0, 0)
    heartbeat_msg = create_mavlink_message(0, heartbeat_data)
    sock.sendto(heartbeat_msg, target_addr)
    print("💓 HEARTBEAT sent")

def send_global_position_int(sock, target_addr):
    """Kirim GLOBAL_POSITION_INT message (ID 33)."""
    lat = int(47.397742 * 1e7)  # Degrees * 1e7
    lon = int(8.545594 * 1e7)   # Degrees * 1e7
    alt = 50000                 # Millimeters
    relative_alt = 50000        # Millimeters
    
    # time_boot_ms, lat, lon, alt, relative_alt, vx, vy, vz, hdg
    position_data = struct.pack("<IiiiihhH", 
        int(time.time() * 1000) % (2**32),  # time_boot_ms
        lat, lon, alt, relative_alt,        # position
        0, 0, 0, 0                         # velocity and heading
    )
    position_msg = create_mavlink_message(33, position_data)
    sock.sendto(position_msg, target_addr)
    print("📍 GLOBAL_POSITION_INT sent")

def send_sys_status(sock, target_addr):
    """Kirim SYS_STATUS message (ID 1)."""
    # onboard_control_sensors_present, enabled, health, load, voltage_battery, current_battery, battery_remaining, drop_rate_comm, errors_comm, errors_count1, errors_count2, errors_count3, errors_count4
    sys_status_data = struct.pack("<IIIhHhbHHHHHH", 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0)
    sys_status_msg = create_mavlink_message(1, sys_status_data)
    sock.sendto(sys_status_msg, target_addr)
    print("🔋 SYS_STATUS sent")

def handle_client(sock, addr):
    """Handle koneksi dari MAVSDK client."""
    print(f"🚁 Terhubung dengan MAVSDK client: {addr}")
    
    try:
        # Kirim paket secara periodik
        while True:
            send_heartbeat(sock, addr)
            send_sys_status(sock, addr) 
            send_global_position_int(sock, addr)
            time.sleep(1)  # Kirim setiap 1 detik
            
    except Exception as e:
        print(f"❌ Error dengan client {addr}: {e}")

def run_mock_drone():
    """Jalankan mock drone server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", 14540))
    sock.settimeout(1.0)
    
    print("🚁 Mock Drone Server berjalan di udp://localhost:14540")
    print("Menunggu MAVSDK adapter untuk terhubung...")
    
    clients = {}
    
    while True:
        try:
            # Terima data dari client
            data, addr = sock.recvfrom(1024)
            
            if addr not in clients:
                # Client baru, mulai thread untuk handle client ini
                clients[addr] = True
                client_thread = threading.Thread(
                    target=handle_client, 
                    args=(sock, addr),
                    daemon=True
                )
                client_thread.start()
                print(f"✅ Memulai handler untuk client {addr}")
                
        except socket.timeout:
            continue  # Timeout normal, continue looping
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    print("Mock Drone dimatikan.")
    sock.close()

if __name__ == "__main__":
    run_mock_drone()
