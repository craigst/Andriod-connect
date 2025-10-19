# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-01-07

### Added
- Initial release of ADB Device Manager Home Assistant Addon
- Device management for multiple Android devices via ADB over network
- Web-based interface with Home Assistant Ingress support
- Sidebar panel integration with custom icon
- App management (install, uninstall, start, stop)
- SQL database synchronization from device apps
- Screen detection using OpenCV template matching
- Macro automation system for device interactions
- Auto-login functionality with credential management
- Paperwork generation (loadsheets and timesheets)
- REST API for automation and integration
- Auto-refresh capability for scheduled database updates
- Multi-architecture support (amd64, aarch64, armv7)
- Persistent data storage in /data directory
- Comprehensive logging with rotation
- Screenshot capture from devices
- Template-based screen recognition
- Macro execution with multiple action types (tap, swipe, text, wait)

### Features
- 🔌 Multi-device ADB connection management
- 📱 Remote app control
- 📥 Database sync from rooted devices
- 📊 Excel document generation
- 🖼️ Automated screen detection
- 🤖 Macro automation system
- 🔐 Encrypted credential storage
- 🌐 Full-featured web UI via Ingress
- 📡 REST API for Home Assistant automation
- 🔄 Automatic database refresh scheduling

### Configuration Options
- Device list management
- App package configuration
- Auto-refresh settings
- Log level control

### Supported Architectures
- AMD64 (x86_64)
- AARCH64 (ARM 64-bit)
- ARMV7 (ARM 32-bit)

[1.0.0]: https://github.com/yourusername/adb-device-manager/releases/tag/v1.0.0
