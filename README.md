
# OM1 SmartFarm Clean Repo
# 🚁 Smart Farm Drone System

A comprehensive perception agent system for smart farming that detects crop diseases and automatically commands drones for precision spraying.

## 📋 Quick Links

- **📖 Documentation**: [README_SMARTFARM.md](./README_SMARTFARM.md)
- **🚁 MAVSDK Adapter**: [bridge/mavsdk_adapter/](./bridge/mavsdk_adapter/)
- **🤖 Perception Agent**: [agents/perception_agent/](./agents/perception_agent/)
- **🧪 Tests**: [tests/integration/](./tests/integration/)

## 🎯 System Overview

This project implements a complete workflow from disease detection to drone navigation:

Perception Agent → MAVSDK Writer → MAVSDK Reader → Mock Drone
(Port 5001) (Port 5002) (Port 5000)


## 🚀 Quick Start

```bash
# Navigate to the MAVSDK adapter directory
cd bridge/mavsdk_adapter/

# Install dependencies
pip install fastapi uvicorn pyserial mavsdk requests

# Run health check to verify system
../tests/integration/test_health_local.sh

# Start all services (see full documentation)
python mock_drone_correct.py    # Terminal 1
python server_writer.py         # Terminal 2  
python server_reader.py         # Terminal 3
python ../agents/perception_agent/app.py  # Terminal 4

📊 Features
✅ Disease Detection: AI-powered crop disease identification
✅ GPS Navigation: Automatic drone positioning
✅ Precision Spraying: Targeted treatment application
✅ Real-time Monitoring: Live status and telemetry
✅ RESTful APIs: Easy integration with external systems
✅ Full Testing: Comprehensive health checks and unit tests

📁 Project Structure

├── bridge/mavsdk_adapter/          # Core drone communication system
├── agents/perception_agent/        # AI disease detection
├── tests/integration/              # Health checks and integration tests
└── README_SMARTFARM.md            # Complete documentation

📞 Documentation
For complete documentation, API references, and troubleshooting guides, please see:

📖 README_SMARTFARM.md

Built with ❤️ for smart farming and precision agriculture.


