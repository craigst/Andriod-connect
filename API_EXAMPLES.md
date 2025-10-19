# ADB Device Manager - API Examples (curl)

Complete curl examples for all API endpoints on port 5020.

## 🔍 Health & Status

### Health Check
```bash
curl http://localhost:5020/api/health
```

### Get All Devices
```bash
curl http://localhost:5020/api/devices
```

### Get Database Info
```bash
curl http://localhost:5020/api/database/info
```

---

## 📱 Device Management

### Connect to All Devices
```bash
curl -X POST http://localhost:5020/api/devices/connect
```

### Add New Device
```bash
curl -X POST http://localhost:5020/api/devices/add \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "10.10.254.20",
    "port": "5555",
    "name": "My New Device"
  }'
```

### Remove Device
```bash
curl -X POST http://localhost:5020/api/devices/remove \
  -H "Content-Type: application/json" \
  -d '{
    "address": "10.10.254.20:5555"
  }'
```

---

## 🎮 App Control (Per-Device)

### Start App on Device
```bash
curl -X POST "http://localhost:5020/api/devices/127.0.0.1:5555/start"
```

### Stop App on Device
```bash
curl -X POST "http://localhost:5020/api/devices/127.0.0.1:5555/stop"
```

### Reinstall App on Device
```bash
curl -X POST "http://localhost:5020/api/devices/127.0.0.1:5555/reinstall"
```

### Examples for Other Devices
```bash
# Device 1
curl -X POST "http://localhost:5020/api/devices/10.10.254.62:5555/start"
curl -X POST "http://localhost:5020/api/devices/10.10.254.62:5555/stop"
curl -X POST "http://localhost:5020/api/devices/10.10.254.62:5555/reinstall"

# Device 2
curl -X POST "http://localhost:5020/api/devices/10.10.254.13:5555/start"
curl -X POST "http://localhost:5020/api/devices/10.10.254.13:5555/stop"
curl -X POST "http://localhost:5020/api/devices/10.10.254.13:5555/reinstall"
```

---

## 💾 SQL Data Management

### Pull SQL from First Available Device
```bash
curl -X POST http://localhost:5020/api/sql/pull \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Pull SQL from Specific Device (by index)
```bash
curl -X POST http://localhost:5020/api/sql/pull \
  -H "Content-Type: application/json" \
  -d '{
    "device_index": 1
  }'
```

### Get Job Data (DWJJOB)
```bash
curl http://localhost:5020/api/sql/data/dwjjob
```

### Get Vehicle Data (DWVVEH)
```bash
curl http://localhost:5020/api/sql/data/dwvveh
```

### Get Load Overview
```bash
curl http://localhost:5020/api/loads
```

---

## 🔄 Auto-Refresh Control

### Get Auto-Refresh Status
```bash
curl http://localhost:5020/api/auto-refresh
```

### Enable Auto-Refresh (10 minutes)
```bash
curl -X POST http://localhost:5020/api/auto-refresh \
  -H "Content-Type: application/json" \
  -d '{
    "enable": true,
    "interval_minutes": 10
  }'
```

### Disable Auto-Refresh
```bash
curl -X POST http://localhost:5020/api/auto-refresh \
  -H "Content-Type: application/json" \
  -d '{
    "enable": false
  }'
```

### Change Interval (15 minutes)
```bash
curl -X POST http://localhost:5020/api/auto-refresh \
  -H "Content-Type: application/json" \
  -d '{
    "enable": true,
    "interval_minutes": 15
  }'
```

---

## 📦 App Installation (Legacy)

### Install App on Specific Device
```bash
curl -X POST http://localhost:5020/api/app/install \
  -H "Content-Type: application/json" \
  -d '{
    "device_index": 1,
    "reinstall": false
  }'
```

### Reinstall App on All Devices
```bash
curl -X POST http://localhost:5020/api/app/install \
  -H "Content-Type: application/json" \
  -d '{
    "all_devices": true,
    "reinstall": true
  }'
```

---

## 📊 Example Workflows

### Complete Device Setup Workflow
```bash
# 1. Add a new device
curl -X POST http://localhost:5020/api/devices/add \
  -H "Content-Type: application/json" \
  -d '{"ip": "10.10.254.50", "port": "5555", "name": "Test Device"}'

# 2. Connect to all devices
curl -X POST http://localhost:5020/api/devices/connect

# 3. Check device status
curl http://localhost:5020/api/devices

# 4. Start app on new device
curl -X POST "http://localhost:5020/api/devices/10.10.254.50:5555/start"
```

### Data Collection Workflow
```bash
# 1. Pull SQL from device
curl -X POST http://localhost:5020/api/sql/pull \
  -H "Content-Type: application/json" \
  -d '{}'

# 2. Get load overview
curl http://localhost:5020/api/loads

# 3. Get detailed job data
curl http://localhost:5020/api/sql/data/dwjjob > jobs.json

# 4. Get detailed vehicle data
curl http://localhost:5020/api/sql/data/dwvveh > vehicles.json
```

### Maintenance Workflow
```bash
# 1. Stop app on device
curl -X POST "http://localhost:5020/api/devices/127.0.0.1:5555/stop"

# 2. Reinstall app
curl -X POST "http://localhost:5020/api/devices/127.0.0.1:5555/reinstall"

# 3. Start app
curl -X POST "http://localhost:5020/api/devices/127.0.0.1:5555/start"

# 4. Pull fresh SQL data
curl -X POST http://localhost:5020/api/sql/pull \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 🔧 Advanced Examples

### Pretty Print JSON Output
```bash
curl http://localhost:5020/api/loads | jq '.'
```

### Save Response to File
```bash
curl http://localhost:5020/api/sql/data/dwjjob > job_data.json
```

### Check Response Status
```bash
curl -w "\nHTTP Status: %{http_code}\n" http://localhost:5020/api/health
```

### Verbose Output (Debug)
```bash
curl -v http://localhost:5020/api/devices
```

### Silent Mode (No Progress)
```bash
curl -s http://localhost:5020/api/health
```

### Follow Redirects
```bash
curl -L http://localhost:5020/api/loads
```

---

## 📝 Response Formats

All endpoints return JSON with this structure:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { /* endpoint-specific data */ },
  "timestamp": "2025-10-04T20:00:00.000Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message here"
}
```

---

## 🌐 Remote Access Examples

### Access from Another Machine
```bash
# Replace localhost with server IP
curl http://10.10.254.10:5020/api/health
```

### Access from n8n Workflow
```json
{
  "method": "POST",
  "url": "http://10.10.254.10:5020/api/sql/pull",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {}
}
```

---

## 🧪 Testing Script

Complete test of all endpoints:

```bash
#!/bin/bash
BASE_URL="http://localhost:5020"

echo "Testing ADB Device Manager API..."

echo -e "\n1. Health Check"
curl -s $BASE_URL/api/health | jq '.'

echo -e "\n2. Get Devices"
curl -s $BASE_URL/api/devices | jq '.devices'

echo -e "\n3. Database Info"
curl -s $BASE_URL/api/database/info | jq '.'

echo -e "\n4. Pull SQL"
curl -s -X POST $BASE_URL/api/sql/pull \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.'

echo -e "\n5. Get Loads"
curl -s $BASE_URL/api/loads | jq '.total_loads'

echo -e "\nAll tests complete!"
```

Save as `test_all.sh`, make executable with `chmod +x test_all.sh`, and run with `./test_all.sh`

---

## 📖 Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/devices` | GET | List all devices |
| `/api/devices/connect` | POST | Connect all devices |
| `/api/devices/add` | POST | Add new device |
| `/api/devices/remove` | POST | Remove device |
| `/api/devices/{address}/start` | POST | Start app on device |
| `/api/devices/{address}/stop` | POST | Stop app on device |
| `/api/devices/{address}/reinstall` | POST | Reinstall app |
| `/api/sql/pull` | POST | Pull SQL database |
| `/api/sql/data/dwjjob` | GET | Get job data |
| `/api/sql/data/dwvveh` | GET | Get vehicle data |
| `/api/loads` | GET | Get load overview |
| `/api/auto-refresh` | GET/POST | Control auto-refresh |
| `/api/database/info` | GET | Database file info |

---

**Note**: Replace `localhost:5020` with your server's IP address when accessing remotely.
