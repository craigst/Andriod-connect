# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Starting the Server
```bash
# Development (local Python)
python server.py

# Alternative with virtual environment
source venv/bin/activate
python server.py

# Using provided script
./start_server.sh
```

### Docker/Podman Deployment
```bash
# Navigate to compose directory
cd compose

# Build and start with Docker
docker-compose build
docker-compose up -d

# Or with Podman
podman-compose build
podman-compose up -d

# Check logs
docker-compose logs -f
# or
podman logs -f adb-device-manager
```

### Testing
```bash
# Quick API test (use correct server address)
python test_api.py

# Test health endpoint (use IP or hostname)
curl http://zues:5020/api/health
# or if zues hostname unavailable:
curl http://10.10.254.13:5020/api/health

# Test MCP server (if needed)
cd mcp-server
python mcp_server.py
```

### MCP Server (Separate Project)
```bash
cd mcp-server

# For Claude Desktop (stdio)
python mcp_server.py

# For n8n/web clients (HTTP) - use correct Flask API URL
source ../venv/bin/activate
FLASK_API_URL=http://zues:5020 python mcp_server_http.py
# or if zues hostname unavailable:
FLASK_API_URL=http://10.10.254.13:5020 python mcp_server_http.py
```

## Architecture Overview

This is a Flask-based Android device management system with the following core architecture:

### Main Components
- **server.py** - Flask web server and REST API (port 5020)
- **adb_manager.py** - Core ADB device management and SQL database operations
- **screen_detector.py** - Computer vision for screen template matching
- **screen_macros.py** - Device automation and macro execution
- **vehicle_lookup.py** - Vehicle registration lookup and override system
- **credentials_manager.py** - Device login credential storage
- **mcp-server/** - Separate MCP (Model Context Protocol) server for AI integration

### Data Flow
1. **Android Devices** (tablets running BCA Track app) ↔ **ADB Manager** ↔ **Flask API** ↔ **Web UI/MCP Server**
2. **SQL Database Extraction**: Devices → ADB pull → local sqlite files → API endpoints
3. **Paperwork Generation**: SQL data → Excel templates → generated loadsheets/timesheets

### Key Directories
- **data/** - SQLite databases (sql.db from devices, screen_control.db for app config)
- **paperwork/** - Generated Excel and PDF files organized by week
- **scripts/** - Loadsheet and timesheet generation scripts
- **templates/** - Excel templates and web UI templates
- **signature/** - Signature images for document generation
- **screen_templates/** - Template images for screen detection
- **mcp-server/** - Standalone MCP server for AI integration

## Database Architecture

### Primary Database (data/sql.db)
Pulled from Android devices, contains:
- **DWJJOB** - Job/load information (collections, deliveries, handovers)
- **DWVVEH** - Vehicle details linked to loads
- **DW5TRK** - Fleet vehicle registrations

### Application Database (data/screen_control.db)
Application-managed, contains:
- **timesheet_entries** - Weekly work hours and dates
- **credentials** - Device login credentials
- **vehicle_overrides** - Custom vehicle make/model corrections
- **screen_templates** and **screen_macros** - Automation system

## Business Logic

### Load Types
- **Standard Load**: Collection (C) + Delivery (D)
- **Handover Load**: Collection (C) + Shunt/Handover (S) → "BTT YARD FOR HAND OVER"
- **Multi-Location**: Multiple collections or deliveries with location-specific vehicle notes

### Date Handling
- Work week: Monday-Sunday (UK standard)
- Database dates: YYYYMMDD integer format
- Display dates: DD/MM/YYYY format
- File organization: DD-MM-YY folders by week ending Sunday

### Document Generation
- **Loadsheets**: Excel templates with vehicle details, signatures, load summaries
- **Timesheets**: Weekly hour tracking with load details per day
- **PDF Conversion**: Uses LibreOffice for Excel → PDF conversion

## Configuration Files

### Device Configuration
Edit `adb_manager.py` DEVICES list:
```python
DEVICES = [
    {"ip": "10.10.254.62", "port": "5555", "name": "Device 1"},
    {"ip": "10.10.254.13", "port": "5555", "name": "Device 2"}
]
```

### Flask Server Settings
In `server.py`:
```python
SERVER_PORT = 5020
LOG_FILE = "logs/server.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
```

## API Endpoints

### Core Endpoints
- `/api/health` - Health check
- `/api/devices` - Device status and management
- `/api/sql/pull` - Pull database from devices
- `/api/loads` - Load listing and filtering
- `/api/paperwork/loadsheet` - Generate loadsheets
- `/api/paperwork/timesheet` - Generate timesheets

### Device Operations
- `/api/devices/connect` - Connect to all devices
- `/api/devices/{address}/screenshot` - Capture device screenshot
- `/api/devices/{address}/auto-login` - Automated login

### Data Management
- `/api/timesheet/entries` - Timesheet hour management
- `/api/vehicles/lookup/{registration}` - Vehicle information lookup
- `/api/vehicles/override` - Save vehicle corrections

## Common Development Patterns

### Error Handling
The system uses comprehensive logging to `logs/server.log` with rotation. Check logs for device connection issues, SQL pull failures, or document generation problems.

### Vehicle Data Override
Use the vehicle override system when make/model data from devices is incorrect:
```python
# Save override via API
POST /api/vehicles/override
{"registration": "AB12CDE", "make_model": "FORD FIESTA"}
```

### Screen Automation
The system uses OpenCV template matching for screen detection and macro execution. Templates are stored in `screen_templates/` and macros in the database.

### Multi-Device Management
The system can manage multiple Android devices simultaneously. Each device is identified by IP:PORT and can be controlled independently.

## Development Notes

### Dependencies
Core dependencies in `requirements.txt`:
- Flask 3.0.0 - Web framework
- openpyxl 3.1.2 - Excel file manipulation
- opencv-python 4.8.1.78 - Computer vision for screen detection
- Pillow 10.2.0 - Image processing

### File Organization
- Week-based folder structure in `paperwork/` (DD-MM-YY format)
- Generated files include both Excel and PDF versions
- Templates use random signature selection from `signature/` directories

### MCP Integration
The MCP server (`mcp-server/`) is a separate project that provides AI-friendly tools for:
- Natural language load searching
- Automated paperwork generation
- Device management through AI assistants

Use the MCP server when you need to provide AI assistants with structured access to the Android-Connect functionality.

## Production Configuration

### Network Setup
The production system runs on:
- **Flask Server**: `http://zues:5020` (IP: 10.10.254.13:5020)
- **MCP HTTP Server**: `http://zues:8100`

### Verified Working Configuration
As of October 29, 2025, the following configuration is confirmed working:

#### MCP Server Environment
```bash
cd mcp-server
source ../venv/bin/activate
FLASK_API_URL=http://zues:5020 python mcp_server_http.py
```

#### API Testing
```bash
# Direct API access
curl -s "http://zeus:5020/api/loads"

# Health check
curl "http://zues:5020/api/health"
```

#### Claude Code Integration
The MCP tools are fully functional with Claude Code for:
- Load searching by date (`mcp__android-connect__search_loads_by_date`)
- Device status checking (`mcp__android-connect__get_device_status`)
- Paperwork generation (`mcp__android-connect__generate_loadsheet`)
- Timesheet management
- Vehicle lookup and overrides

### Troubleshooting
- If hostname `zues` is unavailable, use IP address `10.10.254.13`
- Ensure virtual environment is activated for MCP server
- Check `logs/server.log` for Flask server issues
- MCP server runs on port 8100, Flask on port 5020