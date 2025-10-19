# ADB Device Manager - API Documentation

Complete REST API reference for the ADB Device Manager application.

**Base URL:** `http://localhost:5020`  
**Version:** 2.0  
**Content-Type:** `application/json`

---

## Table of Contents

- [Health & Status](#health--status)
- [Device Management](#device-management)
- [SQL Database Operations](#sql-database-operations)
- [Load Management](#load-management)
- [Paperwork Generation](#paperwork-generation)
- [Auto-Refresh](#auto-refresh)
- [Error Handling](#error-handling)

---

## Health & Status

### GET /api/health

Check server health and status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-05T07:56:22.123456",
  "auto_refresh_enabled": false
}
```

**Example:**
```bash
curl http://localhost:5020/api/health
```

---

## Device Management

### GET /api/devices

Get status of all configured devices.

**Response:**
```json
{
  "success": true,
  "devices": [
    {
      "name": "Device 1",
      "address": "10.10.254.62:5555",
      "connected": true,
      "app_installed": true,
      "app_running": false
    }
  ],
  "timestamp": "2025-10-05T07:56:22.123456"
}
```

**Example:**
```bash
curl http://localhost:5020/api/devices | jq '.'
```

---

### POST /api/devices/connect

Connect to all configured devices.

**Response:**
```json
{
  "success": true,
  "message": "Connection attempted for all devices",
  "timestamp": "2025-10-05T07:56:22.123456"
}
```

**Example:**
```bash
curl -X POST http://localhost:5020/api/devices/connect
```

---

### POST /api/devices/add

Add a new device to the manager.

**Request Body:**
```json
{
  "ip": "10.10.254.100",
  "port": "5555",
  "name": "New Device"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device New Device added successfully",
  "device": {
    "name": "New Device",
    "address": "10.10.254.100:5555",
    "connected": false,
    "app_installed": false,
    "app_running": false
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5020/api/devices/add \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "10.10.254.100",
    "port": "5555",
    "name": "New Device"
  }'
```

---

### POST /api/devices/remove

Remove a device from the manager.

**Request Body:**
```json
{
  "address": "10.10.254.100:5555"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device New Device removed successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:5020/api/devices/remove \
  -H "Content-Type: application/json" \
  -d '{"address": "10.10.254.100:5555"}'
```

---

### POST /api/devices/{address}/start

Start the BCA Track app on a specific device.

**URL Parameters:**
- `address` - Device address (e.g., `10.10.254.62:5555`)

**Response:**
```json
{
  "success": true,
  "message": "App started on Device 1"
}
```

**Example:**
```bash
curl -X POST "http://localhost:5020/api/devices/10.10.254.62:5555/start"
```

---

### POST /api/devices/{address}/stop

Stop the BCA Track app on a specific device.

**URL Parameters:**
- `address` - Device address

**Response:**
```json
{
  "success": true,
  "message": "App stopped on Device 1"
}
```

**Example:**
```bash
curl -X POST "http://localhost:5020/api/devices/10.10.254.62:5555/stop"
```

---

### POST /api/devices/{address}/reinstall

Reinstall the BCA Track app on a specific device.

**URL Parameters:**
- `address` - Device address

**Response:**
```json
{
  "success": true,
  "message": "App reinstalled on Device 1"
}
```

**Example:**
```bash
curl -X POST "http://localhost:5020/api/devices/10.10.254.62:5555/reinstall"
```

---

## SQL Database Operations

### POST /api/sql/pull

Pull SQL database from a device.

**Request Body (Optional):**
```json
{
  "device_index": 1
}
```

If `device_index` is omitted, pulls from first available device.

**Response:**
```json
{
  "success": true,
  "message": "SQL file downloaded successfully",
  "file_path": "/app/data/sql.db",
  "timestamp": "2025-10-05T07:56:22.123456"
}
```

**Examples:**
```bash
# Pull from any available device
curl -X POST http://localhost:5020/api/sql/pull

# Pull from specific device (index starts at 1)
curl -X POST http://localhost:5020/api/sql/pull \
  -H "Content-Type: application/json" \
  -d '{"device_index": 1}'
```

---

### GET /api/sql/data/dwjjob

Get all job data from DWJJOB table.

**Response:**
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "dwjLoad": "$S275052",
      "dwjType": "C",
      "dwjDate": 20251004,
      "dwjDate_formatted": "04/10/2025",
      "dwjName": "WBAC Ashford",
      "dwjCust": "WBAC",
      "dwjPostco": "TN23 4YW",
      "dwjTown": "Ashford",
      "dwjVehs": 5
    }
  ],
  "timestamp": "2025-10-05T07:56:22.123456"
}
```

**Example:**
```bash
curl http://localhost:5020/api/sql/data/dwjjob | jq '.'
```

---

### GET /api/sql/data/dwvveh

Get all vehicle data from DWVVEH table.

**Response:**
```json
{
  "success": true,
  "count": 50,
  "data": [
    {
      "dwvLoad": "$S275052",
      "dwvVehRef": "ABC123",
      "dwvModDes": "Ford Transit",
      "dwvColDes": "White",
      "dwvStatus": 1,
      "dwvPos": 1
    }
  ],
  "timestamp": "2025-10-05T07:56:22.123456"
}
```

**Example:**
```bash
curl http://localhost:5020/api/sql/data/dwvveh | jq '.'
```

---

### GET /api/database/info

Get database file information.

**Response:**
```json
{
  "exists": true,
  "path": "/app/data/sql.db",
  "size_bytes": 524288,
  "size_mb": 0.5,
  "last_modified": "2025-10-05T07:56:22.123456",
  "last_modified_human": "2025-10-05 07:56:22"
}
```

**Example:**
```bash
curl http://localhost:5020/api/database/info | jq '.'
```

---

## Load Management

### GET /api/loads

Get overview of all loads with collections, deliveries, and vehicles.

**Response:**
```json
{
  "success": true,
  "total_loads": 5,
  "loads": [
    {
      "load_number": "$S275052",
      "collections": [
        {
          "date": "04/10/2025",
          "time": 1037,
          "customer": "WBAC",
          "location": "WBAC Ashford",
          "town": "Ashford",
          "postcode": "TN23 4YW",
          "vehicle_count": 5,
          "address_code": "005348"
        }
      ],
      "deliveries": [
        {
          "date": "04/10/2025",
          "time": 1200,
          "customer": "BCA",
          "location": "BCA PADDOCK WOOD",
          "town": "Paddock Wood",
          "postcode": "TN12 6YH",
          "vehicle_count": 5,
          "address_code": "001234"
        }
      ],
      "vehicles": [
        {
          "ref": "ABC123",
          "model": "Ford Transit",
          "color": "White",
          "status": 1,
          "position": 1
        }
      ],
      "total_vehicles": 5
    }
  ],
  "last_updated": "2025-10-05T07:56:22.123456"
}
```

**Example:**
```bash
curl http://localhost:5020/api/loads | jq '.'
```

---

## Paperwork Generation

### POST /api/paperwork/loadsheet

Generate loadsheet for a specific load.

**Request Body:**
```json
{
  "load_number": "$S275052"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Loadsheet generated successfully",
  "xlsx_path": "/app/paperwork/05-10-25/$S275052_WBAC_Ashford.xlsx",
  "load_number": "$S275052"
}
```

**Example:**
```bash
curl -X POST http://localhost:5020/api/paperwork/loadsheet \
  -H "Content-Type: application/json" \
  -d '{"load_number": "$S275052"}'
```

---

### POST /api/paperwork/timesheet

Generate timesheet for a date range.

**Request Body:**
```json
{
  "start_date": "2025-09-29",
  "end_date": "2025-10-05"
}
```

**Date Format:** `YYYY-MM-DD`

**Response:**
```json
{
  "success": true,
  "message": "Timesheet generated successfully",
  "xlsx_path": "/app/paperwork/05-10-25/timesheet_2025-10-05.xlsx"
}
```

**Example:**
```bash
curl -X POST http://localhost:5020/api/paperwork/timesheet \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-09-29",
    "end_date": "2025-10-05"
  }'
```

---

### GET /api/paperwork/weeks

Get available weeks with loads for timesheet generation.

**Response:**
```json
{
  "success": true,
  "weeks": [
    {
      "week_ending": "2025-10-05",
      "monday": "2025-09-29",
      "sunday": "2025-10-05",
      "load_count": 5
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5020/api/paperwork/weeks | jq '.'
```

---

### GET /api/paperwork/exists/{load_number}

Check if loadsheet exists for a load.

**URL Parameters:**
- `load_number` - Load number to check

**Response:**
```json
{
  "success": true,
  "exists": true,
  "xlsx_path": "/app/paperwork/05-10-25/$S275052_WBAC_Ashford.xlsx"
}
```

**Example:**
```bash
curl "http://localhost:5020/api/paperwork/exists/\$S275052" | jq '.'
```

---

### GET /api/paperwork/download/{filename}

Download a generated paperwork file.

**URL Parameters:**
- `filename` - Filename or load number

**Response:** Binary Excel file download

**Examples:**
```bash
# Download by filename
curl -O "http://localhost:5020/api/paperwork/download/\$S275052_WBAC_Ashford.xlsx"

# Download by load number (searches for matching file)
curl -O "http://localhost:5020/api/paperwork/download/\$S275052"
```

---

## Auto-Refresh

### GET /api/auto-refresh

Get auto-refresh status.

**Response:**
```json
{
  "enabled": false,
  "interval_seconds": 600,
  "interval_minutes": 10
}
```

**Example:**
```bash
curl http://localhost:5020/api/auto-refresh
```

---

### POST /api/auto-refresh

Control auto-refresh functionality.

**Request Body:**
```json
{
  "enable": true,
  "interval_minutes": 10
}
```

**Response:**
```json
{
  "success": true,
  "enabled": true,
  "message": "Auto-refresh enabled (every 10 minutes)"
}
```

**Examples:**
```bash
# Enable auto-refresh (10 minute interval)
curl -X POST http://localhost:5020/api/auto-refresh \
  -H "Content-Type: application/json" \
  -d '{
    "enable": true,
    "interval_minutes": 10
  }'

# Disable auto-refresh
curl -X POST http://localhost:5020/api/auto-refresh \
  -H "Content-Type: application/json" \
  -d '{"enable": false}'
```

---

## Error Handling

### Error Response Format

All errors return a JSON response with `success: false`:

```json
{
  "success": false,
  "error": "Error message description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

### Common Error Scenarios

#### 1. Database Not Found

```json
{
  "success": false,
  "error": "Database not found. Please pull SQL file first."
}
```

**Solution:** Pull SQL database first using `/api/sql/pull`

---

#### 2. Load Not Found

```json
{
  "success": false,
  "error": "Load $S275052 not found in database"
}
```

**Solution:** Verify load number exists using `/api/loads`

---

#### 3. No Devices Available

```json
{
  "success": false,
  "error": "No devices available with app installed"
}
```

**Solution:** Connect devices and ensure app is installed

---

#### 4. Device Not Found

```json
{
  "success": false,
  "error": "Device not found"
}
```

**Solution:** Check device address using `/api/devices`

---

## Complete Examples

### Example 1: Complete Workflow - Pull DB and Generate Loadsheets

```bash
#!/bin/bash

# 1. Check health
curl http://localhost:5020/api/health

# 2. Connect to devices
curl -X POST http://localhost:5020/api/devices/connect

# 3. Pull SQL database
curl -X POST http://localhost:5020/api/sql/pull

# 4. Get all loads
curl http://localhost:5020/api/loads | jq -r '.loads[].load_number'

# 5. Generate loadsheets for all loads
curl -s http://localhost:5020/api/loads | jq -r '.loads[].load_number' | \
while read load; do
  echo "Generating loadsheet for: $load"
  curl -X POST http://localhost:5020/api/paperwork/loadsheet \
    -H "Content-Type: application/json" \
    -d "{\"load_number\":\"$load\"}"
  sleep 1
done
```

---

### Example 2: Generate Weekly Timesheet

```bash
#!/bin/bash

# Get available weeks
curl -s http://localhost:5020/api/paperwork/weeks | jq '.'

# Generate timesheet for latest week
MONDAY=$(curl -s http://localhost:5020/api/paperwork/weeks | jq -r '.weeks[0].monday')
SUNDAY=$(curl -s http://localhost:5020/api/paperwork/weeks | jq -r '.weeks[0].sunday')

curl -X POST http://localhost:5020/api/paperwork/timesheet \
  -H "Content-Type: application/json" \
  -d "{
    \"start_date\": \"$MONDAY\",
    \"end_date\": \"$SUNDAY\"
  }"
```

---

### Example 3: Python Script Integration

```python
#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:5020"

def get_devices():
    """Get all devices status"""
    response = requests.get(f"{BASE_URL}/api/devices")
    return response.json()

def pull_sql():
    """Pull SQL database from first available device"""
    response = requests.post(f"{BASE_URL}/api/sql/pull")
    return response.json()

def get_loads():
    """Get all loads"""
    response = requests.get(f"{BASE_URL}/api/loads")
    return response.json()

def generate_loadsheet(load_number):
    """Generate loadsheet for a specific load"""
    data = {"load_number": load_number}
    response = requests.post(
        f"{BASE_URL}/api/paperwork/loadsheet",
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )
    return response.json()

def main():
    # Connect and pull data
    print("Pulling SQL database...")
    result = pull_sql()
    print(f"Pull result: {result['message']}")
    
    # Get loads
    print("\nFetching loads...")
    loads_data = get_loads()
    print(f"Found {loads_data['total_loads']} loads")
    
    # Generate loadsheets
    print("\nGenerating loadsheets...")
    for load in loads_data['loads']:
        load_number = load['load_number']
        print(f"Generating loadsheet for {load_number}...")
        result = generate_loadsheet(load_number)
        if result['success']:
            print(f"  ✓ {result['xlsx_path']}")
        else:
            print(f"  ✗ {result['error']}")

if __name__ == "__main__":
    main()
```

---

### Example 4: Node.js Integration

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:5020';

async function pullSQL() {
  const response = await axios.post(`${BASE_URL}/api/sql/pull`);
  return response.data;
}

async function getLoads() {
  const response = await axios.get(`${BASE_URL}/api/loads`);
  return response.data;
}

async function generateLoadsheet(loadNumber) {
  const response = await axios.post(
    `${BASE_URL}/api/paperwork/loadsheet`,
    { load_number: loadNumber },
    { headers: { 'Content-Type': 'application/json' } }
  );
  return response.data;
}

async function main() {
  try {
    // Pull database
    console.log('Pulling SQL database...');
    const pullResult = await pullSQL();
    console.log(`Pull result: ${pullResult.message}`);
    
    // Get loads
    console.log('\nFetching loads...');
    const loadsData = await getLoads();
    console.log(`Found ${loadsData.total_loads} loads`);
    
    // Generate loadsheets
    console.log('\nGenerating loadsheets...');
    for (const load of loadsData.loads) {
      console.log(`Generating loadsheet for ${load.load_number}...`);
      const result = await generateLoadsheet(load.load_number);
      if (result.success) {
        console.log(`  ✓ ${result.xlsx_path}`);
      } else {
        console.log(`  ✗ ${result.error}`);
      }
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
```

---

## Rate Limiting

Currently, there are no rate limits enforced. However, it's recommended to:
- Add small delays (1 second) between bulk operations
- Use auto-refresh instead of frequent manual pulls
- Avoid concurrent requests to the same endpoint

---

## WebSocket Support

WebSocket support is not currently implemented. The API uses standard HTTP REST endpoints.

---

## Authentication

Currently, no authentication is required. The server should be run on a trusted internal network and not exposed to the public internet.

For production deployments, consider:
- Adding API key authentication
- Implementing OAuth2
- Using reverse proxy with authentication (nginx, Apache)
- Firewall restrictions

---

## Changelog

### Version 2.0 (October 2025)
- Added paperwork generation endpoints
- Fixed data format conversion issues
- Added comprehensive error handling
- Improved device management

### Version 1.0
- Initial release
- Basic device management
- SQL database operations

---

## Support

For issues or questions:
- Review this documentation
- Check server logs: `podman logs adb-device-manager`
- Verify device connectivity
- Ensure SQL database is pulled before paperwork generation

---

**Last Updated:** October 2025  
**API Version:** 2.0
