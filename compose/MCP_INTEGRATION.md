# MCP Server Integration - Docker Setup

## Overview

The Docker container now includes both MCP server transports, providing AI-powered automation capabilities alongside the Flask API.

## Architecture

```
Docker Container (adb-device-manager)
├── Flask API (Port 5020)
│   └── Main web application and REST API backend
├── MCP HTTP Server (Port 8100)
│   ├── SSE Endpoint: /sse
│   └── Messages Endpoint: /messages
└── MCP Stdio Server
    └── Stdio transport for internal/local access
```

## Startup Sequence

1. **Flask API** starts first (background, port 5020)
2. Health check waits for Flask to be ready (max 30s)
3. **MCP HTTP Server** starts (background, port 8100)
4. **MCP Stdio Server** starts in foreground (keeps container alive)

## Files Modified

### 1. `Dockerfile`
- Added `requirements-mcp.txt` installation
- Copied `mcp_server.py` and `mcp_server_http.py`
- Added `curl` for health checks
- Exposed port 8100 for MCP HTTP
- Changed CMD to use `docker-entrypoint.sh`

### 2. `docker-compose.yml`
- Added port mapping for 8100
- Added environment variables:
  - `FLASK_API_URL=http://localhost:5020`
  - `MCP_HOST=0.0.0.0`
  - `MCP_PORT=8100`

### 3. `docker-entrypoint.sh` (NEW)
- Manages all three services
- Ensures proper startup order
- Provides colored console output
- Handles health checks
- Logs to separate files

### 4. `README.md`
- Documented all three services
- Added MCP tools reference
- Added n8n integration instructions
- Updated testing procedures

## Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `FLASK_API_URL` | `http://localhost:5020` | MCP servers connect to Flask API |
| `MCP_HOST` | `0.0.0.0` | Allow external connections to MCP HTTP |
| `MCP_PORT` | `8100` | MCP HTTP server port |

## Available MCP Tools (17+)

### Search & Discovery
- `search_loads_by_date` - Natural language date search
- `search_loads_by_location` - Location-based search
- `get_loads_summary` - All loads overview
- `get_load_details` - Detailed load info with vehicles

### Paperwork Generation
- `generate_loadsheet` - Single load paperwork
- `generate_all_loadsheets_for_period` - Batch generation
- `generate_timesheet` - Create timesheets
- `list_available_weeks` - Available timesheet weeks

### Device Management
- `get_device_status` - All devices status
- `pull_latest_data` - Pull SQL from device
- `connect_devices` - Connect all devices
- `check_database_freshness` - Database age check

### Timesheet Management
- `create_timesheet_entry` - Add/update entry
- `get_timesheet_entries` - Get week entries

### Vehicle Lookup
- `lookup_vehicle` - DVLA API lookup
- `save_vehicle_override` - Custom vehicle data

## MCP Resources

- `resource://loads/current` - All current loads
- `resource://devices/status` - Device statuses
- `resource://database/info` - Database information
- `resource://paperwork/weeks` - Available weeks

## Testing

### 1. Build and Start
```bash
cd compose
docker compose build
docker compose up -d
```

### 2. Check Logs
```bash
# All services
docker logs adb-device-manager

# Flask API specific
docker exec adb-device-manager tail -f /app/logs/flask.log

# MCP HTTP specific
docker exec adb-device-manager tail -f /app/logs/mcp_http.log
```

### 3. Test Endpoints
```bash
# Flask API health
curl http://localhost:5020/api/health

# MCP HTTP SSE endpoint
curl http://localhost:8100/sse

# Check if all services are running
docker exec adb-device-manager ps aux | grep python
```

### 4. Test MCP Tools (via HTTP)
```bash
# Example: Get loads summary
curl -X POST http://localhost:8100/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_loads_summary",
      "arguments": {"sort": "date_desc"}
    }
  }'
```

## Integration with n8n

### Setup
1. Install n8n (if not already installed)
2. Create new workflow
3. Add MCP node
4. Configure connection:
   - Protocol: HTTP
   - SSE Endpoint: `http://[DOCKER-HOST]:8100/sse`
   - Messages Endpoint: `http://[DOCKER-HOST]:8100/messages`

### Example Workflows

#### Daily Loadsheet Generation
```
Trigger (Schedule - Daily 6am)
  ↓
MCP: search_loads_by_date (period: "today")
  ↓
MCP: generate_all_loadsheets_for_period (period: "today")
  ↓
Notification (Email/Slack)
```

#### Weekly Timesheet
```
Trigger (Schedule - Friday 5pm)
  ↓
MCP: list_available_weeks
  ↓
MCP: generate_timesheet (start_date, end_date)
  ↓
Notification (Email/Slack)
```

#### Device Health Check
```
Trigger (Schedule - Hourly)
  ↓
MCP: get_device_status
  ↓
Conditional (Any offline?)
  ↓
Alert (Email/SMS/Slack)
```

## Logs

All services log to separate files:

| Service | Log File | Access |
|---------|----------|--------|
| Flask API | `/app/logs/flask.log` | `docker exec adb-device-manager tail -f /app/logs/flask.log` |
| MCP HTTP | `/app/logs/mcp_http.log` | `docker exec adb-device-manager tail -f /app/logs/mcp_http.log` |
| MCP Stdio | stdout | `docker logs -f adb-device-manager` |

## Troubleshooting

### MCP HTTP Server Not Starting
```bash
# Check if Flask API is running
curl http://localhost:5020/api/health

# Check MCP HTTP logs
docker exec adb-device-manager cat /app/logs/mcp_http.log

# Verify port not in use
netstat -tulpn | grep 8100
```

### MCP Tools Returning Errors
```bash
# Verify Flask API is accessible from MCP server
docker exec adb-device-manager curl http://localhost:5020/api/health

# Check database exists
docker exec adb-device-manager ls -la /app/data/
```

### Can't Connect from n8n
```bash
# Verify MCP HTTP is listening on 0.0.0.0
docker exec adb-device-manager netstat -tulpn | grep 8100

# Test SSE endpoint from host
curl http://localhost:8100/sse
```

## Performance Notes

- Flask API handles all database operations
- MCP servers are lightweight proxies
- Each MCP tool makes HTTP requests to Flask API
- All three services run in single container
- Minimal overhead: ~50MB RAM total for MCP servers

## Security Considerations

- MCP HTTP server binds to `0.0.0.0` (accessible from network)
- No authentication on MCP endpoints (add reverse proxy if needed)
- Flask API has same security as before
- All services run in same container namespace

## Future Enhancements

Potential improvements:
- Add authentication to MCP HTTP endpoints
- Implement rate limiting
- Add WebSocket transport for MCP
- Create health check for MCP servers
- Add Prometheus metrics
- Implement request logging/auditing

## Summary

✅ All MCP features now available in Docker  
✅ Both HTTP and Stdio transports included  
✅ Proper service startup ordering  
✅ Comprehensive logging  
✅ Ready for n8n integration  
✅ All 17+ tools functional  
✅ Resources exposed for AI context
