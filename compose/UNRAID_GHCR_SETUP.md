# ADB Device Manager - Unraid Setup with GitHub Container Registry

This guide explains how to deploy the ADB Device Manager on Unraid using the pre-built image from GitHub Container Registry.

## 🚀 Quick Start

### Prerequisites
- Unraid server
- Docker installed (default on Unraid)
- SSH access to Unraid

### Setup Steps

1. **Create Directory Structure on Unraid**
   ```bash
   mkdir -p /mnt/user/appdata/adb-device-manager/compose
   mkdir -p /mnt/user/appdata/adb-device-manager/data
   mkdir -p /mnt/user/appdata/adb-device-manager/logs
   mkdir -p /mnt/user/appdata/adb-device-manager/apk
   mkdir -p /mnt/user/appdata/adb-device-manager/paperwork
   ```

2. **Upload Configuration Files**
   - Copy `docker-compose.yml` to `/mnt/user/appdata/adb-device-manager/compose/`
   - Copy `.env` to `/mnt/user/appdata/adb-device-manager/compose/`

3. **Update .env File for Unraid**
   
   Edit `/mnt/user/appdata/adb-device-manager/compose/.env`:
   ```bash
   # Timezone
   TZ=Europe/London
   
   # Python settings
   PYTHONUNBUFFERED=1
   
   # Host paths for Unraid
   DATA_PATH=/mnt/user/appdata/adb-device-manager/data
   LOGS_PATH=/mnt/user/appdata/adb-device-manager/logs
   APK_PATH=/mnt/user/appdata/adb-device-manager/apk
   PAPERWORK_PATH=/mnt/user/appdata/adb-device-manager/paperwork
   
   # Templates are built into container - only uncomment if customizing
   # TEMPLATES_PATH=/mnt/user/appdata/adb-device-manager/templates
   
   # Container port
   HOST_PORT=5020
   CONTAINER_PORT=5020
   
   # Image version
   IMAGE_TAG=latest
   ```

4. **Deploy the Container**
   ```bash
   cd /mnt/user/appdata/adb-device-manager/compose
   docker compose pull
   docker compose up -d
   ```

5. **Verify Deployment**
   ```bash
   # Check container status
   docker ps | grep adb-device-manager
   
   # Check logs
   docker logs adb-device-manager
   
   # Test health endpoint
   curl http://localhost:5020/api/health
   ```

## 📁 Volume Mappings

The compose file uses environment variables for flexible path configuration:

| Environment Variable | Default (dev) | Unraid Path | Container Path | Purpose |
|---------------------|---------------|-------------|----------------|---------|
| `DATA_PATH` | `../data` | `/mnt/user/appdata/adb-device-manager/data` | `/app/data` | SQL database |
| `LOGS_PATH` | `../logs` | `/mnt/user/appdata/adb-device-manager/logs` | `/app/logs` | Application logs |
| `APK_PATH` | `../apk` | `/mnt/user/appdata/adb-device-manager/apk` | `/app/apk` | APK files |
| `PAPERWORK_PATH` | `../paperwork` | `/mnt/user/appdata/adb-device-manager/paperwork` | `/app/paperwork` | Generated docs |

**Note:** Templates are built into the container image. The `TEMPLATES_PATH` volume mount is commented out by default. Only uncomment if you need to customize the web UI templates.

## 🔄 Updating the Container

When a new version is released:

```bash
cd /mnt/user/appdata/adb-device-manager/compose

# Pull latest image
docker compose pull

# Recreate container with new image
docker compose up -d

# Verify update
docker logs adb-device-manager
```

## 🌐 Access the Web UI

- **Local:** http://localhost:5020
- **Network:** http://[UNRAID-IP]:5020
- **Example:** http://10.10.254.10:5020

## 🔧 Configuration

### Using Different Image Versions

Edit `.env` file:
```bash
# Use specific version tag
IMAGE_TAG=v1.0.0

# Or use latest (default)
IMAGE_TAG=latest
```

Then recreate the container:
```bash
docker compose up -d
```

### Custom Port

Edit `.env` file:
```bash
HOST_PORT=8080
CONTAINER_PORT=5020
```

### Custom Timezone

Edit `.env` file:
```bash
TZ=America/New_York
```

## 📊 Container Management

### View Logs
```bash
# Real-time logs
docker logs -f adb-device-manager

# Last 100 lines
docker logs --tail 100 adb-device-manager
```

### Restart Container
```bash
docker compose restart
```

### Stop Container
```bash
docker compose down
```

### Start Container
```bash
docker compose up -d
```

### View Resource Usage
```bash
docker stats adb-device-manager
```

## 🐛 Troubleshooting

### Container Won't Start

1. Check logs:
   ```bash
   docker logs adb-device-manager
   ```

2. Verify paths exist:
   ```bash
   ls -la /mnt/user/appdata/adb-device-manager/
   ```

3. Check if port is in use:
   ```bash
   netstat -tulpn | grep 5020
   ```

### Can't Access Web UI

1. Verify container is running:
   ```bash
   docker ps | grep adb-device-manager
   ```

2. Check health:
   ```bash
   curl http://localhost:5020/api/health
   ```

3. Verify network mode:
   ```bash
   docker inspect adb-device-manager | grep NetworkMode
   ```

### USB Devices Not Detected

1. Ensure privileged mode is enabled (already set in compose file)
2. Verify USB device access:
   ```bash
   docker exec -it adb-device-manager ls -la /dev/bus/usb
   ```

3. Test ADB inside container:
   ```bash
   docker exec -it adb-device-manager adb devices
   ```

## 🔐 Security Notes

- Container runs in **privileged mode** for USB/ADB access
- Uses **host network** for direct device communication
- All data persists in mounted volumes
- Logs are rotated automatically

## 📝 Pre-configured Features

✅ **Auto-restart** - Container restarts automatically  
✅ **Health checks** - Built-in monitoring  
✅ **Host network** - Direct network device access  
✅ **USB passthrough** - Full ADB functionality  
✅ **Persistent storage** - Data survives restarts  
✅ **Unraid labels** - Proper Unraid integration

## 💡 Unraid-Specific Tips

### Add WebUI to Unraid Dashboard
The compose file includes Unraid labels:
- WebUI will appear in Docker tab
- Auto-detected URL: `http://[IP]:[PORT:5020]`

### Backup Configuration
Backup this directory:
```bash
/mnt/user/appdata/adb-device-manager/
```

### Auto-update Setup
Consider using:
- Unraid's Docker Auto Update plugin
- Watchtower container
- Manual updates via `docker compose pull`

## 🎯 Differences from Local Build

| Feature | Local Build | GitHub Image |
|---------|-------------|--------------|
| **Build time** | ~5 minutes | Instant |
| **Updates** | Manual rebuild | `docker compose pull` |
| **Image source** | Local Dockerfile | ghcr.io/craigst/andriod-connect |
| **Storage** | Local image cache | Pulled from registry |
| **Version control** | Git commits | Image tags |

## 🔗 Image Information

- **Registry:** GitHub Container Registry (ghcr.io)
- **Repository:** craigst/andriod-connect
- **Image URL:** ghcr.io/craigst/andriod-connect:latest
- **Source:** https://github.com/craigst/Andriod-connect

## ✅ Verification Checklist

After deployment, verify:

- [ ] Container is running: `docker ps`
- [ ] Health check passes: `curl http://localhost:5020/api/health`
- [ ] Web UI accessible: http://[UNRAID-IP]:5020
- [ ] Logs are writing: `ls -la /mnt/user/appdata/adb-device-manager/logs/`
- [ ] Data directory exists: `ls -la /mnt/user/appdata/adb-device-manager/data/`
- [ ] USB devices visible: `docker exec -it adb-device-manager adb devices`

## 📚 Additional Resources

- Main README: `/mnt/user/appdata/adb-device-manager/README.md`
- API Documentation: See project GitHub repository
- Unraid Forums: https://forums.unraid.net/

---

**All systems ready! 🚀**
