# Android-Connect MCP Tool Description

## Overview

**Android-Connect** is an MCP (Model Context Protocol) server that provides AI agents with powerful tools to manage Android-based logistics and paperwork automation. It connects to Android devices running the BCA Track app to pull vehicle transport load data and generate automated paperwork.

## What It Does

Android-Connect bridges the gap between Android devices running logistics apps and AI assistants, enabling natural language control of:

- **Load Management**: Search, query, and analyze vehicle transport loads
- **Paperwork Generation**: Automatically create loadsheets and timesheets in Excel format
- **Device Control**: Monitor and manage Android device connections
- **Database Synchronization**: Pull the latest data from connected Android devices
- **Date Management**: Override and manage delivery dates for organizational purposes

## Primary Use Cases

### 1. Logistics Query & Search
- "Show me all loads going to Ashford this week"
- "What vehicles are on load $S275052?"
- "Find all loads for WBAC today"

### 2. Automated Paperwork
- "Generate a loadsheet for $S275052"
- "Create timesheets for last week"
- "Generate all loadsheets for loads this week"

### 3. Device Management
- "Check if the Android device is connected"
- "Pull the latest database from the device"
- "What's the status of all devices?"

### 4. Timesheet Management
- "Add Monday 7am to 7pm to my timesheet"
- "Show me timesheet entries for this week"
- "Create timesheet entry for Thursday 19:00 to 03:00"

### 5. Vehicle Lookup
- "Look up registration WK67 FCX"
- "What make and model is VU19 YNO?"

## Available Tools

The MCP server provides 15+ specialized tools:

- `search_loads_by_date` - Search loads by natural language dates (today, this_week, etc.)
- `search_loads_by_location` - Find loads by customer, town, or postcode
- `get_loads_summary` - Get overview of all loads
- `get_load_details` - Detailed information about a specific load
- `generate_loadsheet` - Create Excel loadsheet for a load
- `generate_timesheet` - Create timesheet for date range
- `generate_all_loadsheets_for_period` - Bulk loadsheet generation
- `create_timesheet_entry` - Add/update timesheet entries
- `get_timesheet_entries` - View timesheet for a week
- `list_available_weeks` - Show weeks with available data
- `get_device_status` - Check Android device connections
- `pull_latest_data` - Sync database from device
- `connect_devices` - Connect to configured devices
- `lookup_vehicle` - Get vehicle make/model by registration
- `set_load_date_override` - Override delivery dates for grouping
- `delete_load_date_override` - Remove date overrides

## Data Sources

The system pulls data from:
- **BCA Track App** on Android devices (vehicle transport management system)
- **Local SQL Database** (synchronized from devices)
- **Excel Templates** (for paperwork generation)
- **DVLA API** (for vehicle registration lookups)

## Output Formats

- **Load Information**: Human-readable summaries and detailed breakdowns
- **Paperwork**: Excel files (.xlsx) with professional formatting
- **Device Status**: Real-time connection and database status
- **Timesheet Data**: Structured weekly timesheet information

## Integration

This MCP server can be integrated with:
- **n8n** - Workflow automation platform
- **Claude Desktop** - AI assistant with MCP support
- **Any MCP-compatible client** - Via HTTP/SSE or stdio transport

## Technical Details

- **Transport**: HTTP/SSE (Server-Sent Events) for web clients, stdio for desktop
- **Default Port**: 8100
- **API Backend**: Flask server on port 5020
- **Authentication**: Configurable (currently supports Bearer and Header auth)

## Example Interactions

**User:** "Show me loads for today"
**Response:** Lists all vehicle transport loads scheduled for today with locations and vehicle counts

**User:** "Generate paperwork for load $S275052"
**Response:** Creates an Excel loadsheet with all vehicle details, collection/delivery points, and signatures

**User:** "Add Tuesday 07:00 to 19:00 to my timesheet"
**Response:** Creates/updates timesheet entry for the current week's Tuesday

**User:** "What's the status of the Android device?"
**Response:** Shows connection status, database age, and device details

## Benefits

- **Natural Language Control**: Use conversational commands instead of manual data entry
- **Automation**: Generate paperwork for dozens of loads in seconds
- **Real-time Data**: Always working with the latest information from devices
- **Time Savings**: Reduces manual paperwork time from hours to minutes
- **Error Reduction**: Automated data extraction eliminates transcription errors
- **Flexibility**: Handles complex queries and date management scenarios

## For n8n Users

When configuring the MCP Client Tool node in n8n:

1. **SSE Endpoint**: `http://10.10.254.10:8100/sse` (or your server's IP)
2. **Authentication**: None (or configure as needed)
3. **Tools to Include**: All (to access all 15+ tools)

Once connected, your n8n workflows can:
- Trigger on schedule to generate daily paperwork
- Query load data for customer notifications
- Sync device data automatically
- Create timesheet entries from calendar events
- And much more!

---

**Project:** Android-Connect / ADB Device Manager  
**Protocol:** Model Context Protocol (MCP)  
**Version:** 2.0  
**Last Updated:** October 2025
