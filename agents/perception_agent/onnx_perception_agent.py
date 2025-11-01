#!/usr/bin/env python3
"""
ONNX-based Perception Agent for Smart Farm Drone System
Real plant disease detection using ONNX models
"""

import cv2
import numpy as np
import onnxruntime as ort
import requests
from typing import List, Dict, Optional
import json
from datetime import datetime

class ONNXPerceptionAgent:
    def __init__(self, model_path: str = "../../models/plant_disease_yolov8n.onnx"):
        self.model_path = model_path
        self.session = None
        self.class_names = [
            "leaf_blight", "powdery_mildew", "rust", "bacterial_spot",
            "healthy_leaf", "yellow_leaf", "pest_damage"
        ]
        
    def load_model(self):
        """Load ONNX model"""
        try:
            self.session = ort.InferenceSession(self.model_path)
            print(f"✅ ONNX model loaded: {self.model_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for ONNX inference"""
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Resize to 640x640 (YOLOv8 input size)
        img = cv2.resize(img, (640, 640))
        
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Normalize to 0-1
        img = img.astype(np.float32) / 255.0
        
        # Add batch dimension: (1, 3, 640, 640)
        img = np.transpose(img, (2, 0, 1))  # HWC to CHW
        img = np.expand_dims(img, axis=0)
        
        return img
    
    def run_inference(self, image_path: str) -> List[Dict]:
        """Run ONNX inference on image"""
        if self.session is None:
            if not self.load_model():
                return []
        
        try:
            # Preprocess image
            input_tensor = self.preprocess_image(image_path)
            
            # Get input name
            input_name = self.session.get_inputs()[0].name
            
            # Run inference
            outputs = self.session.run(None, {input_name: input_tensor})
            
            # Process outputs (YOLOv8 format)
            detections = self.process_yolo_output(outputs[0], image_path)
            
            return detections
            
        except Exception as e:
            print(f"❌ Inference failed: {e}")
            return []
    
    def process_yolo_output(self, output: np.ndarray, image_path: str) -> List[Dict]:
        """Process YOLOv8 output to detections"""
        detections = []
        
        # YOLOv8 output format: [batch, 84, 8400] (for 80 classes)
        # Transpose to [8400, 84]
        output = output[0].T
        
        # Filter by confidence
        confidence_threshold = 0.5
        for detection in output:
            # Get class probabilities
            class_probs = detection[4:]
            max_confidence = np.max(class_probs)
            
            if max_confidence > confidence_threshold:
                class_id = np.argmax(class_probs)
                if class_id < len(self.class_names):
                    
                    # Get bounding box (center_x, center_y, width, height)
                    cx, cy, w, h = detection[:4]
                    
                    # Convert to x1, y1, x2, y2
                    x1 = cx - w/2
                    y1 = cy - h/2
                    x2 = cx + w/2
                    y2 = cy + h/2
                    
                    detection_info = {
                        "class_name": self.class_names[class_id],
                        "confidence": float(max_confidence),
                        "bbox": {
                            "x1": float(x1), "y1": float(y1),
                            "x2": float(x2), "y2": float(y2)
                        },
                        "image_path": image_path,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    detections.append(detection_info)
        
        return detections
    
    def detect_disease_from_image(self, image_path: str) -> Optional[Dict]:
        """Detect disease from image and return spray command"""
        detections = self.run_inference(image_path)
        
        # Filter for disease detections (exclude healthy)
        disease_detections = [
            d for d in detections 
            if d["class_name"] not in ["healthy_leaf", "yellow_leaf"]
        ]
        
        if disease_detections:
            # Get highest confidence detection
            best_detection = max(disease_detections, key=lambda x: x["confidence"])
            
            # Calculate center point for spray target
            bbox = best_detection["bbox"]
            center_x = (bbox["x1"] + bbox["x2"]) / 2
            center_y = (bbox["y1"] + bbox["y2"]) / 2
            
            # Generate spray command
            spray_command = {
                "command_type": "spray",
                "disease_info": best_detection,
                "target_location": {
                    "image_coordinates": {"x": center_x, "y": center_y},
                    "confidence": best_detection["confidence"]
                },
                "spray_parameters": {
                    "substance": f"treatment_{best_detection['class_name']}",
                    "quantity": 2.0,  # Liters
                    "duration": 10     # Seconds
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return spray_command
        
        return None

def main():
    """Test ONNX Perception Agent"""
    agent = ONNXPerceptionAgent()
    
    if not agent.load_model():
        print("❌ Failed to initialize agent")
        return
    
    # Test with sample image (you need to provide one)
    test_image = "test_plant_image.jpg"
    
    try:
        spray_command = agent.detect_disease_from_image(test_image)
        if spray_command:
            print("✅ Disease detected!")
            print(json.dumps(spray_command, indent=2))
        else:
            print("🔍 No disease detected")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
