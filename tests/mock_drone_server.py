#!/usr/bin/env python3
"""Server kecil yang berpura-pura menjadi drone dan mengirim data posisi (versi persisten)."""
import socket
import time
import struct

def send_heartbeat(sock, target_addr):
    """Kirim pesan HEARTBEAT dasar."""
    heartbeat_msg = struct.pack("<BBBBBBBBH", 0xFE, 9, 1, 1, 0, 2, 81, 4, 3)
    sock.sendto(heartbeat_msg, target_addr)

def send_position(sock, target_addr):
    """Kirim pesan GLOBAL_POSITION_INT."""
    lat, lon, alt = int(47.397742 * 1e7), int(8.545594 * 1e7), 500
    position_msg = struct.pack("<BBBBBBBBiiiiHHH", 0xFE, 28, 1, 1, 33, 0, 0, 0, lat, lon, alt, alt, 0, 0, 0)
    sock.sendto(position_msg, target_addr)

def run_mock_drone():
    """Jalankan server drone palsu yang persisten."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", 14540))
    print("🚁 Mock Drone Server berjalan di udp://localhost:14540")
    print("Menunggu MAVSDK adapter untuk terhubung...")

    while True:
        try:
            # Tunggu data apapun dari adapter
            data, addr = sock.recvfrom(1024)
            print(f"Menerima koneksi dari {addr}. Mengirim data posisi...")
            
            # Kirim beberapa pesan
            send_heartbeat(sock, addr)
            send_position(sock, addr)
            time.sleep(0.1)
            send_position(sock, addr)
            print("✅ Data terkirim. Menunggu koneksi berikutnya...")
            # TIDAK ADA 'break' DI SINI, jadi loop akan terus berjalan

        except Exception as e:
            print(f"Error: {e}")
            break
    
    print("Mock Drone dimatikan.")
    sock.close()

if __name__ == "__main__":
    run_mock_drone()
