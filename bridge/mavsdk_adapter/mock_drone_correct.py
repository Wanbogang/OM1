#!/usr/bin/env python3
"""
Mock Drone Server - Simulates MAVLink protocol for testing
Implements realistic drone behavior with socket communication
"""

import socket
import struct
import time
import threading
from typing import Dict, Tuple

class MockDrone:
    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.client_socket = None
        
        # Drone state
        self.position = {"lat": -6.1751, "lon": 106.8650, "alt": 10.0}
        self.battery = {"voltage": 12.6, "percentage": 85.0}
        self.armed = False
        self.flight_mode = "STABILIZE"
        
    def start(self):
        """Start the mock drone server"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        
        print(f"🚁 Mock Drone listening on {self.host}:{self.port}")
        
        try:
            while self.running:
                self.client_socket, addr = self.server_socket.accept()
                print(f"✅ Connected to {addr}")
                
                # Start sending heartbeat
                heartbeat_thread = threading.Thread(target=self._send_heartbeat)
                heartbeat_thread.daemon = True
                heartbeat_thread.start()
                
                # Handle commands
                self._handle_commands()
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down mock drone...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the mock drone server"""
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
    
    def _send_heartbeat(self):
        """Send periodic heartbeat messages"""
        while self.running and self.client_socket:
            try:
                heartbeat = struct.pack('<BBBBBB', 
                    0xFE, 9, 0, 1, 1, 0
                )
                self.client_socket.send(heartbeat)
                time.sleep(1)
            except:
                break
    
    def _handle_commands(self):
        """Handle incoming commands"""
        while self.running and self.client_socket:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                
                if len(data) >= 6:
                    msg_id = data[5]
                    
                    if msg_id == 33:  # Position request
                        self._send_position()
                    elif msg_id == 1:  # Status request
                        self._send_status()
                    else:
                        self._handle_command(data)
                        
            except Exception as e:
                print(f"❌ Command error: {e}")
                break
    
    def _send_position(self):
        """Send current position"""
        try:
            pos_msg = struct.pack('<BBBBBBiiiiHHH',
                0xFE, 28, 0, 1, 1, 33,
                int(self.position["lat"] * 1e7),
                int(self.position["lon"] * 1e7),
                int(self.position["alt"] * 1000),
                0, 0, 0, 0, 0
            )
            self.client_socket.send(pos_msg)
        except:
            pass
    
    def _send_status(self):
        """Send system status"""
        try:
            status_msg = struct.pack('<BBBBBBHHHH',
                0xFE, 11, 0, 1, 1, 1,
                int(self.battery["voltage"] * 1000),
                int(self.battery["percentage"] * 10),
                0, 0
            )
            self.client_socket.send(status_msg)
        except:
            pass
    
    def _handle_command(self, data: bytes):
        """Handle specific commands"""
        try:
            if len(data) >= 10:
                cmd_type = data[6]
                
                if cmd_type == 0x01:  # Arm
                    self.armed = True
                    print("🚁 Drone armed!")
                elif cmd_type == 0x02:  # Disarm
                    self.armed = False
                    print("🛑 Drone disarmed!")
                elif cmd_type == 0x03:  # Goto
                    lat = struct.unpack('<i', data[10:14])[0] / 1e7
                    lon = struct.unpack('<i', data[14:18])[0] / 1e7
                    self.position["lat"] = lat
                    self.position["lon"] = lon
                    print(f"🧭 Going to: {lat}, {lon}")
                    
        except Exception as e:
            print(f"❌ Command error: {e}")

def main():
    drone = MockDrone()
    try:
        drone.start()
    except KeyboardInterrupt:
        print("\n👋 Mock drone stopped")
    finally:
        drone.stop()

if __name__ == "__main__":
    main()
