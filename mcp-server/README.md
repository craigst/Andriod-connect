# Android-Connect MCP Server

Model Context Protocol (MCP) server for Android-Connect paperwork automation. This server provides AI-friendly tools for managing loads, generating paperwork, and controlling Android devices.

## Overview

This MCP server acts as a bridge between AI assistants (like Claude) and the Android-Connect Flask API. It provides:

- **Search Tools**: Find loads by date, location, or other criteria
- **Paperwork Generation**: Create loadsheets and timesheets
- **Device Management**: Control Android devices and pull data
- **Vehicle Lookup**: Query vehicle information
- **Date Overrides**: Manage delivery date overrides for loads

## Requirements

- Python 3.11+
- Access to Android-Connect Flask API (default: http://localhost:5020)

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure the Flask API endpoint** (optional):
```bash
export FLASK_API_URL="http://localhost:5020"
```

## Usage

### Stdio Transport (for Claude Desktop, etc.)

Run the stdio version for local AI assistants:

```bash
python mcp_server.py
```

**Claude Desktop Configuration**:

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "android-connect": {
      "command": "python",
      "args": ["/path/to/mcp-server/mcp_server.py"],
      "env": {
        "FLASK_API_URL": "http://localhost:5020"
      }
    }
  }
}
```

### HTTP/SSE Transport (for n8n, web clients, etc.)

Run the HTTP version for network-accessible MCP server:

```bash
python mcp_server_http.py
```

**Configuration**:
- `MCP_HOST`: Bind address (default: 0.0.0.0)
- `MCP_PORT`: Bind port (default: 8100)
- `FLASK_API_URL`: Flask API endpoint (default: http://localhost:5020)

**Example**:
```bash
export MCP_HOST=0.0.0.0
export MCP_PORT=8100
export FLASK_API_URL="http://192.168.1.100:5020"
python mcp_server_http.py
```

**Endpoints**:
- SSE: `http://localhost:8100/sse`
- Messages: `http://localhost:8100/messages` (POST)

## Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py .
COPY mcp_server_http.py .

EXPOSE 8100

ENV FLASK_API_URL=http://host.docker.internal:5020
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8100

CMD ["python", "mcp_server_http.py"]
```

Build and run:

```bash
docker build -t android-connect-mcp .
docker run -p 8100:8100 -e FLASK_API_URL=http://host.docker.internal:5020 android-connect-mcp
```

## Available Tools

### Search & Discovery
- `search_loads_by_date` - Search loads by date/period
- `search_loads_by_location` - Search loads by location
- `get_loads_summary` - Get all loads summary
- `get_load_details` - Get detailed load information

### Paperwork Generation
- `generate_loadsheet` - Generate loadsheet for a load
- `generate_all_loadsheets_for_period` - Generate multiple loadsheets
- `generate_timesheet` - Generate timesheet for date range
- `list_available_weeks` - List weeks with loads

### Device Management
- `get_device_status` - Check device connection status
- `pull_latest_data` - Pull SQL database from device
- `connect_devices` - Connect to Android devices
- `check_database_freshness` - Check database age

### Timesheet Management
- `create_timesheet_entry` - Create/update timesheet entry
- `get_timesheet_entries` - Get entries for a week

### Vehicle Operations
- `lookup_vehicle` - Look up vehicle by registration
- `save_vehicle_override` - Save custom vehicle info

### Date Overrides
- `get_load_date_override` - Check date override
- `set_load_date_override` - Set date override
- `delete_load_date_override` - Remove date override

## Available Resources

- `resource://loads/current` - Current loads in database
- `resource://devices/status` - Device connection status
- `resource://database/info` - Database information
- `resource://paperwork/weeks` - Available weeks for timesheets

## Architecture

```
┌─────────────┐          ┌──────────────┐          ┌─────────────────┐
│  AI Client  │◄────────►│  MCP Server  │◄────────►│  Flask API      │
│  (Claude)   │   MCP    │   (This)     │   HTTP   │  (Port 5020)    │
└─────────────┘          └──────────────┘          └─────────────────┘
                                                            │
                                                            ▼
                                                    ┌─────────────────┐
                                                    │ Android Device  │
                                                    │  (via ADB)      │
                                                    └─────────────────┘
```

## Development

The MCP server is completely independent from the main Android-Connect project. It communicates via HTTP API calls to the Flask backend.

### Adding New Tools

Edit `mcp_server.py` or `mcp_server_http.py`:

1. Add tool definition in `list_tools()`
2. Add tool handler in `call_tool()`
3. Make HTTP request to Flask API endpoint

### Testing

Test the server with MCP inspector:

```bash
npx @modelcontextprotocol/inspector python mcp_server.py
```

Or test the HTTP version:

```bash
curl http://localhost:8100/sse
```

## Troubleshooting

**Connection refused to Flask API**:
- Ensure Flask API is running on port 5020
- Check `FLASK_API_URL` environment variable
- For Docker: Use `host.docker.internal:5020` or container network

**Tools not appearing**:
- Check MCP server logs for errors
- Verify Python dependencies are installed
- Test Flask API endpoints directly with curl

**Permission errors**:
- Ensure the MCP server can access the Flask API
- Check firewall rules if running across network

## License

Same as Android-Connect main project.

## Related Documentation

- [Android-Connect Main Project](../README.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Flask API Documentation](../API_DOCUMENTATION.md)
