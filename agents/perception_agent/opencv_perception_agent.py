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

class OpenCVPerceptionAgent:
    def __init__(self):
        # Enhanced disease signatures with 5 disease types
        self.disease_signatures = {
            "leaf_blight": {
                "color_range": {
                    "lower": np.array([20, 50, 50]),     # Yellowish-brown lower
                    "upper": np.array([30, 255, 255])    # Yellowish-brown upper
                },
                "symptoms": "Brown/yellow spots on leaves",
                "severity_factor": 1.0,
                "typical_size_range": (100, 2000)
            },
            "powdery_mildew": {
                "color_range": {
                    "lower": np.array([0, 0, 200]),      # White/gray lower
                    "upper": np.array([180, 50, 255])    # White/gray upper
                },
                "symptoms": "White powdery coating",
                "severity_factor": 0.8,
                "typical_size_range": (200, 3000)
            },
            "rust": {
                "color_range": {
                    "lower": np.array([5, 100, 100]),     # Orange/rust lower
                    "upper": np.array([15, 255, 255])    # Orange/rust upper
                },
                "symptoms": "Rust-colored spots",
                "severity_factor": 1.2,
                "typical_size_range": (50, 1500)
            },
            "bacterial_spot": {
                "color_range": {
                    "lower": np.array([0, 0, 0]),         # Dark/black lower
                    "upper": np.array([20, 50, 50])       # Dark brown upper
                },
                "symptoms": "Dark water-soaked spots",
                "severity_factor": 1.5,
                "typical_size_range": (30, 800)
            },
            "yellow_leaf": {
                "color_range": {
                    "lower": np.array([20, 30, 50]),      # Yellow lower
                    "upper": np.array([35, 255, 255])     # Light green upper
                },
                "symptoms": "Yellowing/nutrient deficiency",
                "severity_factor": 0.6,
                "typical_size_range": (500, 5000)
            }
        }

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Load and preprocess image with enhanced preprocessing"""
        print(f"DEBUG: Trying to read image: {image_path}")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Read image
        img = cv2.imread(image_path)
        print(f"DEBUG: cv2.imread result: {img is not None}")

        if img is None:
            print(f"DEBUG: Image is None, checking file...")
            print(f"DEBUG: File size: {os.path.getsize(image_path)} bytes")
            raise ValueError(f"Cannot read image: {image_path}")

        print(f"DEBUG: Image shape: {img.shape}")

        # Enhanced preprocessing
        # Apply Gaussian blur to reduce noise
        img_blurred = cv2.GaussianBlur(img, (5, 5), 0)
        
        # Enhance contrast using CLAHE
        lab = cv2.cvtColor(img_blurred, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        lab[:,:,0] = clahe.apply(lab[:,:,0])
        img_enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        return img_enhanced

    def detect_disease_regions(self, image: np.ndarray) -> List[Dict]:
        """Enhanced disease detection using multiple analysis techniques"""
        detections = []

        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Apply morphological operations to reduce noise
        kernel = np.ones((3,3), np.uint8)
        hsv_processed = cv2.morphologyEx(hsv, cv2.MORPH_OPEN, kernel)
        hsv_processed = cv2.morphologyEx(hsv_processed, cv2.MORPH_CLOSE, kernel)

        for disease_name, disease_info in self.disease_signatures.items():
            # Create mask for disease color range
            mask = cv2.inRange(hsv_processed, 
                             disease_info["color_range"]["lower"],
                             disease_info["color_range"]["upper"])

            # Additional noise reduction
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # Enhanced filtering
                area = cv2.contourArea(contour)
                min_size, max_size = disease_info["typical_size_range"]
                
                if min_size < area < max_size:  # Size filtering
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)

                    # Enhanced confidence calculation
                    confidence = self._calculate_enhanced_confidence(contour, hsv_processed, disease_name, area)
                    
                    if confidence > 0.5:  # Minimum confidence threshold
                        detection = {
                            "class": disease_name,
                            "confidence": round(confidence, 3),
                            "bbox": {
                                "x": x,
                                "y": y,
                                "width": w,
                                "height": h
                            },
                            "severity": self._assess_disease_severity(confidence, area, disease_name),
                            "area": area,
                            "symptoms": disease_info["symptoms"],
                            "detection_method": "opencv_enhanced_traditional_cv",
                            "timestamp": datetime.now().isoformat()
                        }
                        detections.append(detection)

        return detections

    def _calculate_enhanced_confidence(self, contour, hsv_image, disease_name, area):
        """Enhanced confidence calculation with multiple factors"""
        
        # Base confidence from area
        area_confidence = min(0.95, area / 800.0)
        
        # Shape analysis - compactness
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            compactness = 4 * np.pi * area / (perimeter * perimeter)
            shape_confidence = min(0.9, compactness * 1.5)
        else:
            shape_confidence = 0.3
        
        # Color purity - check HSV consistency
        x, y, w, h = cv2.boundingRect(contour)
        roi = hsv_image[y:y+h, x:x+w]
        
        if roi.size > 0:
            # Calculate color standard deviation
            mean_h = np.mean(roi[:, :, 0])
            std_h = np.std(roi[:, :, 0])
            color_consistency = max(0.3, 1.0 - (std_h / 50.0))
            
            # Check if color matches expected range
            disease_range = self.disease_signatures[disease_name]["color_range"]
            color_match = 1.0 if disease_range["lower"][0] <= mean_h <= disease_range["upper"][0] else 0.5
        else:
            color_consistency = 0.3
            color_match = 0.5
        
        # Disease-specific factors
        disease_info = self.disease_signatures[disease_name]
        severity_factor = disease_info.get("severity_factor", 1.0)
        
        # Weighted combination
        final_confidence = (
            area_confidence * 0.35 +      # 35% weight on area
            shape_confidence * 0.25 +     # 25% weight on shape
            color_consistency * 0.25 +    # 25% weight on color consistency
            color_match * 0.15            # 15% weight on color matching
        ) * severity_factor
        
        return min(0.98, max(0.1, final_confidence))

    def _assess_disease_severity(self, confidence, area, disease_name):
        """Assess disease severity based on multiple factors"""
        
        disease_info = self.disease_signatures[disease_name]
        base_severity = disease_info.get("severity_factor", 1.0)
        
        # Enhanced severity assessment
        if confidence > 0.85 and area > 1000:
            return "severe"
        elif confidence > 0.75 and area > 500:
            return "moderate"
        elif confidence > 0.6 and area > 200:
            return "mild"
        else:
            return "early"

    def analyze_leaf_health(self, image: np.ndarray) -> Dict:
        """Enhanced leaf health analysis"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Calculate green coverage (health indicator)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        total_pixels = image.shape[0] * image.shape[1]
        green_pixels = np.sum(green_mask > 0)
        health_ratio = green_pixels / total_pixels
        
        return {
            "health_ratio": round(health_ratio, 3),
            "health_status": "healthy" if health_ratio > 0.7 else "stressed" if health_ratio > 0.4 else "unhealthy",
            "green_coverage": round(green_pixels / total_pixels * 100, 1)
        }

    def detect_disease_from_image(self, image_path: str) -> Optional[Dict]:
        """Enhanced main disease detection function"""
        try:
            # Load and preprocess image
            image = self.preprocess_image(image_path)

            # Detect disease regions
            disease_detections = self.detect_disease_regions(image)

            # Analyze overall health
            health_analysis = self.analyze_leaf_health(image)

            if disease_detections:
                # Sort by confidence and get top detections
                disease_detections.sort(key=lambda x: x["confidence"], reverse=True)
                
                # Get best detection
                best_detection = disease_detections[0]

                # Calculate spray target (center of bbox)
                bbox = best_detection["bbox"]
                target_x = bbox["x"] + bbox["width"] / 2
                target_y = bbox["y"] + bbox["height"] / 2

                # Enhanced spray command
                spray_command = {
                    "command_type": "spray",
                    "detection_method": "opencv_enhanced_traditional_cv",
                    "disease_info": best_detection,
                    "target_coordinates": {
                        "x": int(target_x),
                        "y": int(target_y)
                    },
                    "all_detections": disease_detections[:3],  # Top 3 detections
                    "health_analysis": health_analysis,
                    "image_info": {
                        "path": image_path,
                        "processed_at": datetime.now().isoformat(),
                        "image_shape": image.shape
                    },
                    "confidence_threshold_met": bool(best_detection["confidence"] > 0.7),
                    "recommended_action": self._get_recommended_action(best_detection, health_analysis)
                }

                return spray_command
            else:
                # No disease detected
                return {
                    "command_type": "monitor",
                    "detection_method": "opencv_enhanced_traditional_cv",
                    "disease_info": None,
                    "health_analysis": health_analysis,
                    "message": "No disease detected - plant appears healthy",
                    "recommended_action": "continue_monitoring"
                }

        except Exception as e:
            return {
                "error": f"Detection failed: {str(e)}",
                "command_type": "error",
                "timestamp": datetime.now().isoformat()
            }

    def _get_recommended_action(self, detection, health_analysis):
        """Get recommended action based on detection and health"""
        severity = detection["severity"]
        confidence = detection["confidence"]
        disease_class = detection["class"]
        
        if severity == "severe" and confidence > 0.8:
            return "immediate_treatment_required"
        elif severity == "moderate" and confidence > 0.7:
            return "treatment_recommended"
        elif severity == "mild" and confidence > 0.6:
            return "monitor_closely"
        else:
            return "continue_monitoring"

    def create_detection_visualization(self, image_path: str, detections: List[Dict]) -> str:
        """Create visualization with detections"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return image_path

            # Draw bounding boxes and labels
            for detection in detections:
                bbox = detection["bbox"]
                confidence = detection["confidence"]
                disease_class = detection["class"]
                
                # Draw rectangle
                cv2.rectangle(image, 
                            (bbox["x"], bbox["y"]), 
                            (bbox["x"] + bbox["width"], bbox["y"] + bbox["height"]),
                            (0, 255, 0), 2)
                
                # Add label
                label = f"{disease_class}: {confidence:.2f}"
                cv2.putText(image, label, 
                           (bbox["x"], bbox["y"] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Save visualization
            output_path = image_path.replace(".", "_detected.")
            cv2.imwrite(output_path, image)
            
            return output_path

        except Exception as e:
            print(f"Visualization error: {e}")
            return image_path

# Flask API Integration
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize perception agent
perception_agent = OpenCVPerceptionAgent()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "opencv_perception_agent",
        "version": "3.0.0",
        "phase": "enhanced_multi_disease_detection",
        "supported_diseases": list(perception_agent.disease_signatures.keys()),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/detect', methods=['POST'])
def detect_disease():
    """Detect disease from uploaded image"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No image file selected"}), 400
        
        # Save temporary file
        temp_path = f"/tmp/temp_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        file.save(temp_path)
        
        # Detect disease
        result = perception_agent.detect_disease_from_image(temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Detection failed: {str(e)}"}), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Get information about disease detection capabilities"""
    # Convert numpy arrays to lists for JSON serialization
    disease_details_safe = {}
    for disease, info in perception_agent.disease_signatures.items():
        disease_details_safe[disease] = {
            "color_range": {
                "lower": info["color_range"]["lower"].tolist(),
                "upper": info["color_range"]["upper"].tolist()
            },
            "symptoms": info["symptoms"],
            "severity_factor": info["severity_factor"],
            "typical_size_range": info["typical_size_range"]
        }
    
    return jsonify({
        "supported_diseases": list(perception_agent.disease_signatures.keys()),
        "disease_details": disease_details_safe,
        "version": "3.0.0",
        "features": [
            "Multi-disease detection (5 types)",
            "Enhanced confidence calculation",
            "Severity assessment",
            "Health analysis",
            "Improved accuracy (95%+ target)"
        ]
    })
@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint with sample detection"""
    return jsonify({
        "message": "Enhanced OpenCV Perception Agent - Phase 3 Ready",
        "supported_diseases": list(perception_agent.disease_signatures.keys()),
        "features": [
            "5 disease types detection",
            "Enhanced accuracy calculation",
            "Severity assessment",
            "Health analysis"
        ],
        "status": "ready_for_phase_3_testing"
    })

if __name__ == '__main__':
    print("🌿 Enhanced OpenCV Perception Agent - Phase 3: Multi-Disease Detection")
    print("🎯 Supporting 5 disease types with enhanced accuracy")
    print("🚀 Starting API server on port 5001...")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
