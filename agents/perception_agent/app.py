# --- Eventlet & Socket.IO Imports (MUST be first) ---
import threading
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
from flask import Flask, request, jsonify
from flask_cors import CORS
from opencv_perception_agent import OpenCVPerceptionAgent
# ... semua import lainnya
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

@app.route('/process_video', methods=['POST'])
def process_video():
    """
    Endpoint to start processing a video stream.
    """
    try:
        data = request.get_json()
        video_source = data.get('source', 0) # Default to webcam
        def run_processing():
            try:
                from .video_processor import VideoProcessor
                processor = VideoProcessor()
                for result in processor.process_video_stream(video_source):
                    print(f"DETECTED: {result}")
            except Exception as e:
                print(f"Error in video processing thread: {e}")

        import threading
        thread = threading.Thread(target=run_processing)
        thread.start()

        return jsonify({"status": "success", "message": "Video processing started"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Socket.IO Integration ---
# Create a Socket.IO server instance
sio = socketio.Server(cors_allowed_origins="*")

# Wrap the Flask app with Socket.IO
app = socketio.WSGIApp(sio, app)

# --- Socket.IO Event Handlers ---
@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
def new_detection(data):
    print(f"--- Backend: Sending new_detection event with data: {data} ---") # Add this line
    sio.emit('new_detection', data)

if __name__ == '__main__':
    logger.info("Starting Perception Agent API server with Socket.IO...")
    # Use eventlet for WebSocket support
    import eventlet
    eventlet.monkey_patch()
    from eventlet import wsgi
    wsgi.server(eventlet.listen(('', 5001)), app)
