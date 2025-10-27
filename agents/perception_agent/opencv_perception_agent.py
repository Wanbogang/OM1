#!/usr/bin/env python3
"""
OpenCV-based Perception Agent for Smart Farm Drone System
Traditional computer vision for plant disease detection
"""

import cv2
import numpy as np
import requests
from typing import List, Dict, Optional
import json
from datetime import datetime
import os

class OpenCVPerceptionAgent:
    def __init__(self):
        self.disease_signatures = {
            "leaf_blight": {
                "color_range": {
                    "lower": np.array([20, 50, 50]),     # Yellowish-brown lower
                    "upper": np.array([30, 255, 255])    # Yellowish-brown upper
                },
                "symptoms": "Brown/yellow spots on leaves"
            },
            "powdery_mildew": {
                "color_range": {
                    "lower": np.array([0, 0, 200]),      # White/gray lower
                    "upper": np.array([180, 50, 255])    # White/gray upper
                },
                "symptoms": "White powdery coating"
            },
            "rust": {
                "color_range": {
                    "lower": np.array([5, 100, 100]),     # Orange/rust lower
                    "upper": np.array([15, 255, 255])    # Orange/rust upper
                },
                "symptoms": "Rust-colored spots"
            }
        }
        
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Load and preprocess image"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Resize for processing
        img = cv2.resize(img, (640, 480))
        
        return img
    
    def detect_disease_regions(self, image: np.ndarray) -> List[Dict]:
        """Detect disease regions using color analysis"""
        detections = []
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        for disease_name, disease_info in self.disease_signatures.items():
            # Create mask for disease color range
            mask = cv2.inRange(hsv, disease_info["color_range"]["lower"], 
                             disease_info["color_range"]["upper"])
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Filter small contours
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calculate confidence based on area and shape
                    confidence = min(0.9, area / 1000.0)
                    
                    detection = {
                        "disease_name": disease_name,
                        "confidence": float(confidence),
                        "bbox": {
                            "x": int(x), "y": int(y), 
                            "width": int(w), "height": int(h)
                        },
                        "area": float(area),
                        "symptoms": disease_info["symptoms"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    detections.append(detection)
        
        return detections
    
    def analyze_leaf_health(self, image: np.ndarray) -> Dict:
        """Analyze overall leaf health"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate green ratio (healthy leaves have more green)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define green range for healthy leaves
        green_lower = np.array([35, 40, 40])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        green_ratio = np.sum(green_mask > 0) / (image.shape[0] * image.shape[1])
        
        # Calculate texture (using variance)
        texture_variance = np.var(gray)
        
        health_score = {
            "green_ratio": float(green_ratio),
            "texture_variance": float(texture_variance),
            "health_status": "healthy" if green_ratio > 0.3 else "stressed",
            "overall_health": float(min(1.0, green_ratio * 2))
        }
        
        return health_score
    
    def detect_disease_from_image(self, image_path: str) -> Optional[Dict]:
        """Main disease detection function"""
        try:
            # Load and preprocess image
            image = self.preprocess_image(image_path)
            
            # Detect disease regions
            disease_detections = self.detect_disease_regions(image)
            
            # Analyze overall health
            health_analysis = self.analyze_leaf_health(image)
            
            if disease_detections:
                # Get most confident detection
                best_detection = max(disease_detections, key=lambda x: x["confidence"])
                
                # Calculate spray target (center of bbox)
                bbox = best_detection["bbox"]
                target_x = bbox["x"] + bbox["width"] / 2
                target_y = bbox["y"] + bbox["height"] / 2
                
                # Generate spray command
                spray_command = {
                    "command_type": "spray",
                    "detection_method": "opencv_traditional_cv",
                    "disease_info": best_detection,
                    "health_analysis": health_analysis,
                    "target_location": {
                        "image_coordinates": {"x": target_x, "y": target_y},
                        "bbox": bbox
                    },
                    "spray_parameters": {
                        "substance": f"treatment_{best_detection['disease_name']}",
                        "quantity": max(1.0, best_detection["area"] / 500),  # Scale with area
                        "duration": max(5, int(best_detection["area"] / 100))
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                return spray_command
            else:
                # No disease detected, return health analysis
                return {
                    "command_type": "monitoring",
                    "detection_method": "opencv_traditional_cv",
                    "disease_info": None,
                    "health_analysis": health_analysis,
                    "message": "No disease detected - plant appears healthy",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Error in disease detection: {e}")
            return None
    
    def create_detection_visualization(self, image_path: str, detections: List[Dict]) -> str:
        """Create visualization with bounding boxes"""
        try:
            image = self.preprocess_image(image_path)
            
            for detection in detections:
                bbox = detection["bbox"]
                disease_name = detection["disease_name"]
                confidence = detection["confidence"]
                
                # Draw bounding box
                cv2.rectangle(image, (bbox["x"], bbox["y"]), 
                            (bbox["x"] + bbox["width"], bbox["y"] + bbox["height"]), 
                            (0, 0, 255), 2)
                
                # Add label
                label = f"{disease_name}: {confidence:.2f}"
                cv2.putText(image, label, (bbox["x"], bbox["y"] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Save visualization
            output_path = f"detection_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(output_path, image)
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error creating visualization: {e}")
            return None

def main():
    """Test OpenCV Perception Agent"""
    agent = OpenCVPerceptionAgent()
    
    # Test with sample image
    test_image = "test_plant_image.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        print("Please provide a plant image for testing")
        return
    
    try:
        result = agent.detect_disease_from_image(test_image)
        if result:
            print("✅ Analysis complete!")
            print(json.dumps(result, indent=2))
        else:
            print("❌ Analysis failed")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
