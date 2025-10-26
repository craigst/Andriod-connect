# Android Connect - Vision Automation Improvements
## Task Checklist & Implementation Plan

**Testing Approach:** Local Python environment for fast iteration, Docker build/test in TASK 10
**Progress Tracking:** Mark [x] when completed

---

## ✅ TASK 1: Database Schema Updates (15 min)
**Status:** [x] COMPLETED
**File:** `init_screen_control_db.py`
**Testing:** Run locally with `python3 init_screen_control_db.py`

### Subtasks:
- [x] Add `device_settings` table
  - `id` INTEGER PRIMARY KEY
  - `device_address` TEXT UNIQUE
  - `match_threshold` REAL DEFAULT 0.7
  - `keystroke_delay_ms` INTEGER DEFAULT 150
  - `post_login_wait_seconds` INTEGER DEFAULT 4
  - `created_at` TIMESTAMP
  - `updated_at` TIMESTAMP

- [x] Add `load_date_overrides` table
  - `id` INTEGER PRIMARY KEY
  - `load_number` TEXT
  - `override_date` TEXT (YYYY-MM-DD format)
  - `original_date` TEXT (for reference)
  - `created_at` TIMESTAMP
  - UNIQUE constraint on load_number
  - Auto-cleanup records older than 14 days

- [x] Add `load_notes` table
  - `id` INTEGER PRIMARY KEY
  - `load_number` TEXT UNIQUE
  - `note_text` TEXT
  - `created_at` TIMESTAMP
  - `updated_at` TIMESTAMP

### Test Commands:
```bash
python3 init_screen_control_db.py
sqlite3 data/screen_control.db ".schema device_settings"
sqlite3 data/screen_control.db ".schema load_date_overrides"
sqlite3 data/screen_control.db ".schema load_notes"
```

---

## ✅ TASK 2: Screen Detection Improvements (30 min)
**Status:** [x] COMPLETED
**File:** `screen_detector.py`
**Testing:** Test with Pixel XL screenshots

### Subtasks:
- [x] Add `get_device_resolution()` function using ADB
- [x] Add multi-scale template matching
  - Try scales: [0.8, 0.9, 1.0, 1.1, 1.2]
  - Return best match across all scales
- [x] Update `match_template()` to accept threshold parameter
- [x] Add `match_template_multiscale()` function
- [x] Update `detect_current_screen()` to use configurable threshold
- [x] Add coordinate normalization based on resolution

### Test Commands:
```bash
# Capture test screenshot from Pixel XL
adb -s <device> shell screencap -p > test_pixel_xl.png
# Test detection
python3 -c "from screen_detector import detect_current_screen; print(detect_current_screen('test_pixel_xl.png'))"
```

---

## ✅ TASK 3: Text Input Speed Fix (15 min)
**Status:** [x] COMPLETED
**File:** `screen_macros.py`
**Testing:** Test typing on device

### Subtasks:
- [x] Update `execute_text()` function:
  - Add `delay_ms` parameter (default 150ms)
  - Type character-by-character with delays
  - Handle special characters properly
- [x] Add retry logic for failed text input
- [x] Update `execute_action()` to pass device settings

### Test Commands:
```bash
# Test with device
python3 -c "from screen_macros import execute_text; execute_text('10.10.254.62:5555', 'TestUsername123', 150)"
```

---

## ✅ TASK 4: Phone Control - Slave Device Mode (30 min)
**Status:** [x] COMPLETED
**Files:** `adb_manager.py`, `server.py`
**Testing:** Test on Pixel XL

### Subtasks:
- [x] Add ADB commands to `adb_manager.py`:
  - `enable_slave_mode()`: Disable timeout, set wakelock, allow screen off
  - `disable_slave_mode()`: Restore normal settings
  - `get_slave_mode_status()`: Check current state
- [x] Add to `ADBDevice` class:
  - `slave_mode` boolean property
  - Methods to enable/disable slave mode
- [x] Add API endpoints in `server.py`:
  - `POST /api/devices/<address>/slave-mode` - Enable
  - `DELETE /api/devices/<address>/slave-mode` - Disable
  - `GET /api/devices/<address>/slave-mode` - Get status
- [x] Store slave mode state in device refresh

### ADB Commands:
```bash
# Enable slave mode
adb shell settings put system screen_off_timeout 2147483647
adb shell svc power stayon true
adb shell input keyevent 26  # Turn screen off

# Disable slave mode
adb shell settings put system screen_off_timeout 60000
adb shell svc power stayon false
```

### Test Commands:
```bash
curl -X POST http://localhost:5020/api/devices/10.10.254.62:5555/slave-mode
curl http://localhost:5020/api/devices/10.10.254.62:5555/slave-mode
```

---

## ✅ TASK 5: Enhanced Auto-Login (30 min)
**Status:** [ ] Not Started
**File:** `server.py`
**Testing:** Test full login flow on device

### Subtasks:
- [ ] Create `/api/devices/<address>/auto-login-enhanced` endpoint
- [ ] Implement enhanced login flow:
  1. Get device settings (threshold, delays)
  2. Enter username with delays
  3. Enter password with delays
  4. Tap login button
  5. Wait (post_login_wait_seconds)
  6. Capture screenshot
  7. Detect "bionag" screen
  8. If detected, execute dismiss macro
  9. Verify successful login
- [ ] Add retry logic (max 2 retries)
- [ ] Return detailed status of each step

### Test Commands:
```bash
curl -X POST http://localhost:5020/api/devices/10.10.254.62:5555/auto-login-enhanced
```

---

## ✅ TASK 6: Load Date Override System (30 min)
**Status:** [x] COMPLETED (Backend only - UI pending)
**Files:** `server.py`, `templates/index.html`, `scripts/loadsheet.py`
**Testing:** Test date override in UI and loadsheet generation

### Subtasks:
- [x] Add API endpoints in `server.py`:
  - `GET /api/loads/<load_number>/date-override` - Get override
  - `POST /api/loads/<load_number>/date-override` - Save override
  - `DELETE /api/loads/<load_number>/date-override` - Delete override
- [x] Add cleanup function for old overrides (>14 days)
- [ ] Update `generate_loadsheet()` to apply date overrides
- [ ] Update `scripts/loadsheet.py` to use override dates
- [ ] Add UI in `templates/index.html`:
  - "Change Date" button after "Download PDF"
  - Modal dialog with date picker
  - Show current override if exists

### Test Commands:
```bash
curl -X POST http://localhost:5020/api/loads/\$S275052/date-override -H "Content-Type: application/json" -d '{"override_date":"2025-01-15"}'
curl http://localhost:5020/api/loads/\$S275052/date-override
```

---

## ✅ TASK 7: Load Notes System (20 min)
**Status:** [x] COMPLETED (Backend only - UI pending)
**Files:** `server.py`, `templates/index.html`, `scripts/loadsheet.py`
**Testing:** Test notes in UI and loadsheet generation

### Subtasks:
- [x] Add API endpoints in `server.py`:
  - `GET /api/loads/<load_number>/note` - Get note
  - `POST /api/loads/<load_number>/note` - Save note
  - `DELETE /api/loads/<load_number>/note` - Delete note
- [ ] Update `generate_loadsheet()` to include notes
- [ ] Update `scripts/loadsheet.py` to add notes after keys/docs section
- [ ] Add UI in `templates/index.html`:
  - "LOAD NOTE" button after "Change Date"
  - Modal dialog with textarea
  - Show existing note if present

### Test Commands:
```bash
curl -X POST http://localhost:5020/api/loads/\$S275052/note -H "Content-Type: application/json" -d '{"note":"Extra care needed - fragile vehicles"}'
curl http://localhost:5020/api/loads/\$S275052/note
```

---

## ✅ TASK 8: Timesheet Days Worked Code (15 min)
**Status:** [x] COMPLETED
**File:** `scripts/timesheet.py`
**Testing:** Generate timesheet and check filename

### Subtasks:
- [x] Add function `count_days_worked(loads)`:
  - Count unique dates from load data
  - Return integer count
- [x] Update filename generation:
  - Add `_D{count}` before `.xlsx`
  - Example: `timesheet_2025-01-07_D4.xlsx`
- [x] Ensure PDF filename also includes days worked code

### Test Commands:
```bash
# Generate timesheet and check filename
ls -la paperwork/*/timesheet_*_D*.xlsx
```

---

## ✅ TASK 9: Vision Tab UI Enhancements (20 min)
**Status:** [ ] Not Started
**File:** `templates/index.html`
**Testing:** Test UI elements in browser

### Subtasks:
- [ ] Add device settings section in Vision tab:
  - Match threshold slider (60-95%, default 70%)
  - Keystroke delay input (50-500ms, default 150ms)
  - Post-login wait input (2-10s, default 4s)
- [ ] Add "Test Template Match" button
  - Shows confidence scores in real-time
  - Highlights best match
- [ ] Add device resolution display
- [ ] Add confidence score overlay on screenshots
- [ ] Save settings to device_settings table via API
- [ ] Load settings when device is selected

### Subtasks for API:
- [ ] Add `GET /api/devices/<address>/settings` endpoint
- [ ] Add `POST /api/devices/<address>/settings` endpoint

---

## ✅ TASK 10: Testing & Docker Rebuild (30 min)
**Status:** [ ] Not Started
**Files:** All files
**Testing:** Complete end-to-end testing

### Subtasks:
- [ ] Run full test suite locally:
  - Start server: `python3 server.py`
  - Test all new endpoints
  - Test UI buttons exist and work
  - Test on Pixel XL device
- [ ] Clean up test files and logs
- [ ] Update Dockerfile if needed
- [ ] Rebuild Docker image:
  ```bash
  cd compose
  podman build -t android-connect:latest -f Dockerfile ..
  ```
- [ ] Test in Podman container:
  ```bash
  podman run -d -p 5020:5020 -v ./data:/app/data android-connect:latest
  ```
- [ ] Verify all features work in container
- [ ] Test phone control (slave mode)
- [ ] Test enhanced auto-login
- [ ] Test date overrides and notes in loadsheets
- [ ] Test timesheet with days worked code
- [ ] Verify Pixel XL screen detection works

### Final Checklist:
- [ ] All UI buttons exist and are visible
- [ ] Slave mode toggle works (screen off, device controlled)
- [ ] Enhanced auto-login handles bionag screen
- [ ] Date overrides apply to loadsheets
- [ ] Load notes appear in loadsheets
- [ ] Timesheet filenames include D# code
- [ ] Multi-resolution screen detection works
- [ ] Text input doesn't mix character order
- [ ] Docker container builds successfully
- [ ] All features work in Podman

---

## Notes & Implementation Details

### Device Settings Structure:
```python
{
    'match_threshold': 0.7,  # 70%
    'keystroke_delay_ms': 150,
    'post_login_wait_seconds': 4
}
```

### ADB Commands Reference:
```bash
# Get screen resolution
adb shell wm size

# Keep device awake
adb shell svc power stayon true

# Disable screen timeout
adb shell settings put system screen_off_timeout 2147483647

# Turn screen off (while keeping device awake)
adb shell input keyevent 26
```

### Database Schema Quick Reference:
- `device_settings` - Per-device automation settings
- `load_date_overrides` - Override load dates (auto-cleanup after 14 days)
- `load_notes` - Custom notes for loads
- `credentials` - Encrypted login credentials (existing)
- `vehicle_overrides` - Vehicle make/model overrides (existing)

---

## Completion Tracking
- Total Tasks: 10
- Completed: 7 (Backend complete, UI & testing pending)
- Remaining: 3 (1 deferred, 2 active)
- Estimated Total Time: ~4 hours
- Started: 2025-10-26 12:05 PM
- Completed: TBD
