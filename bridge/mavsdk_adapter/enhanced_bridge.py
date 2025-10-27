#!/usr/bin/env python3
"""
Enhanced Bridge for Smart Farm Drone System
Complete automated workflow: GPS simulation → REAL OpenCV disease detection → Spray commands
Integrated with real computer vision perception agent
"""

import requests
import time
import random
import json
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add perception agent path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../agents/perception_agent'))

from opencv_perception_agent import OpenCVPerceptionAgent

class EnhancedBridge:
    def __init__(self):
        self.mavsdk_writer_url = "http://localhost:5002"
        self.gps_data = {
            "latitude": -6.9175,
            "longitude": 107.6191,
            "altitude": 50.0,
            "timestamp": datetime.now().isoformat()
        }
        self.disease_count = 0
        self.last_spray_time = None
        
        # REAL OPENCV PERCEPTION AGENT
        self.perception_agent = OpenCVPerceptionAgent()
        self.test_image_path = "../../agents/perception_agent/test_sick_plant.jpg"
        
        # Check if test image exists
        if not os.path.exists(self.test_image_path):
            print(f"⚠️  Test image not found: {self.test_image_path}")
            print("   Using healthy image for testing...")
            self.test_image_path = "../../agents/perception_agent/test_plant_image.jpg"
        
    def simulate_gps_movement(self):
        """Simulate GPS movement for drone patrol"""
        lat_offset = random.uniform(-0.001, 0.001)
        lon_offset = random.uniform(-0.001, 0.001)
        alt_offset = random.uniform(-5, 5)
        
        self.gps_data["latitude"] += lat_offset
        self.gps_data["longitude"] += lon_offset
        self.gps_data["altitude"] = max(20, min(100, self.gps_data["altitude"] + alt_offset))
        self.gps_data["timestamp"] = datetime.now().isoformat()
        
        return self.gps_data
    
    def detect_disease_with_opencv(self) -> Optional[Dict]:
        """Use real OpenCV detection instead of simulation"""
        try:
            # Use real computer vision
            result = self.perception_agent.detect_disease_from_image(self.test_image_path)
            
            if result and result.get("command_type") == "spray":
                # Add GPS coordinates to detected disease
                result["target_location"]["gps_coordinates"] = {
                    "latitude": self.gps_data["latitude"],
                    "longitude": self.gps_data["longitude"],
                    "altitude": self.gps_data["altitude"]
                }
                
                self.disease_count += 1
                self.last_spray_time = datetime.now()
                
                print(f"🔍 REAL DETECTION: {result['disease_info']['disease_name'].title()}")
                print(f"   Confidence: {result['disease_info']['confidence']:.2f}")
                print(f"   Image Location: {result['target_location']['image_coordinates']}")
                print(f"   GPS Location: {result['target_location']['gps_coordinates']['latitude']:.6f}, {result['target_location']['gps_coordinates']['longitude']:.6f}")
                print(f"   Treatment: {result['spray_parameters']['substance']}")
                print(f"   Quantity: {result['spray_parameters']['quantity']}L for {result['spray_parameters']['duration']}s")
                
                return result
            else:
                print("🔍 Real detection: No disease found - plant appears healthy")
                return None
                
        except Exception as e:
            print(f"❌ Error in real detection: {e}")
            return None
    
    def generate_spray_command_from_opencv(self, detection_result: Dict) -> Dict:
        """Generate spray command from OpenCV detection result"""
        command = {
            "type": "spray",  # HARUS 'type' bukan 'command_type'
            "agent": "perception_agent",  # WAJIB ada field 'agent'
            "latitude": detection_result["target_location"]["gps_coordinates"]["latitude"],
            "longitude": detection_result["target_location"]["gps_coordinates"]["longitude"],
            "altitude": detection_result["target_location"]["gps_coordinates"]["altitude"],
            "substance": detection_result["spray_parameters"]["substance"],
            "quantity": float(detection_result["spray_parameters"]["quantity"]),
            "duration": int(detection_result["spray_parameters"]["duration"]),
            "confidence": detection_result["disease_info"]["confidence"],
            "disease_info": detection_result["disease_info"],
            "timestamp": datetime.now().isoformat()
        }
        
        return command
    
    def send_spray_command(self, command: Dict) -> bool:
        """Send spray command to MAVSDK Writer"""
        try:
            response = requests.post(
                f"{self.mavsdk_writer_url}/command",
                json=command,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Spray command sent to MAVSDK Writer!")
                print(f"   Command ID: {result.get('command_id')}")
                print(f"   Status: {result.get('status')}")
                print(f"   Target GPS: {command['latitude']:.6f}, {command['longitude']:.6f}")
                print(f"   Substance: {command['substance']}")
                print(f"   Quantity: {command['quantity']}L")
                print(f"   Duration: {command['duration']}s")
                print(f"   Confidence: {command['confidence']:.2f}")
                return True
            else:
                print(f"❌ Failed to send command: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending command: {e}")
            return False
    
    def check_mavsdk_writer_status(self) -> bool:
        """Check if MAVSDK Writer is running"""
        try:
            response = requests.get(f"{self.mavsdk_writer_url}/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"📡 MAVSDK Writer Status: ✅ Connected")
                print(f"   Pending commands: {status.get('pending_commands', 0)}")
                print(f"   Processed commands: {status.get('processed_commands', 0)}")
                return True
        except:
            pass
        print(f"📡 MAVSDK Writer Status: ❌ Connection failed")
        return False
    
    def run_automated_workflow(self):
        """Run the complete automated workflow with REAL computer vision"""
        print("🚁 Enhanced Bridge with REAL OpenCV Computer Vision")
        print("=" * 60)
        
        # Check MAVSDK Writer status
        if not self.check_mavsdk_writer_status():
            print("❌ MAVSDK Writer is not running. Please start it first.")
            print("   Run: python server_writer.py")
            return
        
        print("\n🔄 Starting automated workflow with REAL Computer Vision...")
        print("   - GPS simulation: Active")
        print("   - OpenCV disease detection: ACTIVE") 
        print("   - Spray commands: Auto-generated from real detection")
        print("   - Image analysis: Real-time processing")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                print(f"\n--- Cycle {cycle_count} ---")
                
                # 1. Update GPS position
                gps_data = self.simulate_gps_movement()
                print(f"📍 GPS Position: {gps_data['latitude']:.6f}, {gps_data['longitude']:.6f}, Alt: {gps_data['altitude']:.1f}m")
                
                # 2. REAL disease detection with OpenCV
                disease_info = self.detect_disease_with_opencv()
                
                if disease_info:
                    print(f"🎯 REAL DISEASE DETECTED! Processing spray command...")
                    
                    # 3. Generate and send spray command from real detection
                    spray_command = self.generate_spray_command_from_opencv(disease_info)
                    self.send_spray_command(spray_command)
                else:
                    print("🔍 No disease detected - continuing patrol")
                
                # 4. Wait before next cycle
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            print("\n\n🛑 Workflow stopped by user")
            print("📊 Summary:")
            print(f"   Total cycles: {cycle_count}")
            print(f"   Diseases detected: {self.disease_count}")
            print(f"   Detection method: REAL OpenCV Computer Vision")
            if self.last_spray_time:
                print(f"   Last detection: {self.last_spray_time.strftime('%H:%M:%S')}")
            
            # Final status check
            print("\n📡 Final MAVSDK Writer Status:")
            self.check_mavsdk_writer_status()

def main():
    """Main function"""
    bridge = EnhancedBridge()
    bridge.run_automated_workflow()

if __name__ == "__main__":
    main()
