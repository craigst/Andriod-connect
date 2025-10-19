# Home Assistant Addon Installation Guide

## Quick Start

Your ADB Device Manager has been converted to a Home Assistant addon and is ready to use!

## Addon Structure

```
ha-addon/
├── config.yaml           ✅ Addon configuration with Ingress enabled
├── Dockerfile            ✅ Home Assistant compatible Docker build
├── build.yaml           ✅ Multi-architecture support (amd64, aarch64, armv7)
├── README.md            ✅ Comprehensive documentation
├── CHANGELOG.md         ✅ Version history
└── rootfs/              ✅ Root filesystem overlay
    └── app/             
        ├── adb_manager.py
        ├── server.py
        ├── credentials_manager.py
        ├── screen_detector.py
        ├── screen_macros.py
        ├── init_screen_control_db.py
        ├── requirements.txt
        ├── templates/
        ├── scripts/
        ├── signature/
        └── screen_templates/
```

## Installation Methods

### Method 1: Local Installation (Testing)

1. **Copy addon to Home Assistant:**
   ```bash
   # If running Home Assistant OS/Supervised
   scp -r ha-addon/ root@your-ha-ip:/addons/adb_device_manager/
   
   # Or using Samba/SMB share
   # Copy ha-addon folder to \\YOUR-HA-IP\addons\adb_device_manager\
   ```

2. **Reload addons:**
   - Go to **Settings** → **Add-ons** → **⋮** (menu) → **Reload**
   - The addon should appear under "Local add-ons"

3. **Install and configure:**
   - Click the addon
   - Click **Install**
   - Go to **Configuration** tab
   - Adjust device settings as needed
   - Click **Start**

4. **Access the interface:**
   - Click **OPEN WEB UI** button
   - Or find "ADB Manager" tab in your Home Assistant sidebar

### Method 2: GitHub Repository (Production)

1. **Create a GitHub repository:**
   ```bash
   cd ha-addon
   git init
   git add .
   git commit -m "Initial commit: ADB Device Manager v1.0.0"
   git remote add origin https://github.com/YOUR-USERNAME/ha-adb-manager.git
   git push -u origin main
   ```

2. **Add repository to Home Assistant:**
   - Go to **Settings** → **Add-ons** → **Add-on Store**
   - Click **⋮** (three dots) → **Repositories**
   - Add: `https://github.com/YOUR-USERNAME/ha-adb-manager`
   - Click **Add**

3. **Install the addon:**
   - Find "ADB Device Manager" in the add-on store
   - Click **Install**
   - Configure and start

## Configuration

After installation, configure your devices in the addon configuration:

```yaml
devices:
  - ip: "10.10.254.62"
    port: "5555"
    name: "Device 1"
  - ip: "10.10.254.13"
    port: "5555"
    name: "Device 2"
app_package: "com.bca.bcatrack"
auto_refresh_enabled: false
auto_refresh_interval_minutes: 10
log_level: "info"
```

## Important Notes

### APK File Placement

If you want to install apps on devices, place your APK file at:
- **Path:** `/addon_configs/adb_device_manager/apk/BCAApp.apk`
- Or use the Samba share: `\\YOUR-HA-IP\addon_configs\adb_device_manager\apk\`

### Data Persistence

All data is stored in `/data` within the addon:
- Databases: `/data/sql.db`
- Logs: `/data/logs/`
- Screenshots: `/data/screenshots/`
- Paperwork: `/data/paperwork/`

This data persists across addon restarts and updates.

### Network Requirements

The addon uses **host networking mode** to access ADB devices on your network. Ensure:
- Android devices have ADB over network enabled
- Devices are on the same network as Home Assistant
- Firewall allows ADB connections (port 5555)

### Ingress Features

With Ingress enabled:
- ✅ No need to expose port 5020 externally
- ✅ Automatic SSL/TLS encryption
- ✅ Home Assistant authentication
- ✅ Sidebar tab integration
- ✅ Works with reverse proxies (Nginx, Caddy, etc.)

## Troubleshooting

### Addon won't start

Check logs:
```bash
# Home Assistant logs
ha addons logs adb_device_manager

# Or via UI: Settings → System → Logs → ADB Device Manager
```

### Can't connect to devices

1. Check device IP addresses are correct
2. Verify ADB debugging is enabled on devices
3. Test connection manually:
   ```bash
   # Enter addon container
   docker exec -it addon_adb_device_manager /bin/sh
   
   # Test ADB connection
   adb connect 10.10.254.62:5555
   adb devices
   ```

### Ingress not working

1. Ensure `ingress: true` in `config.yaml`
2. Restart the addon
3. Clear browser cache
4. Check Home Assistant logs for Ingress errors

## Updating the Addon

### Local Installation
1. Update files in `/addons/adb_device_manager/`
2. Increment version in `config.yaml`
3. Reload addons in HA
4. Click **Update** on the addon

### GitHub Installation
1. Update version in `config.yaml` and `CHANGELOG.md`
2. Commit and push changes
3. Tag release: `git tag v1.0.1 && git push --tags`
4. Update available in HA add-on store

## Features Enabled

✅ **Ingress Panel** - Access via sidebar tab  
✅ **Host Network** - Direct ADB device access  
✅ **Multi-arch** - Works on x86, ARM32, ARM64  
✅ **Persistent Storage** - Data survives restarts  
✅ **Auto-start** - Starts with Home Assistant  
✅ **Web UI** - Full-featured interface  
✅ **REST API** - Automation ready  

## Next Steps

1. **Test locally** - Install and test on your HA instance
2. **Upload APK** - Place your app's APK in the data folder
3. **Configure devices** - Add your Android device IPs
4. **Test connections** - Connect to devices and verify status
5. **Set up automation** - Use the REST API in HA automations
6. **Create repository** - Publish to GitHub for easy updates

## Support

For issues or questions:
- Check addon logs
- Review README.md for detailed documentation
- Check Home Assistant community forums

---

**Your ADB Manager is now a fully-integrated Home Assistant addon!** 🎉
