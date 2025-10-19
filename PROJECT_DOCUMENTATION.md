# Android Connect - Complete Project Documentation

## Project Overview

**Android Connect** is a Flask-based web application that manages Android ADB devices for automated data extraction, paperwork generation, and device automation. The system interfaces with BCA Auto (British Car Auctions) application running on Android tablets to:

1. Extract job/load data from SQLite databases
2. Generate professional loadsheets and timesheets
3. Automate device interactions via screen detection and macros
4. Manage vehicle lookup and override data
5. Provide REST API for web-based management

## System Architecture

### Core Components

```
/app
├── server.py                    # Main Flask web server (Port 5020)
├── adb_manager.py              # ADB device management
├── credentials_manager.py      # Device login credentials storage
├── screen_detector.py          # Screen template matching
├── screen_macros.py            # Macro automation system
├── vehicle_lookup.py           # Vehicle registration lookup
├── init_screen_control_db.py  # Database initialization
├── /scripts
│   ├── loadsheet.py           # Loadsheet generation script
│   └── timesheet.py           # Timesheet generation script
├── /templates                  # Flask HTML templates
├── /static                     # Static web assets
├── /data                       # Database storage
│   ├── sql.db                 # Main job/vehicle data (from devices)
│   └── screen_control.db      # App configuration and timesheet entries
├── /logs                       # Application logs
├── /paperwork                  # Generated documents (organized by week)
├── /signature                  # Signature images (sig1/, sig2/)
└── /screen_templates           # Screen template images for detection
```

## Database Schemas

### 1. sql.db (Main Data - Pulled from Android Devices)

**DWJJOB Table** - Job/Load Information
```sql
Fields:
- dwjkey: TEXT (Primary key)
- dwjDriver: TEXT (Driver code)
- dwjDate: INTEGER (Format: YYYYMMDD)
- dwjTime: INTEGER (Format: HHMM)
- dwjSeq: INTEGER (Sequence number)
- dwjRec: INTEGER (Record number)
- dwjLoad: TEXT (Load number, e.g., "$S295198", "M9295527")
- dwjType: TEXT (Job type: "C"=Collection, "D"=Delivery, "S"=Handover/Shunt, "B"=Pre-book)
- dwjCust: TEXT (Customer code)
- dwjAdrCod: TEXT (Address code)
- dwjVehs: INTEGER (Number of vehicles)
- dwjExpD: INTEGER (Expected date)
- dwjExpT: INTEGER (Expected time)
- dwjName: TEXT (Location name)
- dwjAdd1-4: TEXT (Address lines)
- dwjTown: TEXT (Town/city)
- dwjPostco: TEXT (Postcode)
- dwjLat: DECIMAL(9,6) (Latitude)
- dwjLong: DECIMAL(9,6) (Longitude)
- dwjPhoneN: CHAR (Phone number)
- dwjInfTxt: TEXT (Information text)
- dwjInfTyp: TEXT (Information type)
- dwjDeck: TEXT (Deck information)
- dwjSeqOld: INTEGER
- dwjColTyp: TEXT (Collection type)
- dwjCompPh: TEXT
- dwjCompVi: TEXT
- dwjStatus: INTEGER (Status code)
- dwjComInd: TEXT
- dwjRadius: INTEGER
- std_int: INTEGER
- dwjOthVeh: TEXT
- dwjForm: TEXT
- dwjsign: TEXT
- dwjclamrq: INTEGER
- dwjferry: TEXT
- dwjMulEdt: TEXT
- dwjcantad: TEXT
- dwjdrvsgn: TEXT
```

**DWVVEH Table** - Vehicle Information
```sql
Fields:
- dwvkey: TEXT (Primary key)
- dwvLoad: TEXT (Load number - links to DWJJOB.dwjLoad)
- dwvVehRef: TEXT (Vehicle registration)
- dwvModDes: TEXT (Make/model description)
- dwvColDes: TEXT (Color description)
- dwvStatus: TEXT (Vehicle status)
- dwvPos: INTEGER (Position in load)
- dwvColCus: TEXT (Collection customer)
- dwvColCod: TEXT (Collection address code)
- dwvDelCus: TEXT (Delivery customer)
- dwvDelCod: TEXT (Delivery address code)
- offload: TEXT ("Y"/"N" - if vehicle was offloaded)
- docs: TEXT ("Y"/"N" - if documents included)
- sparekeys: TEXT ("Y"/"N" - if spare keys included)
- car_notes: TEXT (Additional notes)
```

**DW5TRK Table** - Fleet Vehicle Registration
```sql
Fields:
- dw5Reg: CHAR(10) (Vehicle registration)
- dw5Desc: CHAR(30) (Description)
- dw5Trlr: CHAR(10) (Trailer)
```

### 2. screen_control.db (Application Database)

**timesheet_entries Table** - Weekly Work Hours
```sql
CREATE TABLE timesheet_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_ending_date TEXT NOT NULL,          -- Format: "YYYY-MM-DD" (Sunday)
    day_name TEXT NOT NULL,                  -- "Monday", "Tuesday", etc.
    entry_date TEXT,                         -- Format: "DD/MM/YY"
    start_time TEXT,                         -- Format: "HH:MM" or "SICK"
    finish_time TEXT,                        -- Format: "HH:MM" or "SICK"
    total_hours TEXT,                        -- Numeric hours or "0" for sick
    driver TEXT,                             -- Driver name
    fleet_reg TEXT,                          -- Fleet vehicle registration
    start_mileage TEXT,                      -- Starting mileage
    end_mileage TEXT,                        -- Ending mileage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_ending_date, day_name)
);
```

**credentials Table** - Device Login Credentials
```sql
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_address TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**screen_templates Table** - Screen Detection Templates
```sql
CREATE TABLE screen_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    image_path TEXT NOT NULL,
    threshold REAL DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**screen_macros Table** - Automation Macros
```sql
CREATE TABLE screen_macros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    actions TEXT NOT NULL,  -- JSON array of actions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**template_macro_links Table** - Template-Macro Associations
```sql
CREATE TABLE template_macro_links (
    template_id INTEGER,
    macro_id INTEGER,
    PRIMARY KEY (template_id, macro_id),
    FOREIGN KEY (template_id) REFERENCES screen_templates(id),
    FOREIGN KEY (macro_id) REFERENCES screen_macros(id)
);
```

**vehicle_overrides Table** - Vehicle Make/Model Overrides
```sql
CREATE TABLE vehicle_overrides (
    registration TEXT PRIMARY KEY,
    make_model TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_date TIMESTAMP
);
```

## Business Logic & Rules

### Load Types

1. **Standard Load**: Has Collection (C) and Delivery (D) jobs
2. **Handover Load**: Has Collection (C) and Shunt/Handover (S) jobs
   - Special Rule: Destination = "BTT YARD FOR HAND OVER"
3. **Multi-Location Load**: Multiple collections or deliveries
   - Vehicle notes include location information

### Vehicle Rules (Loadsheet Generation)

```python
# Default values for vehicle fields:
offloaded = "N"  # Default if null
docs = "Y"       # Default if null, unless offloaded="Y" then "N"
spare_keys = "Y" # Default if null, unless offloaded="Y" then "N"

# If offloaded = "Y":
#   - docs = "N"
#   - spare_keys = "N"
```

### Date Handling

**Week Ending Calculation** (UK work week: Monday-Sunday)
```python
def get_week_end_from_date(load_date: date) -> date:
    """Get Sunday (week end) from any date"""
    days_to_sunday = 6 - load_date.weekday()
    return load_date + timedelta(days=days_to_sunday)
```

**Date Formats**:
- Database: `YYYYMMDD` (integer, e.g., 20251019)
- Display: `DD/MM/YYYY` (e.g., "19/10/2025")
- Excel Cell: `"Monday 19/10/25"` format
- Folder: `DD-MM-YY` (e.g., "19-10-25")

### Paperwork File Organization

```
/paperwork/
  ├── 19-10-25/                    # Week ending Sunday 19 Oct 2025
  │   ├── $S295198_WBAC_SOUTHEND_rigid_only.xlsx
  │   ├── $S295198_WBAC_SOUTHEND_rigid_only.pdf
  │   ├── M9295527_MOTORLINE_HYUNDAI_GATWICK.xlsx
  │   ├── M9295527_MOTORLINE_HYUNDAI_GATWICK.pdf
  │   ├── timesheet_2025-10-19.xlsx
  │   └── timesheet_2025-10-19.pdf
  └── 12-10-25/                    # Week ending Sunday 12 Oct 2025
      └── ...
```

**Filename Format**:
- Loadsheet: `{LOAD_NUMBER}_{COLLECTION_NAME}.xlsx`
- Timesheet: `timesheet_{WEEK_ENDING_DATE}.xlsx`

## Loadsheet Generation

### Template Structure

Excel template: `/app/templates/loadsheet.xlsx`

**Fixed Cells**:
```
C6: Load Date (formatted: "Monday 19/10/25")
G6: Load Number
B9: Collection Point (UPPERCASE: "NAME - POSTCODE")
F9: Delivery Point (UPPERCASE: "NAME - POSTCODE" or "BTT YARD FOR HAND OVER")
C46: Collection Signature Date
H46: Delivery Signature Date
```

**Car Details** (8 slots available):
```
Car 1: make_model=B11, reg=B13, offloaded=E10, docs=G10, spare_keys=I10, notes=C11
Car 2: make_model=B15, reg=B17, offloaded=E14, docs=G14, spare_keys=I14, notes=C15
Car 3: make_model=B19, reg=B21, offloaded=E18, docs=G18, spare_keys=I18, notes=C19
Car 4: make_model=B23, reg=B25, offloaded=E22, docs=G22, spare_keys=I22, notes=C23
Car 5: make_model=B27, reg=B29, offloaded=E26, docs=G26, spare_keys=I26, notes=C27
Car 6: make_model=B31, reg=B33, offloaded=E30, docs=G30, spare_keys=I30, notes=C31
Car 7: make_model=B35, reg=B37, offloaded=E34, docs=G34, spare_keys=I34, notes=C35
Car 8: make_model=B39, reg=B41, offloaded=E38, docs=G38, spare_keys=I38, notes=C39
```

**Load Summary Cell**: C39
Format: "{X} CARS LOADED, {Y} CARS HAVE DOCUMENTS AND HAVE BEEN PLACED ON THE PASSENGER SEAT, {Z} CARS HAVE SPARE KEYS"

**Signatures**:
- Collection: C42 (random from `/app/signature/sig1/`)
- Delivery: H42 (random from `/app/signature/sig2/`)

### Multi-Location Logic

When multiple collection or delivery points exist:
```python
# Add to vehicle notes:
if is_multi_collection:
    location_info.append(f"FROM: {collection_location_name} - {postcode}")

if is_multi_delivery:
    location_info.append(f"TO: {delivery_location_name} - {postcode}")

# Combined with car_notes:
final_notes = f"{location_info}\n{car_notes}" if car_notes else location_info
```

## Timesheet Generation

### Template Structure

Excel template: `/app/templates/timesheet.xlsx`

**Fixed Cells**:
```
E5: Week Ending Date (formatted: "Sunday 19/10/25")
H2: Driver Name (UPPERCASE)
H4: Start Mileage
H5: End Mileage
K5: Fleet Registration
```

**Day Row Mappings**:
```python
row_mapping = {
    "Monday": 8,
    "Tuesday": 11,
    "Wednesday": 14,
    "Thursday": 17,
    "Friday": 20,
    "Saturday": 23,
    "Sunday": 26
}
```

**Load Data Columns** (up to 3 loads per day):
```
Column C (3): Customer/Contractor
Column D (4): Number of Cars
Column E (5): Collection Town
Column F (6): Delivery Town
```

**Time Data Columns** (at base_row for each day):
```
Column H (8): Start Time
Column I (9): Finish Time
Column J (10): Total Hours
```

**Overflow Loads**: If more than 3 loads per day, start at row 29

**Total Weekly Hours**: Row 29, Column J (10)

### Time Entry Data Format

Expected JSON format from server:
```json
{
  "date": "17/10/25",
  "day": "Monday",
  "start_time": "08:00",
  "finsh_time": "19:00",  // Note: typo is intentional (matches script)
  "total_hours": "11",
  "driver": "JOHN SMITH",
  "fleet_reg": "AB12 CDE",
  "start_mileage": "1000",
  "end_mileage": "1250"
}
```

**Special Case - Sick Day**:
```json
{
  "start_time": "SICK",
  "finsh_time": "SICK",
  "total_hours": "0"
}
```

## API Endpoints

### Device Management

```
GET  /api/devices
POST /api/devices/connect
POST /api/devices/add
POST /api/devices/remove
POST /api/devices/{address}/start
POST /api/devices/{address}/stop
POST /api/devices/{address}/reinstall
POST /api/devices/{address}/delete-sql
```

### SQL Data

```
POST /api/sql/pull
GET  /api/sql/data/dwjjob
GET  /api/sql/data/dwvveh
GET  /api/loads?sort={date_desc|date_asc|load_number}
```

### Paperwork Generation

```
POST /api/paperwork/loadsheet
     Body: {"load_number": "$S295198"}
     
POST /api/paperwork/timesheet
     Body: {"start_date": "2025-10-14", "end_date": "2025-10-19"}
     
GET  /api/paperwork/weeks
GET  /api/paperwork/exists/{load_number}
GET  /api/paperwork/download/{filename}
```

### Timesheet Entries

```
GET  /api/timesheet/entries?week_ending=2025-10-19
POST /api/timesheet/entries
     Body: {"entries": [{...}]}
     
DELETE /api/timesheet/entries/{id}
GET  /api/timesheet/calculate-total?week_ending=2025-10-19
```

### Vehicle Lookup

```
GET  /api/vehicles/lookup/{registration}
POST /api/vehicles/override
     Body: {"registration": "AB12CDE", "make_model": "FORD FIESTA"}
     
POST /api/vehicles/cleanup
```

### Screen Control

```
GET  /api/devices/{address}/screenshot
GET  /api/devices/{address}/current-screen
GET  /api/templates
POST /api/macros
POST /api/macros/{id}/execute
POST /api/devices/{address}/auto-login
```

## Configuration

### Device Configuration (adb_manager.py)

```python
DEVICES = [
    {"ip": "127.0.0.1", "port": "5555", "name": "Local Device"},
    {"ip": "10.10.254.62", "port": "5555", "name": "Device 1"},
    {"ip": "10.10.254.13", "port": "5555", "name": "Device 2"}
]

APP_PACKAGE = "com.lansa.bca"
DATA_FOLDER = "data"
SQL_PATH = "/data/data/com.lansa.bca/files/sql.db"
```

### Server Configuration (server.py)

```python
SERVER_PORT = 5020
LOG_FILE = "logs/server.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
```

## Dependencies (requirements.txt)

```
Flask==3.0.0
flask-cors==4.0.0
openpyxl==3.1.2
opencv-python==4.8.1.78
numpy==1.24.3
Pillow==10.1.0
requests==2.31.0
beautifulsoup4==4.12.2
```

## Docker/Podman Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    android-tools-adb \
    libgl1 \
    libglib2.0-0 \
    libreoffice \
    libreoffice-calc \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY adb_manager.py server.py credentials_manager.py \
     screen_detector.py screen_macros.py init_screen_control_db.py \
     vehicle_lookup.py .
COPY templates/ templates/
COPY scripts/ scripts/
COPY signature/ signature/
COPY screen_templates/ screen_templates/

# Create directories
RUN mkdir -p logs data apk templates static screenshots

EXPOSE 5020

ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
```

### docker-compose.yml

```yaml
services:
  adb-device-manager:
    build:
      context: ..
      dockerfile: compose/Dockerfile
    container_name: adb-device-manager
    restart: unless-stopped
    network_mode: host
    ports:
      - "5020:5020"
    volumes:
      - ../data:/app/data
      - ../logs:/app/logs
      - ../apk:/app/apk
      - ../templates:/app/templates
      - ../paperwork:/app/paperwork
    environment:
      - PYTHONUNBUFFERED=1
      - TZ=Europe/London
    privileged: true
    devices:
      - /dev/bus/usb:/dev/bus/usb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5020/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Podman Notes

**Issue**: USB device paths are dynamic and change when devices reconnect
**Solution**: Restart container when USB devices change:
```bash
podman-compose down && podman-compose up -d
```

**Alternative** (more flexible):
```yaml
device_cgroup_rules:
  - 'c 189:* rmw'  # Allow all USB devices
```

## Error Handling

### Common Issues

1. **No destination for handover loads**
   - Check: dwjType = "S" instead of "D"
   - Fix: Use handover job with destination "BTT YARD FOR HAND OVER"

2. **Missing timesheet hours**
   - Check: timesheet_entries table has data
   - Check: week_ending_date matches correctly
   - Check: server includes time entries in JSON

3. **USB device not found in Podman**
   - Check: `/dev/bus/usb` exists
   - Solution: Restart container to refresh USB mappings

4. **Vehicle make/model incorrect**
   - Check: vehicle_overrides table
   - Use: `/api/vehicles/override` to save corrections

## Logging

All components log to:
- Console (INFO level)
- `/app/logs/server.log` (rotating, max 10MB, 5 backups)
- `/app/logs/n8n_loadsheet.log` (loadsheet generation)
- `/app/logs/n8n_timesheet.log` (timesheet generation)

Log format:
```
%(asctime)s - %(levelname)s - %(message)s
```

## Security Considerations

1. **Credentials**: Stored in SQLite database (should encrypt in production)
2. **Network**: Runs on all interfaces (0.0.0.0) - firewall recommended
3. **Privileged Container**: Required for USB access - security risk
4. **File Uploads**: Signature images and templates - validate formats

## Extending the System

### Adding New Screen Template

```python
# 1. Capture screenshot of target screen
# 2. Save to /app/screen_templates/{name}.png
# 3. Add to database:
INSERT INTO screen_templates (name, description, image_path, threshold)
VALUES ('new_screen', 'Description', 'screen_templates/new_screen.png', 0.8);
```

### Adding New Macro

```python
actions = [
    {"type": "tap", "x": 100, "y": 200},
    {"type": "wait", "seconds": 1},
    {"type": "text", "value": "Hello"},
    {"type": "keyevent", "code": 66}  # ENTER
]

# POST /api/macros
{
  "name": "macro_name",
  "description": "What it does",
  "actions": actions
}
```

### Adding New Device

```python
# POST /api/devices/add
{
  "ip": "192.168.1.100",
  "port": "5555",
  "name": "New Device"
}
```

## Recovery Procedures

### Database Corruption

```bash
# Backup
cp data/screen_control.db data/screen_control.db.backup

# Reinitialize
python init_screen_control_db.py

# Restore specific tables if needed
sqlite3 data/screen_control.db.backup ".dump timesheet_entries" | \
  sqlite3 data/screen_control.db
```

### Pull Fresh Data

```bash
# Via API
curl -X POST http://localhost:5020/api/sql/pull

# Via ADB directly
adb -s 10.10.254.13:5555 pull /data/data/com.lansa.bca/files/sql.db data/sql.db
```

## Testing

### Manual Testing Checklist

1. ✅ Device connection and status
2. ✅ SQL data pull from device
3. ✅ Load listing and filtering
4. ✅ Loadsheet generation (standard load)
5. ✅ Loadsheet generation (handover load)
6. ✅ Timesheet generation (with hours)
7. ✅ Vehicle lookup and override
8. ✅ PDF conversion (LibreOffice)

### API Testing Examples

```bash
# Health check
curl http://localhost:5020/api/health

# Get loads
curl http://localhost:5020/api/loads?sort=date_desc

# Generate loadsheet
curl -X POST http://localhost:5020/api/paperwork/loadsheet \
  -H "Content-Type: application/json" \
  -d '{"load_number": "$S295198"}'

# Save timesheet entries
curl -X POST http://localhost:5020/api/timesheet/entries \
  -H "Content-Type: application/json" \
  -d '{
    "entries": [{
      "week_ending_date": "2025-10-19",
      "day_name": "Monday",
      "start_time": "08:00",
      "finish_time": "17:00",
      "total_hours": "9"
    }]
  }'
```

## Future Enhancements

1. **Authentication**: Add user login and API keys
2. **Multi-tenant**: Support multiple driver accounts
3. **Email Integration**: Auto-send generated paperwork
4. **Mobile App**: Native app for drivers
5. **Real-time Updates**: WebSocket for live device status
6. **Cloud Backup**: Automated backup to cloud storage
7. **Analytics**: Dashboard with statistics and trends

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-19  
**Maintainer**: Android Connect Development Team
