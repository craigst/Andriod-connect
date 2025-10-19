# Screen Control System Implementation

## Overview
A comprehensive screen detection and automation system has been implemented for the Android Connect project, integrating OpenCV-based template matching with macro automation capabilities.

## Components Created

### 1. Database Schema (`init_screen_control_db.py`)
- **credentials**: Stores encrypted device login credentials
- **screen_templates**: Stores template image definitions with confidence thresholds and priorities
- **macros**: Stores macro definitions (sequences of automated actions)
- **template_macro_links**: Links templates to macros for auto-execution

**Usage:**
```bash
python3 init_screen_control_db.py
```

### 2. Credentials Manager (`credentials_manager.py`)
- Fernet symmetric encryption for password storage
- Functions: `store_credentials()`, `get_credentials()`, `delete_credentials()`
- Encryption key stored securely at `data/.screen_control_key`

### 3. Screen Detector (`screen_detector.py`)
- OpenCV template matching with configurable confidence thresholds
- Captures screenshots from Android devices via ADB
- Detects current screen by matching against template database
- Priority-based matching (highest priority checked first)
- Returns detected screen with confidence scores

### 4. Screen Macros (`screen_macros.py`)
- Executes automated action sequences on Android devices
- **Supported Actions:**
  - `tap`: Tap at coordinates (x, y)
  - `swipe`: Swipe from (x1, y1) to (x2, y2)
  - `text`: Type text input
  - `keyevent`: Send key event codes
  - `long_press`: Long press at coordinates
  - `back`: Back button
  - `home`: Home button
  - `wait`: Wait for seconds

### 5. API Endpoints (added to `server.py`)

#### Screenshot Management
- `GET /api/devices/<address>/screenshot` - Capture screenshot
- `GET /api/devices/<address>/current-screen` - Detect current screen

#### Credentials Management
- `GET /api/devices/<address>/credentials` - Get credentials (masked)
- `POST /api/devices/<address>/credentials` - Save credentials
- `DELETE /api/devices/<address>/credentials` - Delete credentials

#### Template Management
- `GET /api/templates` - List all templates
- `POST /api/templates/<id>/test` - Test template matching

#### Macro Management
- `GET /api/macros` - List all macros
- `POST /api/macros` - Create macro
- `GET /api/macros/<id>` - Get specific macro
- `PUT /api/macros/<id>` - Update macro
- `DELETE /api/macros/<id>` - Delete macro
- `POST /api/macros/<id>/execute` - Execute macro on device

#### Template-Macro Links
- `POST /api/templates/<tid>/link-macro/<mid>` - Link template to macro
- `DELETE /api/templates/<tid>/link-macro/<mid>` - Unlink template from macro

#### Auto-Login
- `POST /api/devices/<address>/auto-login` - Execute auto-login with stored credentials

## Pre-loaded Templates
8 templates copied from v5 system:
1. `login` - Login screen (priority: 5)
2. `bionag` - Bio nag popup (priority: 8)
3. `noload` - No load screen (priority: 10 - highest)
4. `firstloadnag` - First load nag (priority: 7)
5. `nagload2` - Load nag 2 (priority: 6)
6. `nagload3` - Load nag 3 (priority: 6)
7. `loadlist` - Load list screen (priority: 3)
8. `cartoload` - Cart to load screen (priority: 4)

## Dependencies Added
```
opencv-python==4.8.1.78
numpy>=1.24.0
cryptography>=41.0.0
```

## Docker Support
Dockerfile updated with:
- OpenCV system dependencies (`libgl1-mesa-glx`, `libglib2.0-0`)
- New Python modules copied to container
- Screenshot directory created

## Directory Structure
```
project/
├── credentials_manager.py       (NEW)
├── screen_detector.py           (NEW)
├── screen_macros.py             (NEW)
├── init_screen_control_db.py    (NEW)
├── screen_templates/            (8 template images)
├── screenshots/                 (device screenshots)
│   └── <device_address>/
├── data/
│   ├── screen_control.db        (NEW database)
│   └── .screen_control_key      (Encryption key)
```

## Example Usage

### 1. Store Device Credentials
```python
from credentials_manager import store_credentials

store_credentials("10.10.254.13:5555", "username", "password123")
```

### 2. Capture and Detect Screen
```python
from screen_detector import capture_screenshot, detect_current_screen

screenshot = capture_screenshot("10.10.254.13:5555")
result = detect_current_screen(screenshot)
print(f"Detected: {result['screen']} ({result['confidence']:.2%})")
```

### 3. Create and Execute Macro
```python
from screen_macros import save_macro, execute_macro

actions = [
    {"type": "tap", "x": 500, "y": 500},
    {"type": "wait", "seconds": 1},
    {"type": "text", "value": "Hello"}
]

save_macro("test_macro", "A test macro", actions)
result = execute_macro("10.10.254.13:5555", actions)
```

### 4. Auto-Login via API
```bash
# Store credentials
curl -X POST http://localhost:5020/api/devices/10.10.254.13:5555/credentials \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Execute auto-login
curl -X POST http://localhost:5020/api/devices/10.10.254.13:5555/auto-login
```

## Web UI Integration (Next Step)
A new "Screen Control" tab needs to be added to `templates/index.html` with:

1. **Live Screenshot Viewer**
   - Auto-refresh every 5 seconds
   - Display detected screen with confidence
   
2. **Quick Actions Panel**
   - Auto Login button
   - Capture Screenshot button
   - Manual macro triggers
   
3. **Template Management**
   - Upload/manage templates
   - Test template matching
   - Adjust confidence thresholds
   
4. **Macro Builder**
   - Visual macro editor
   - Action type dropdown
   - Test macro execution
   
5. **Credentials Management**
   - Save/edit device credentials
   - Delete credentials

## Testing Checklist

### Backend Tests
- [ ] Initialize database: `python3 init_screen_control_db.py`
- [ ] Test credentials: `python3 credentials_manager.py`
- [ ] Test screen detector: `python3 screen_detector.py`
- [ ] Test macros: `python3 screen_macros.py`
- [ ] Start server: `python3 server.py`

### API Tests
- [ ] Test screenshot capture
- [ ] Test screen detection
- [ ] Test credential storage
- [ ] Test macro creation
- [ ] Test macro execution
- [ ] Test auto-login

### Integration Tests
- [ ] Connect to Android device via ADB
- [ ] Capture screenshot from device
- [ ] Detect login screen
- [ ] Execute auto-login macro
- [ ] Verify template-macro linking

## Security Notes
- Passwords encrypted using Fernet (symmetric encryption)
- Encryption key stored with 600 permissions
- API endpoints do not expose passwords in responses
- Screenshot storage organized by device address

## Future Enhancements
- [ ] Multi-scale template matching
- [ ] Template image upload via web UI
- [ ] Macro recording feature
- [ ] Screen monitoring with auto-trigger
- [ ] Macro execution history/logs
- [ ] Template confidence tuning interface
