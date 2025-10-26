#!/usr/bin/env python3
"""
MAVSDK Reader Server - Reads commands from file and sends to drone via MAVSDK
"""

import json
import time
import os
import socket
import struct
from datetime import datetime
import threading

class MAVSDKReader:
    def __init__(self, command_file: str = "drone_commands.json", drone_host: str = "localhost", drone_port: int = 5000):
        self.command_file = command_file
        self.drone_host = drone_host
        self.drone_port = drone_port
        self.running = False
        self.drone_socket = None
        self.processed_commands = set()
        
    def start(self):
        """Start the reader server"""
        self.running = True
        self._connect_to_drone()
        
        processing_thread = threading.Thread(target=self._process_commands)
        processing_thread.daemon = True
        processing_thread.start()
        
        print("🔍 MAVSDK Reader Server started - monitoring for commands...")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Reader server stopped by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the reader server"""
        self.running = False
        if self.drone_socket:
            self.drone_socket.close()
    
    def _connect_to_drone(self):
        """Connect to mock drone"""
        try:
            self.drone_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.drone_socket.connect((self.drone_host, self.drone_port))
            print(f"✅ Connected to drone at {self.drone_host}:{self.drone_port}")
        except Exception as e:
            print(f"❌ Failed to connect to drone: {e}")
            print("⚠️  Make sure mock_drone_correct.py is running!")
    
    def _process_commands(self):
        """Main command processing loop"""
        while self.running:
            try:
                commands = self._read_pending_commands()
                
                for command in commands:
                    if command["id"] not in self.processed_commands:
                        self._execute_command(command)
                        self.processed_commands.add(command["id"])
                        self._mark_command_processed(command["id"])
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing commands: {e}")
                time.sleep(2)
    
    def _read_pending_commands(self):
        """Read pending commands from file"""
        try:
            if not os.path.exists(self.command_file):
                return []
            
            with open(self.command_file, 'r') as f:
                data = json.load(f)
            
            pending = [cmd for cmd in data["commands"] if cmd["status"] == "pending"]
            return pending
            
        except Exception as e:
            print(f"❌ Error reading commands: {e}")
            return []
    
    def _execute_command(self, command):
        """Execute command on drone"""
        cmd_type = command["command"]["type"]
        agent = command["command"]["agent"]
        
        print(f"🚀 Executing {cmd_type} command from {agent}")
        
        try:
            if cmd_type == "goto":
                self._execute_goto(command["command"])
            elif cmd_type == "spray":
                self._execute_spray(command["command"])
            elif cmd_type == "takeoff":
                self._execute_takeoff(command["command"])
            elif cmd_type == "land":
                self._execute_land(command["command"])
            elif cmd_type == "arm":
                self._execute_arm(command["command"])
            elif cmd_type == "disarm":
                self._execute_disarm(command["command"])
            else:
                print(f"⚠️  Unknown command type: {cmd_type}")
                
        except Exception as e:
            print(f"❌ Error executing command: {e}")
    
    def _execute_goto(self, command):
        """Execute goto command"""
        lat = command["latitude"]
        lon = command["longitude"]
        alt = command.get("altitude", 10.0)
        
        print(f"🧭 Going to lat={lat}, lon={lon}, alt={alt}")
        
        if self.drone_socket:
            goto_msg = struct.pack('<BBBBBBiiif',
                0xFE, 22, 0, 1, 1, 0x03,
                int(lat * 1e7), int(lon * 1e7), int(alt * 1000), 0.0
            )
            self.drone_socket.send(goto_msg)
            time.sleep(0.1)
    
    def _execute_spray(self, command):
        """Execute spray command"""
        duration = command.get("duration", 5.0)
        area = command.get("area", [])
        
        print(f"💨 Spraying for {duration}s in area {area}")
        time.sleep(duration)
        print("✅ Spraying completed")
    
    def _execute_takeoff(self, command):
        """Execute takeoff command"""
        altitude = command.get("altitude", 10.0)
        print(f"🛫 Taking off to {altitude}m")
        
        if self.drone_socket:
            takeoff_msg = struct.pack('<BBBBBBf',
                0xFE, 6, 0, 1, 1, 0x04, altitude
            )
            self.drone_socket.send(takeoff_msg)
            time.sleep(0.1)
    
    def _execute_land(self, command):
        """Execute land command"""
        print(f"🛬 Landing")
        
        if self.drone_socket:
            land_msg = struct.pack('<BBBBBB',
                0xFE, 2, 0, 1, 1, 0x05
            )
            self.drone_socket.send(land_msg)
            time.sleep(0.1)
    
    def _execute_arm(self, command):
        """Execute arm command"""
        print(f"🔧 Arming drone")
        
        if self.drone_socket:
            arm_msg = struct.pack('<BBBBBB',
                0xFE, 2, 0, 1, 1, 0x01
            )
            self.drone_socket.send(arm_msg)
            time.sleep(0.1)
    
    def _execute_disarm(self, command):
        """Execute disarm command"""
        print(f"🔧 Disarming drone")
        
        if self.drone_socket:
            disarm_msg = struct.pack('<BBBBBB',
                0xFE, 2, 0, 1, 1, 0x02
            )
            self.drone_socket.send(disarm_msg)
            time.sleep(0.1)
    
    def _mark_command_processed(self, command_id):
        """Mark command as processed in file"""
        try:
            with open(self.command_file, 'r') as f:
                data = json.load(f)
            
            for cmd in data["commands"]:
                if cmd["id"] == command_id:
                    cmd["status"] = "completed"
                    cmd["completed_at"] = datetime.now().isoformat()
                    break
            
            with open(self.command_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error marking command processed: {e}")

def main():
    reader = MAVSDKReader()
    try:
        reader.start()
    except KeyboardInterrupt:
        print("\n🛑 Reader server stopped by user")
    except Exception as e:
        print(f"❌ Reader server error: {e}")

if __name__ == "__main__":
    main()
