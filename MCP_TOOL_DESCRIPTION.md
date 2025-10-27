# Android-Connect MCP Tool - AI Assistant Guide

## For AI Assistants Using This Tool

This document provides comprehensive instructions for AI assistants to effectively use the Android-Connect MCP server. Read this carefully to understand all available capabilities and how to use them.

## System Overview

**Android-Connect** is an MCP (Model Context Protocol) server that provides AI agents with tools to manage Android-based logistics and paperwork automation. The system:

1. **Connects** to Android devices running the BCA Track app
2. **Pulls** vehicle transport load data from the Android app's SQL database
3. **Generates** professional loadsheets and timesheets in PDF format
4. **Manages** delivery dates, timesheet entries, and vehicle information
5. **Provides** download links for all generated paperwork

### Data Flow
```
Android Device (BCA Track App) 
    ↓ [ADB Connection]
SQL Database 
    ↓ [Pull Latest Data]
Flask API Server (Port 5020)
    ↓ [API Requests]
MCP Server (Port 8100)
    ↓ [Tools]
AI Assistant (You)
```

## Core Concepts

### Loads
- **Load Number**: Unique identifier (e.g., `$S275052`)
- **Collection Points**: Where vehicles are picked up
- **Delivery Points**: Where vehicles are delivered
- **Vehicles**: List of vehicles on each load (registration, make/model, color)
- **Dates**: Delivery dates (can be overridden for grouping)

### Paperwork Organization
- Files are organized by week ending (Sunday)
- Folder format: `DD-MM-YY` (e.g., `27-10-25` for October 27, 2025)
- Each load gets both `.xlsx` and `.pdf` files
- PDFs are automatically generated from Excel files

### Timesheets
- Organized by week ending date
- Track daily hours: start time, finish time, total hours
- Support for driver and fleet registration information

## How to Use as an AI Assistant

### General Workflow

**1. Check Database Freshness (if needed)**
```
Tool: check_database_freshness
Purpose: See when database was last updated
When: User asks about current/recent loads
```

**2. Pull Latest Data (if database is old)**
```
Tool: pull_latest_data
Purpose: Sync database from Android device
When: Database is >1 hour old or user requests fresh data
```

**3. Search/Query Loads**
```
Tool: search_loads_by_date or search_loads_by_location
Purpose: Find specific loads
When: User asks about loads
```

**4. Generate Paperwork**
```
Tool: generate_loadsheet
Purpose: Create PDF loadsheet
When: User requests paperwork
Returns: PDF download URL
```

**5. Manage Files**
```
Tool: get_paperwork_files or list_paperwork_weeks
Purpose: List available paperwork
When: User wants to download existing files
```

### Common User Requests & How to Handle

#### "Show me loads for today"
```
1. Use: search_loads_by_date with period="today"
2. Parse results and present in readable format
3. Mention total count and key details
```

#### "Generate paperwork for load $S275052"
```
1. Use: generate_loadsheet with load_number="$S275052"
2. Extract PDF download URL from response
3. Present download link to user
4. Note: PDF is automatically created from Excel
```

#### "Get all PDFs from last week"
```
1. Calculate last week's Sunday date
2. Use: get_paperwork_files with week_ending="DD-MM-YY"
3. Filter results to show only PDFs
4. Present all PDF download URLs
```

#### "Add timesheet entry for Monday 7am to 5pm"
```
1. Use: create_timesheet_entry
2. Params: day_name="Monday", start_time="07:00", finish_time="17:00"
3. System auto-calculates date and week ending
4. Confirm entry created
```

#### "What vehicles are on load $S275052?"
```
1. Use: get_load_details with load_number="$S275052"
2. Parse vehicles list from response
3. Present each vehicle with reg, make/model, color
```

## Complete Tool Reference

### 🔍 Search & Query Tools

#### `search_loads_by_date`
**Purpose:** Find loads by date or date range  
**Input:** `{"period": "today|yesterday|this_week|last_week|next_week|this_month|YYYY-MM-DD"}`  
**Returns:** List of loads with descriptions  
**Example:**
```
Input: {"period": "this_week"}
Output: Found 15 load(s) for this_week:
        $S275052: FROM WBAC Ashford (TN23) TO BTT Yard (ME2) 3 vehicles on 27/10/25
```

#### `search_loads_by_location`
**Purpose:** Find loads by customer, town, or postcode  
**Input:** `{"location": "search term"}`  
**Returns:** Matching loads  
**Example:**
```
Input: {"location": "Ashford"}
Output: Loads with "Ashford" in collection or delivery locations
```

#### `get_loads_summary`
**Purpose:** Get overview of all loads in database  
**Input:** `{"sort": "date_desc|date_asc|load_number"}` (optional)  
**Returns:** All loads with summary info  
**When to use:** User wants to see all available loads

#### `get_load_details`
**Purpose:** Get detailed information about a specific load  
**Input:** `{"load_number": "$S275052"}`  
**Returns:** Full details including all vehicles, collection/delivery points, dates  
**When to use:** User asks about a specific load's details

### 📄 Paperwork Generation Tools

#### `generate_loadsheet`
**Purpose:** Generate PDF loadsheet for a specific load  
**Input:** `{"load_number": "$S275052"}`  
**Returns:** Success message with PDF download URL  
**Important:** Always present the PDF download link to the user  
**Example Output:**
```
✅ Loadsheet generated successfully
📄 PDF Download: http://10.10.254.10:5020/api/paperwork/download/$S275052_WBAC_Ashford.pdf
📁 File: $S275052_WBAC_Ashford.pdf
```

#### `generate_all_loadsheets_for_period`
**Purpose:** Bulk generate loadsheets for all loads in a time period  
**Input:** `{"period": "today|this_week|etc."}`  
**Returns:** Status of bulk generation  
**When to use:** User wants paperwork for multiple loads

#### `generate_timesheet`
**Purpose:** Generate timesheet for a date range  
**Input:** `{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}`  
**Returns:** Excel file path  
**When to use:** End of week timesheet generation

### 📁 File Management Tools

#### `get_paperwork_files` ⭐ NEW
**Purpose:** List all files in a specific week folder  
**Input:** `{"week_ending": "2025-10-27"}` or `{"week_ending": "27-10-25"}`  
**Returns:** List of all files (PDFs, images, Excel) with download URLs  
**When to use:** User wants to see or download existing paperwork  
**Example Output:**
```
📁 Files in 27-10-25 (15 files):

PDFs:
  • $S275052_WBAC_Ashford.pdf (0.85 MB)
    🔗 http://10.10.254.10:5020/api/paperwork/download/27-10-25/$S275052_WBAC_Ashford.pdf
  • $S275053_WBAC_Dover.pdf (0.92 MB)
    🔗 http://10.10.254.10:5020/api/paperwork/download/27-10-25/$S275053_WBAC_Dover.pdf

Images:
  • signature_scan.png (0.15 MB)
    🔗 http://10.10.254.10:5020/api/paperwork/download/27-10-25/signature_scan.png
```

#### `list_paperwork_weeks` ⭐ NEW
**Purpose:** Show all available week folders  
**Input:** None required  
**Returns:** List of week folders with file counts  
**When to use:** User wants to see what paperwork is available  
**Example Output:**
```
📁 Available Paperwork Weeks (4 weeks):
  • 27-10-25: 15 files (12 PDFs)
  • 20-10-25: 18 files (15 PDFs)
  • 13-10-25: 22 files (19 PDFs)
  • 06-10-25: 14 files (11 PDFs)
```

#### `list_available_weeks`
**Purpose:** Get weeks with loads for timesheet generation  
**Input:** None  
**Returns:** Weeks with load data  
**Different from:** `list_paperwork_weeks` (which shows generated files)

### ⏰ Timesheet Management Tools

#### `create_timesheet_entry`
**Purpose:** Add or update a timesheet entry  
**Input:** 
```json
{
  "day_name": "Monday|Tuesday|etc.",
  "start_time": "07:00",
  "finish_time": "17:00",
  "driver": "optional",
  "fleet_reg": "optional"
}
```
**Returns:** Confirmation of entry  
**Smart Features:**
- Auto-calculates week ending date
- Flexible time formats: "7", "07", "7:00", "19:00"
- Handles overnight shifts (e.g., 19:00 to 03:00)

#### `get_timesheet_entries`
**Purpose:** View timesheet entries for a week  
**Input:** `{"week_ending": "YYYY-MM-DD"}`  
**Returns:** All entries for that week  
**When to use:** User wants to review their timesheet

### 🔧 Device Management Tools

#### `get_device_status`
**Purpose:** Check Android device connection status  
**Input:** None  
**Returns:** Status of all configured devices  
**When to use:** Troubleshooting connection issues

#### `pull_latest_data`
**Purpose:** Sync SQL database from Android device  
**Input:** `{"device_index": 1}` (optional)  
**Returns:** Success/failure status  
**When to use:** Before querying loads, if database is stale

#### `connect_devices`
**Purpose:** Attempt to connect to all configured devices  
**Input:** None  
**Returns:** Connection status  
**When to use:** Device appears offline

#### `check_database_freshness`
**Purpose:** Check how old the current database is  
**Input:** None  
**Returns:** Database age and last update time  
**When to use:** Determining if data pull is needed

### 🚗 Vehicle Lookup Tools

#### `lookup_vehicle`
**Purpose:** Get vehicle make/model by registration  
**Input:** `{"registration": "WK67FCX"}`  
**Returns:** Vehicle make and model  
**Data source:** DVLA API + local overrides  
**When to use:** User asks about a specific registration

#### `save_vehicle_override`
**Purpose:** Save custom make/model for a registration  
**Input:** `{"registration": "WK67FCX", "make_model": "Ford Transit"}`  
**When to use:** Correcting incorrect vehicle data

### 📅 Date Management Tools

#### `get_load_date_override`
**Purpose:** Check if a load has a date override  
**Input:** `{"load_number": "$S305187"}`  
**Returns:** Override info if exists  
**When to use:** Checking why a load appears on different date

#### `set_load_date_override`
**Purpose:** Override delivery date for a load  
**Input:** 
```json
{
  "load_number": "$S305187",
  "override_date": "2025-10-24",
  "original_date": "2025-10-25"
}
```
**Returns:** Confirmation  
**Use case:** Grouping loads by different dates for paperwork

#### `delete_load_date_override`
**Purpose:** Remove date override, restore original date  
**Input:** `{"load_number": "$S305187"}`  
**Returns:** Confirmation  
**When to use:** Undoing date override

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

## AI Assistant Best Practices

### 1. Always Provide Download Links
When generating paperwork, ALWAYS extract and present the PDF download URL to the user.

❌ **Bad:** "Loadsheet generated successfully"  
✅ **Good:** "Loadsheet generated successfully! Download your PDF here: http://10.10.254.10:5020/api/paperwork/download/$S275052_WBAC_Ashford.pdf"

### 2. Check Data Freshness
Before searching for "today" or "this week" loads, consider checking database age:
```
If user asks about recent/current loads:
  1. Check database_freshness
  2. If > 1 hour old, suggest pulling latest data
  3. Then search loads
```

### 3. Handle Errors Gracefully
- If load not found: Suggest checking load number or pulling latest data
- If device offline: Provide device status and troubleshooting steps
- If file not found: Use list_paperwork_weeks to show what's available

### 4. Be Proactive with Related Information
When showing load details, mention:
- Vehicle count
- Key locations
- Date
- Whether paperwork exists (check with get_paperwork_files)

### 5. Understand User Intent
- "Show loads" = search and display
- "Generate paperwork" = create PDF + provide download link
- "Get files" = list existing files with download links
- "Check device" = device status

### 6. Use Tool Combinations
**Example - Complete paperwork workflow:**
```
1. search_loads_by_date (find loads)
2. generate_loadsheet for each load
3. get_paperwork_files (confirm all PDFs created)
4. Present all download links to user
```

### 7. Natural Language Date Handling
Support flexible date expressions:
- "today" → search_loads_by_date with "today"
- "this week" → "this_week"
- "last Monday" → calculate date, use specific date
- "next week" → "next_week"

### 8. Timesheet Time Formats
Accept flexible time inputs:
- "7am" → "07:00"
- "7" → "07:00" (assume morning)
- "19" or "7pm" → "19:00"
- "5:30pm" → "17:30"

## Example Complete Workflows

### Workflow 1: Daily Paperwork Generation
```
User: "Generate all paperwork for today"

AI Steps:
1. search_loads_by_date({"period": "today"})
2. For each load found:
   - generate_loadsheet({"load_number": "{load}"})
   - Extract PDF URL from response
3. Compile all PDF URLs
4. Present to user:
   "Generated 5 loadsheets for today:
    - $S275052: [PDF URL]
    - $S275053: [PDF URL]
    ..."
```

### Workflow 2: Weekly Paperwork Review
```
User: "Show me all files from last week"

AI Steps:
1. Calculate last week's Sunday (week ending)
2. list_paperwork_weeks() to verify week exists
3. get_paperwork_files({"week_ending": "DD-MM-YY"})
4. Present organized list:
   "Last week (20-10-25) has 18 files:
    
    PDFs (15):
    - [filename]: [URL]
    ...
    
    Images (3):
    - [filename]: [URL]"
```

### Workflow 3: Timesheet Entry
```
User: "Add my hours for Monday to Friday, 7am to 5pm each day"

AI Steps:
1. For each day (Monday-Friday):
   - create_timesheet_entry({
       "day_name": "{day}",
       "start_time": "07:00",
       "finish_time": "17:00"
     })
2. Confirm all entries created
3. get_timesheet_entries({"week_ending": "{this week}"})
4. Show summary of week's hours
```

### Workflow 4: Load Investigation
```
User: "Tell me everything about load $S275052"

AI Steps:
1. get_load_details({"load_number": "$S275052"})
2. Check for existing paperwork:
   - list_paperwork_weeks()
   - get_paperwork_files() for relevant week
3. Check for date override:
   - get_load_date_override({"load_number": "$S275052"})
4. Present comprehensive information:
   - Collection/delivery points
   - All vehicles
   - Date info (including any overrides)
   - Existing paperwork with download links
```

## Error Handling Guide

### "Database not found"
→ Use `pull_latest_data` to sync from device

### "Load not found"
→ Suggest `pull_latest_data` or verify load number

### "Device offline"
→ Use `get_device_status` and provide troubleshooting

### "Folder not found" (in get_paperwork_files)
→ Use `list_paperwork_weeks` to show available weeks

### "No loads found for period"
→ Suggest different date range or `pull_latest_data`

## Important Notes for AI Assistants

1. **PDF URLs are for downloading** - Present them as clickable links when possible
2. **Folder names use DD-MM-YY format** - Convert from YYYY-MM-DD if needed
3. **Load numbers start with $** - Don't forget the dollar sign (e.g., `$S275052`)
4. **Week ending is always Sunday** - Used for folder/timesheet organization
5. **PDFs are auto-generated** - No separate PDF generation tool needed
6. **Multiple tools can be used together** - Chain tools for complex requests
7. **Time format flexibility** - System handles various time input formats
8. **Date overrides affect paperwork grouping** - Check for overrides when dates seem wrong

## Quick Reference - Most Common Tasks

| User Request | Tool(s) to Use | Key Points |
|--------------|----------------|------------|
| "Show loads today" | search_loads_by_date | Use period="today" |
| "Generate paperwork" | generate_loadsheet | Return PDF URL |
| "Get last week's files" | get_paperwork_files | Calculate week ending |
| "Add timesheet hours" | create_timesheet_entry | Flexible time formats |
| "Check device" | get_device_status | Shows connection status |
| "Pull new data" | pull_latest_data | Syncs from Android |
| "List all weeks" | list_paperwork_weeks | Shows available paperwork |
| "Load details" | get_load_details | Full load information |

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
