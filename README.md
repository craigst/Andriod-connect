# ADB Device Manager

A comprehensive Flask-based web application for managing Android devices via ADB (Android Debug Bridge), pulling SQL databases, and generating automated paperwork (loadsheets and timesheets).

## 🚀 Features

- **Multi-Device Management**: Connect and manage multiple Android devices simultaneously
- **SQL Database Access**: Pull SQLite databases from Android devices with BCA Track app installed
- **Automated Paperwork Generation**: 
  - Generate loadsheets for individual loads
  - Generate timesheets for date ranges
  - Export to Excel (.xlsx) format
- **REST API**: Full-featured API for automation and integration
- **Web UI**: User-friendly web interface for manual operations
- **Docker Support**: Easy deployment with Docker/Podman

## 🤖 AI Integration

The MCP (Model Context Protocol) server is now a **separate project** in the `mcp-server/` directory. 

This allows AI assistants like Claude to control the system with natural language:
- "Generate paperwork for all loads this week"
- "Pull the latest database from the device"
- "Show me loads going to Ashford"

**See:** [mcp-server/README.md](mcp-server/README.md) for setup and usage.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Docker Deployment](#docker-deployment)
- [MCP Server](#mcp-server)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## � Prerequisites

### For Local Development:
- Python 3.11+
- ADB (Android Debug Bridge) installed
- Android devices with:
  - ADB debugging enabled
  - Network ADB enabled
  - BCA Track app installed (for SQL operations)

### For Docker Deployment:
- Docker or Podman installed
- Network access to Android devices

## 📦 Installation

### Local Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Andriod-connect
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Install ADB (if not already installed):**
```bash
# Ubuntu/Debian
sudo apt-get install android-tools-adb

# macOS
brew install android-platform-tools

# Windows - Download from Android SDK Platform Tools
```

## 🚀 Quick Start

### Option 1: Local Python (Development)

```bash
# Start the server
python server.py

# Server will be available at:
# http://localhost:5020
```

### Option 2: Docker/Podman (Production)

```bash
# Navigate to compose directory
cd compose

# Build the container
docker-compose build
# OR with Podman
podman-compose build

# Start the container
docker-compose up -d
# OR with Podman
podman-compose up -d

# Check container status
docker-compose ps
# OR
podman ps

# View logs
docker-compose logs -f
# OR
podman logs -f adb-device-manager
```

## 💡 Usage

### Web Interface

Open your browser and navigate to:
```
http://localhost:5020
```

The web interface provides:
- Device status overview
- Connect/disconnect controls
- SQL database operations
- Paperwork generation interface

### Command Line (API)

#### 1. Check Server Health

```bash
curl http://localhost:5020/api/health
```

#### 2. Connect to Devices

```bash
curl -X POST http://localhost:5020/api/devices/connect
```

#### 3. View Device Status

```bash
curl http://localhost:5020/api/devices | jq '.'
```

#### 4. Pull SQL Database

```bash
# From any available device
curl -X POST http://localhost:5020/api/sql/pull

# From specific device
curl -X POST http://localhost:5020/api/sql/pull \
  -H "Content-Type: application/json" \
  -d '{"device_index": 1}'
```

#### 5. View Loads

```bash
curl http://localhost:5020/api/loads | jq '.'
```

#### 6. Generate Loadsheet

```bash
curl -X POST http://localhost:5020/api/paperwork/loadsheet \
  -H "Content-Type: application/json" \
  -d '{"load_number": "$S275052"}'
```

#### 7. Generate Timesheet

```bash
curl -X POST http://localhost:5020/api/paperwork/timesheet \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-09-29", "end_date": "2025-10-05"}'
```

#### 8. Generate ALL Loadsheets

```bash
curl -s http://localhost:5020/api/loads | jq -r '.loads[].load_number' | \
while read load; do
  curl -X POST http://localhost:5020/api/paperwork/loadsheet \
    -H "Content-Type: application/json" \
    -d "{\"load_number\":\"$load\"}"
  sleep 1
done
```

## 📚 API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

### Quick API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/devices` | GET | Get all devices status |
| `/api/devices/connect` | POST | Connect to all devices |
| `/api/devices/add` | POST | Add new device |
| `/api/devices/remove` | POST | Remove device |
| `/api/sql/pull` | POST | Pull SQL database |
| `/api/loads` | GET | Get all loads |
| `/api/paperwork/loadsheet` | POST | Generate loadsheet |
| `/api/paperwork/timesheet` | POST | Generate timesheet |
| `/api/paperwork/weeks` | GET | Get available weeks |

## 🐳 Docker Deployment

### Build and Run

```bash
cd compose

# Build image
docker-compose build --no-cache

# Start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down
```

### Using Podman (Docker alternative)

```bash
cd compose

# Build image
podman build --no-cache -t compose_adb-device-manager -f Dockerfile ..

# Run container
podman run -d \
  --name adb-device-manager \
  --network host \
  -v ../data:/app/data \
  -v ../logs:/app/logs \
  -v ../apk:/app/apk \
  -v ../paperwork:/app/paperwork \
  -e PYTHONUNBUFFERED=1 \
  -e TZ=Europe/London \
  localhost/compose_adb-device-manager:latest

# View logs
podman logs -f adb-device-manager

# Stop container
podman stop adb-device-manager
podman rm adb-device-manager
```

### Docker Compose Configuration

The `docker-compose.yml` includes:
- Network host mode for ADB access
- Volume mounts for persistence:
  - `data/` - SQL database storage
  - `logs/` - Server logs
  - `apk/` - APK files for installation
  - `paperwork/` - Generated Excel files
  - `templates/` - Excel templates and signatures

### GitHub Container Registry

- Every push to `main` (and any tag that starts with `v`) automatically builds and publishes `ghcr.io/craigst/andriod-connect` via `.github/workflows/publish-container.yml`.
- To pull the latest image: `docker pull ghcr.io/craigst/andriod-connect:latest`
- To run locally: `docker run --rm -p 5020:5020 ghcr.io/craigst/andriod-connect:latest`
- Republishing from a fork or local build:
  1. `echo $TOKEN | docker login ghcr.io -u <github-username> --password-stdin` (`TOKEN` needs `write:packages`)
  2. `docker build -f compose/Dockerfile -t ghcr.io/<namespace>/andriod-connect:latest .`
  3. `docker push ghcr.io/<namespace>/andriod-connect:latest`

## ⚙️ Configuration

### Device Configuration

Edit `adb_manager.py` to configure default devices:

```python
DEVICES = [
    {"ip": "10.10.254.62", "port": "5555", "name": "Device 1"},
    {"ip": "10.10.254.13", "port": "5555", "name": "Device 2"},
]
```

### Server Configuration

Edit `server.py` for server settings:

```python
SERVER_PORT = 5020  # Change server port
LOG_FILE = "logs/server.log"  # Log file location
LOG_MAX_SIZE = 10 * 1024 * 1024  # Log rotation size
```

### App Configuration

Edit constants in `adb_manager.py`:

```python
APP_PACKAGE = "com.bca.bcatrack"  # App package name
APK_PATH = "apk/BCAApp.apk"  # APK file location
DATA_FOLDER = "data"  # Database storage folder
```

## 🤖 MCP Server

The MCP (Model Context Protocol) server is a **separate project** located in `mcp-server/`.

It provides AI assistants like Claude with tools to:
- Search and query loads
- Generate paperwork automatically
- Control devices
- Manage timesheet entries

**Quick Start:**
```bash
cd mcp-server
pip install -r requirements.txt

# For Claude Desktop (stdio)
python mcp_server.py

# For n8n/web clients (HTTP)
python mcp_server_http.py
```

**See full documentation:** [mcp-server/README.md](mcp-server/README.md)

## 📁 Project Structure

```
Andriod-connect/
├── adb_manager.py          # Core ADB management logic
├── server.py               # Flask web server and API
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── API_DOCUMENTATION.md   # Complete API docs
├── mcp-server/            # MCP Server (separate project)
│   ├── mcp_server.py      # Stdio transport (Claude Desktop)
│   ├── mcp_server_http.py # HTTP/SSE transport (n8n, web)
│   ├── requirements.txt   # MCP dependencies
│   └── README.md          # MCP documentation
├── compose/
│   ├── Dockerfile         # Docker container definition
│   └── docker-compose.yml # Docker Compose config
├── scripts/
│   ├── loadsheet.py       # Loadsheet generation script
│   └── timesheet.py       # Timesheet generation script
├── templates/
│   └── index.html         # Web UI
├── signature/             # Signature images for paperwork
├── data/                  # SQL database storage
├── logs/                  # Server logs
├── apk/                   # APK files
└── paperwork/             # Generated Excel files
```

## 🔍 Troubleshooting

### Container won't start

```bash
# Check Docker/Podman is running
systemctl status docker
# OR
systemctl status podman

# Start Docker/Podman
sudo systemctl start docker
```

### Cannot connect to devices

```bash
# Test ADB connectivity manually
adb connect 10.10.254.62:5555

# Check if device is reachable
ping 10.10.254.62

# Restart ADB server
adb kill-server
adb start-server
```

### Loadsheet/Timesheet generation fails

1. Ensure SQL database is pulled first:
```bash
curl -X POST http://localhost:5020/api/sql/pull
```

2. Check if load exists:
```bash
curl http://localhost:5020/api/loads | jq '.loads[].load_number'
```

3. Check container logs:
```bash
podman logs --tail 50 adb-device-manager
```

### Port 5020 already in use

```bash
# Find process using port 5020
lsof -i :5020

# Kill the process or change SERVER_PORT in server.py
```

## 📝 Generated Files

### Loadsheets
- **Location:** `paperwork/DD-MM-YY/`
- **Format:** `{load_number}_{location}.xlsx`
- **Example:** `$S275052_WBAC_Ashford.xlsx`

### Timesheets
- **Location:** `paperwork/DD-MM-YY/`
- **Format:** `timesheet_{date}.xlsx`
- **Example:** `timesheet_2025-10-05.xlsx`

## � Security Notes

- This tool requires ADB access to devices
- Ensure devices are on a trusted network
- Use firewall rules to restrict access to port 5020
- Never expose the server directly to the internet

## 📄 License

[Your License Here]

## 👥 Contributors

[Your Contributors Here]

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the API documentation
- Review container logs

---

**Version:** 2.0  
**Last Updated:** October 2025
