# MCP Server Setup for Cline (VS Code)

This guide explains how to set up the MCP (Model Context Protocol) server for Android-Connect paperwork automation with Cline in VS Code.

## What is This?

The MCP server allows AI assistants (like Cline) to interact with your Android-Connect system using natural language. Instead of manually using the API or web interface, you can simply ask:

- "What loads do I have today?"
- "Generate paperwork for all work this week"
- "Pull latest data from my phone"
- "Create my timesheet - I worked 8 hours Monday through Friday"

## Prerequisites

1. **Python 3.11+** installed
2. **VS Code** with **Cline extension** installed
3. **Flask API running** on port 5020 (from this project)

## Installation

### Step 1: Install MCP Dependencies

```bash
# In your Andriod-connect directory
pip install -r requirements-mcp.txt
```

Or install manually:

```bash
pip install mcp httpx
```

### Step 2: Make MCP Server Executable

```bash
chmod +x mcp_server.py
```

### Step 3: Test the MCP Server (Optional)

First, ensure your Flask API is running:

```bash
python server.py
```

Then in another terminal, test the MCP server:

```bash
python mcp_server.py
```

If it starts without errors, press `Ctrl+C` to stop it. It's working correctly.

## Cline Configuration

### Step 1: Open Cline Settings

In VS Code:
1. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "Cline: Open MCP Settings"
3. Or open `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

### Step 2: Add MCP Server Configuration

Add this to your Cline MCP settings:

```json
{
  "mcpServers": {
    "android-paperwork": {
      "command": "python3",
      "args": [
        "/full/path/to/Andriod-connect/mcp_server.py"
      ],
      "env": {
        "FLASK_API_URL": "http://localhost:5020"
      }
    }
  }
}
```

**Important:** Replace `/full/path/to/Andriod-connect/` with your actual project path!

Example:
```json
{
  "mcpServers": {
    "android-paperwork": {
      "command": "python3",
      "args": [
        "/home/craigst/Nextcloud/Documents/projects/Andriod-connect/mcp_server.py"
      ],
      "env": {
        "FLASK_API_URL": "http://localhost:5020"
      }
    }
  }
}
```

### Step 3: Restart Cline

1. Restart VS Code, or
2. Reload the Cline extension

### Step 4: Verify Connection

In Cline chat, ask:

```
Check device status
```

If the MCP server is configured correctly, Cline will use the `get_device_status` tool and show you your device status.

## Usage Examples

Once configured, you can use natural language with Cline:

### View Loads

```
What loads do I have today?
```

```
Show me all loads for this week
```

```
Find loads going to WBAC Ashford
```

### Generate Paperwork

```
Generate paperwork for all loads this week
```

```
Make a loadsheet for load $S275052
```

```
Create all loadsheets for today
```

### Check Status

```
Is my data up to date?
```

```
What's the status of my phones?
```

```
Pull latest data from device
```

### Create Timesheet

```
Help me create my timesheet for this week
```

Then Cline will interactively ask you for:
- Each day's start time
- Each day's finish time
- Driver name, fleet registration, etc.

And finally generate the Excel timesheet.

### Vehicle Lookup

```
Look up vehicle registration ABC123
```

```
Save vehicle override for ABC123 as "Ford Transit Custom"
```

## Available MCP Tools

The MCP server provides these tools to Cline:

### Search & Discovery
- `search_loads_by_date` - Find loads by date (today, this_week, etc.)
- `search_loads_by_location` - Find loads by location/customer
- `get_loads_summary` - Get all loads with descriptions

### Paperwork Generation
- `generate_loadsheet` - Generate single loadsheet
- `generate_all_loadsheets_for_period` - Batch generate loadsheets
- `generate_timesheet` - Create timesheet for date range
- `list_available_weeks` - Show weeks with loads

### Device Management
- `get_device_status` - Check device connection status
- `pull_latest_data` - Pull SQL from device
- `connect_devices` - Connect to all devices
- `check_database_freshness` - Check database age

### Timesheet Management
- `create_timesheet_entry` - Add/update timesheet entry
- `get_timesheet_entries` - View entries for a week

### Vehicle Tools
- `lookup_vehicle` - Look up vehicle by registration
- `save_vehicle_override` - Save custom vehicle info

## MCP Resources

The server also provides context resources that Cline can reference:

- `resource://loads/current` - Current loads data
- `resource://devices/status` - Device connection status
- `resource://database/info` - Database information
- `resource://paperwork/weeks` - Available weeks for timesheets

## Troubleshooting

### MCP Server Not Connecting

**Problem:** Cline shows "Failed to connect to MCP server"

**Solutions:**
1. Check the path in MCP settings is correct
2. Ensure Python 3 is in your PATH
3. Verify `pip install mcp httpx` was successful
4. Check Flask API is running on port 5020

Test manually:
```bash
cd /path/to/Andriod-connect
python3 mcp_server.py
```

### Flask API Not Running

**Problem:** "API request failed: Connection refused"

**Solution:** Start the Flask server:
```bash
python server.py
```

Or use the Docker container:
```bash
cd compose
docker-compose up -d
```

### Database Not Found

**Problem:** "Database not found. Pull data from a device first."

**Solution:** Pull SQL database from device:
```
Pull latest data from device
```

Or manually:
```bash
curl -X POST http://localhost:5020/api/sql/pull
```

### Port 5020 Already in Use

**Problem:** Flask API won't start - port in use

**Solution:** Find and kill the process:
```bash
lsof -i :5020
kill -9 <PID>
```

Or change the port in `server.py` and update MCP settings.

## Advanced Configuration

### Custom API Port

If your Flask API runs on a different port, update the MCP settings:

```json
{
  "mcpServers": {
    "android-paperwork": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "FLASK_API_URL": "http://localhost:8080"
      }
    }
  }
}
```

### Remote Flask API

If Flask API is on another machine:

```json
{
  "mcpServers": {
    "android-paperwork": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "FLASK_API_URL": "http://192.168.1.100:5020"
      }
    }
  }
}
```

### Running Both Services Together

Create a startup script to launch both Flask and ensure it's ready:

```bash
#!/bin/bash
# start_all.sh

# Start Flask API in background
python server.py &
FLASK_PID=$!

# Wait for Flask to be ready
echo "Waiting for Flask API..."
sleep 5

# Keep Flask running
wait $FLASK_PID
```

Then in MCP settings, you could use this script if needed.

## Example Conversation

```
You: What loads do I have today?

Cline: Let me check your loads for today.
[Uses search_loads_by_date tool]

Found 3 loads for today:

1. $S275052: FROM WBAC Ashford (TN23 4YW) TO BCA Paddock Wood (TN12 6YH) - 5 vehicles on 20/10/2025
2. $S275053: FROM Motorpoint Derby (DE21 6BZ) TO BCA Blackbushe (GU17 9LG) - 3 vehicles on 20/10/2025
3. $S275054: FROM CarShop Swindon (SN2 2DY) TO BCA Bedford (MK42 0PE) - 4 vehicles on 20/10/2025

---

You: Generate loadsheets for all of them

Cline: I'll generate loadsheets for all 3 loads.
[Uses generate_all_loadsheets_for_period tool]

Generated 3/3 loadsheets for today:

✅ $S275052
✅ $S275053
✅ $S275054

All loadsheets have been saved to the paperwork directory.

---

You: Is my data fresh?

Cline: Let me check the database status.
[Uses check_database_freshness tool]

Database Information:
Last updated: 2025-10-20 07:30:15
Age: 2 hour(s) old
Size: 0.5 MB

Your data is 2 hours old. Would you like me to pull the latest data from your device?
```

## Tips for Best Results

1. **Keep Flask Running:** The MCP server needs the Flask API to be running
2. **Be Specific:** "loads for WBAC" is better than just "loads"
3. **Use Natural Language:** Cline understands "today", "this week", etc.
4. **Check Data Age:** Regularly pull fresh data from your device
5. **Review Generated Files:** Always verify the paperwork before submitting

## Support

For issues:
1. Check Flask API logs: `logs/server.log`
2. Test Flask API directly: `curl http://localhost:5020/api/health`
3. Verify MCP server path in settings
4. Ensure all dependencies are installed

## What's Next?

Once you have it working, you can:
- Use voice commands (if your IDE supports it)
- Create custom workflows with Cline
- Automate daily paperwork generation
- Build reports and summaries

Enjoy your AI-powered paperwork automation! 🚀
