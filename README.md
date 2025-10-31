![OM_Banner_X2 (1)](https://github.com/user-attachments/assets/853153b7-351a-433d-9e1a-d257b781f93c)

# OM1 SmartFarm Clean Repo
## 🚁 Smart Farm Drone System

<p align="center">
<a href="https://arxiv.org/abs/2412.18588">Technical Paper</a> |
<a href="https://docs.openmind.org/">Documentation</a> |
<a href="https://x.com/openmind_agi">X</a> |
<a href="https://discord.gg/VUjpg4ef5n">Discord</a>
</p>

A comprehensive perception agent system for smart farming that detects crop diseases and automatically commands drones for precision spraying.

## 📋 Quick Links
- **Documentation**: [README_SMARTFARM.md](./README_SMARTFARM.md)
- **🚁 MAVSDK Adapter**: [bridge/mavsdk_adapter/](./bridge/mavsdk_adapter/)
- **🤖 Perception Agent**: [agents/perception_agent/](./agents/perception_agent/)
- **🧪 Tests**: [tests/integration/](./tests/integration/)

## Architecture Overview
![Artboard 1@4x 1 (1)](https://github.com/user-attachments/assets/14e9b916-4df7-4700-9336-2983c85be311)

This project implements a complete workflow from disease detection to drone navigation:

**Perception Agent → MAVSDK Writer → MAVSDK Reader → Mock Drone**  
(Ports: Perception 5001, Writer 5002, Reader 5003)

## 🚀 Quick Start
### Navigate to the MAVSDK adapter directory
```bash
cd bridge/mavsdk_adapter/
```
Install dependencies
```bash
pip install fastapi uvicorn pyserial mavsdk requests
```
Run health check (example)
```bash
../tests/integration/test_health_local.sh
```
Start all services (sample)
```bash
python mock_drone_correct.py      # Terminal 1
python server_writer.py           # Terminal 2
python server_reader.py           # Terminal 3
python ../agents/perception_agent/app.py  # Terminal 4
```
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

Full Autonomy Guidance

We're excited to introduce full autonomy mode, where multiple services work together in a loop without manual intervention:

-   om1

-   unitree_sdk – ROS 2 package (SLAM + Nav2)

-   om1-avatar – React frontend / avatar display

Clone supporting repos if needed:

-   https://github.com/OpenMind/OM1.git

-   https://github.com/OpenMind/unitree_sdk.git

-   https://github.com/OpenMind/OM1-avatar.git

Starting the system (docker examples)

Set your API key in shell config ( ~/.bashrc  or  ~/.zshrc ):
```bash
export OM_API_KEY="your_api_key"
```
Example docker commands:
```bash
cd OM1
docker-compose up om1 -d --no-build

cd unitree_sdk
docker-compose up orchestrator -d --no-build
docker-compose up om1_sensor -d --no-build
docker-compose up watchdog -d --no-build

cd OM1-avatar
docker-compose up om1_avatar -d --no-build
```
Detailed Documentation

More detailed documentation available at: https://docs.openmind.org/

Contributing

Please read the CONTRIBUTING.md
 before making PRs.

License

MIT License

Built with ❤️ for smart farming and precision agriculture.
