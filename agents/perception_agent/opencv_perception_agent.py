#!/usr/bin/env python3
"""
Enhanced OpenCV-based Perception Agent for Smart Farm Drone System
Phase 3: Multi-Disease Detection with Enhanced Accuracy
Traditional computer vision for plant disease detection - 5 Disease Types
"""

import cv2
import numpy as np
import requests
from typing import List, Dict, Optional
import json
from datetime import datetime
import os
from prisma import Prisma
import base64
from io import BytesIO
from PIL import Image

class OpenCVPerceptionAgent:
    def __init__(self):
        # Placeholder for disease signatures, should be loaded or defined
        self.disease_signatures = {
            "Leaf Blight": {
                "color_range": {"lower": np.array([10, 50, 50]), "upper": np.array([30, 255, 255])},
                "symptoms": ["Yellowing leaves", "Brown spots"],
                "severity_factor": 1.2,
                "typical_size_range": (200, 2000)
            },
            "Powdery Mildew": {
                "color_range": {"lower": np.array([0, 0, 100]), "upper": np.array([20, 50, 255])},
                "symptoms": ["White powdery spots"],
                "severity_factor": 1.0,
                "typical_size_range": (100, 1500)
            },
            # ... add other diseases here
        }
        self.db = Prisma()

    # --- FIX: Added this missing method ---
    def detect_disease_base64(self, image_b64):
        """Detects disease from a base64 encoded image string."""
        print("🐞 DEBUG: detect_disease_base64 called.")
        try:
            print("🐞 DEBUG: Trying to decode base64...")
            # Decode base64 string
            img_data = base64.b64decode(image_b64)
            print("🐞 DEBUG: Base64 decoded successfully.")

            print("🐞 DEBUG: Trying to open image with PIL...")
            img = Image.open(BytesIO(img_data))
            print("🐞 DEBUG: Image opened successfully.")

            # Convert PIL image to OpenCV format
            print("🐞 DEBUG: Trying to convert to OpenCV format...")
            cv2_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            print("🐞 DEBUG: Image converted successfully.")

            # Use the existing detection logic
            print("🐞 DEBUG: Calling detect_disease_regions...")
            disease_detections = self.detect_disease_regions(cv2_image)
            print(f"🐞 DEBUG: detect_disease_regions returned: {disease_detections}")

            # Analyze overall health
            health_analysis = self.analyze_leaf_health(cv2_image)

            # Format the result to match what save_detection_to_db expects
            result_json = {
                'detections': [],
                'plant_health_coverage': health_analysis,
                'processing_time_ms': 0 # Placeholder
            }

            if disease_detections:
                print("🐞 DEBUG: disease_detections is not empty. Populating result_json...")
                for det in disease_detections:
                    # Re-map the keys to match the database schema
                    mapped_det = {
                        'disease_type': det['class'],
                        'confidence': det['confidence'],
                        'severity': det['severity'],
                        'bounding_box': det['bbox']
                    }
                    result_json['detections'].append(mapped_det)
                print(f"🐞 DEBUG: Final result_json to be returned: {result_json}")
            else:
                print("🐞 DEBUG: disease_detections is empty.")

            return result_json

        except Exception as e:
            print(f"🐞 DEBUG: EXCEPTION CAUGHT! Error: {e}")
            import traceback
            traceback.print_exc() # This will print the full error details
            return {"error": f"Failed to process image: {str(e)}"}

    async def save_detection_to_db(self, detection_result):
        """
        Saves detection results to the database.
        This function iterates through each detection found in an image
        and creates a new record in the DetectionAnalytics table.
        """
        try:
            # Connect to the database
            await self.db.connect()

            # Iterate through all detections found in the result
            for det in detection_result.get('detections', []):
                await self.db.detectionanalytics.create(
                    data={
                        'disease_type': det['disease_type'],
                        'confidence': det['confidence'],
                        'severity': det['severity'],
                        'coordinates': str(det['bounding_box']),
                        'plant_health': detection_result.get('plant_health_coverage', {}).get('health_ratio', 0.0),
                        'processing_time_ms': detection_result.get('processing_time_ms')
                    }
                )
            print(f"✅ Saved {len(detection_result.get('detections', []))} detection(s) to DB.")
        except Exception as e:
            print(f"❌ Error saving to DB: {e}")
        finally:
            # Always ensure the connection is closed
            await self.db.disconnect()

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Load and preprocess image with enhanced preprocessing"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        # ... (rest of the method is fine)
        return img

    def detect_disease_regions(self, image: np.ndarray) -> List[Dict]:
        """
        MOCK/DEMO: Generates fake disease detections for testing purposes.
        In a real implementation, this would contain the actual computer vision logic.
        """
        import random

        # List of possible diseases to detect
        disease_types = ["Leaf Blight", "Powdery Mildew", "Leaf Spot", "Rust", "Healthy"]
        
        # We'll randomly generate 1 or 2 detections per image
        num_detections = random.randint(1, 2)
        detections = []
        
        for _ in range(num_detections):
            # Randomly pick a disease
            disease_type = random.choice(disease_types)
            
            # Generate a fake confidence score
            confidence = round(random.uniform(0.75, 0.98), 2)
            
            # Generate a fake bounding box (x, y, w, h)
            h, w = image.shape[:2]
            x = random.randint(0, w // 2)
            y = random.randint(0, h // 2)
            bbox_w = random.randint(w // 4, w // 2)
            bbox_h = random.randint(h // 4, h // 2)
            
            detection = {
                'class': disease_type,
                'confidence': confidence,
                'bbox': [x, y, bbox_w, bbox_h],
                'severity': random.choice(['mild', 'moderate', 'severe'])
            }
            detections.append(detection)
            
        return detections

    def _calculate_enhanced_confidence(self, contour, hsv_image, disease_name, area):
        # ... (rest of the method is fine)
        return 0.8 # Placeholder

    def _assess_disease_severity(self, confidence, area, disease_name):
        # ... (rest of the method is fine)
        return "mild" # Placeholder

    def analyze_leaf_health(self, image: np.ndarray) -> Dict:
        """Enhanced leaf health analysis"""
        # ... (rest of the method is fine)
        return {"health_ratio": 0.8, "health_status": "healthy", "green_coverage": 80.0} # Placeholder

    def detect_disease_from_image(self, image_path: str) -> Optional[Dict]:
        """Enhanced main disease detection function"""
        # ... (rest of the method is fine)
        return {"command_type": "monitor", "detection_info": None, "health_analysis": {}}

    def _get_recommended_action(self, detection, health_analysis):
        # ... (rest of the method is fine)
        return "continue_monitoring"

    def create_detection_visualization(self, image_path: str, detections: List[Dict]) -> str:
        # ... (rest of the method is fine)
        return image_path

# --- REMOVED THE FLASK APP PART TO AVOID CONFLICTS ---
# The Flask app should only be in your main app.py file.
