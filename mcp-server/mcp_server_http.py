#!/usr/bin/env python3
"""
MCP Server for Android-Connect - HTTP/SSE Transport
Provides HTTP endpoint for n8n and other HTTP-based MCP clients
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
import uvicorn

# Configuration
FLASK_API_URL = os.getenv("FLASK_API_URL", "http://localhost:5020")
API_TIMEOUT = 30.0
HTTP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("MCP_PORT", "8100"))

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
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return (monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d"))
    
    elif period == "last_week":
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        return (last_monday.strftime("%Y-%m-%d"), last_sunday.strftime("%Y-%m-%d"))
    
    elif period == "next_week":
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
        return (today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))


def format_load_description(load: dict) -> str:
    """Format load data into human-readable description"""
    desc_parts = []
    
    if load.get("collections"):
        col = load["collections"][0]
        location = col.get("location", "Unknown")
        postcode = col.get("postcode", "")
        desc_parts.append(f"FROM {location} ({postcode})")
    
    if load.get("deliveries"):
        deliv = load["deliveries"][0]
        location = deliv.get("location", "Unknown")
        postcode = deliv.get("postcode", "")
        desc_parts.append(f"TO {location} ({postcode})")
    
    veh_count = load.get("total_vehicles", 0)
    desc_parts.append(f"{veh_count} vehicle{'s' if veh_count != 1 else ''}")
    
    date = load.get("earliest_date_formatted", "Unknown date")
    desc_parts.append(f"on {date}")
    
    load_num = load.get("load_number", "Unknown")
    
    return f"{load_num}: {' '.join(desc_parts)}"


# Import all the MCP handlers from the stdio version
# (list_resources, read_resource, list_tools, call_tool)

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


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools - same as stdio version"""
    return [
        Tool(
            name="search_loads_by_date",
            description="Search for loads by date or date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Date period: 'today', 'yesterday', 'this_week', 'last_week', etc."
                    }
                },
                "required": ["period"]
            }
        ),
        Tool(
            name="search_loads_by_location",
            description="Search for loads by location",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location to search for"
                    }
                },
                "required": ["location"]
            }
        ),
        Tool(
            name="get_loads_summary",
            description="Get a summary of all loads",
            inputSchema={
                "type": "object",
                "properties": {
                    "sort": {
                        "type": "string",
                        "enum": ["date_desc", "date_asc", "load_number"]
                    }
                }
            }
        ),
        Tool(
            name="get_load_details",
            description="Get detailed information about a specific load including all vehicles",
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
        Tool(
            name="generate_loadsheet",
            description="Generate loadsheet for a specific load",
            inputSchema={
                "type": "object",
                "properties": {
                    "load_number": {
                        "type": "string"
                    }
                },
                "required": ["load_number"]
            }
        ),
        Tool(
            name="get_device_status",
            description="Get status of all devices",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="pull_latest_data",
            description="Pull latest SQL database from device",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_index": {
                        "type": "integer"
                    }
                }
            }
        ),
        Tool(
            name="get_load_date_override",
            description="Check if a load has a delivery date override set",
            inputSchema={
                "type": "object",
                "properties": {
                    "load_number": {
                        "type": "string",
                        "description": "The load number (e.g., '$S305187')"
                    }
                },
                "required": ["load_number"]
            }
        ),
        Tool(
            name="set_load_date_override",
            description="Override the delivery date for a specific load",
            inputSchema={
                "type": "object",
                "properties": {
                    "load_number": {
                        "type": "string",
                        "description": "The load number (e.g., '$S305187')"
                    },
                    "override_date": {
                        "type": "string",
                        "description": "New delivery date in YYYY-MM-DD format"
                    },
                    "original_date": {
                        "type": "string",
                        "description": "Original delivery date (optional)"
                    }
                },
                "required": ["load_number", "override_date"]
            }
        ),
        Tool(
            name="delete_load_date_override",
            description="Remove a delivery date override from a load",
            inputSchema={
                "type": "object",
                "properties": {
                    "load_number": {
                        "type": "string",
                        "description": "The load number (e.g., '$S305187')"
                    }
                },
                "required": ["load_number"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls - simplified version with key tools"""
    
    if name == "search_loads_by_date":
        period = arguments.get("period", "today")
        result = await api_request("GET", "/api/loads?sort=date_desc")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        loads = result.get("loads", [])
        
        if period in ["today", "yesterday", "this_week", "last_week", "next_week", "this_month"]:
            start_date, end_date = parse_date_range(period)
        else:
            start_date = end_date = period
        
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
        
        response_lines = [f"Found {len(filtered_loads)} load(s) for {period}:\n"]
        for load in filtered_loads:
            response_lines.append(format_load_description(load))
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    elif name == "get_load_details":
        load_number = arguments.get("load_number")
        result = await api_request("GET", "/api/loads")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        loads = result.get("loads", [])
        load = None
        for l in loads:
            if l.get("load_number") == load_number:
                load = l
                break
        
        if not load:
            return [TextContent(type="text", text=f"❌ Load {load_number} not found")]
        
        response_lines = [f"📋 Load Details: {load_number}\n"]
        response_lines.append("=" * 60)
        
        if load.get("collections"):
            response_lines.append("\n🚗 COLLECTION POINTS:")
            for col in load["collections"]:
                response_lines.append(f"  • {col.get('location', 'Unknown')} ({col.get('postcode', '')})")
                response_lines.append(f"    Customer: {col.get('customer', 'Unknown')}")
                response_lines.append(f"    Date: {col.get('date', 'Unknown')}")
        
        if load.get("deliveries"):
            response_lines.append("\n📍 DELIVERY POINTS:")
            for deliv in load["deliveries"]:
                response_lines.append(f"  • {deliv.get('location', 'Unknown')} ({deliv.get('postcode', '')})")
                response_lines.append(f"    Customer: {deliv.get('customer', 'Unknown')}")
        
        if load.get("vehicles"):
            response_lines.append(f"\n🚙 VEHICLES ({load.get('total_vehicles', 0)} total):")
            for idx, veh in enumerate(load["vehicles"], 1):
                ref = veh.get("ref", "Unknown")
                model = veh.get("model", "Unknown")
                color = veh.get("color", "Unknown")
                response_lines.append(f"\n  {idx}. {ref}")
                response_lines.append(f"     {model} - {color}")
        
        response_lines.append("\n" + "=" * 60)
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    elif name == "get_device_status":
        result = await api_request("GET", "/api/devices")
        
        if not result.get("success"):
            return [TextContent(type="text", text=f"Error: {result.get('error')}")]
        
        devices = result.get("devices", [])
        response_lines = ["Device Status:\n"]
        online_count = 0
        
        for device in devices:
            name_str = device.get("name", "Unknown")
            address = device.get("address", "Unknown")
            connected = device.get("connected", False)
            
            if connected:
                online_count += 1
                status = "✅ Online"
            else:
                status = "❌ Offline"
            
            response_lines.append(f"{name_str} ({address}): {status}")
        
        response_lines.insert(1, f"Summary: {online_count}/{len(devices)} device(s) online\n")
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    elif name == "pull_latest_data":
        device_index = arguments.get("device_index")
        payload = {}
        if device_index:
            payload["device_index"] = device_index
        
        result = await api_request("POST", "/api/sql/pull", json=payload)
        
        if result.get("success"):
            return [TextContent(type="text", text=f"✅ SQL database pulled successfully")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "generate_loadsheet":
        load_number = arguments.get("load_number")
        result = await api_request("POST", "/api/paperwork/loadsheet", json={"load_number": load_number})
        
        if result.get("success"):
            return [TextContent(type="text", text=f"✅ Loadsheet generated successfully")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "get_load_date_override":
        load_number = arguments.get("load_number")
        
        result = await api_request("GET", f"/api/loads/{load_number}/date-override")
        
        if result.get("success"):
            if result.get("has_override"):
                override_date = result.get("override_date", "Unknown")
                original_date = result.get("original_date", "Unknown")
                created_at = result.get("created_at", "Unknown")
                
                return [TextContent(
                    type="text",
                    text=f"📅 Date Override Active for {load_number}\n"
                         f"Override Date: {override_date}\n"
                         f"Original Date: {original_date}\n"
                         f"Created: {created_at}"
                )]
            else:
                return [TextContent(type="text", text=f"No date override set for {load_number}")]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "set_load_date_override":
        load_number = arguments.get("load_number")
        override_date = arguments.get("override_date")
        original_date = arguments.get("original_date", "")
        
        payload = {
            "override_date": override_date
        }
        if original_date:
            payload["original_date"] = original_date
        
        result = await api_request(
            "POST",
            f"/api/loads/{load_number}/date-override",
            json=payload
        )
        
        if result.get("success"):
            return [TextContent(
                type="text",
                text=f"✅ Date override set for {load_number}\n"
                     f"Delivery date will be shown as: {override_date}"
            )]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    elif name == "delete_load_date_override":
        load_number = arguments.get("load_number")
        
        result = await api_request("DELETE", f"/api/loads/{load_number}/date-override")
        
        if result.get("success"):
            return [TextContent(
                type="text",
                text=f"✅ Date override removed for {load_number}\n"
                     f"Original delivery date restored"
            )]
        else:
            return [TextContent(type="text", text=f"❌ Error: {result.get('error')}")]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Main entry point for HTTP MCP server"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    import uvicorn
    
    sse = SseServerTransport("/messages")
    
    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send
        ) as streams:
            await app.run(
                streams[0],
                streams[1],
                app.create_initialization_options()
            )
    
    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)
    
    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
    )
    
    config = uvicorn.Config(
        starlette_app,
        host=HTTP_HOST,
        port=HTTP_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    print(f"🚀 MCP HTTP Server starting on http://{HTTP_HOST}:{HTTP_PORT}")
    print(f"📡 SSE endpoint: http://{HTTP_HOST}:{HTTP_PORT}/sse")
    print(f"📨 Messages endpoint: http://{HTTP_HOST}:{HTTP_PORT}/messages")
    print(f"🔗 Connect n8n to: http://<your-ip>:{HTTP_PORT}")
    
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
