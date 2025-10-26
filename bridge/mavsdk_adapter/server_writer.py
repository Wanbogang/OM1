#!/usr/bin/env python3
"""
MAVSDK Writer Server - Receives commands from agents and writes to shared file
"""

import json
import time
import os
from datetime import datetime
from flask import Flask, request, jsonify

class MAVSDKWriter:
    def __init__(self, command_file: str = "drone_commands.json"):
        self.command_file = command_file
        self.last_command_id = 0
        self._init_command_file()
        
    def _init_command_file(self):
        """Initialize the shared command file"""
        initial_data = {
            "timestamp": datetime.now().isoformat(),
            "commands": [],
            "status": "ready"
        }
        with open(self.command_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        print(f"📝 Command file initialized: {self.command_file}")
    
    def start(self):
        """Start the writer server"""
        app = Flask(__name__)
        
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy",
                "service": "mavsdk_writer",
                "timestamp": datetime.now().isoformat()
            })
        
        @app.route('/command', methods=['POST'])
        def receive_command():
            try:
                command_data = request.json
                
                if not self._validate_command(command_data):
                    return jsonify({"error": "Invalid command"}), 400
                
                self.last_command_id += 1
                command = {
                    "id": self.last_command_id,
                    "timestamp": datetime.now().isoformat(),
                    "command": command_data,
                    "status": "pending"
                }
                
                self._write_command(command)
                print(f"📨 Received command: {command_data['type']}")
                
                return jsonify({
                    "success": True,
                    "command_id": self.last_command_id,
                    "status": "queued"
                })
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @app.route('/status', methods=['GET'])
        def get_status():
            try:
                with open(self.command_file, 'r') as f:
                    data = json.load(f)
                return jsonify({
                    "status": data["status"],
                    "pending_commands": len([c for c in data["commands"] if c["status"] == "pending"]),
                    "total_commands": len(data["commands"])
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        print("🚀 MAVSDK Writer Server starting on port 5002...")
        app.run(host='0.0.0.0', port=5002, debug=False)
    
    def _validate_command(self, command: dict) -> bool:
        """Validate command structure"""
        required_fields = ['type', 'agent']
        for field in required_fields:
            if field not in command:
                return False
        
        valid_types = ['goto', 'spray', 'takeoff', 'land', 'arm', 'disarm']
        if command['type'] not in valid_types:
            return False
        
        if command['type'] == 'goto':
            if 'latitude' not in command or 'longitude' not in command:
                return False
        
        return True
    
    def _write_command(self, command: dict):
        """Write command to shared file"""
        try:
            with open(self.command_file, 'r') as f:
                data = json.load(f)
            
            data["commands"].append(command)
            data["timestamp"] = datetime.now().isoformat()
            
            if len(data["commands"]) > 100:
                data["commands"] = data["commands"][-100:]
            
            with open(self.command_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error writing command: {e}")

def main():
    writer = MAVSDKWriter()
    try:
        writer.start()
    except KeyboardInterrupt:
        print("\n🛑 Writer server stopped")
    except Exception as e:
        print(f"❌ Writer server error: {e}")

if __name__ == "__main__":
    main()
