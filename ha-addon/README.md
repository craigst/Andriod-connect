# ADB Device Manager - Home Assistant Addon

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armv7 Architecture][armv7-shield]

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg

Manage Android devices via ADB (Android Debug Bridge) with a web interface, screen automation, and paperwork generation - all from within Home Assistant!

## About

This addon provides a comprehensive solution for managing Android devices on your network using ADB. It includes:

- 🔌 **Device Management** - Connect to and manage multiple Android devices over WiFi
- 📱 **App Control** - Install, uninstall, start, and stop apps remotely
- 📥 **SQL Database Sync** - Pull SQLite databases from device apps
- 📊 **Paperwork Generation** - Generate loadsheets and timesheets from synced data
- 🖼️ **Screen Detection** - Automated screen recognition using OpenCV
- 🤖 **Macro Automation** - Create and execute automated actions on devices
- 🔐 **Credential Management** - Secure storage of device credentials
- 🌐 **Web Interface** - Full-featured web UI accessible via Home Assistant Ingress

## Features

### Device Management
- Connect to multiple Android devices via TCP/IP
- Real-time status monitoring (online/offline, app installed/running)
- One-click connection to all configured devices
- Add/remove devices dynamically

### App Management
- Install/reinstall APK files on devices
- Start and stop apps remotely
- Uninstall apps with a single click
- Check app installation and running status

### Database Management
- Pull SQLite databases from app data directories
- Automatic database updates on schedule
- Support for rooted devices
- Database query and analysis tools

### Screen Automation
- Capture screenshots from devices
- Automatic screen detection using template matching
- Create macros for automated interactions
- Auto-login functionality
- Link macros to specific screens for context-aware automation

### Paperwork Generation
- Generate Excel loadsheets from database data
- Create timesheets for date ranges
- Automatic PDF conversion
- Organized storage by date

## Installation

### Prerequisites

1. **Android Devices** must have:
   - ADB debugging enabled
   - Network ADB enabled (wireless debugging)
   - For advanced features: root access

2. **Home Assistant** requirements:
   - Home Assistant OS, Supervised, or Container
   - Network access to Android devices

### Steps

1. Add this repository to Home Assistant:
   - Go to **Supervisor** → **Add-on Store** → **⋮** (three dots) → **Repositories**
   - Add: `https://github.com/yourusername/adb-device-manager`

2. Find "ADB Device Manager" in the add-on store and click **Install**

3. Configure the addon (see Configuration section below)

4. Start the addon

5. Access the web interface:
   - Click "OPEN WEB UI" button
   - Or find "ADB Manager" in your Home Assistant sidebar

## Configuration

### Basic Configuration

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

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `devices` | List of Android devices to manage | See example |
| `devices[].ip` | IP address of the device | Required |
| `devices[].port` | ADB port (usually 5555) | Required |
| `devices[].name` | Friendly name for the device | Required |
| `app_package` | Package name of the app to manage | `com.bca.bcatrack` |
| `auto_refresh_enabled` | Enable automatic database refresh | `false` |
| `auto_refresh_interval_minutes` | Minutes between auto-refreshes | `10` |
| `log_level` | Logging level (debug/info/warning/error) | `info` |

## Usage

### Connecting to Devices

1. Open the ADB Manager web interface from the sidebar
2. Click "Connect All Devices"
3. View device status in the dashboard

### Managing Apps

1. Select a device from the device list
2. Use the action buttons to:
   - **Start App** - Launch the managed app
   - **Stop App** - Force stop the app
   - **Reinstall** - Reinstall the app (clears data)

### Pulling Database

1. Click "Pull SQL Database" for any connected device
2. Database will be downloaded to `/data/sql.db`
3. Use the "View Loads" tab to see database contents

### Creating Macros

1. Go to the "Macros" section
2. Click "Create New Macro"
3. Define actions (tap, swipe, text input, wait)
4. Link macro to screen templates for automatic execution

### Auto-Login

1. Save device credentials in the Credentials section
2. Click "Auto-Login" on the device
3. The addon will automatically fill in username/password and login

## API Endpoints

The addon exposes a REST API for automation:

- `GET /api/devices` - List all devices
- `POST /api/devices/connect` - Connect to all devices
- `POST /api/devices/{address}/start` - Start app on device
- `POST /api/devices/{address}/stop` - Stop app on device
- `POST /api/sql/pull` - Pull SQL database
- `GET /api/loads` - Get load overview
- `POST /api/macros/{id}/execute` - Execute a macro

Full API documentation available in the web interface.

## Data Storage

All persistent data is stored in `/data`:

- `/data/sql.db` - Synced database file
- `/data/logs/` - Application logs
- `/data/apk/` - APK files for installation
- `/data/screenshots/` - Device screenshots
- `/data/paperwork/` - Generated documents
- `/data/screen_control.db` - Screen templates and macros

## Troubleshooting

### Devices Won't Connect

- Ensure ADB debugging is enabled on the device
- Check network connectivity between Home Assistant and devices
- Verify the correct IP address and port
- Try connecting manually: `adb connect IP:PORT`

### App Installation Fails

- Check that APK file exists in `/data/apk/BCAApp.apk`
- Verify sufficient storage on the device
- Ensure "Install from unknown sources" is enabled

### Database Pull Fails

- Device must be rooted for database access
- App must be stopped before pulling database
- Check ADB root permissions

### Ingress Not Working

- Ensure `ingress: true` in config.yaml
- Restart the addon after configuration changes
- Check Home Assistant logs for Ingress errors

## Support

For issues, feature requests, or questions:
- GitHub Issues: https://github.com/yourusername/adb-device-manager/issues
- Home Assistant Community: https://community.home-assistant.io/

## License

MIT License - see LICENSE file for details

## Credits

Built with:
- Python & Flask
- OpenCV for screen detection
- ADB (Android Debug Bridge)
- Home Assistant Addon Framework
