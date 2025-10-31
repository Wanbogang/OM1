
1→# 🚁 Smart Farm Drone System - Perception Agent
2→
3→## 📋 Overview
4→
5→This project implements a **Perception Agent** for a smart farm drone system that can detect crop diseases and automatically command drones to spray affected areas. The system simulates a complete workflow from disease detection to drone navigation and spraying operations.
6→
7→## 🏗️ System Architecture
8→
9→```
10→┌─────────────────┐ HTTP ┌─────────────────┐ File ┌─────────────────┐ Serial ┌─────────────────┐
11→│ Perception │ ────────► │ MAVSDK │ ────────► │ MAVSDK │ ────────► │ Mock Drone │
12→│ Agent │ │ Writer │ │ Reader │ │ (MAVLink) │
13→│ (Port 5001) │ │ (Port 5002) │ │ │ │ (Port 5000) │
14→└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
15→ │ │ │ │
16→ ▼ ▼ ▼ ▼
17→📸 Image Analysis 📝 Command Queue ⚙️ Command Execution 🚁 Drone Simulation
18→🤖 Disease Detection 💾 JSON Storage 🔄 MAVLink Protocol 📡 Telemetry Response
19→📍 GPS Coordinate Generation 🌐 HTTP API 📡 Serial Communication ✅ Status Updates
20→```
21→
22→## 🎯 Core Components
23→
24→### 1. 🚁 Mock Drone (`mock_drone_correct.py`)
25→- **Port**: 5000
26→- **Purpose**: Simulates a real drone using MAVLink protocol
27→- **Features**:
28→ - Responds to `goto` commands with position updates
29→ - Handles `spray` commands with execution confirmation
30→ - Simulates realistic drone movement and timing
31→
32→### 2. 📝 MAVSDK Writer (`server_writer.py`)
33→- **Port**: 5002
34→- **Purpose**: Receives HTTP commands and writes them to JSON file
35→- **Features**:
36→ - RESTful API endpoint `/command`
37→ - JSON file queue system
38→ - Command validation and logging
39→
40→### 3. 📖 MAVSDK Reader (`server_reader.py`)
41→- **Purpose**: Reads JSON commands and executes them via mock drone
42→- **Features**:
43→ - File-based command processing
44→ - MAVLink communication with drone
45→ - Real-time status updates
46→
47→### 4. 🤖 Perception Agent (`app.py`)
48→- **Port**: 5001
49→- **Purpose**: Detects diseases and generates drone commands
50→- **Features**:
51→ - Simulated disease detection (60% probability)
52→ - GPS coordinate generation
53→ - Automatic drone commanding
54→ - Web interface for monitoring
55→
56→## 🚀 Quick Start
57→
58→### Prerequisites
59→```bash
60→# Install required Python packages
61→pip install fastapi uvicorn pyserial mavsdk requests
62→```
63→
64→### Step 1: Start Mock Drone
65→```bash
66→# Terminal 1
67→python mock_drone_correct.py
68→# Expected: Server listening on port 5000
69→```
70→
71→### Step 2: Start MAVSDK Writer
72→```bash
73→# Terminal 2
74→python server_writer.py
75→# Expected: Server running on http://localhost:5002
76→```
77→
78→### Step 3: Start MAVSDK Reader
79→```bash
80→# Terminal 3
81→python server_reader.py
82→# Expected: MAVSDK Reader started
83→```
84→
85→### Step 4: Start Perception Agent
86→```bash
87→# Terminal 4
88→python app.py
89→# Expected: Application startup complete
90→```
91→
92→### Step 5: Test the System
93→```bash
94→# Terminal 5
95→./test_health_local.sh
96→# Expected: All 6 health checks should pass
97→```
98→
99→## 📊 API Endpoints
100→
101→### Perception Agent (Port 5001)
102→- `GET /` - Web interface
103→- `GET /health` - Health check
104→- `GET /detect` - Trigger disease detection
105→- `GET /status` - System status
106→
107→### MAVSDK Writer (Port 5002)
108→- `POST /command` - Submit drone command
109→ ```json
110→ {
111→ "command": "goto|spray",
112→ "lat": -6.9175,
113→ "lon": 107.6191,
114→ "alt": 10.0
115→ }
116→ ```
117→
118→### Mock Drone (Port 5000)
119→- **Protocol**: MAVLink over TCP
120→- **Purpose**: Drone simulation and telemetry
121→
122→## 🧪 Testing
123→
124→### Health Check Script
125→```bash
126→./test_health_local.sh
127→```
128→This script performs 6 critical tests:
129→1. Mock Drone connectivity (Port 5000)
130→2. MAVSDK Writer API (Port 5002)
131→3. MAVSDK Reader process
132→4. Perception Agent API (Port 5001)
133→5. File system permissions
134→6. End-to-end workflow
135→
136→### Unit Tests
137→```bash
138→python test_adapter_mock.py
139→```
140→
141→### Manual Testing
142→```bash
143→# Test disease detection
144→curl http://localhost:5001/detect
145→
146→# Test MAVSDK Writer
147→curl -X POST http://localhost:5002/command \
148→ -H "Content-Type: application/json" \
149→ -d '{"command":"goto","lat":-6.9175,"lon":107.6191,"alt":10.0}'
150→```
151→
152→## 📁 File Structure
153→
154→```
155→smartfarm/
156→├── README_SMARTFARM.md # This documentation
157→├── mock_drone_correct.py # MAVLink drone simulator
158→├── server_writer.py # HTTP to JSON command converter
159→├── server_reader.py # JSON to MAVLink executor
160→├── app.py # Main perception agent
161→├── test_adapter_mock.py # Unit tests
162→├── test_health_local.sh # Integration health checks
163→├── commands.json # Command queue file
164→└── requirements.txt # Python dependencies
165→```
166→
167→## 🔄 Workflow Example
168→
169→1. **Disease Detection**: Perception agent detects disease in rice field
170→2. **GPS Generation**: Creates GPS coordinates for affected area
171→3. **Command Queue**: Sends `goto` command to MAVSDK Writer
172→4. **Navigation**: Drone flies to specified coordinates
173→5. **Spraying**: Executes `spray` command at target location
174→6. **Confirmation**: Returns success status to perception agent
175→
176→## 📈 System Monitoring
177→
178→### Real-time Status
179→- Visit `http://localhost:5001` for web interface
180→- Check terminal logs for real-time updates
181→- Monitor `commands.json` for command queue status
182→
183→### Debug Information
184→Each component provides detailed logging:
185→- Mock Drone: MAVLink message logs
186→- MAVSDK Writer: HTTP request/response logs
187→- MAVSDK Reader: Command execution logs
188→- Perception Agent: Detection and command logs
189→
190→## 🛠️ Configuration
191→
192→### Default Settings
193→- **Mock Drone Port**: 5000
194→- **MAVSDK Writer Port**: 5002
195→- **Perception Agent Port**: 5001
196→- **Command File**: `commands.json`
197→- **Disease Detection Rate**: 60%
198→
199→### Customization
200→Edit the following variables in respective files:
201→- GPS coordinates in `app.py`
202→- Port numbers in each service file
203→- Detection probability in perception agent
204→- MAVLink parameters in mock drone
205→
206→## 🚨 Troubleshooting
207→
208→### Common Issues
209→
210→1. **Port Already in Use**
211→ ```bash
212→ # Find and kill process using port
213→ lsof -ti:5000 | xargs kill -9
214→ ```
215→
216→2. **Permission Denied**
217→ ```bash
218→ # Make scripts executable
219→ chmod +x test_health_local.sh
220→ ```
221→
222→3. **Module Not Found**
223→ ```bash
224→ # Install dependencies
225→ pip install -r requirements.txt
226→ ```
227→
228→4. **Connection Refused**
229→ - Ensure all services are running in correct order
230→ - Check firewall settings
231→ - Verify port availability
232→
233→### Debug Mode
234→Enable verbose logging by setting environment variable:
235→```bash
236→export DEBUG=true
237→python app.py
238→```
239→
240→## 🎯 Next Steps
241→
242→### Production Enhancements
243→1. **Real ONNX Models**: Replace simulated detection with actual ML models
244→2. **PX4 SITL Integration**: Connect to real PX4 simulation
245→3. **Database Integration**: Add PostgreSQL for persistent storage
246→4. **Web Dashboard**: Create comprehensive monitoring interface
247→5. **Authentication**: Add security for API endpoints
248→
249→### Advanced Features
250→1. **Multiple Drone Support**: Coordinate multiple drones simultaneously
251→2. **Weather Integration**: Add weather data for flight planning
252→3. **Field Mapping**: Integrate with GIS systems
253→4. **Analytics Dashboard**: Track spraying efficiency and disease patterns
254→
255→## 📞 Support
256→
257→For issues and questions:
258→1. Check the troubleshooting section above
259→2. Review the health check script output
260→3. Examine individual service logs
261→4. Verify all services are running in correct order
262→
263→---
264→
265→**Status**: ✅ Fully functional and tested
266→**Last Updated**: 2025-06-17
267→**Version**: 1.0.0 - MVP Release
