# Add these imports at the top
import sys
import os
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
        
        # ADD OPENCV AGENT
        self.perception_agent = OpenCVPerceptionAgent()
        self.test_image_path = "../../agents/perception_agent/test_sick_plant.jpg"        
        # Store latest data
        self.latest_data = {
            'gps': None,
            'disease_detections': []
        }
        
        # Disease detection cache
        self.last_spray_time = 0
        self.spray_cooldown = 30
        
        print("🚀 Enhanced Bridge initialized")
        
    def start(self):
        """Start the enhanced bridge"""
        self.running = True
        print("🚀 Starting Enhanced Bridge...")
        
        # Test MAVSDK connection
        if not self._test_mavsdk_connection():
            print("❌ Cannot connect to MAVSDK Writer")
            return False
        
        # Start background threads
        self._start_background_threads()
        
        # Start GPS simulation
        self._start_gps_simulation()
        
        print("✅ Enhanced Bridge started successfully!")
        return True
        
    def stop(self):
        """Stop the bridge"""
        self.running = False
        print("🛑 Enhanced Bridge stopped")
        
    def _test_mavsdk_connection(self):
        """Test connection to MAVSDK Writer"""
        try:
            response = requests.get(f"{self.mavsdk_writer_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Connected to MAVSDK Writer")
                return True
            else:
                print(f"❌ MAVSDK Writer returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to MAVSDK Writer: {e}")
            return False
    
    def _start_background_threads(self):
        """Start background processing threads"""
        # Disease detection processing thread
        threading.Thread(target=self._disease_processing_loop, daemon=True).start()
        
        # Status monitoring thread
        threading.Thread(target=self._status_monitoring_loop, daemon=True).start()
        
        print("✅ Background threads started")
        
    def _start_gps_simulation(self):
        """Start GPS data simulation"""
        threading.Thread(target=self._gps_simulation_loop, daemon=True).start()
        print("✅ GPS simulation started")
        
    def _gps_simulation_loop(self):
        """Simulate GPS data"""
        while self.running:
            # Simulate GPS movement around Jakarta
            self.latest_data['gps'] = {
                'latitude': -6.2088 + (random.random() - 0.5) * 0.001,
                'longitude': 106.8456 + (random.random() - 0.5) * 0.001,
                'altitude': 100.0 + (random.random() - 0.5) * 10.0,
                'timestamp': time.time()
            }
            time.sleep(0.1)  # 10Hz
    
    def _disease_processing_loop(self):
        """Process disease detections and trigger spraying"""
        while self.running:
            current_time = time.time()
            
            # Simulate random disease detection
            if random.random() < 0.1:  # 10% chance every 5 seconds
                self._simulate_disease_detection()
            
            # Check if we have disease detections
            if self.latest_data['disease_detections']:
                latest_disease = self.latest_data['disease_detections'][-1]
                
                # Check cooldown and trigger spraying
                if (current_time - self.last_spray_time > self.spray_cooldown and 
                    latest_disease['severity'] in ['medium', 'high']):
                    
                    self._send_spray_command(
                        latest_disease['location']['latitude'],
                        latest_disease['location']['longitude'],
                        flow_rate=5.0,
                        duration=10.0
                    )
                    
                    self.last_spray_time = current_time
                    
            time.sleep(5.0)
    
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
            print(f"   Location: {result['target_location']['image_coordinates']}")
            print(f"   Treatment: {result['spray_parameters']['substance']}")
            
            return result
        else:
            print("🔍 Real detection: No disease found")
            return None
            
    except Exception as e:
        print(f"❌ Error in real detection: {e}")
        return None        
        self.latest_data['disease_detections'].append(disease)
        print(f"🔍 Disease detected: {disease['disease']} (Severity: {disease['severity']}) at {disease['location']['latitude']:.6f}, {disease['location']['longitude']:.6f}")
    
    def _status_monitoring_loop(self):
        """Monitor system status"""
        while self.running:
            gps_status = "✅" if self.latest_data['gps'] else "❌"
            
            print(f"📊 Status: GPS{gps_status} Diseases: {len(self.latest_data['disease_detections'])} Last Spray: {time.strftime('%H:%M:%S', time.localtime(self.last_spray_time)) if self.last_spray_time > 0 else 'Never'}")
            
            time.sleep(10.0)
    
    def _send_spray_command(self, latitude: float, longitude: float, flow_rate: float, duration: float):
        """Send spray command to MAVSDK"""
        command = {
            "type": "spray",
            "agent": "enhanced_bridge",
            "latitude": latitude,
            "longitude": longitude,
            "flow_rate": flow_rate,
            "duration": duration
        }
        
        try:
            response = requests.post(
                f"{self.mavsdk_writer_url}/command",
                json=command,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Spray command sent: {flow_rate}L/min for {duration}s at {latitude:.6f}, {longitude:.6f}")
            else:
                print(f"❌ Failed to send spray command: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error sending spray command: {e}")

def main():
    """Main entry point"""
    bridge = EnhancedBridge()
    
    try:
        if bridge.start():
            print("🎯 Enhanced Bridge running! Press Ctrl+C to stop...")
            
            # Keep the bridge running
            while True:
                time.sleep(1)
        else:
            print("❌ Failed to start Enhanced Bridge")
            
    except KeyboardInterrupt:
        print("\n🛑 Enhanced Bridge stopped by user")
        bridge.stop()
    except Exception as e:
        print(f"❌ Bridge error: {e}")
        bridge.stop()

if __name__ == "__main__":
    main()
