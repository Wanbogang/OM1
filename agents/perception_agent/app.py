import os
import base64
import asyncio
import logging
from flask import Flask, request, jsonify
from opencv_perception_agent import OpenCVPerceptionAgent
from prisma import Prisma
from flask_cors import CORS

# --- Basic Setup ---
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- API Endpoints ---

@app.route('/')
def index():
    """API information."""
    return jsonify({
        "service": "Perception Agent API",
        "version": "1.0.0",
        "description": "AI-powered crop disease detection service",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "GET /info": "Get disease class information",
            "GET /test": "Test endpoint with sample detection",
            "POST /detect": "Detect disease from uploaded image",
            "POST /detect_url": "Detect disease from image URL",
            "POST /detect_base64": "Detect disease from base64 string",
            "POST /process_video": "Start video stream processing",
            "GET /analytics": "Get analytics data"
        },
        "usage": {
            "detect": "POST /detect with multipart/form-data file field named 'image'",
            "detect_url": "POST /detect_url with JSON {'image_url': 'url'}",
            "detect_base64": "POST /detect_base64 with JSON {'image_base64': 'base64_string'}"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "Perception Agent"}), 200

@app.route('/detect_base64', methods=['POST'])
def detect_disease_base64():
    """Detects disease from a base64 encoded image string."""
    try:
        data = request.get_json()
        if not data or 'image_base64' not in data:
            return jsonify({"error": "image_base64 field is required"}), 400

        image_b64 = data['image_base64']
        
        # Create an instance of the perception agent
        agent = OpenCVPerceptionAgent()
        
        # 1. Run the synchronous processing function
        result = agent.detect_disease_base64(image_b64)
        
        # 2. If processing was successful, save the result to DB asynchronously
        if 'error' not in result:
            try:
                asyncio.run(agent.save_detection_to_db(result))
            except Exception as db_error:
                logger.error(f"Failed to save to DB: {db_error}")
                # We can still return the result, but log the DB error
        
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in detect_disease_base64 endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/detect', methods=['POST'])
def detect_disease_from_file():
    """Detects disease from an uploaded image file."""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        
        file = request.files['file']
        
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if file:
            # Read the file in binary mode
            img_bytes = file.read()
            # Encode to base64
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Create an instance of the perception agent
            agent = OpenCVPerceptionAgent()
            
            # Run the synchronous processing function
            result = agent.detect_disease_base64(img_b64)
            
            # If processing was successful, save the result to DB asynchronously
            if 'error' not in result:
                try:
                    asyncio.run(agent.save_detection_to_db(result))
                except Exception as db_error:
                    logger.error(f"Failed to save to DB: {db_error}")
            
            return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in detect endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Fetches analytics data from the database."""
    try:
        async def fetch_data():
            db = Prisma()
            await db.connect()
            analytics_data = await db.detectionanalytics.find_many(
                order={'timestamp': 'desc'},
                take=100
            )
            await db.disconnect()
            
            disease_counts = {}
            for record in analytics_data:
                disease = record.disease_type
                disease_counts[disease] = disease_counts.get(disease, 0) + 1
            
            return {
                "recent_detections": [dict(item) for item in analytics_data],
                "disease_counts": disease_counts
            }

        result = asyncio.run(fetch_data())
        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        logger.error(f"Error in analytics endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("Starting Perception Agent API server...")
    app.run(host='0.0.0.0', port=5001, debug=True)
