#!/usr/bin/env python3
"""
ROS2-MAVSDK Bridge - Connects ROS2 Smart Farm nodes to existing MAVSDK system
Bridges ROS2 topics to MAVSDK Writer REST API (Port 5002)
"""

import json
import time
import threading
import requests
import math
from datetime import datetime
from typing import Dict, Any, Optional

# Mock ROS2 classes (since we don't have ROS2 installed)
class MockSubscriber:
    def __init__(self, topic_name, callback, msg_type):
        self.topic_name = topic_name
        self.callback = callback
        self.msg_type = msg_type
        self.running = False
        
class MockNode:
    def __init__(self, node_name):
        self.node_name = node_name
        self.subscribers = []
        self.logger = MockLogger()
        
    def create_subscription(self, msg_type, topic_name, callback, qos_profile=10):
        sub = MockSubscriber(topic_name, callback, msg_type)
        self.subscribers.append(sub)
        return sub
        
    def spin(self):
        pass

class MockLogger:
    def info(self, msg):
        print(f"[INFO] {datetime.now()}: {msg}")
    
    def warn(self, msg):
        print(f"[WARN] {datetime.now()}: {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {datetime.now()}: {msg}")

class ROS2MAVSDKBridge:
    def __init__(self):
        self.node = MockNode("ros2_mavsdk_bridge")
        self.mavsdk_writer_url = "http://localhost:5002"
        self.running = False
        
        # Store latest data from ROS2 topics
        self.latest_data = {
            'gps': None,
            'sprayer': None,
            'camera': None,
            'mavlink': None,
            'multispectral': None
        }
        
        # Disease detection cache
        self.disease_detections = []
        self.last_spray_time = 0
        self.spray_cooldown = 30  # 30 seconds between spray commands
        
        self.node.logger.info("ROS2-MAVSDK Bridge initialized")
        
    def start(self):
        """Start the bridge"""
        self.running = True
        self.node.logger.info("Starting ROS2-MAVSDK Bridge...")
        
        # Create ROS2 subscriptions
        self._setup_subscriptions()
        
        # Start background threads
        self._start_background_threads()
        
        # Test MAVSDK connection
        self._test_mavsdk_connection()
        
        self.node.logger.info("ROS2-MAVSDK Bridge started successfully!")
        
    def stop(self):
        """Stop the bridge"""
        self.running = False
        self.node.logger.info("ROS2-MAVSDK Bridge stopped")
        
    def _setup_subscriptions(self):
        """Setup ROS2 topic subscriptions"""
        # GPS subscription
        self.node.create_subscription(
            self.MockNavSatFix, 
            "/gps/fix", 
            self._gps_callback
        )
        
        # Sprayer subscription
        self.node.create_subscription(
            self.MockString,
            "/sprayer/status", 
            self._sprayer_callback
        )
        
        # Camera subscription
        self.node.create_subscription(
            self.MockImage,
            "/camera/image_raw",
            self._camera_callback
        )
        
        # MAVLink telemetry subscription
        self.node.create_subscription(
            self.MockString,
            "/mavlink/telemetry",
            self._mavlink_callback
        )
        
        # Multispectral/NDVI subscription
        self.node.create_subscription(
            self.MockString,
            "/multispectral/ndvi",
            self._multispectral_callback
        )
        
        self.node.logger.info("ROS2 subscriptions created")
        
    def _start_background_threads(self):
        """Start background processing threads"""
        # GPS navigation thread
        threading.Thread(target=self._gps_navigation_loop, daemon=True).start()
        
        # Disease detection processing thread
        threading.Thread(target=self._disease_processing_loop, daemon=True).start()
        
        # Status monitoring thread
        threading.Thread(target=self._status_monitoring_loop, daemon=True).start()
        
        self.node.logger.info("Background threads started")
        
    def _test_mavsdk_connection(self):
        """Test connection to MAVSDK Writer"""
        try:
            response = requests.get(f"{self.mavsdk_writer_url}/health", timeout=5)
            if response.status_code == 200:
                self.node.logger.info("✅ Connected to MAVSDK Writer")
                return True
            else:
                self.node.logger.error(f"❌ MAVSDK Writer returned status {response.status_code}")
                return False
        except Exception as e:
            self.node.logger.error(f"❌ Cannot connect to MAVSDK Writer: {e}")
            return False
    
    # ROS2 Callback Functions
    def _gps_callback(self, msg):
        """Handle GPS data"""
        self.latest_data['gps'] = {
            'latitude': msg.latitude,
            'longitude': msg.longitude,
            'altitude': msg.altitude,
            'timestamp': time.time()
        }
        
    def _sprayer_callback(self, msg):
        """Handle sprayer status"""
        try:
            status = json.loads(msg.data)
            self.latest_data['sprayer'] = status
        except:
            pass
            
    def _camera_callback(self, msg):
        """Handle camera data"""
        self.latest_data['camera'] = {
            'width': msg.width,
            'height': msg.height,
            'timestamp': time.time()
        }
        
    def _mavlink_callback(self, msg):
        """Handle MAVLink telemetry"""
        try:
            telemetry = json.loads(msg.data)
            self.latest_data['mavlink'] = telemetry
        except:
            pass
            
    def _multispectral_callback(self, msg):
        """Handle multispectral/NDVI data"""
        try:
            ndvi_data = json.loads(msg.data)
            self.latest_data['multispectral'] = ndvi_data
            
            # Check for disease detection
            if 'ndvi_value' in ndvi_data:
                self._process_disease_detection(ndvi_data)
        except:
            pass
    
    def _process_disease_detection(self, ndvi_data):
        """Process NDVI data for disease detection"""
        ndvi = ndvi_data.get('ndvi_value', 0.5)
        vegetation_health = ndvi_data.get('vegetation_health', 'moderate_vegetation')
        
        # Simulate disease detection based on NDVI
        if ndvi < 0.3 and vegetation_health in ['bare_soil', 'sparse_vegetation']:
            # Simulate disease detection
            disease = {
                'id': f"disease_{int(time.time())}",
                'timestamp': time.time(),
                'disease': 'Leaf Blight',
                'confidence': 0.8,
                'location': {
                    'latitude': self.latest_data['gps']['latitude'] if self.latest_data['gps'] else 35.6762,
                    'longitude': self.latest_data['gps']['longitude'] if self.latest_data['gps'] else 139.6503
                },
                'severity': 'high' if ndvi < 0.2 else 'medium',
                'ndvi': ndvi
            }
            
            self.disease_detections.append(disease)
            self.node.logger.info(f"🔍 Disease detected: {disease['disease']} at {disease['location']['latitude']:.6f}, {disease['location']['longitude']:.6f}")
    
    # Background Processing Loops
    def _gps_navigation_loop(self):
        """Process GPS data for navigation"""
        while self.running:
            if self.latest_data['gps']:
                gps_data = self.latest_data['gps']
                
                # Check if drone needs to move to treatment area
                if self.disease_detections:
                    latest_disease = self.disease_detections[-1]
                    
                    # Calculate distance to disease location
                    distance = self._calculate_distance(
                        gps_data['latitude'], gps_data['longitude'],
                        latest_disease['location']['latitude'], latest_disease['location']['longitude']
                    )
                    
                    # If far from disease location, send goto command
                    if distance > 5.0:  # 5 meters threshold
                        self._send_goto_command(
                            latest_disease['location']['latitude'],
                            latest_disease['location']['longitude'],
                            20.0  # 20m altitude
                        )
                        
            time.sleep(2.0)  # Check every 2 seconds
    
    def _disease_processing_loop(self):
        """Process disease detections and trigger spraying"""
        while self.running:
            current_time = time.time()
            
            # Check if we have recent disease detections
            if self.disease_detections:
                latest_disease = self.disease_detections[-1]
                
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
                    
            time.sleep(5.0)  # Check every 5 seconds
    
    def _status_monitoring_loop(self):
        """Monitor system status and send updates"""
        while self.running:
            # Log current status
            gps_status = "✅" if self.latest_data['gps'] else "❌"
            sprayer_status = "✅" if self.latest_data['sprayer'] else "❌"
            camera_status = "✅" if self.latest_data['camera'] else "❌"
            
            self.node.logger.info(f"📊 Status: GPS{gps_status} Sprayer{sprayer_status} Camera{camera_status} Diseases: {len(self.disease_detections)}")
            
            time.sleep(10.0)  # Log every 10 seconds
    
    # MAVSDK Command Functions
    def _send_goto_command(self, latitude: float, longitude: float, altitude: float):
        """Send goto command to MAVSDK"""
        command = {
            "type": "goto",
            "agent": "ros2_bridge",
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude
        }
        
        try:
            response = requests.post(
                f"{self.mavsdk_writer_url}/command",
                json=command,
                timeout=5
            )
            
            if response.status_code == 200:
                self.node.logger.info(f"✅ Goto command sent: {latitude:.6f}, {longitude:.6f}, {altitude}m")
            else:
                self.node.logger.error(f"❌ Failed to send goto command: {response.status_code}")
                
        except Exception as e:
            self.node.logger.error(f"❌ Error sending goto command: {e}")
    
    def _send_spray_command(self, latitude: float, longitude: float, flow_rate: float, duration: float):
        """Send spray command to MAVSDK"""
        command = {
            "type": "spray",
            "agent": "ros2_bridge",
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
                self.node.logger.info(f"✅ Spray command sent: {flow_rate}L/min for {duration}s at {latitude:.6f}, {longitude:.6f}")
            else:
                self.node.logger.error(f"❌ Failed to send spray command: {response.status_code}")
                
        except Exception as e:
            self.node.logger.error(f"❌ Error sending spray command: {e}")
    
    def _send_takeoff_command(self):
        """Send takeoff command"""
        command = {
            "type": "takeoff",
            "agent": "ros2_bridge",
            "altitude": 20.0
        }
        
        try:
            response = requests.post(
                f"{self.mavsdk_writer_url}/command",
                json=command,
                timeout=5
            )
            
            if response.status_code == 200:
                self.node.logger.info("✅ Takeoff command sent")
            else:
                self.node.logger.error(f"❌ Failed to send takeoff command: {response.status_code}")
                
        except Exception as e:
            self.node.logger.error(f"❌ Error sending takeoff command: {e}")
    
    # Utility Functions
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    # Mock classes for ROS2 message types
    class MockNavSatFix:
        def __init__(self):
            self.latitude = 0.0
            self.longitude = 0.0
            self.altitude = 0.0
    
    class MockString:
        def __init__(self):
            self.data = ""
    
    class MockImage:
        def __init__(self):
            self.width = 640
            self.height = 480

def main():
    """Main entry point"""
    bridge = ROS2MAVSDKBridge()
    
    try:
        bridge.start()
        
        # Keep the bridge running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 ROS2-MAVSDK Bridge stopped by user")
        bridge.stop()
    except Exception as e:
        print(f"❌ Bridge error: {e}")
        bridge.stop()

if __name__ == "__main__":
    main()
