# ADB Device Manager - Docker Deployment

Docker container for the ADB Device Manager web application.

## ✅ Testing Results

**Container Status:** ✅ Running Successfully

```bash
# Health check
curl http://localhost:5020/api/health
# Response: {"status": "healthy", "auto_refresh_enabled": false, "timestamp": "..."}

# Devices check
curl http://localhost:5020/api/devices
# Response: 3 devices configured (Local Device, Device 1, Device 2)
```

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
- Container Port: `5020` → Host Port: `5020`

**Path Mappings:**
- `/app/data` → `/mnt/user/appdata/adb-device-manager/data`
- `/app/logs` → `/mnt/user/appdata/adb-device-manager/logs`
- `/app/apk` → `/mnt/user/appdata/adb-device-manager/apk`
- `/app/templates` → `/mnt/user/appdata/adb-device-manager/templates`

**Environment Variables:**
- `PYTHONUNBUFFERED` = `1`
- `TZ` = `Europe/London`

**Devices:**
- `/dev/bus/usb` → `/dev/bus/usb`

---

## 🌐 Access the Web UI

Once running:
- **Local:** http://localhost:5020
- **Network:** http://[UNRAID-IP]:5020
- **Example:** http://10.10.254.10:5020

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
- ✅ Server starts on port 5020
- ✅ Health check endpoint responds
- ✅ Device management works
- ✅ ADB tools available
- ✅ Network connectivity confirmed
- ✅ Logs writing correctly
- ✅ Volumes mount properly

---

## 🎉 Quick Test

After starting the container:

```bash
# Test health
curl http://localhost:5020/api/health

# Test devices
curl http://localhost:5020/api/devices

# View in browser
open http://localhost:5020
```

All systems operational! 🚀
