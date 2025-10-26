#!/usr/bin/env python3
"""
Perception Agent - Computer vision for crop disease detection
Provides REST API for image processing and disease detection
"""

import json
import base64
import io
from datetime import datetime
from flask import Flask, request, jsonify
import requests

class PerceptionAgent:
    def __init__(self, mavsdk_url: str = "http://localhost:5002"):
        self.mavsdk_url = mavsdk_url
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy",
                "service": "perception_agent",
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/detect', methods=['POST'])
        def detect_disease():
            """Detect disease in uploaded image"""
            try:
                if 'image' not in request.files:
                    return jsonify({"error": "No image file provided"}), 400
                
                image_file = request.files['image']
                if image_file.filename == '':
                    return jsonify({"error": "No image selected"}), 400
                
                image_bytes = image_file.read()
                results = self._process_image(image_bytes)
                
                if results.get("detections"):
                    self._handle_disease_detection(results)
                
                return jsonify({
                    "success": True,
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/detect_base64', methods=['POST'])
        def detect_base64():
            """Detect disease in base64 encoded image"""
            try:
                data = request.json
                
                if 'image' not in data:
                    return jsonify({"error": "No image data provided"}), 400
                
                image_data = base64.b64decode(data['image'])
                results = self._process_image(image_data)
                
                if results.get("detections"):
                    self._handle_disease_detection(results)
                
                return jsonify({
                    "success": True,
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """Get agent status"""
            return jsonify({
                "agent": "perception",
                "status": "active",
                "mavsdk_connected": self._test_mavsdk_connection(),
                "capabilities": [
                    "disease_detection",
                    "coordinate_extraction",
                    "severity_assessment"
                ]
            })
    
    def _process_image(self, image_bytes):
        """Process image and detect diseases"""
        try:
            # Mock disease detection (nanti diganti ONNX)
            detections = self._mock_disease_detection()
            
            # Extract coordinates for detected diseases
            coordinates = self._extract_coordinates(detections)
            
            results = {
                "image_shape": [1080, 1920, 3],  # Mock dimensions
                "detections": detections,
                "coordinates": coordinates,
                "processing_time": 0.1,
                "confidence_threshold": 0.5
            }
            
            return results
            
        except Exception as e:
            print(f"❌ Error processing image: {e}")
            return {"error": str(e)}
    
    def _mock_disease_detection(self):
        """Mock disease detection (akan diganti ONNX nanti)"""
        detections = [
            {
                "class": "leaf_blight",
                "confidence": 0.85,
                "bbox": {
                    "x": 576, "y": 432, "width": 192, "height": 108
                },
                "severity": "moderate"
            },
            {
                "class": "pest_damage",
                "confidence": 0.72,
                "bbox": {
                    "x": 1152, "y": 216, "width": 154, "height": 130
                },
                "severity": "severe"
            }
        ]
        return detections
    
    def _extract_coordinates(self, detections):
        """Extract GPS coordinates for detected areas"""
        coordinates = []
        
        # Mock GPS coordinates (Jakarta)
        base_lat = -6.1751
        base_lon = 106.8650
        
        for i, detection in enumerate(detections):
            bbox = detection["bbox"]
            center_x = bbox["x"] + bbox["width"] / 2
            center_y = bbox["y"] + bbox["height"] / 2
            
            # Convert pixel to GPS offsets (mock)
            lat_offset = (center_y - 540) * 0.00001
            lon_offset = (center_x - 960) * 0.00001
            
            coordinates.append({
                "latitude": base_lat + lat_offset,
                "longitude": base_lon + lon_offset,
                "detection": detection["class"],
                "confidence": detection["confidence"],
                "severity": detection["severity"]
            })
        
        return coordinates
    
    def _handle_disease_detection(self, results):
        """Handle disease detection by sending commands to other agents"""
        try:
            coordinates = results.get("coordinates", [])
            
            for coord in coordinates:
                if coord["confidence"] > 0.7:
                    self._send_goto_command(coord)
                    
                    if coord["severity"] == "severe":
                        self._send_spray_command(coord)
        
        except Exception as e:
            print(f"❌ Error handling disease detection: {e}")
    
    def _send_goto_command(self, coordinate):
        """Send goto command to MAVSDK"""
        try:
            command = {
                "type": "goto",
                "agent": "perception",
                "latitude": coordinate["latitude"],
                "longitude": coordinate["longitude"],
                "altitude": 10.0,
                "reason": f"disease_detection_{coordinate['detection']}"
            }
            
            response = requests.post(f"{self.mavsdk_url}/command", json=command, timeout=5)
            
            if response.status_code == 200:
                print(f"🧭 Sent goto command for {coordinate['detection']} at {coordinate['latitude']:.6f}, {coordinate['longitude']:.6f}")
            else:
                print(f"❌ Failed to send goto command: {response.text}")
                
        except Exception as e:
            print(f"❌ Error sending goto command: {e}")
    
    def _send_spray_command(self, coordinate):
        """Send spray command to MAVSDK"""
        try:
            command = {
                "type": "spray",
                "agent": "perception",
                "latitude": coordinate["latitude"],
                "longitude": coordinate["longitude"],
                "duration": 5.0,
                "area": [
                    [coordinate["latitude"] - 0.00001, coordinate["longitude"] - 0.00001],
                    [coordinate["latitude"] + 0.00001, coordinate["longitude"] + 0.00001]
                ],
                "reason": f"severe_{coordinate['detection']}"
            }
            
            response = requests.post(f"{self.mavsdk_url}/command", json=command, timeout=5)
            
            if response.status_code == 200:
                print(f"💨 Sent spray command for severe {coordinate['detection']}")
            else:
                print(f"❌ Failed to send spray command: {response.text}")
                
        except Exception as e:
            print(f"❌ Error sending spray command: {e}")
    
    def _test_mavsdk_connection(self):
        """Test connection to MAVSDK"""
        try:
            response = requests.get(f"{self.mavsdk_url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Run the Flask app"""
        print(f"🤖 Perception Agent starting on port {port}...")
        self.app.run(host=host, port=port, debug=debug)

def main():
    agent = PerceptionAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n🛑 Perception agent stopped by user")
    except Exception as e:
        print(f"❌ Perception agent error: {e}")

if __name__ == "__main__":
    main()
