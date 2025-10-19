#!/usr/bin/env python3
"""
ADB Device Manager Web Server
Flask-based web interface and REST API for managing ADB devices
Port: 5020
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import subprocess
import os
import sys
import time
import threading
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# Import our ADB manager
from adb_manager import ADBManager, DEVICES, APP_PACKAGE, DATA_FOLDER

# Import screen control modules
import credentials_manager
import screen_detector
import screen_macros
import vehicle_lookup

# Flask app setup
app = Flask(__name__)
CORS(app)

# Configuration
SERVER_PORT = 5020
LOG_FILE = "logs/server.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Global manager instance
adb_manager = ADBManager()

# Auto-refresh settings
auto_refresh_enabled = False
auto_refresh_interval = 600  # 10 minutes in seconds
auto_refresh_thread = None

# Setup logging
os.makedirs("logs", exist_ok=True)

# Create rotating file handler
file_handler = RotatingFileHandler(
    LOG_FILE, 
    maxBytes=LOG_MAX_SIZE, 
    backupCount=LOG_BACKUP_COUNT
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(file_formatter)

# Setup app logger
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
app.logger.addHandler(console_handler)


# ==================== Database Functions ====================

def get_db_path():
    """Get the path to the SQL database"""
    return os.path.join(DATA_FOLDER, "sql.db")


def connect_database():
    """Connect to SQLite database"""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        app.logger.error(f"Database connection error: {e}")
        return None


def format_date(date_str):
    """Convert YYYYMMDD format to DD/MM/YYYY"""
    if date_str and len(str(date_str)) == 8:
        try:
            date_str = str(date_str)
            return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
        except:
            return date_str
    return date_str


def extract_job_data(conn):
    """Extract job data from DWJJOB table"""
    query = """
    SELECT * FROM DWJJOB 
    WHERE dwjLoad IS NOT NULL AND dwjLoad != ''
    ORDER BY dwjLoad, dwjType
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        app.logger.error(f"Error extracting job data: {e}")
        return []


def extract_vehicle_data(conn):
    """Extract vehicle data from DWVVEH table"""
    query = """
    SELECT * FROM DWVVEH 
    WHERE dwvLoad IS NOT NULL AND dwvLoad != ''
    ORDER BY dwvLoad, dwvPos
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        app.logger.error(f"Error extracting vehicle data: {e}")
        return []


def get_load_overview(sort_order='date_desc'):
    """Get overview of all loads in the database
    
    Args:
        sort_order: How to sort loads - 'date_desc' (newest first), 'date_asc' (oldest first), or 'load_number'
    """
    conn = connect_database()
    if not conn:
        return {"error": "Database not found", "loads": []}
    
    try:
        job_data = extract_job_data(conn)
        vehicle_data = extract_vehicle_data(conn)
        
        # Organize by load number
        loads = defaultdict(lambda: {
            'load_number': '',
            'collections': [],
            'deliveries': [],
            'prebook': None,
            'vehicles': [],
            'total_vehicles': 0,
            'earliest_date': None,
            'earliest_date_formatted': None
        })
        
        # Process jobs
        for job in job_data:
            load_num = job['dwjLoad']
            loads[load_num]['load_number'] = load_num
            
            # Track earliest date for sorting
            job_date = job.get('dwjDate')
            if job_date:
                if loads[load_num]['earliest_date'] is None or job_date < loads[load_num]['earliest_date']:
                    loads[load_num]['earliest_date'] = job_date
                    loads[load_num]['earliest_date_formatted'] = format_date(job_date)
            
            job_info = {
                'date': format_date(job.get('dwjDate')),
                'time': job.get('dwjTime'),
                'customer': job.get('dwjCust'),
                'location': job.get('dwjName'),
                'town': job.get('dwjTown'),
                'postcode': job.get('dwjPostco'),
                'vehicle_count': job.get('dwjVehs', 0),
                'address_code': job.get('dwjAdrCod')
            }
            
            if job['dwjType'] == 'C':
                loads[load_num]['collections'].append(job_info)
            elif job['dwjType'] == 'D':
                loads[load_num]['deliveries'].append(job_info)
            elif job['dwjType'] == 'B':
                # PRE-BOOK type
                loads[load_num]['prebook'] = job_info
        
        # Build location mappings for multi-location loads
        location_maps = {}
        for load_num in loads:
            collection_locations = {}
            delivery_locations = {}
            
            # Build location maps from jobs
            for job in job_data:
                if job['dwjLoad'] == load_num:
                    location_key = f"{job.get('dwjCust', '')}_{job.get('dwjAdrCod', '')}"
                    location_name = f"{job.get('dwjName', '')} - {job.get('dwjPostco', '')}"
                    
                    if job['dwjType'] == 'C':
                        collection_locations[location_key] = location_name
                    elif job['dwjType'] == 'D':
                        delivery_locations[location_key] = location_name
            
            location_maps[load_num] = {
                'collections': collection_locations,
                'deliveries': delivery_locations,
                'is_multi_collection': len(collection_locations) > 1,
                'is_multi_delivery': len(delivery_locations) > 1
            }
        
        # Process vehicles
        for vehicle in vehicle_data:
            load_num = vehicle['dwvLoad']
            if load_num in loads:
                # Check for vehicle override
                reg = vehicle.get('dwvVehRef')
                model = vehicle.get('dwvModDes')
                
                if reg:
                    override = vehicle_lookup.get_vehicle_override(reg)
                    if override:
                        model = override['make_model']
                        app.logger.debug(f"Using override for {reg}: {model}")
                
                vehicle_info = {
                    'ref': reg,
                    'model': model,
                    'color': vehicle.get('dwvColDes'),
                    'status': vehicle.get('dwvStatus'),
                    'position': vehicle.get('dwvPos')
                }
                
                # Add location information for multi-location loads
                location_info = []
                loc_map = location_maps.get(load_num, {})
                
                if loc_map.get('is_multi_collection'):
                    col_key = f"{vehicle.get('dwvColCus', '')}_{vehicle.get('dwvColCod', '')}"
                    if col_key in loc_map.get('collections', {}):
                        location_info.append(f"FROM: {loc_map['collections'][col_key]}")
                
                if loc_map.get('is_multi_delivery'):
                    del_key = f"{vehicle.get('dwvDelCus', '')}_{vehicle.get('dwvDelCod', '')}"
                    if del_key in loc_map.get('deliveries', {}):
                        location_info.append(f"TO: {loc_map['deliveries'][del_key]}")
                
                if location_info:
                    vehicle_info['location_info'] = ' | '.join(location_info)
                
                loads[load_num]['vehicles'].append(vehicle_info)
                loads[load_num]['total_vehicles'] = len(loads[load_num]['vehicles'])
        
        # Convert to list and sort
        loads_list = list(loads.values())
        
        # Sort based on requested order
        if sort_order == 'date_desc':
            # Newest first - loads without dates go to the end
            loads_list.sort(key=lambda x: x['earliest_date'] if x['earliest_date'] else 0, reverse=True)
        elif sort_order == 'date_asc':
            # Oldest first - loads without dates go to the end
            loads_list.sort(key=lambda x: x['earliest_date'] if x['earliest_date'] else float('inf'))
        elif sort_order == 'load_number':
            loads_list.sort(key=lambda x: x['load_number'])
        
        result = {
            'total_loads': len(loads),
            'loads': loads_list,
            'last_updated': datetime.now().isoformat(),
            'sort_order': sort_order
        }
        
        return result
        
    except Exception as e:
        app.logger.error(f"Error getting load overview: {e}")
        return {"error": str(e), "loads": []}
    finally:
        conn.close()


# ==================== Auto-Refresh Functionality ====================

def auto_refresh_task():
    """Background task to auto-refresh SQL data"""
    global auto_refresh_enabled
    
    while auto_refresh_enabled:
        try:
            app.logger.info("Auto-refresh: Pulling latest SQL data from devices...")
            available = adb_manager.get_online_devices_with_app()
            
            if available:
                # Pull from first available device
                device = available[0]
                result = device.pull_sql_file()
                if result:
                    app.logger.info(f"Auto-refresh: Successfully updated SQL data from {device.name}")
                else:
                    app.logger.warning(f"Auto-refresh: Failed to pull SQL from {device.name}")
            else:
                app.logger.warning("Auto-refresh: No devices available")
            
        except Exception as e:
            app.logger.error(f"Auto-refresh error: {e}")
        
        # Wait for the interval
        time.sleep(auto_refresh_interval)


def start_auto_refresh():
    """Start the auto-refresh background thread"""
    global auto_refresh_enabled, auto_refresh_thread
    
    if not auto_refresh_enabled:
        auto_refresh_enabled = True
        auto_refresh_thread = threading.Thread(target=auto_refresh_task, daemon=True)
        auto_refresh_thread.start()
        app.logger.info("Auto-refresh started")
        return True
    return False


def stop_auto_refresh():
    """Stop the auto-refresh background thread"""
    global auto_refresh_enabled
    
    if auto_refresh_enabled:
        auto_refresh_enabled = False
        app.logger.info("Auto-refresh stopped")
        return True
    return False


# ==================== API Routes ====================

@app.route('/')
def index():
    """Serve the main web UI"""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'auto_refresh_enabled': auto_refresh_enabled
    })


@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get status of all devices"""
    try:
        adb_manager.refresh_status()
        
        devices = []
        for device in adb_manager.devices:
            devices.append({
                'name': device.name,
                'address': device.address,
                'connected': device.connected,
                'app_installed': device.app_installed,
                'app_running': device.app_running
            })
        
        return jsonify({
            'success': True,
            'devices': devices,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error getting devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/connect', methods=['POST'])
def connect_devices():
    """Connect to all devices"""
    try:
        adb_manager.connect_all()
        adb_manager.refresh_status()
        
        return jsonify({
            'success': True,
            'message': 'Connection attempted for all devices',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error connecting devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/add', methods=['POST'])
def add_device():
    """Add a new device"""
    try:
        data = request.get_json(silent=True) or {}
        ip = data.get('ip')
        port = data.get('port', '5555')
        name = data.get('name')
        
        if not ip or not name:
            return jsonify({
                'success': False,
                'error': 'IP and name are required'
            }), 400
        
        # Import ADBDevice class
        from adb_manager import ADBDevice
        
        # Create new device
        new_device = ADBDevice(ip, port, name)
        adb_manager.devices.append(new_device)
        
        app.logger.info(f"Added device: {name} ({ip}:{port})")
        
        return jsonify({
            'success': True,
            'message': f'Device {name} added successfully',
            'device': {
                'name': new_device.name,
                'address': new_device.address,
                'connected': new_device.connected,
                'app_installed': new_device.app_installed,
                'app_running': new_device.app_running
            }
        })
    except Exception as e:
        app.logger.error(f"Error adding device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/remove', methods=['POST'])
def remove_device():
    """Remove a device"""
    try:
        data = request.get_json(silent=True) or {}
        address = data.get('address')
        
        if not address:
            return jsonify({
                'success': False,
                'error': 'Device address is required'
            }), 400
        
        # Find and remove device
        for i, device in enumerate(adb_manager.devices):
            if device.address == address:
                removed_device = adb_manager.devices.pop(i)
                app.logger.info(f"Removed device: {removed_device.name} ({address})")
                
                return jsonify({
                    'success': True,
                    'message': f'Device {removed_device.name} removed successfully'
                })
        
        return jsonify({
            'success': False,
            'error': 'Device not found'
        }), 404
        
    except Exception as e:
        app.logger.error(f"Error removing device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<path:address>/start', methods=['POST'])
def start_app_on_device(address):
    """Start app on a specific device"""
    try:
        # Find device by address
        device = None
        for d in adb_manager.devices:
            if d.address == address:
                device = d
                break
        
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        # Start the app
        result = device.run_adb_command(['shell', 'am', 'start', '-n', f'{APP_PACKAGE}/com.lansa.ui.Activity'])
        
        if result and result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'App started on {device.name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start app'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error starting app: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<path:address>/stop', methods=['POST'])
def stop_app_on_device(address):
    """Stop app on a specific device"""
    try:
        # Find device by address
        device = None
        for d in adb_manager.devices:
            if d.address == address:
                device = d
                break
        
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        # Stop the app
        result = device.run_adb_command(['shell', 'am', 'force-stop', APP_PACKAGE])
        
        if result and result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'App stopped on {device.name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to stop app'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error stopping app: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<path:address>/reinstall', methods=['POST'])
def reinstall_app_on_device(address):
    """Reinstall app on a specific device"""
    try:
        # Find device by address
        device = None
        device_index = None
        for i, d in enumerate(adb_manager.devices):
            if d.address == address:
                device = d
                device_index = i + 1
                break
        
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        # Reinstall the app
        result = adb_manager.install_app_on_device(device_index, reinstall=True)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'App reinstalled on {device.name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reinstall app'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error reinstalling app: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<path:address>/delete-sql', methods=['POST'])
def delete_sql_on_device(address):
    """Delete SQL database from device app data"""
    try:
        # Find device by address
        device = None
        for d in adb_manager.devices:
            if d.address == address:
                device = d
                break
        
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        # Delete SQL file (now returns a dict with detailed error info)
        result = device.delete_sql_file()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message', f'SQL database deleted from {device.name}'),
                'reason': result.get('reason')
            })
        else:
            # Return detailed error information
            reason = result.get('reason', 'unknown')
            message = result.get('message', 'Failed to delete SQL file')
            
            # Map reasons to HTTP status codes
            status_code = 500
            if reason == 'device_not_connected':
                status_code = 503  # Service Unavailable
            elif reason == 'app_not_installed':
                status_code = 400  # Bad Request
            elif reason == 'app_running':
                status_code = 409  # Conflict
            elif reason == 'file_not_found':
                status_code = 404  # Not Found
            elif reason == 'permission_denied':
                status_code = 403  # Forbidden
            
            return jsonify({
                'success': False,
                'error': message,
                'reason': reason,
                'device': device.name
            }), status_code
            
    except Exception as e:
        app.logger.error(f"Error deleting SQL file: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'reason': 'exception'
        }), 500


@app.route('/api/sql/pull', methods=['POST'])
def pull_sql():
    """Pull SQL file from a device"""
    try:
        # Handle both JSON and no-body requests
        try:
            data = request.get_json(silent=True) or {}
        except:
            data = {}
        
        device_index = data.get('device_index')
        
        if device_index is not None:
            # Pull from specific device
            result = adb_manager.pull_sql_from_device(device_index)
        else:
            # Pull from first available device
            available = adb_manager.get_online_devices_with_app()
            if not available:
                return jsonify({
                    'success': False,
                    'error': 'No devices available with app installed'
                }), 400
            
            result = available[0].pull_sql_file()
        
        if result:
            return jsonify({
                'success': True,
                'message': 'SQL file downloaded successfully',
                'file_path': result,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to download SQL file'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error pulling SQL: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sql/data/dwjjob', methods=['GET'])
def get_dwjjob_data():
    """Get all data from DWJJOB table"""
    try:
        conn = connect_database()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database not found. Please pull SQL file first.'
            }), 404
        
        data = extract_job_data(conn)
        conn.close()
        
        # Format dates
        for row in data:
            if 'dwjDate' in row:
                row['dwjDate_formatted'] = format_date(row['dwjDate'])
        
        return jsonify({
            'success': True,
            'count': len(data),
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error getting DWJJOB data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sql/data/dwvveh', methods=['GET'])
def get_dwvveh_data():
    """Get all data from DWVVEH table"""
    try:
        conn = connect_database()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database not found. Please pull SQL file first.'
            }), 404
        
        data = extract_vehicle_data(conn)
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(data),
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error getting DWVVEH data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/loads', methods=['GET'])
def get_loads():
    """Get load overview with all details
    
    Query Parameters:
        sort: Sort order - 'date_desc' (newest first, default), 'date_asc' (oldest first), or 'load_number'
    """
    try:
        # Get sort parameter from query string, default to date_desc
        sort_order = request.args.get('sort', 'date_desc')
        
        # Validate sort parameter
        valid_sorts = ['date_desc', 'date_asc', 'load_number']
        if sort_order not in valid_sorts:
            sort_order = 'date_desc'
        
        overview = get_load_overview(sort_order)
        
        if 'error' in overview:
            return jsonify({
                'success': False,
                'error': overview['error'],
                'loads': []
            }), 404 if 'not found' in overview['error'] else 500
        
        return jsonify({
            'success': True,
            **overview
        })
        
    except Exception as e:
        app.logger.error(f"Error getting loads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/app/install', methods=['POST'])
def install_app():
    """Install or reinstall app on device(s)"""
    try:
        data = request.json or {}
        device_index = data.get('device_index')
        reinstall = data.get('reinstall', False)
        all_devices = data.get('all_devices', False)
        
        if all_devices:
            adb_manager.install_app_on_all(reinstall)
            return jsonify({
                'success': True,
                'message': 'App installation initiated on all connected devices'
            })
        elif device_index is not None:
            result = adb_manager.install_app_on_device(device_index, reinstall)
            return jsonify({
                'success': result,
                'message': 'App installed successfully' if result else 'App installation failed'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Please specify device_index or all_devices'
            }), 400
            
    except Exception as e:
        app.logger.error(f"Error installing app: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-refresh', methods=['GET', 'POST'])
def auto_refresh_control():
    """Control auto-refresh functionality"""
    global auto_refresh_interval
    
    if request.method == 'GET':
        return jsonify({
            'enabled': auto_refresh_enabled,
            'interval_seconds': auto_refresh_interval,
            'interval_minutes': auto_refresh_interval // 60
        })
    
    elif request.method == 'POST':
        try:
            data = request.json or {}
            enable = data.get('enable', False)
            interval = data.get('interval_minutes')
            
            if interval is not None and interval > 0:
                auto_refresh_interval = interval * 60
            
            if enable:
                start_auto_refresh()
                return jsonify({
                    'success': True,
                    'enabled': True,
                    'message': f'Auto-refresh enabled (every {auto_refresh_interval // 60} minutes)'
                })
            else:
                stop_auto_refresh()
                return jsonify({
                    'success': True,
                    'enabled': False,
                    'message': 'Auto-refresh disabled'
                })
                
        except Exception as e:
            app.logger.error(f"Error controlling auto-refresh: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/database/info', methods=['GET'])
def database_info():
    """Get database file information"""
    try:
        db_path = get_db_path()
        
        if not os.path.exists(db_path):
            return jsonify({
                'exists': False,
                'message': 'Database file not found. Please pull SQL file from a device.'
            })
        
        file_size = os.path.getsize(db_path)
        modified_time = datetime.fromtimestamp(os.path.getmtime(db_path))
        
        return jsonify({
            'exists': True,
            'path': db_path,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'last_modified': modified_time.isoformat(),
            'last_modified_human': modified_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        app.logger.error(f"Error getting database info: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== Paperwork Generation Routes ====================

@app.route('/api/paperwork/loadsheet', methods=['POST'])
def generate_loadsheet():
    """Generate loadsheet for a specific load"""
    try:
        data = request.get_json(silent=True) or {}
        load_number = data.get('load_number')
        
        if not load_number:
            return jsonify({
                'success': False,
                'error': 'Load number is required'
            }), 400
        
        # Get database connection
        conn = connect_database()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database not found. Please pull SQL file first.'
            }), 404
        
        # Extract job and vehicle data for this load
        jobs = extract_job_data(conn)
        vehicles = extract_vehicle_data(conn)
        conn.close()
        
        # Filter for this load number
        load_jobs = [j for j in jobs if j.get('dwjLoad') == load_number]
        load_vehicles = [v for v in vehicles if v.get('dwvLoad') == load_number]
        
        if not load_jobs:
            return jsonify({
                'success': False,
                'error': f'Load {load_number} not found in database'
            }), 404
        
        # Enrich vehicle data with overrides
        for vehicle in load_vehicles:
            reg = vehicle.get('dwvVehRef')
            if reg:
                override = vehicle_lookup.get_vehicle_override(reg)
                if override:
                    vehicle['dwvModDes'] = override['make_model']
                    app.logger.info(f"Applied override for {reg}: {override['make_model']}")
        
        # Convert keys to lowercase and ensure dates are strings for script compatibility
        def convert_for_script(d):
            converted = {}
            for k, v in d.items():
                key = k.lower()
                # Convert date integers to strings
                if key == 'dwjdate' and isinstance(v, int):
                    converted[key] = str(v)
                else:
                    converted[key] = v
            return converted
        
        # Build JSON data for loadsheet script
        json_data = {
            'data': [convert_for_script(j) for j in load_jobs] + [convert_for_script(v) for v in load_vehicles]
        }
        
        # Execute loadsheet script
        import json as json_lib
        script_path = os.path.join(os.getcwd(), 'scripts', 'loadsheet.py')
        
        result = subprocess.run(
            ['python3', script_path, json_lib.dumps(json_data)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            output = json_lib.loads(result.stdout)
            if output.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Loadsheet generated successfully',
                    'xlsx_path': output.get('excel_path'),
                    'load_number': load_number
                })
            else:
                return jsonify({
                    'success': False,
                    'error': output.get('error', 'Unknown error')
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'Script execution failed: {result.stderr}'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error generating loadsheet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/paperwork/timesheet', methods=['POST'])
def generate_timesheet():
    """Generate timesheet for a date range"""
    try:
        data = request.get_json(silent=True) or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'error': 'Start date and end date are required'
            }), 400
        
        # Get database connection
        conn = connect_database()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database not found. Please pull SQL file first.'
            }), 404
        
        # Extract all data
        jobs = extract_job_data(conn)
        vehicles = extract_vehicle_data(conn)
        conn.close()
        
        # Filter jobs by date range (convert dates for comparison)
        from datetime import datetime as dt
        start_dt = dt.strptime(start_date, '%Y-%m-%d')
        end_dt = dt.strptime(end_date, '%Y-%m-%d')
        
        filtered_jobs = []
        for job in jobs:
            if job.get('dwjDate'):
                try:
                    job_date = dt.strptime(str(job['dwjDate']), '%Y%m%d')
                    if start_dt <= job_date <= end_dt:
                        filtered_jobs.append(job)
                except:
                    pass
        
        # Get timesheet entries from screen_control.db for this week
        time_entries = []
        try:
            control_conn = sqlite3.connect('data/screen_control.db')
            control_conn.row_factory = sqlite3.Row
            cursor = control_conn.cursor()
            
            # Calculate week ending date (Sunday) from end_date
            days_to_sunday = 6 - end_dt.weekday()
            week_end = end_dt + timedelta(days=days_to_sunday)
            week_ending_str = week_end.strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT * FROM timesheet_entries
                WHERE week_ending_date = ?
                ORDER BY 
                    CASE day_name
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END
            """, (week_ending_str,))
            
            rows = cursor.fetchall()
            control_conn.close()
            
            # Convert to format expected by timesheet script
            for row in rows:
                time_entries.append({
                    'date': row['entry_date'] or '',
                    'day': row['day_name'] or '',
                    'start_time': row['start_time'] or '',
                    'finsh_time': row['finish_time'] or '',  # Note: typo in script
                    'total_hours': row['total_hours'] or '',
                    'driver': row['driver'] or '',
                    'fleet_reg': row['fleet_reg'] or '',
                    'start_mileage': row.get('start_mileage') or '',
                    'end_mileage': row.get('end_mileage') or ''
                })
            
            app.logger.info(f"Found {len(time_entries)} timesheet entries for week ending {week_ending_str}")
        except Exception as e:
            app.logger.warning(f"Could not fetch timesheet entries: {e}")
        
        # Convert keys to lowercase and ensure dates are strings for script compatibility
        def convert_for_script(d):
            converted = {}
            for k, v in d.items():
                key = k.lower()
                # Convert date integers to strings
                if key == 'dwjdate' and isinstance(v, int):
                    converted[key] = str(v)
                else:
                    converted[key] = v
            return converted
        
        # Build JSON data for timesheet script (include both jobs and time entries)
        json_data = {
            'data': [convert_for_script(j) for j in filtered_jobs] + time_entries
        }
        
        # Execute timesheet script
        import json as json_lib
        script_path = os.path.join(os.getcwd(), 'scripts', 'timesheet.py')
        
        result = subprocess.run(
            ['python3', script_path, json_lib.dumps(json_data)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            output = json_lib.loads(result.stdout)
            if output.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Timesheet generated successfully',
                    'xlsx_path': output.get('excel_path')
                })
            else:
                return jsonify({
                    'success': False,
                    'error': output.get('error', 'Unknown error')
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'Script execution failed: {result.stderr}'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error generating timesheet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/paperwork/weeks', methods=['GET'])
def get_paperwork_weeks():
    """Get available weeks with loads"""
    try:
        conn = connect_database()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database not found',
                'weeks': []
            }), 404
        
        jobs = extract_job_data(conn)
        conn.close()
        
        from datetime import datetime as dt, timedelta
        
        # Extract unique week endings and track unique loads per week
        weeks = {}
        for job in jobs:
            if job.get('dwjDate') and job.get('dwjLoad'):
                try:
                    job_date = dt.strptime(str(job['dwjDate']), '%Y%m%d')
                    # Calculate week ending (Sunday) - UK work week is Monday to Sunday
                    days_to_sunday = 6 - job_date.weekday()
                    week_end = job_date + timedelta(days=days_to_sunday)
                    week_start = week_end - timedelta(days=6)
                    
                    week_key = week_end.strftime('%Y-%m-%d')
                    if week_key not in weeks:
                        weeks[week_key] = {
                            'week_ending': week_key,
                            'monday': week_start.strftime('%Y-%m-%d'),
                            'sunday': week_end.strftime('%Y-%m-%d'),
                            'loads': set()  # Track unique load numbers
                        }
                    # Add the unique load number to the set
                    weeks[week_key]['loads'].add(job['dwjLoad'])
                except:
                    pass
        
        # Convert sets to counts
        for week_data in weeks.values():
            week_data['load_count'] = len(week_data['loads'])
            del week_data['loads']  # Remove the set from output
        
        # Sort by week ending (newest first)
        sorted_weeks = sorted(weeks.values(), key=lambda x: x['week_ending'], reverse=True)
        
        return jsonify({
            'success': True,
            'weeks': sorted_weeks
        })
        
    except Exception as e:
        app.logger.error(f"Error getting weeks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/paperwork/exists/<load_number>', methods=['GET'])
def check_loadsheet_exists(load_number):
    """Check if loadsheet exists for a load"""
    try:
        paperwork_dir = 'paperwork'
        
        # Search for loadsheet file
        for root, dirs, files in os.walk(paperwork_dir):
            for file in files:
                if file.startswith(load_number) and file.endswith('.xlsx'):
                    return jsonify({
                        'success': True,
                        'exists': True,
                        'xlsx_path': os.path.join(root, file)
                    })
        
        return jsonify({
            'success': True,
            'exists': False
        })
        
    except Exception as e:
        app.logger.error(f"Error checking loadsheet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/paperwork/download/<path:filename>', methods=['GET'])
def download_paperwork(filename):
    """Download a paperwork file"""
    try:
        paperwork_dir = 'paperwork'
        
        # Determine requested file type
        requested_type = None
        if filename.endswith('.pdf'):
            requested_type = '.pdf'
            base_filename = filename.replace('.pdf', '')
        elif filename.endswith('.xlsx'):
            requested_type = '.xlsx'
            base_filename = filename.replace('.xlsx', '')
        else:
            base_filename = filename
        
        # Search for files starting with the load number
        for root, dirs, files in os.walk(paperwork_dir):
            for file in files:
                # Match if the file starts with the base filename
                if file.startswith(base_filename):
                    # If a specific type was requested, only match that type
                    if requested_type:
                        if file.endswith(requested_type):
                            return send_file(
                                os.path.join(root, file),
                                as_attachment=True,
                                download_name=file
                            )
                    # Otherwise match any valid type (.xlsx or .pdf)
                    elif file.endswith('.xlsx') or file.endswith('.pdf'):
                        return send_file(
                            os.path.join(root, file),
                            as_attachment=True,
                            download_name=file
                        )
        
        # Direct file path (fallback)
        if os.path.exists(filename):
            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename)
            )
        
        return jsonify({
            'success': False,
            'error': 'File not found'
        }), 404
        
    except Exception as e:
        app.logger.error(f"Error downloading paperwork: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Screen Control API Routes ====================

# Screenshot Management
@app.route('/api/devices/<path:address>/screenshot', methods=['GET'])
def capture_screenshot(address):
    """Capture screenshot from device"""
    try:
        screenshot_path = screen_detector.capture_screenshot(address)
        
        if not screenshot_path:
            return jsonify({
                'success': False,
                'error': 'Failed to capture screenshot'
            }), 500
        
        # Get base64 image for web display
        base64_image = screen_detector.get_screenshot_as_base64(screenshot_path)
        
        return jsonify({
            'success': True,
            'screenshot_path': screenshot_path,
            'screenshot_base64': base64_image,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error capturing screenshot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/devices/<path:address>/current-screen', methods=['GET'])
def detect_screen(address):
    """Detect current screen on device"""
    try:
        # First capture screenshot
        screenshot_path = screen_detector.capture_screenshot(address)
        
        if not screenshot_path:
            return jsonify({
                'success': False,
                'error': 'Failed to capture screenshot'
            }), 500
        
        # Detect screen
        result = screen_detector.detect_current_screen(screenshot_path)
        
        if result['success'] and result.get('screen'):
            # Get linked macros for detected screen
            macros = screen_macros.get_macros_for_template(result['template_id'])
            result['linked_macros'] = macros
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error detecting screen: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Credentials Management
@app.route('/api/devices/<path:address>/credentials', methods=['GET', 'POST', 'DELETE'])
def manage_credentials(address):
    """Manage device credentials"""
    try:
        if request.method == 'GET':
            creds = credentials_manager.get_credentials(address)
            if creds:
                return jsonify({
                    'success': True,
                    'username': creds['username'],
                    'has_password': True
                })
            else:
                return jsonify({
                    'success': True,
                    'has_credentials': False
                })
        
        elif request.method == 'POST':
            data = request.get_json(silent=True) or {}
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({
                    'success': False,
                    'error': 'Username and password are required'
                }), 400
            
            result = credentials_manager.store_credentials(address, username, password)
            
            if result:
                return jsonify({
                    'success': True,
                    'message': 'Credentials saved successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to save credentials'
                }), 500
        
        elif request.method == 'DELETE':
            result = credentials_manager.delete_credentials(address)
            
            if result:
                return jsonify({
                    'success': True,
                    'message': 'Credentials deleted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to delete credentials'
                }), 500
    except Exception as e:
        app.logger.error(f"Error managing credentials: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Template Management
@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List all screen templates"""
    try:
        templates = screen_detector.load_templates_from_db()
        
        # Get linked macros for each template
        for template in templates:
            template['linked_macros'] = screen_macros.get_macros_for_template(template['id'])
        
        return jsonify({
            'success': True,
            'templates': templates
        })
    except Exception as e:
        app.logger.error(f"Error listing templates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/templates/<int:template_id>/test', methods=['POST'])
def test_template(template_id):
    """Test template against current screenshot"""
    try:
        data = request.get_json(silent=True) or {}
        device_address = data.get('device_address')
        
        if not device_address:
            return jsonify({
                'success': False,
                'error': 'Device address is required'
            }), 400
        
        # Capture screenshot
        screenshot_path = screen_detector.capture_screenshot(device_address)
        
        if not screenshot_path:
            return jsonify({
                'success': False,
                'error': 'Failed to capture screenshot'
            }), 500
        
        # Detect screen
        result = screen_detector.detect_current_screen(screenshot_path)
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error testing template: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Macro Management
@app.route('/api/macros', methods=['GET', 'POST'])
def manage_macros():
    """List or create macros"""
    try:
        if request.method == 'GET':
            macros = screen_macros.list_macros()
            
            return jsonify({
                'success': True,
                'macros': macros
            })
        
        elif request.method == 'POST':
            data = request.get_json(silent=True) or {}
            name = data.get('name')
            description = data.get('description', '')
            actions = data.get('actions', [])
            
            if not name or not actions:
                return jsonify({
                    'success': False,
                    'error': 'Name and actions are required'
                }), 400
            
            result = screen_macros.save_macro(name, description, actions)
            
            if result:
                return jsonify({
                    'success': True,
                    'message': f'Macro "{name}" saved successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to save macro'
                }), 500
    except Exception as e:
        app.logger.error(f"Error managing macros: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/macros/<int:macro_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_macro(macro_id):
    """Get, update, or delete a specific macro"""
    try:
        if request.method == 'GET':
            macro = screen_macros.get_macro_by_id(macro_id)
            
            if macro:
                return jsonify({
                    'success': True,
                    'macro': macro
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Macro not found'
                }), 404
        
        elif request.method == 'PUT':
            data = request.get_json(silent=True) or {}
            name = data.get('name')
            description = data.get('description', '')
            actions = data.get('actions', [])
            
            if not name or not actions:
                return jsonify({
                    'success': False,
                    'error': 'Name and actions are required'
                }), 400
            
            result = screen_macros.save_macro(name, description, actions)
            
            if result:
                return jsonify({
                    'success': True,
                    'message': f'Macro "{name}" updated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update macro'
                }), 500
        
        elif request.method == 'DELETE':
            # Get macro name first
            macro = screen_macros.get_macro_by_id(macro_id)
            if not macro:
                return jsonify({
                    'success': False,
                    'error': 'Macro not found'
                }), 404
            
            result = screen_macros.delete_macro(macro['name'])
            
            if result:
                return jsonify({
                    'success': True,
                    'message': 'Macro deleted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to delete macro'
                }), 500
    except Exception as e:
        app.logger.error(f"Error managing macro: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/macros/<int:macro_id>/execute', methods=['POST'])
def execute_macro(macro_id):
    """Execute a macro on a device"""
    try:
        data = request.get_json(silent=True) or {}
        device_address = data.get('device_address')
        
        if not device_address:
            return jsonify({
                'success': False,
                'error': 'Device address is required'
            }), 400
        
        # Get macro
        macro = screen_macros.get_macro_by_id(macro_id)
        
        if not macro:
            return jsonify({
                'success': False,
                'error': 'Macro not found'
            }), 404
        
        # Execute macro
        result = screen_macros.execute_macro(device_address, macro['actions'])
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error executing macro: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Template-Macro Links
@app.route('/api/templates/<int:template_id>/link-macro/<int:macro_id>', methods=['POST', 'DELETE'])
def manage_template_macro_link(template_id, macro_id):
    """Link or unlink template to macro"""
    try:
        if request.method == 'POST':
            result = screen_macros.link_template_to_macro(template_id, macro_id)
            
            if result:
                return jsonify({
                    'success': True,
                    'message': 'Template linked to macro successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to link template to macro'
                }), 500
        
        elif request.method == 'DELETE':
            result = screen_macros.unlink_template_from_macro(template_id, macro_id)
            
            if result:
                return jsonify({
                    'success': True,
                    'message': 'Template unlinked from macro successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to unlink template from macro'
                }), 500
    except Exception as e:
        app.logger.error(f"Error managing template-macro link: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Auto-Login
@app.route('/api/devices/<path:address>/auto-login', methods=['POST'])
def auto_login(address):
    """Execute auto-login on device"""
    try:
        # Get credentials
        creds = credentials_manager.get_credentials(address)
        
        if not creds:
            return jsonify({
                'success': False,
                'error': 'No credentials found for this device'
            }), 404
        
        # Build login macro actions
        login_actions = [
            {"type": "keyevent", "code": 61},  # TAB to username
            {"type": "text", "value": creds['username']},
            {"type": "keyevent", "code": 61},  # TAB to password
            {"type": "text", "value": creds['password']},
            {"type": "tap", "x": 702, "y": 1311},  # Login button
            {"type": "wait", "seconds": 2}
        ]
        
        # Execute login macro
        result = screen_macros.execute_macro(address, login_actions)
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error during auto-login: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Vehicle Lookup API Routes ====================

@app.route('/api/vehicles/lookup/<registration>', methods=['GET'])
def lookup_vehicle_registration(registration):
    """Lookup vehicle make/model by registration"""
    try:
        result = vehicle_lookup.lookup_vehicle(registration)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error'],
                'registration': result.get('registration')
            }), 404
        
        # Check for existing override
        override_data = vehicle_lookup.get_vehicle_override(result.get('registration', registration))
        
        # Always try to get motorcheck data for comparison
        motorcheck_result = None
        if result.get('source') == 'motorcheck':
            motorcheck_result = result.get('makeModel')
        elif result.get('source') == 'override':
            # If we have an override, still try to fetch motorcheck data
            clean_reg = vehicle_lookup.normalize_registration(registration)
            motorcheck_data = vehicle_lookup.scrape_motorcheck(clean_reg)
            if motorcheck_data:
                motorcheck_result = motorcheck_data.get('makeModel')
        
        response = {
            'success': True,
            'registration': result.get('registration'),
            'makeModel': result.get('makeModel'),
            'source': result.get('source', 'unknown')
        }
        
        # Add motorcheck result if available
        if motorcheck_result:
            response['motorcheck'] = {
                'makeModel': motorcheck_result
            }
        
        # Add override data if exists
        if override_data:
            response['override'] = {
                'make_model': override_data['make_model'],
                'created_at': override_data['created_date'],
                'last_used': override_data.get('last_used_date')
            }
        
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error looking up vehicle: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vehicles/override', methods=['POST'])
def save_vehicle_override():
    """Save vehicle make/model override"""
    try:
        data = request.get_json(silent=True) or {}
        registration = data.get('registration')
        make_model = data.get('make_model')
        
        if not registration or not make_model:
            return jsonify({
                'success': False,
                'error': 'Registration and make_model are required'
            }), 400
        
        result = vehicle_lookup.save_vehicle_override(registration, make_model)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Vehicle override saved successfully',
                'registration': registration,
                'make_model': make_model
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save vehicle override'
            }), 500
    except Exception as e:
        app.logger.error(f"Error saving vehicle override: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vehicles/cleanup', methods=['POST'])
def cleanup_vehicle_overrides():
    """Cleanup old vehicle overrides (>14 days)"""
    try:
        deleted_count = vehicle_lookup.cleanup_old_overrides(days=14)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} old vehicle overrides',
            'deleted_count': deleted_count
        })
    except Exception as e:
        app.logger.error(f"Error cleaning up overrides: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Timesheet Entry API Routes ====================

@app.route('/api/timesheet/entries', methods=['GET', 'POST'])
def manage_timesheet_entries():
    """Get or save timesheet entries"""
    try:
        if request.method == 'GET':
            week_ending = request.args.get('week_ending')
            
            if not week_ending:
                return jsonify({
                    'success': False,
                    'error': 'week_ending parameter is required'
                }), 400
            
            conn = sqlite3.connect('data/screen_control.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM timesheet_entries
                WHERE week_ending_date = ?
                ORDER BY 
                    CASE day_name
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END
            """, (week_ending,))
            
            rows = cursor.fetchall()
            conn.close()
            
            entries = [dict(row) for row in rows]
            
            return jsonify({
                'success': True,
                'entries': entries,
                'week_ending': week_ending
            })
        
        elif request.method == 'POST':
            data = request.get_json(silent=True) or {}
            entries = data.get('entries', [])
            
            if not entries:
                return jsonify({
                    'success': False,
                    'error': 'No entries provided'
                }), 400
            
            conn = sqlite3.connect('data/screen_control.db')
            cursor = conn.cursor()
            
            for entry in entries:
                cursor.execute("""
                    INSERT INTO timesheet_entries 
                    (week_ending_date, day_name, entry_date, start_time, finish_time, 
                     total_hours, driver, fleet_reg, start_mileage, end_mileage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(week_ending_date, day_name) DO UPDATE SET
                        entry_date = excluded.entry_date,
                        start_time = excluded.start_time,
                        finish_time = excluded.finish_time,
                        total_hours = excluded.total_hours,
                        driver = excluded.driver,
                        fleet_reg = excluded.fleet_reg,
                        start_mileage = excluded.start_mileage,
                        end_mileage = excluded.end_mileage
                """, (
                    entry.get('week_ending_date'),
                    entry.get('day_name'),
                    entry.get('entry_date'),
                    entry.get('start_time'),
                    entry.get('finish_time'),
                    entry.get('total_hours'),
                    entry.get('driver'),
                    entry.get('fleet_reg'),
                    entry.get('start_mileage'),
                    entry.get('end_mileage')
                ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Saved {len(entries)} timesheet entries'
            })
    except Exception as e:
        app.logger.error(f"Error managing timesheet entries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/timesheet/entries/<int:entry_id>', methods=['DELETE'])
def delete_timesheet_entry(entry_id):
    """Delete a timesheet entry"""
    try:
        conn = sqlite3.connect('data/screen_control.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM timesheet_entries WHERE id = ?", (entry_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Timesheet entry deleted successfully'
        })
    except Exception as e:
        app.logger.error(f"Error deleting timesheet entry: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/timesheet/calculate-total', methods=['GET'])
def calculate_weekly_total():
    """Calculate total hours for a week"""
    try:
        week_ending = request.args.get('week_ending')
        
        if not week_ending:
            return jsonify({
                'success': False,
                'error': 'week_ending parameter is required'
            }), 400
        
        conn = sqlite3.connect('data/screen_control.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(CAST(total_hours AS REAL)) as total
            FROM timesheet_entries
            WHERE week_ending_date = ? AND total_hours IS NOT NULL AND total_hours != ''
        """, (week_ending,))
        
        result = cursor.fetchone()
        conn.close()
        
        total = result[0] if result and result[0] else 0
        
        return jsonify({
            'success': True,
            'total_hours': round(total, 2),
            'week_ending': week_ending
        })
    except Exception as e:
        app.logger.error(f"Error calculating weekly total: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


# ==================== Main ====================

if __name__ == '__main__':
    app.logger.info(f"Starting ADB Device Manager Web Server on port {SERVER_PORT}")
    app.logger.info(f"Logs will be written to {LOG_FILE}")
    app.logger.info(f"Log rotation: max {LOG_MAX_SIZE / (1024*1024)}MB per file, {LOG_BACKUP_COUNT} backups")
    
    # Create necessary directories
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    
    # Auto-connect to all configured devices on startup
    app.logger.info("Auto-connecting to configured devices...")
    try:
        adb_manager.connect_all()
        adb_manager.refresh_status()
        
        connected_count = sum(1 for d in adb_manager.devices if d.connected)
        app.logger.info(f"Auto-connect complete: {connected_count}/{len(adb_manager.devices)} devices connected")
        
        for device in adb_manager.devices:
            if device.connected:
                app.logger.info(f"  ✓ {device.name} ({device.address}) - Connected")
            else:
                app.logger.warning(f"  ✗ {device.name} ({device.address}) - Connection failed")
    except Exception as e:
        app.logger.error(f"Error during auto-connect: {e}")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=SERVER_PORT,
        debug=False,
        threaded=True
    )
