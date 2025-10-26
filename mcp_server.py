#!/usr/bin/env python3
"""
MCP Server for Android-Connect Paperwork Automation
Provides AI-friendly tools for managing loads, generating paperwork, and controlling devices
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Optional
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Configuration
FLASK_API_URL = os.getenv("FLASK_API_URL", "http://localhost:5020")
API_TIMEOUT = 30.0

# Initialize MCP server
app = Server("android-paperwork")

# HTTP client for API calls
http_client = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client"""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=API_TIMEOUT)
    return http_client


async def api_request(method: str, endpoint: str, **kwargs) -> dict:
    """Make request to Flask API"""
    client = await get_http_client()
    url = f"{FLASK_API_URL}{endpoint}"
    
    try:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        return {
            "success": False,
            "error": f"API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def parse_date_range(period: str) -> tuple[str, str]:
    """Parse natural language date periods to start/end dates"""
    today = datetime.now().date()
    
    if period == "today":
        return (today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
    
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return (yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d"))
    
    elif period == "this_week":
        # Monday to Sunday of current week
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return (monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d"))
    
    elif period == "last_week":
        # Previous Monday to Sunday
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        return (last_monday.strftime("%Y-%m-%d"), last_sunday.strftime("%Y-%m-%d"))
    
    elif period == "next_week":
        # Next Monday to Sunday
        next_monday = today - timedelta(days=today.weekday()) + timedelta(days=7)
        next_sunday = next_monday + timedelta(days=6)
        return (next_monday.strftime("%Y-%m-%d"), next_sunday.strftime("%Y-%m-%d"))
    
    elif period == "this_month":
        first_day = today.replace(day=1)
        if today.month == 12:
            last_day = today.replace(day=31)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
            last_day = next_month - timedelta(days=1)
        return (first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))
    
    else:
        # Default to today
        return (today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))


def format_load_description(load: dict) -> str:
    """Format load data into human-readable description"""
    desc_parts = []
    
    # Collection info
    if load.get("collections"):
        col = load["collections"][0]
        location = col.get("location", "Unknown")
        postcode = col.get("postcode", "")
        desc_parts.append(f"FROM {location} ({postcode})")
    
    # Delivery info
    if load.get("deliveries"):
        deliv = load["deliveries"][0]
        location = deliv.get("location", "Unknown")
        postcode = deliv.get("postcode", "")
        desc_parts.append(f"TO {location} ({postcode})")
    
    # Vehicle count
    veh_count = load.get("total_vehicles", 0)
    desc_parts.append(f"{veh_count} vehicle{'s' if veh_count != 1 else ''}")
    
    # Date
    date = load.get("earliest_date_formatted", "Unknown date")
    desc_parts.append(f"on {date}")
    
    # Load number
    load_num = load.get("load_number", "Unknown")
    
    return f"{load_num}: {' '.join(desc_parts)}"


# ==================== MCP Resources ====================

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="resource://loads/current",
            name="Current Loads",
            description="All current loads in the database with locations and details",
            mimeType="application/json"
        ),
        Resource(
            uri="resource://devices/status",
            name="Device Status",
            description="Status of all connected Android devices",
            mimeType="application/json"
        ),
        Resource(
            uri="resource://database/info",
            name="Database Information",
            description="Information about the SQL database (age, size, etc.)",
            mimeType="application/json"
        ),
        Resource(
            uri="resource://paperwork/weeks",
            name="Available Weeks",
            description="Weeks with loads available for timesheet generation",
            mimeType="application/json"
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI"""
    
    if uri == "resource://loads/current":
        result = await api_request("GET", "/api/loads")
        if result.get("success"):
            loads = result.get("loads", [])
            formatted = [
                {
                    "description": format_load_description(load),
                    "load_number": load.get("load_number"),
                    "date": load.get("earliest_date_formatted"),
                    "vehicles": load.get("total_vehicles"),
                    "collections": load.get("collections", []),
                    "deliveries": load.get("deliveries", [])
                }
                for load in loads
            ]
            return json.dumps({"loads": formatted}, indent=2)
        return json.dumps({"error": result.get("error")}, indent=2)
    
    elif uri == "resource://devices/status":
        result = await api_request("GET", "/api/devices")
        return json.dumps(result, indent=2)
    
    elif uri == "resource://database/info":
        result = await api_request("GET", "/api/database/info")
        return json.dumps(result, indent=2)
    
    elif uri == "resource://paperwork/weeks":
        result = await api_request("GET", "/api/paperwork/weeks")
        return json.dumps(result, indent=2)
    
    return json.dumps({"error": "Unknown resource"})


# ==================== MCP Tools ====================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        # Search & Discovery
        Tool(
            name="search_loads_by_date",
            description="Search for loads by date or date range. Supports natural language like 'today', 'this_week', 'last_week', or specific dates (YYYY-MM-DD)",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Date period: 'today', 'yesterday', 'this_week', 'last_week', 'next_week', 'this_month', or specific date (YYYY-MM-DD)"
                    }
                },
                "required": ["period"]
            }
        ),
        Tool(
            name="search_loads_by_location",
            description="Search for loads by location (customer name, town, or postcode)",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location to search for (e.g., 'WBAC', 'Ashford', 'TN23')"
                    }
                },
                "required": ["location"]
            }
        ),
        Tool(
            name="get_loads_summary",
            description="Get a summary of all loads with human-readable descriptions",
            inputSchema={
                "type": "object",
                "properties": {
                    "sort": {
                        "type": "string",
                        "description": "Sort order: 'date_desc' (newest first), 'date_asc' (oldest first), or 'load_number'",
                        "enum": ["date_desc", "date_asc", "load_number"]
                    }
                }
            }
        ),
        
        # Paperwork Generation
        Tool(
            name="generate_loadsheet",
            description="Generate loadsheet for a specific load number",
            inputSchema={
                "type": "object",
                "properties": {
                    "load_number": {
                        "type": "string",
                        "description": "The load number (e.g., '$S275052')"
                    }
                },
                "required": ["load_number"]
            }
        ),
        Tool(
            name="generate_all_loadsheets_for_period",
            description="Generate loadsheets for all loads in a time period",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period: 'today', 'this_week', 'last_week', etc."
                    }
                },
                "required": ["period"]
            }
        ),
        Tool(
            name="generate_timesheet",
            description="Generate timesheet for a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    }
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="list_available_weeks",
            description="List weeks with loads available for timesheet generation",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        # Device Management
        Tool(
            name="get_device_status",
            description="Get status of all devices in human-readable format",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="pull_latest_data",
            description="Pull latest SQL database from connected device",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_index": {
                        "type": "integer",
                        "description": "Device index (1-based, optional - uses first available if not specified)"
                    }
                }
            }
        ),
        Tool(
            name="connect_devices",
            description="Connect to all configured Android devices",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="check_database_freshness",
            description="Check how old the current database is",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        # Timesheet Entry Management
        Tool(
            name="create_timesheet_entry",
            description="Create or update a timesheet entry for a specific day",
            inputSchema={
                "type": "object",
                "properties": {
                    "week_ending": {
                        "type": "string",
                        "description": "Week ending date (YYYY-MM-DD, should be a Sunday)"
                    },
                    "day_name": {
                        "type": "string",
                        "description": "Day of week (Monday, Tuesday, etc.)"
                    },
                    "entry_date": {
                        "type": "string",
                        "description": "Entry date (YYYY-MM-DD)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time (HH:MM format)"
                    },
                    "finish_time": {
                        "type": "string",
                        "description": "Finish time (HH:MM format)"
                    },
                    "driver": {
                        "type": "string",
                        "description": "Driver name"
                    },
                    "fleet_reg": {
                        "type": "string",
                        "description": "Fleet registration"
                    }
                },
                "required": ["week_ending", "day_name", "entry_date", "start_time", "finish_time"]
            }
        ),
        Tool(
            name="get_timesheet_entries",
            description="Get timesheet entries for a specific week",
            inputSchema={
                "type": "object",
                "properties": {
                    "week_ending": {
                        "type": "string",
                        "description": "Week ending date (YYYY-MM-DD)"
                    }
                },
                "required": ["week_ending"]
            }
        ),
        
        # Vehicle Lookup
        Tool(
            name="lookup_vehicle",
            description="Look up vehicle make/model by registration number",
            inputSchema={
                "type": "object",
                "properties": {
                    "registration": {
                        "type": "string",
                        "description": "Vehicle registration number"
                    }
                },
                "required": ["registration"]
            }
        ),
        Tool(
            name="save_vehicle_override",
            description="Save custom vehicle make/model override",
            inputSchema={
                "type": "object",
                "properties": {
                    "registration": {
                        "type": "string",
                        "description": "Vehicle registration number"
                    },
                    "make_model": {
                        "type": "string",
                        "description": "Vehicle make and model"
                    }
                },
                "required": ["registration", "make_model"]
            }
        ),
        
        # Load Details
        Tool(
            name="get_load_details",
            description="Get detailed information about a specific load including all vehicles, collection/delivery points, and dates",
            inputSchema={
                "type": "object",
                "properties": {
                    "load_number": {
                        "type": "string",
                        "description": "The load number (e.g., '$S295198')"
                    }
                },
                "required": ["load_number"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    
    # Search & Discovery Tools
    if name == "search_loads_by_date":
        period = arguments.get("period", "today")
        
        # Get all loads
        result = await api_request("GET", "/api/loads?sort=date_desc")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        loads = result.get("loads", [])
        
        # Parse the period
        if period in ["today", "yesterday", "this_week", "last_week", "next_week", "this_month"]:
            start_date, end_date = parse_date_range(period)
        else:
            # Assume it's a specific date
            start_date = end_date = period
        
        # Filter loads by date range
        filtered_loads = []
        for load in loads:
            load_date = load.get("earliest_date_formatted")
            if load_date:
                # Convert DD/MM/YYYY to YYYY-MM-DD for comparison
                try:
                    parts = load_date.split("/")
                    if len(parts) == 3:
                        load_date_iso = f"{parts[2]}-{parts[1]}-{parts[0]}"
                        if start_date <= load_date_iso <= end_date:
                            filtered_loads.append(load)
                except:
                    pass
        
        if not filtered_loads:
            return [TextContent(type="text", text=f"No loads found for {period}")]
        
        # Format response
        response_lines = [f"Found {len(filtered_loads)} load(s) for {period}:\n"]
        for load in filtered_loads:
            response_lines.append(format_load_description(load))
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    elif name == "search_loads_by_location":
        location = arguments.get("location", "").lower()
        
        # Get all loads
        result = await api_request("GET", "/api/loads")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        loads = result.get("loads", [])
        
        # Filter by location
        filtered_loads = []
        for load in loads:
            # Check collections
            for col in load.get("collections", []):
                if (location in col.get("location", "").lower() or
                    location in col.get("customer", "").lower() or
                    location in col.get("town", "").lower() or
                    location in col.get("postcode", "").lower()):
                    filtered_loads.append(load)
                    break
            else:
                # Check deliveries
                for deliv in load.get("deliveries", []):
                    if (location in deliv.get("location", "").lower() or
                        location in deliv.get("customer", "").lower() or
                        location in deliv.get("town", "").lower() or
                        location in deliv.get("postcode", "").lower()):
                        filtered_loads.append(load)
                        break
        
        if not filtered_loads:
            return [TextContent(type="text", text=f"No loads found for location: {location}")]
        
        # Format response
        response_lines = [f"Found {len(filtered_loads)} load(s) for '{location}':\n"]
        for load in filtered_loads:
            response_lines.append(format_load_description(load))
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    elif name == "get_loads_summary":
        sort = arguments.get("sort", "date_desc")
        
        result = await api_request("GET", f"/api/loads?sort={sort}")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        loads = result.get("loads", [])
        total = result.get("total_loads", 0)
        
        if not loads:
            return [TextContent(type="text", text="No loads found in database")]
        
        # Format response
        response_lines = [f"Total: {total} load(s)\n"]
        for load in loads:
            response_lines.append(format_load_description(load))
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    # Paperwork Generation Tools
    elif name == "generate_loadsheet":
        load_number = arguments.get("load_number")
        
        result = await api_request(
            "POST",
            "/api/paperwork/loadsheet",
            json={"load_number": load_number}
        )
        
        if result.get("success"):
            xlsx_path = result.get("xlsx_path", "Unknown")
            return [TextContent(type="text", text=f"✅ Loadsheet generated successfully\nFile: {xlsx_path}")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "generate_all_loadsheets_for_period":
        period = arguments.get("period", "today")
        
        # First, search for loads in the period
        search_result = await call_tool("search_loads_by_date", {"period": period})
        
        # Get all loads
        result = await api_request("GET", "/api/loads?sort=date_desc")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        loads = result.get("loads", [])
        
        # Parse the period
        if period in ["today", "yesterday", "this_week", "last_week", "next_week", "this_month"]:
            start_date, end_date = parse_date_range(period)
        else:
            start_date = end_date = period
        
        # Filter loads by date range
        filtered_loads = []
        for load in loads:
            load_date = load.get("earliest_date_formatted")
            if load_date:
                try:
                    parts = load_date.split("/")
                    if len(parts) == 3:
                        load_date_iso = f"{parts[2]}-{parts[1]}-{parts[0]}"
                        if start_date <= load_date_iso <= end_date:
                            filtered_loads.append(load)
                except:
                    pass
        
        if not filtered_loads:
            return [TextContent(type="text", text=f"No loads found for {period}")]
        
        # Generate loadsheets for each load
        results = []
        success_count = 0
        
        for load in filtered_loads:
            load_num = load.get("load_number")
            gen_result = await api_request(
                "POST",
                "/api/paperwork/loadsheet",
                json={"load_number": load_num}
            )
            
            if gen_result.get("success"):
                success_count += 1
                results.append(f"✅ {load_num}")
            else:
                results.append(f"❌ {load_num}: {gen_result.get('error')}")
        
        response = f"Generated {success_count}/{len(filtered_loads)} loadsheets for {period}:\n\n"
        response += "\n".join(results)
        
        return [TextContent(type="text", text=response)]
    
    elif name == "generate_timesheet":
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        
        result = await api_request(
            "POST",
            "/api/paperwork/timesheet",
            json={"start_date": start_date, "end_date": end_date}
        )
        
        if result.get("success"):
            xlsx_path = result.get("xlsx_path", "Unknown")
            return [TextContent(type="text", text=f"✅ Timesheet generated successfully\nFile: {xlsx_path}")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "list_available_weeks":
        result = await api_request("GET", "/api/paperwork/weeks")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        weeks = result.get("weeks", [])
        
        if not weeks:
            return [TextContent(type="text", text="No weeks with loads found")]
        
        response_lines = ["Available weeks for timesheet generation:\n"]
        for week in weeks:
            monday = week.get("monday")
            sunday = week.get("sunday")
            load_count = week.get("load_count", 0)
            response_lines.append(f"Week {monday} to {sunday}: {load_count} load(s)")
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    # Device Management Tools
    elif name == "get_device_status":
        result = await api_request("GET", "/api/devices")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        devices = result.get("devices", [])
        
        response_lines = ["Device Status:\n"]
        online_count = 0
        
        for device in devices:
            name = device.get("name", "Unknown")
            address = device.get("address", "Unknown")
            connected = device.get("connected", False)
            app_installed = device.get("app_installed", False)
            app_running = device.get("app_running", False)
            
            if connected:
                online_count += 1
                status = "✅ Online"
                if app_installed:
                    status += " | App: Installed"
                    if app_running:
                        status += " (Running)"
                    else:
                        status += " (Not running)"
                else:
                    status += " | App: Not installed"
            else:
                status = "❌ Offline"
            
            response_lines.append(f"{name} ({address}): {status}")
        
        response_lines.insert(1, f"Summary: {online_count}/{len(devices)} device(s) online\n")
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    elif name == "pull_latest_data":
        device_index = arguments.get("device_index")
        
        payload = {}
        if device_index:
            payload["device_index"] = device_index
        
        result = await api_request("POST", "/api/sql/pull", json=payload)
        
        if result.get("success"):
            file_path = result.get("file_path", "Unknown")
            return [TextContent(type="text", text=f"✅ SQL database pulled successfully\nFile: {file_path}")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "connect_devices":
        result = await api_request("POST", "/api/devices/connect")
        
        if result.get("success"):
            return [TextContent(type="text", text="✅ Connection attempted for all devices")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "check_database_freshness":
        result = await api_request("GET", "/api/database/info")
        
        if not result.get("exists", False):
            return [TextContent(type="text", text="❌ Database not found. Pull data from a device first.")]
        
        last_modified = result.get("last_modified_human", "Unknown")
        size_mb = result.get("size_mb", 0)
        
        # Calculate age
        try:
            from datetime import datetime
            last_mod_dt = datetime.fromisoformat(result.get("last_modified"))
            age = datetime.now() - last_mod_dt
            
            if age.days > 0:
                age_str = f"{age.days} day(s) old"
            elif age.seconds > 3600:
                age_str = f"{age.seconds // 3600} hour(s) old"
            elif age.seconds > 60:
                age_str = f"{age.seconds // 60} minute(s) old"
            else:
                age_str = f"{age.seconds} second(s) old"
        except:
            age_str = "Unknown age"
        
        return [TextContent(
            type="text",
            text=f"Database Information:\nLast updated: {last_modified}\nAge: {age_str}\nSize: {size_mb} MB"
        )]
    
    # Timesheet Entry Tools
    elif name == "create_timesheet_entry":
        week_ending = arguments.get("week_ending")
        day_name = arguments.get("day_name")
        entry_date = arguments.get("entry_date")
        start_time = arguments.get("start_time")
        finish_time = arguments.get("finish_time")
        driver = arguments.get("driver", "")
        fleet_reg = arguments.get("fleet_reg", "")
        
        # Calculate total hours
        try:
            from datetime import datetime
            start = datetime.strptime(start_time, "%H:%M")
            finish = datetime.strptime(finish_time, "%H:%M")
            diff = finish - start
            total_hours = diff.total_seconds() / 3600
        except:
            total_hours = 0
        
        entry = {
            "week_ending_date": week_ending,
            "day_name": day_name,
            "entry_date": entry_date,
            "start_time": start_time,
            "finish_time": finish_time,
            "total_hours": str(round(total_hours, 2)),
            "driver": driver,
            "fleet_reg": fleet_reg,
            "start_mileage": "",
            "end_mileage": ""
        }
        
        result = await api_request(
            "POST",
            "/api/timesheet/entries",
            json={"entries": [entry]}
        )
        
        if result.get("success"):
            return [TextContent(
                type="text",
                text=f"✅ Timesheet entry saved for {day_name}\nHours worked: {total_hours:.2f}"
            )]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "get_timesheet_entries":
        week_ending = arguments.get("week_ending")
        
        result = await api_request("GET", f"/api/timesheet/entries?week_ending={week_ending}")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        entries = result.get("entries", [])
        
        if not entries:
            return [TextContent(type="text", text=f"No timesheet entries found for week ending {week_ending}")]
        
        response_lines = [f"Timesheet entries for week ending {week_ending}:\n"]
        total_hours = 0
        
        for entry in entries:
            day = entry.get("day_name", "Unknown")
            start = entry.get("start_time", "")
            finish = entry.get("finish_time", "")
            hours = entry.get("total_hours", "0")
            
            try:
                total_hours += float(hours)
            except:
                pass
            
            response_lines.append(f"{day}: {start} - {finish} ({hours} hours)")
        
        response_lines.append(f"\nTotal hours: {total_hours:.2f}")
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    # Vehicle Lookup Tools
    elif name == "lookup_vehicle":
        registration = arguments.get("registration")
        
        result = await api_request("GET", f"/api/vehicles/lookup/{registration}")
        
        if result.get("success"):
            reg = result.get("registration", "Unknown")
            make_model = result.get("makeModel", "Unknown")
            source = result.get("source", "unknown")
            
            return [TextContent(
                type="text",
                text=f"Vehicle: {reg}\nMake/Model: {make_model}\nSource: {source}"
            )]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "save_vehicle_override":
        registration = arguments.get("registration")
        make_model = arguments.get("make_model")
        
        result = await api_request(
            "POST",
            "/api/vehicles/override",
            json={"registration": registration, "make_model": make_model}
        )
        
        if result.get("success"):
            return [TextContent(type="text", text=f"✅ Vehicle override saved for {registration}")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    # Load Details Tool
    elif name == "get_load_details":
        load_number = arguments.get("load_number")
        
        # Get all loads
        result = await api_request("GET", "/api/loads")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        loads = result.get("loads", [])
        
        # Find the specific load
        load = None
        for l in loads:
            if l.get("load_number") == load_number:
                load = l
                break
        
        if not load:
            return [TextContent(type="text", text=f"❌ Load {load_number} not found")]
        
        # Format detailed load information
        response_lines = [f"📋 Load Details: {load_number}\n"]
        response_lines.append("=" * 60)
        
        # Collections
        if load.get("collections"):
            response_lines.append("\n🚗 COLLECTION POINTS:")
            for col in load["collections"]:
                response_lines.append(f"  • {col.get('location', 'Unknown')} ({col.get('postcode', '')})")
                response_lines.append(f"    Customer: {col.get('customer', 'Unknown')}")
                response_lines.append(f"    Town: {col.get('town', 'Unknown')}")
                response_lines.append(f"    Date: {col.get('date', 'Unknown')} at {col.get('time', 'Unknown')}")
                response_lines.append(f"    Vehicles: {col.get('vehicle_count', 0)}")
        
        # Deliveries
        if load.get("deliveries"):
            response_lines.append("\n📍 DELIVERY POINTS:")
            for deliv in load["deliveries"]:
                response_lines.append(f"  • {deliv.get('location', 'Unknown')} ({deliv.get('postcode', '')})")
                response_lines.append(f"    Customer: {deliv.get('customer', 'Unknown')}")
                response_lines.append(f"    Town: {deliv.get('town', 'Unknown')}")
                response_lines.append(f"    Date: {deliv.get('date', 'Unknown')} at {deliv.get('time', 'Unknown')}")
                response_lines.append(f"    Vehicles: {deliv.get('vehicle_count', 0)}")
        
        # Vehicles
        if load.get("vehicles"):
            response_lines.append(f"\n🚙 VEHICLES ({load.get('total_vehicles', 0)} total):")
            for idx, veh in enumerate(load["vehicles"], 1):
                ref = veh.get("ref", "Unknown")
                model = veh.get("model", "Unknown make/model")
                color = veh.get("color", "Unknown color")
                status = veh.get("status", 0)
                pos = veh.get("position", idx)
                
                # Status indicator
                status_icon = "✅" if status == 1 else "⏳"
                
                response_lines.append(f"\n  {idx}. {status_icon} Position {pos}")
                response_lines.append(f"     Registration: {ref}")
                response_lines.append(f"     Vehicle: {model}")
                response_lines.append(f"     Color: {color}")
        else:
            response_lines.append(f"\n🚙 VEHICLES: No vehicle details available")
        
        response_lines.append("\n" + "=" * 60)
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Main entry point for MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
