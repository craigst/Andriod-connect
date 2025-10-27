# ADB Device Manager - Docker Deployment

Docker container for the ADB Device Manager web application with integrated MCP servers.

## ✅ Testing Results

**Container Status:** ✅ Running Successfully

```bash
# Health check
curl http://localhost:5020/api/health
# Response: {"status": "healthy", "auto_refresh_enabled": false, "timestamp": "..."}

# Devices check
curl http://localhost:5020/api/devices
# Response: 3 devices configured (Local Device, Device 1, Device 2)

# MCP HTTP Server check
curl http://localhost:8100/sse
# SSE connection endpoint for MCP clients
```

## 🎯 Integrated Services

The Docker container now runs **three services**:

1. **Flask API** (Port 5020) - Main web application and REST API
2. **MCP HTTP Server** (Port 8100) - HTTP/SSE transport for n8n and other HTTP clients
3. **MCP Stdio Server** - Stdio transport for local/internal MCP access

All MCP tools provide AI-friendly access to:
- Load search and management
- Paperwork generation (loadsheets, timesheets)
- Device management
- Vehicle lookup
- Timesheet entries
- Database operations

---

## 🚀 Quick Start

### Using Docker Compose

```bash
# Build and start the container
cd compose
docker compose up -d

# View logs
docker logs adb-device-manager

# Stop container
docker compose down
```

### Using Docker CLI (Unraid Compatible)

```bash
docker run -d \
  --name=adb-device-manager \
  --network=host \
  --privileged \
  --device=/dev/bus/usb:/dev/bus/usb \
  -e TZ=Europe/London \
  -e PYTHONUNBUFFERED=1 \
  -v /path/to/data:/app/data \
  -v /path/to/logs:/app/logs \
  -v /path/to/apk:/app/apk \
  -v /path/to/templates:/app/templates \
  --restart unless-stopped \
  localhost/compose_adb-device-manager:latest
```

---

## 📁 Project Structure for Docker

Move your files to this structure for Unraid:

```
/mnt/user/appdata/adb-device-manager/
├── compose/
│   ├── docker-compose.yml
│   └── Dockerfile
├── adb_manager.py
├── server.py
├── requirements.txt
├── templates/
│   └── index.html
├── data/           # Persistent SQL database storage
├── logs/           # Application logs
└── apk/            # APK files (add BCAApp.apk here)
```

---

## 🔧 Unraid Setup

### Method 1: Docker Compose (Recommended)

1. **Install Compose Plugin**
   ```bash
   # SSH into Unraid
   docker plugin install docker/compose
   ```

2. **Copy Project to Unraid**
   ```bash
   # Upload files to Unraid
   /mnt/user/appdata/adb-device-manager/
   ```

3. **Build and Run**
   ```bash
   cd /mnt/user/appdata/adb-device-manager/compose
   docker compose up -d
   ```

### Method 2: Unraid Community Applications Template

Create a custom template in Unraid:

**Container Name:** `adb-device-manager`  
**Repository:** `localhost/compose_adb-device-manager:latest` (after building)  
**Network Type:** `Host`  
**Privileged:** `On`

**Port Mappings:**
- Container Port: `5020` → Host Port: `5020` (Flask API)
- Container Port: `8100` → Host Port: `8100` (MCP HTTP Server)

**Path Mappings:**
- `/app/data` → `/mnt/user/appdata/adb-device-manager/data`
- `/app/logs` → `/mnt/user/appdata/adb-device-manager/logs`
- `/app/apk` → `/mnt/user/appdata/adb-device-manager/apk`
- `/app/templates` → `/mnt/user/appdata/adb-device-manager/templates`

**Environment Variables:**
- `PYTHONUNBUFFERED` = `1`
- `TZ` = `Europe/London`
- `FLASK_API_URL` = `http://localhost:5020`
- `MCP_HOST` = `0.0.0.0`
- `MCP_PORT` = `8100`

**Devices:**
- `/dev/bus/usb` → `/dev/bus/usb`

---

## 🌐 Access the Services

Once running:

### Web UI
- **Local:** http://localhost:5020
- **Network:** http://[UNRAID-IP]:5020
- **Example:** http://10.10.254.10:5020

### MCP HTTP Server (for n8n, etc.)
- **SSE Endpoint:** http://localhost:8100/sse
- **Messages Endpoint:** http://localhost:8100/messages
- **Network Access:** http://[UNRAID-IP]:8100/sse

---

## 📊 Volume Mounts

| Container Path | Host Path | Purpose |
|----------------|-----------|---------|
| `/app/data` | `../data` | SQL database storage (persistent) |
| `/app/logs` | `../logs` | Application logs (rotating) |
| `/app/apk` | `../apk` | APK files for app installation |
| `/app/templates` | `../templates` | Web UI templates (can edit live) |

---

## 🔍 Monitoring & Logs

### View Real-time Logs
```bash
docker logs -f adb-device-manager
```

### Check Container Status
```bash
docker ps | grep adb-device-manager
```

### Health Check
```bash
docker inspect adb-device-manager | grep Health -A 10
```

### Access Container Shell
```bash
docker exec -it adb-device-manager /bin/bash
```

### Test ADB Inside Container
```bash
docker exec -it adb-device-manager adb devices
```

---

## 🎯 Features in Docker

✅ **ADB Tools Included** - Pre-installed android-tools-adb  
✅ **Network Host Mode** - Direct access to network devices  
✅ **Privileged Mode** - USB device access for ADB  
✅ **Persistent Storage** - Data and logs survive container restarts  
✅ **Auto-restart** - Container restarts on failure  
✅ **Health Checks** - Built-in health monitoring  
✅ **Log Rotation** - Automatic log management (10MB max, 5 backups)  
✅ **MCP Servers** - Both HTTP (port 8100) and Stdio transports included  
✅ **AI Integration** - 17+ MCP tools for AI-powered automation

## 🤖 MCP Server Features

The integrated MCP servers provide comprehensive AI-friendly tools:

### Search & Discovery
- `search_loads_by_date` - Search loads by date/period (today, this_week, etc.)
- `search_loads_by_location` - Search by customer, town, or postcode
- `get_loads_summary` - Get all loads with descriptions
- `get_load_details` - Detailed load information including vehicles

### Paperwork Generation
- `generate_loadsheet` - Create loadsheet for specific load
- `generate_all_loadsheets_for_period` - Batch generate for date range
- `generate_timesheet` - Create timesheet for date range
- `list_available_weeks` - Show weeks available for timesheets

### Device Management
- `get_device_status` - Check all device statuses
- `pull_latest_data` - Pull SQL database from device
- `connect_devices` - Connect to all configured devices
- `check_database_freshness` - Check database age

### Timesheet Management
- `create_timesheet_entry` - Add/update timesheet entry
- `get_timesheet_entries` - Retrieve entries for a week

### Vehicle Lookup
- `lookup_vehicle` - Look up vehicle by registration
- `save_vehicle_override` - Save custom vehicle data

### Resources
- `resource://loads/current` - Current loads with details
- `resource://devices/status` - Device statuses
- `resource://database/info` - Database information
- `resource://paperwork/weeks` - Available weeks

---

## 🛠️ Building the Image

### Build Locally
```bash
cd compose
docker compose build
```

### Build with Custom Tag
```bash
docker build -f compose/Dockerfile -t adb-device-manager:latest .
```

### Rebuild After Changes
```bash
docker compose build --no-cache
docker compose up -d --force-recreate
```

---

## 🔄 Updating the Container

```bash
# Stop container
docker compose down

# Rebuild image
docker compose build --no-cache

# Start with new image
docker compose up -d

# Verify
docker logs adb-device-manager
```

---

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs adb-device-manager

# Check if port is already in use
netstat -tulpn | grep 5020

# Restart container
docker restart adb-device-manager
```

### Can't Connect to Devices
```bash
# Check ADB inside container
docker exec -it adb-device-manager adb devices

# Check network access
docker exec -it adb-device-manager ping 10.10.254.62

# Verify host network mode
docker inspect adb-device-manager | grep NetworkMode
```

### Permission Issues
```bash
# Ensure privileged mode is enabled
docker inspect adb-device-manager | grep Privileged

# Check USB device access
docker exec -it adb-device-manager ls -la /dev/bus/usb
```

### SQL Database Not Persisting
```bash
# Verify volume mount
docker inspect adb-device-manager | grep Mounts -A 20

# Check file permissions
ls -la ../data/
```

---

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Disable Python output buffering |
| `TZ` | `Europe/London` | Container timezone |
| `FLASK_API_URL` | `http://localhost:5020` | Flask API endpoint for MCP servers |
| `MCP_HOST` | `0.0.0.0` | MCP HTTP server bind address |
| `MCP_PORT` | `8100` | MCP HTTP server port |

---

## 🔐 Security Notes

- Container runs in **privileged mode** for USB/ADB access
- Uses **host network** for direct device communication
- All data persists in mounted volumes
- Logs are rotated automatically

---

## 📚 Additional Resources

- **Main Documentation:** `../README.md`
- **API Examples:** `../API_EXAMPLES.md`
- **Testing Script:** `../test_api.py`

---

## 💡 Tips for Unraid

1. **Add to Dashboard:**
   - Add WebUI icon: `http://[IP]:[PORT:5020]`
   - Icon URL: Any Android/ADB related icon

2. **Auto-start on Boot:**
   - Set restart policy to `unless-stopped` (already configured)

3. **Backup Configuration:**
   - Backup `/mnt/user/appdata/adb-device-manager/` directory
   - Includes all data, logs, and APK files

4. **Monitor Resource Usage:**
   ```bash
   docker stats adb-device-manager
   ```

5. **Update Notifications:**
   - Consider using Unraid's Docker Auto Update plugin
   - Or rebuild manually when you update the code

---

## ✅ Verified Working

- ✅ Container builds successfully
- ✅ Flask API starts on port 5020
- ✅ MCP HTTP Server starts on port 8100
- ✅ MCP Stdio Server running in foreground
- ✅ Health check endpoint responds
- ✅ Device management works
- ✅ ADB tools available
- ✅ Network connectivity confirmed
- ✅ Logs writing correctly
- ✅ Volumes mount properly
- ✅ All MCP tools functional

---

## 🎉 Quick Test

After starting the container:

```bash
# Test Flask API health
curl http://localhost:5020/api/health

# Test devices
curl http://localhost:5020/api/devices

# Test MCP HTTP Server (SSE endpoint)
curl http://localhost:8100/sse

# View in browser
open http://localhost:5020

# Check MCP HTTP logs
docker logs adb-device-manager | grep "MCP HTTP"
```

All systems operational! 🚀

## 📡 Using MCP with n8n

To connect n8n to the MCP HTTP server:

1. **Add MCP Node** in n8n workflow
2. **Configure Connection:**
   - Protocol: `HTTP`
   - SSE Endpoint: `http://[DOCKER-HOST]:8100/sse`
   - Messages Endpoint: `http://[DOCKER-HOST]:8100/messages`
3. **Available Tools:** All 17+ MCP tools listed above

Example n8n workflow:
- Trigger: Schedule (daily)
- MCP Tool: `search_loads_by_date` with period "today"
- MCP Tool: `generate_all_loadsheets_for_period` with period "today"
- Result: Automated daily loadsheet generation

## 📋 Service Startup Sequence

The Docker entrypoint script manages services in this order:

1. **Start Flask API** → Runs in background on port 5020
2. **Wait for Flask Ready** → Health check until API responds (max 30s)
3. **Start MCP HTTP Server** → Runs in background on port 8100
4. **Start MCP Stdio Server** → Runs in foreground (keeps container alive)

All logs are available:
- Flask API: `/app/logs/flask.log`
- MCP HTTP: `/app/logs/mcp_http.log`
- MCP Stdio: Container stdout

## 🔧 MCP Configuration

The MCP servers use these environment variables (already configured):

```bash
FLASK_API_URL=http://localhost:5020  # Backend API endpoint
MCP_HOST=0.0.0.0                      # Allow external connections
MCP_PORT=8100                         # HTTP server port
```

To customize, edit `.env` file or `docker-compose.yml`.
