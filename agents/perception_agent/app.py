# agents/perception_agent/app.py

# --- Eventlet & Socket.IO Imports (MUST be first) ---
import eventlet
import socketio
eventlet.monkey_patch()

# --- Environment Variables ---
from dotenv import load_dotenv
load_dotenv() # This will find .env in the parent directory

# --- Other Imports ---
import os
import asyncio
import logging
import base64  # <-- DITAMBAHKAN: Untuk /detect endpoint
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from opencv_perception_agent import OpenCVPerceptionAgent
from prisma import Prisma
from predictor import predict_confidence # <-- Import utilitas prediksi

# --- Basic Setup ---
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Socket.IO Integration ---
# Create a Socket.IO server instance
sio = socketio.Server(cors_allowed_origins="*")

# --- API Endpoints ---
# SEMUA ROUTE HARUS DIDEFINISIKAN SEBELUM APP DI-WRAP OLEH SOCKET.IO

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
            "POST /detect": "Detect disease from uploaded image",
            "POST /detect_base64": "Detect disease from base64 string",
            "POST /predict": "Predict confidence based on disease type",
            "GET /analytics": "Get analytics data",
            "POST /process_video": "Start video stream processing"
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
        agent = OpenCVPerceptionAgent()
        result = agent.detect_disease_base64(image_b64)

        if 'error' not in result:
            try:
                asyncio.run(agent.save_detection_to_db(result))
            except Exception as db_error:
                logger.error(f"Failed to save to DB: {db_error}")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in detect_disease_base64 endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/detect', methods=['POST'])
def detect_disease_from_file():
    """Detects disease from an uploaded image file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file:
            img_bytes = file.read()
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            agent = OpenCVPerceptionAgent()
            result = agent.detect_disease_base64(img_b64)

            if 'error' not in result:
                try:
                    asyncio.run(agent.save_detection_to_db(result))
                except Exception as db_error:
                    logger.error(f"Failed to save to DB: {db_error}")

            return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in detect endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    """API endpoint untuk memprediksi confidence berdasarkan disease_type."""
    try:
        data = request.get_json()
        if not data or 'disease_type' not in data:
            return jsonify({"error": "disease_type field is required"}), 400

        disease_type = data['disease_type']
        predicted_confidence = predict_confidence(disease_type)

        if predicted_confidence is None:
            return jsonify({"error": f"Could not make a prediction for '{disease_type}'. The disease type might be unknown or the model is not loaded."}), 400

        result = {
            "disease_type": disease_type,
            "predicted_confidence": round(predicted_confidence, 4)
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Fetches analytics data from the database."""
    try:
        async def fetch_data():
            db = Prisma()
            await db.connect()
            
            # Fetch all records
            analytics_data = await db.detectionrecord.find_many(
                order={'timestamp': 'desc'},
                take=100
            )
            await db.disconnect()

            # --- Aggregate for Disease Counts (existing logic) ---
            disease_counts = {}
            for record in analytics_data:
                disease = record.disease_type
                disease_counts[disease] = disease_counts.get(disease, 0) + 1
            
            # --- NEW: Aggregate for Time-Series Data ---
            # We will count detections per day
            from collections import defaultdict
            time_series_counts = defaultdict(int)
            
            for record in analytics_data:
                # Extract just the date part (YYYY-MM-DD) from the timestamp
                date_str = record.timestamp.strftime('%Y-%m-%d')
                time_series_counts[date_str] += 1
            
            # Convert to a sorted list of objects for Recharts
            time_series_data = [
                {'date': date, 'count': count}
                for date, count in sorted(time_series_counts.items())
            ]

            return {
                "recent_detections": [record.model_dump() for record in analytics_data],
                "disease_counts": disease_counts,
                "time_series_data": time_series_data # <-- NEW DATA
            }

        result = asyncio.run(fetch_data())
        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        logger.error(f"Error in analytics endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/process_video', methods=['POST'])
def process_video():
    """Endpoint to start processing a video stream."""
    try:
        data = request.get_json()
        video_source = data.get('source', 0) # Default to webcam

        def run_processing():
            try:
                # FIX: Remove the dot (.) from relative import
                from video_processor import VideoProcessor
                processor = VideoProcessor()
                for result in processor.process_video_stream(video_source):
                    print(f"DETECTED: {result}")
            except Exception as e:
                print(f"Error in video processing thread: {e}")

        thread = threading.Thread(target=run_processing)
        thread.start()

        return jsonify({"status": "success", "message": "Video processing started"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Socket.IO Event Handlers ---
# Event handlers harus didefinisikan setelah route Flask
@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
def new_detection(data):
    print(f"--- Backend: Sending new_detection event with data: {data} ---")
    sio.emit('new_detection', data)

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("Starting Perception Agent API server with Socket.IO...")
    
    # Wrap the Flask app with Socket.IO
    # INI HARUS DILAKUKAN SETELAH SEMUA ROUTE DIDEFINISIKAN
    app = socketio.WSGIApp(sio, app)
    
    # Use eventlet for WebSocket support
    from eventlet import wsgi
    wsgi.server(eventlet.listen(('', 5001)), app)

