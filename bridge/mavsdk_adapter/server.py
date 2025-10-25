import asyncio
import threading
import json
import time
from flask import Flask, jsonify
from mavsdk import System

# --- Global Variables ---
latest_position = None
app = Flask(__name__)

# --- Background MAVSDK Task ---
async def run_mavsdk_loop():
    """Continuously connect to drone and update the latest_position."""
    global latest_position
    drone = System()
    print("🔌 [MAVSDK Task] Connecting to drone...")
    await drone.connect(system_address="udpout://localhost:14540")

    print("✅ [MAVSDK Task] Connected. Waiting for telemetry...")
    async for position in drone.telemetry.position():
        latest_position = {
            "latitude_deg": position.latitude_deg,
            "longitude_deg": position.longitude_deg,
            "relative_altitude_m": position.relative_altitude_m
        }
        print(f"📍 [MAVSDK Task] Updated position: {latest_position}")

def run_flask():
    """Run the Flask app."""
    # Use host='0.0.0.0' to make it accessible from other containers/machines
    app.run(host="0.0.0.0", port=5002, use_reloader=False)

# --- Flask API Endpoints ---
@app.route("/telemetry/position", methods=["GET"])
def get_position():
    """API endpoint to get the latest drone position."""
    if latest_position:
        return jsonify({
            "status": "ok",
            "data": latest_position
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Position data not available yet."
        }), 503

@app.route("/health", methods=["GET"])
def health_check():
    """Health check for the adapter server."""
    return jsonify({"status": "ok", "service": "mavsdk_adapter"})

# --- Main Execution ---
if __name__ == "__main__":
    print("🚀 Starting MAVSDK Adapter Server...")
    
    # Start the Flask app in a separate daemon thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Give Flask a moment to start up
    time.sleep(1)
    
    # Run the asyncio loop in the main thread
    try:
        asyncio.run(run_mavsdk_loop())
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down.")

