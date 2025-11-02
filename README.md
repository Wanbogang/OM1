![OM_Banner_X2 (1)](https://github.com/user-attachments/assets/853153b7-351a-433d-9e1a-d257b781f93c)

# OM1 SmartFarm Clean Repo
## 🚁 Smart Farm Drone System

<p align="center">
<a href="https://arxiv.org/abs/2412.18588">Technical Paper</a> |
<a href="https://docs.openmind.org/">Documentation</a> |
<a href="https://x.com/openmind_agi">X</a> |
<a href="https://discord.gg/openmind">Discord</a>
</p>

A comprehensive perception-agent system for smart farming that detects crop diseases and commands drones for precision spraying.

---

## Quick Links
- **Documentation**: [README_SMARTFARM.md](./README_SMARTFARM.md)  
- **MAVSDK Adapter**: [bridge/mavsdk_adapter/](./bridge/mavsdk_adapter/)  
- **Perception Agent**: [agents/perception_agent/](./agents/perception_agent/)  
- **Tests**: [tests/integration/](./tests/integration/)

---

## Capabilities & Overview
- **Modular Architecture**: Python-first, easy to integrate.  
- **Data & Sensors**: Easily add new inputs (camera, LIDAR, etc.).  
- **Hardware Support via Plugins**: ROS2 / Zenoh / CycloneDDS / Websockets.  
- **Web-Based Debugging**: WebSim for visual debugging (example: http://localhost:8000/).  
- **Pre-configured Endpoints**: LLMs, TTS/ASR, and VLM integrations.

---

## Architecture Overview
![Architecture](https://github.com/user-attachments/assets/14e9b916-4df7-4700-9336-2983c85be311)

**Perception Agent → MAVSDK Writer → MAVSDK Reader → Mock Drone**  
(Ports: Perception 5001, Writer 5002, Reader 5003)

---

## Quick Start

### 1) Clone
```bash
git clone https://github.com/OpenMind/OM1.git
cd OM1
git submodule update --init
```

### 2) Virtual environment
```bash
# using uv:
uv venv
# or python venv:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt || pip install fastapi uvicorn pyserial mavsdk requests
```
### 3) MAVSDK adapter (example)
```bash
cd bridge/mavsdk_adapter/
pip install -r requirements.txt || pip install fastapi uvicorn pyserial mavsdk requests
```
### 4) Run health check (example)
```bash
../tests/integration/test_health_local.sh
```
### 5) Start example services
```bash
# run in separate terminals
python mock_drone_correct.py			# Terminal 1
python server_writer.py				# Terminal 2
python server_reader.py				# Terminal 3
python ../agents/perception_agent/app.py	# Terminal 4
```
Features

-   Disease detection (VLM/ML pipelines)
-   Precision spraying via MAVSDK
-   GPS navigation & telemetry
-   RESTful APIs & WebSim integration
-   Integration tests & health checks

Project Structure

├── bridge/mavsdk_adapter/       # Core drone comms & examples

├── agents/perception_agent/     # AI model + inference server

├── docs/                        # Documentation & guides

├── tests/integration/           # Health checks & CI tests

└── README_SMARTFARM.md          # SmartFarm full documentation

Full Autonomy & Ecosystem Integration

Support for autonomous orchestration involving services such as 'om1','unitree_sdk','om1-avatar', and optional video/processing services. Example supporting repositories:

-   https://github.com/OpenMind/OM1.git
-   https://github.com/OpenMind/unitree_sdk.git
-   https://github.com/OpenMind/OM1-avatar.git
-   (optional) https://github.com/OpenMind/OM1-video-processor.git

## Project Structure

├── bridge/mavsdk_adapter/          # Core drone communication system

├── agents/perception_agent/        # AI disease detection

├── tests/integration/              # Health checks and integration tests

└── README_SMARTFARM.md            # Complete documentation

## Full Autonomy Guidance

We're excited to introduce full autonomy mode, where multiple services work together in a loop without manual intervention:

- om1
- unitree_sdk – ROS 2 package (SLAM + Nav2)
- om1-avatar – React frontend / avatar display

Clone supporting repos if needed:

- https://github.com/OpenMind/OM1.git
- https://github.com/OpenMind/unitree_sdk.git
- https://github.com/OpenMind/OM1-avatar.git

## Starting the system (docker example)

Set your API key in shell config (  `~/.bashrc` or `~/.zshrc` ):

 Bash
```bash
echo 'export OM_API_KEY="your_api_key"' >> ~/.bashrc && source ~/.bashrc"
```
 Zsh
```bash 
echo 'export OM_API_KEY="your_api_key"' >> ~/.zshrc && source ~/.zshrc
```
Example docker commands:
-  Go to the OM1 folder:
```bash
cd OM1
docker-compose up om1 -d --no-build
```
-  Go to the unitree_sdk folder:
```bash
cd unitree_sdk
docker-compose up orchestrator -d --no-build
docker-compose up om1_sensor -d --no-build
docker-compose up watchdog -d --no-build
```
cd OM1-avatar
```bash
docker-compose up om1_avatar -d --no-build
```
Contributing

Please read CONTRIBUTING.md
 before opening pull requests. Use feature branches and include tests/instructions for large changes.
License

MIT License

Built with ❤️ for smart farming and precision agriculture.
