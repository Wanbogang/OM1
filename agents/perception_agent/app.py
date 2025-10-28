#!/usr/bin/env python3
import os
import io
import json
import logging
import time
import random
from datetime import datetime
from typing import Dict, Any, Optional, List

from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerceptionAgent:
    """AI-powered perception agent for crop disease detection"""
    
    def __init__(self):
        logger.info("Initializing Perception Agent (Simplified Version)")
        
        # Class names
        self.class_names = [
            "healthy",
            "leaf_blight", 
            "leaf_spot",
            "powdery_mildew",
            "rust"
        ]
        
        # Disease info database
        self.disease_info = {
            "healthy": {
                "confidence_threshold": 0.7,
                "severity": "none",
                "treatment": "No treatment needed",
                "description": "Plant appears healthy"
            },
            "leaf_blight": {
                "confidence_threshold": 0.6,
                "severity": "moderate",
                "treatment": "Apply fungicide spray, remove affected leaves",
                "description": "Leaf blight detected - fungal infection affecting leaves"
            },
            "leaf_spot": {
                "confidence_threshold": 0.6,
                "severity": "mild",
                "treatment": "Apply copper-based fungicide, improve air circulation",
                "description": "Leaf spots detected - typically caused by fungal or bacterial infection"
            },
            "powdery_mildew": {
                "confidence_threshold": 0.7,
                "severity": "moderate",
                "treatment": "Apply sulfur-based fungicide, reduce humidity",
                "description": "Powdery mildew detected - fungal disease creating white powdery coating"
            },
            "rust": {
                "confidence_threshold": 0.6,
                "severity": "moderate_to_severe",
                "treatment": "Apply systemic fungicide, remove infected plant material",
                "description": "Rust detected - fungal disease creating rust-colored spots"
            }
        }
        
        logger.info("Perception Agent initialized successfully")
    
    def _simulate_disease_detection(self, image_size: int = 1024) -> Dict[str, Any]:
        """Simulate disease detection with realistic confidence scores"""
        try:
            # Generate random probabilities that sum to 1
            probs = [random.random() for _ in range(len(self.class_names))]
            total = sum(probs)
            normalized_probs = [p/total for p in probs]
            
            # Get predicted class and confidence
            max_idx = normalized_probs.index(max(normalized_probs))
            predicted_class = self.class_names[max_idx]
            confidence = normalized_probs[max_idx]
            
            # Create class probabilities dictionary
            class_probabilities = {
                self.class_names[i]: float(normalized_probs[i]) 
                for i in range(len(self.class_names))
            }
            
            # Check confidence threshold
            disease_data = self.disease_info.get(predicted_class, {})
            threshold = disease_data.get("confidence_threshold", 0.5)
            
            # If confidence is too low, mark as uncertain
            if confidence < threshold:
                predicted_class = "uncertain"
                confidence = max(class_probabilities.values())
                description = "Low confidence - recommend manual inspection"
            else:
                description = disease_data.get("description", "Unknown condition")
            
            result = {
                "predicted_class": predicted_class,
                "confidence": round(confidence, 3),
                "all_probabilities": {k: round(v, 3) for k, v in class_probabilities.items()},
                "severity": disease_data.get("severity", "unknown"),
                "treatment": disease_data.get("treatment", "Consult expert"),
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "model_info": {
                    "device": "cpu",
                    "input_size": "224x224",
                    "num_classes": len(self.class_names),
                    "model_type": "simulated"
                },
                "image_info": {
                    "size_bytes": image_size,
                    "processed": True
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in disease detection simulation: {e}")
            return {
                "error": f"Detection failed: {str(e)}",
                "predicted_class": "error",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
    
    def detect_from_file(self, file_path: str) -> Dict[str, Any]:
        """Detect disease from image file"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Image file not found: {file_path}")
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Simulate processing time
            time.sleep(0.1)
            
            return self._simulate_disease_detection(file_size)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {
                "error": f"Failed to process image: {str(e)}",
                "predicted_class": "error",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
    
    def detect_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Detect disease from image bytes"""
        try:
            # Get size of bytes
            byte_size = len(image_bytes)
            
            # Simulate processing time
            time.sleep(0.1)
            
            return self._simulate_disease_detection(byte_size)
            
        except Exception as e:
            logger.error(f"Error processing image bytes: {e}")
            return {
                "error": f"Failed to process image: {str(e)}",
                "predicted_class": "error",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize perception agent
perception_agent = PerceptionAgent()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "perception_agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "device": "cpu",
        "model_loaded": True,
        "model_type": "simulated"
    })

@app.route('/detect', methods=['POST'])
def detect_disease():
    """Detect disease from uploaded image"""
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No image file selected"}), 400
        
        # Process image
        image_bytes = file.read()
        result = perception_agent.detect_from_bytes(image_bytes)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in detect_disease endpoint: {e}")
        return jsonify({"error": f"Detection failed: {str(e)}"}), 500

@app.route('/detect_url', methods=['POST'])
def detect_disease_from_url():
    """Detect disease from image URL"""
    try:
        data = request.get_json()
        if not data or 'image_url' not in data:
            return jsonify({"error": "image_url is required"}), 400
        
        image_url = data['image_url']
        
        # Download image (simple implementation)
        import requests
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Process image
        result = perception_agent.detect_from_bytes(response.content)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in detect_disease_from_url endpoint: {e}")
        return jsonify({"error": f"Detection from URL failed: {str(e)}"}), 500

@app.route('/info', methods=['GET'])
def get_info():
    """Get information about available disease classes"""
    return jsonify({
        "classes": perception_agent.class_names,
        "disease_info": perception_agent.disease_info,
        "model_info": {
            "device": "cpu",
            "input_size": "224x224",
            "num_classes": len(perception_agent.class_names),
            "model_type": "simulated"
        }
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint with sample detection"""
    try:
        # Simulate with a random image size
        result = perception_agent._simulate_disease_detection(2048)
        
        return jsonify({
            "test_result": result,
            "message": "Test completed successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        return jsonify({"error": f"Test failed: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def index():
    """Index endpoint with API information"""
    return jsonify({
        "service": "Perception Agent API",
        "version": "1.0.0",
        "description": "AI-powered crop disease detection service",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "POST /detect": "Detect disease from uploaded image",
            "POST /detect_url": "Detect disease from image URL", 
            "GET /info": "Get disease class information",
            "GET /test": "Test endpoint with sample detection"
        },
        "usage": {
            "detect": "POST /detect with multipart/form-data file field named 'image'",
            "detect_url": "POST /detect_url with JSON {'image_url': 'url'}"
        }
    })

if __name__ == '__main__':
    logger.info("Starting Perception Agent API server...")
    logger.info("Available endpoints:")
    logger.info("  GET  / - API information")
    logger.info("  GET  /health - Health check")
    logger.info("  POST /detect - Detect disease from uploaded image")
    logger.info("  POST /detect_url - Detect disease from image URL")
    logger.info("  GET  /info - Get disease class information")
    logger.info("  GET  /test - Test endpoint with sample detection")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
