#!/usr/bin/env python3
"""
ADB Device Manager - Terminal Interface
Manages multiple Android devices, checks app status, and retrieves SQL files
"""

import subprocess
import os
import sys
import time
import hashlib
import shutil
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# Configuration
DEVICES = [
    {"ip": "127.0.0.1", "port": "5555", "name": "Local Device"},
    {"ip": "10.10.254.62", "port": "5555", "name": "Device 1"},
    {"ip": "10.10.254.13", "port": "5555", "name": "Device 2"}
]

APP_PACKAGE = "com.bca.bcatrack"
APK_FOLDER = "apk"
APK_FILENAME = "BCAApp.apk"
APK_DOWNLOAD_URL = "https://nc.evoonline.co.uk/index.php/s/gWgDSy5nYZnygcC/download"
APK_EXPECTED_SHA1 = "e37b6394bd95bf792c02de6b792ab2558a381548"
DATA_FOLDER = "data"
DEVICE_SQL_FILE = "/data/data/com.bca.bcatrack/cache/cache/data/sql.db"
TEMP_SQL_FILE = "/sdcard/sql.db"


def _compute_sha1(file_path):
    """Return the SHA1 hex digest for the given file."""
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha1.update(chunk)
    return sha1.hexdigest()


def _download_apk(destination, url=APK_DOWNLOAD_URL, expected_sha1=APK_EXPECTED_SHA1):
    """Download the APK from the shared Nextcloud link."""
    temp_path = None
    try:
        with urllib.request.urlopen(url, timeout=60) as response, tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
            temp_path = tmp_file.name

        if expected_sha1:
            downloaded_sha1 = _compute_sha1(temp_path)
            if downloaded_sha1.lower() != expected_sha1.lower():
                print(f"❌ Downloaded APK failed checksum validation (expected {expected_sha1}, got {downloaded_sha1})")
                os.remove(temp_path)
                return False

        os.makedirs(os.path.dirname(destination), exist_ok=True)
        os.replace(temp_path, destination)
        print(f"✅ Downloaded APK to {destination}")
        return True

    except urllib.error.URLError as error:
        print(f"❌ Failed to download APK (network error): {error.reason or error}")
    except Exception as exc:
        print(f"❌ Failed to download APK: {exc}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    return False


class ADBDevice:
    """Represents a single ADB device"""
    
    def __init__(self, ip, port, name):
        self.ip = ip
        self.port = port
        self.name = name
        self.address = f"{ip}:{port}"
        self.connected = False
        self.app_installed = False
        self.app_running = False
        self.slave_mode = False
        
    def run_adb_command(self, command, timeout=10):
        """Execute ADB command for this device"""
        full_command = ["adb", "-s", self.address] + command
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"⚠️  Command timed out for {self.name}")
            return None
        except Exception as e:
            print(f"⚠️  Error executing command for {self.name}: {e}")
            return None
    
    def connect(self):
        """Connect to the device"""
        print(f"🔌 Connecting to {self.name} ({self.address})...")
        result = subprocess.run(
            ["adb", "connect", self.address],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "connected" in result.stdout.lower():
            self.connected = True
            print(f"✅ {self.name} connected")
            return True
        else:
            self.connected = False
            print(f"❌ {self.name} connection failed")
            return False
    
    def check_connection(self):
        """Check if device is still connected"""
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        self.connected = self.address in result.stdout
        return self.connected
    
    def check_app_installed(self):
        """Check if the app is installed"""
        if not self.connected:
            return False
        
        result = self.run_adb_command(["shell", "pm", "list", "packages"])
        if result and result.returncode == 0:
            self.app_installed = APP_PACKAGE in result.stdout
            return self.app_installed
        
        self.app_installed = False
        return False
    
    def check_app_running(self):
        """Check if the app is currently running"""
        if not self.connected:
            return False
        
        result = self.run_adb_command(["shell", "pidof", APP_PACKAGE])
        if result and result.returncode == 0 and result.stdout.strip():
            self.app_running = True
            return True
        
        self.app_running = False
        return False
    
    def get_app_status(self):
        """Get comprehensive app status"""
        if not self.connected:
            return "disconnected"
        
        if not self.check_app_installed():
            return "not_installed"
        
        if not self.check_app_running():
            return "installed_not_running"
        
        return "running"
    
    def install_app(self, apk_path, reinstall=False):
        """Install or reinstall the app"""
        if not self.connected:
            print(f"❌ {self.name} is not connected")
            return False
        
        if not os.path.exists(apk_path):
            print(f"❌ APK file not found: {apk_path}")
            return False
        
        print(f"📦 Installing app on {self.name}...")
        
        try:
            # If reinstall, uninstall first to clear all app data
            if reinstall and self.app_installed:
                print(f"🗑️  Uninstalling existing app first...")
                if not self.uninstall_app():
                    print(f"⚠️  Warning: Uninstall failed, attempting fresh install anyway")
                time.sleep(2)  # Wait for uninstall to complete
            
            # Install the app
            result = subprocess.run(
                ["adb", "-s", self.address, "install", apk_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and "Success" in result.stdout:
                print(f"✅ App installed successfully on {self.name}")
                self.app_installed = True
                
                # If reinstall, start the app after installation
                if reinstall:
                    print(f"🚀 Starting BCA app...")
                    time.sleep(2)  # Wait for installation to settle
                    start_result = self.run_adb_command(
                        ['shell', 'am', 'start', '-n', f'{APP_PACKAGE}/com.lansa.ui.Activity']
                    )
                    if start_result and start_result.returncode == 0:
                        print(f"✅ BCA app started on {self.name}")
                    else:
                        print(f"⚠️  Warning: Failed to start app automatically")
                
                return True
            else:
                print(f"❌ Installation failed on {self.name}")
                if result.stderr:
                    print(f"   Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Installation timed out on {self.name}")
            return False
        except Exception as e:
            print(f"❌ Error installing app on {self.name}: {e}")
            return False
    
    def uninstall_app(self):
        """Uninstall the app"""
        if not self.connected:
            print(f"❌ {self.name} is not connected")
            return False
        
        if not self.app_installed:
            print(f"ℹ️  App not installed on {self.name}")
            return True
        
        print(f"🗑️  Uninstalling app from {self.name}...")
        
        try:
            result = subprocess.run(
                ["adb", "-s", self.address, "uninstall", APP_PACKAGE],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and "Success" in result.stdout:
                print(f"✅ App uninstalled from {self.name}")
                self.app_installed = False
                return True
            else:
                print(f"❌ Uninstallation failed on {self.name}")
                return False
                
        except Exception as e:
            print(f"❌ Error uninstalling app from {self.name}: {e}")
            return False
    
    def stop_app(self):
        """Stop the BCA app"""
        if not self.connected:
            print(f"❌ {self.name} is not connected")
            return False
        
        if not self.app_installed:
            print(f"❌ App not installed on {self.name}")
            return False
        
        print(f"🛑 Stopping BCA app on {self.name}...")
        
        try:
            result = self.run_adb_command(['shell', 'am', 'force-stop', APP_PACKAGE])
            
            if result and result.returncode == 0:
                print(f"✅ App stopped on {self.name}")
                self.app_running = False
                return True
            else:
                print(f"❌ Failed to stop app on {self.name}")
                return False
        except Exception as e:
            print(f"❌ Error stopping app on {self.name}: {e}")
            return False
    
    def start_app(self):
        """Start the BCA app"""
        if not self.connected:
            print(f"❌ {self.name} is not connected")
            return False
        
        if not self.app_installed:
            print(f"❌ App not installed on {self.name}")
            return False
        
        print(f"🚀 Starting BCA app on {self.name}...")
        
        try:
            result = self.run_adb_command(
                ['shell', 'am', 'start', '-n', f'{APP_PACKAGE}/com.lansa.ui.Activity']
            )
            
            if result and result.returncode == 0:
                print(f"✅ App started on {self.name}")
                self.app_running = True
                return True
            else:
                print(f"❌ Failed to start app on {self.name}")
                return False
        except Exception as e:
            print(f"❌ Error starting app on {self.name}: {e}")
            return False
    
    def delete_sql_file(self):
        """Delete SQL database from device app data (forces app to download new DB on next start)"""
        if not self.connected:
            print(f"❌ {self.name} is not connected")
            return {"success": False, "reason": "device_not_connected", "message": "Device is not connected"}
        
        if not self.app_installed:
            print(f"❌ App not installed on {self.name}")
            return {"success": False, "reason": "app_not_installed", "message": "App is not installed on device"}
        
        # Check if app is running - MUST be stopped to delete SQL
        if self.check_app_running():
            print(f"❌ App is currently running on {self.name}")
            print(f"   Please stop the app before deleting SQL database")
            return {"success": False, "reason": "app_running", "message": "App must be stopped before deleting SQL database"}
        
        print(f"🗑️  Deleting SQL database from {self.name}...")
        print(f"   Device: {self.address}, Connected: {self.connected}, App installed: {self.app_installed}, App running: {self.app_running}")
        
        try:
            # First, check if file exists
            print(f"  → Checking if file exists: {DEVICE_SQL_FILE}")
            check_result = self.run_adb_command(
                ['shell', 'su', '0', 'ls', '-la', DEVICE_SQL_FILE],
                timeout=10
            )
            
            if check_result and check_result.returncode != 0:
                print(f"ℹ️  SQL file does not exist or already deleted")
                return {"success": False, "reason": "file_not_found", "message": "SQL database file not found (may already be deleted)"}
            
            print(f"  → File exists, proceeding with deletion")
            
            # Delete the file
            print(f"  → Deleting file: {DEVICE_SQL_FILE}")
            result = self.run_adb_command(
                ['shell', 'su', '0', 'rm', '-f', DEVICE_SQL_FILE],
                timeout=15
            )
            
            print(f"  → Command result: returncode={result.returncode if result else 'None'}")
            print(f"  → stdout: {result.stdout if result else 'None'}")
            print(f"  → stderr: {result.stderr if result else 'None'}")
            
            if result and result.returncode == 0:
                # Verify deletion
                verify_result = self.run_adb_command(
                    ['shell', 'su', '0', 'ls', '-la', DEVICE_SQL_FILE],
                    timeout=10
                )
                
                if verify_result and verify_result.returncode != 0:
                    print(f"✅ SQL database deleted from {self.name}")
                    print(f"   App will download fresh database on next start")
                    return {"success": True, "reason": "deleted", "message": "SQL database deleted successfully"}
                else:
                    print(f"⚠️  Delete command succeeded but file still exists")
                    return {"success": False, "reason": "delete_failed", "message": "File deletion failed - file still exists"}
            
            # Check for specific error conditions
            error_msg = result.stderr if result and result.stderr else ""
            
            if "Permission denied" in error_msg or "permission denied" in error_msg.lower():
                print(f"❌ Permission denied - root access required")
                return {"success": False, "reason": "permission_denied", "message": "Permission denied - device may not be rooted or root access denied"}
            
            if "Read-only file system" in error_msg:
                print(f"❌ Read-only file system")
                return {"success": False, "reason": "readonly_filesystem", "message": "Cannot delete - file system is read-only"}
            
            if "No such file or directory" in error_msg:
                print(f"ℹ️  File not found")
                return {"success": False, "reason": "file_not_found", "message": "SQL database file not found"}
            
            # Generic error
            print(f"❌ Failed to delete SQL file")
            print(f"   Return code: {result.returncode if result else 'None'}")
            print(f"   Error: {error_msg if error_msg else 'Unknown error'}")
            return {"success": False, "reason": "unknown_error", "message": f"Failed to delete SQL file: {error_msg or 'Unknown error'}"}
            
        except Exception as e:
            print(f"❌ Error deleting SQL file: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "reason": "exception", "message": f"Exception occurred: {str(e)}"}
    
    def pull_sql_file(self):
        """Pull SQL database from device"""
        if not self.connected:
            print(f"❌ {self.name} is not connected")
            return False
        
        if not self.app_installed:
            print(f"❌ App not installed on {self.name}")
            return False
        
        # Create data folder if it doesn't exist
        os.makedirs(DATA_FOLDER, exist_ok=True)
        
        # Always use same filename - overwrites previous version (keeps only latest)
        local_file = os.path.join(DATA_FOLDER, "sql.db")
        
        print(f"📥 Pulling SQL file from {self.name}...")
        print(f"  → Overwriting existing database with latest data")
        
        try:
            # Step 1: Copy protected file to accessible location (requires root)
            print(f"  → Copying file on device...")
            result = self.run_adb_command(
                ["shell", "su", "0", "cp", DEVICE_SQL_FILE, TEMP_SQL_FILE],
                timeout=15
            )
            
            if not result or result.returncode != 0:
                print(f"❌ Failed to copy SQL file on device (root access required)")
                return False
            
            # Step 2: Pull file to local machine
            print(f"  → Downloading to {local_file}...")
            result = subprocess.run(
                ["adb", "-s", self.address, "pull", TEMP_SQL_FILE, local_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"❌ Failed to download SQL file")
                return False
            
            # Step 3: Clean up temp file on device
            self.run_adb_command(["shell", "rm", TEMP_SQL_FILE])
            
            # Verify file was downloaded
            if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
                file_size = os.path.getsize(local_file)
                print(f"✅ SQL file downloaded successfully ({file_size:,} bytes)")
                print(f"📁 Saved to: {local_file}")
                return local_file
            else:
                print(f"❌ Downloaded file is empty or missing")
                return False
                
        except Exception as e:
            print(f"❌ Error pulling SQL file: {e}")
            return False
    
    def enable_slave_mode(self):
        """
        Enable slave mode - keeps device awake with screen off
        Device can be controlled remotely without user interaction
        """
        if not self.connected:
            print(f"❌ {self.name} is not connected")
            return False
        
        print(f"🔒 Enabling slave mode on {self.name}...")
        
        try:
            # Step 1: Disable screen timeout (set to max value)
            print(f"  → Disabling screen timeout...")
            result = self.run_adb_command(
                ['shell', 'settings', 'put', 'system', 'screen_off_timeout', '2147483647'],
                timeout=10
            )
            
            if not result or result.returncode != 0:
                print(f"⚠️  Warning: Failed to set screen timeout")
            
            # Step 2: Enable stay-on while charging/USB
            print(f"  → Enabling stay awake mode...")
            result = self.run_adb_command(
                ['shell', 'svc', 'power', 'stayon', 'true'],
                timeout=10
            )
            
            if not result or result.returncode != 0:
                print(f"⚠️  Warning: Failed to enable stay awake")
            
            # Step 3: Turn screen off (but device stays awake)
            print(f"  → Turning screen off...")
            result = self.run_adb_command(
                ['shell', 'input', 'keyevent', '26'],
                timeout=10
            )
            
            if not result or result.returncode != 0:
                print(f"⚠️  Warning: Failed to turn screen off")
            
            self.slave_mode = True
            print(f"✅ Slave mode enabled on {self.name}")
            print(f"   Device is now controlled (screen off, won't sleep)")
            return True
            
        except Exception as e:
            print(f"❌ Error enabling slave mode: {e}")
            return False
    
    def disable_slave_mode(self):
        """
        Disable slave mode - restore normal power settings
        """
        if not self.connected:
            print(f"❌ {self.name} is not connected")
            return False
        
        print(f"🔓 Disabling slave mode on {self.name}...")
        
        try:
            # Step 1: Restore screen timeout (60 seconds)
            print(f"  → Restoring screen timeout...")
            result = self.run_adb_command(
                ['shell', 'settings', 'put', 'system', 'screen_off_timeout', '60000'],
                timeout=10
            )
            
            if not result or result.returncode != 0:
                print(f"⚠️  Warning: Failed to restore screen timeout")
            
            # Step 2: Disable stay-on
            print(f"  → Disabling stay awake mode...")
            result = self.run_adb_command(
                ['shell', 'svc', 'power', 'stayon', 'false'],
                timeout=10
            )
            
            if not result or result.returncode != 0:
                print(f"⚠️  Warning: Failed to disable stay awake")
            
            # Step 3: Wake screen (turn it back on)
            print(f"  → Waking screen...")
            result = self.run_adb_command(
                ['shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'],
                timeout=10
            )
            
            if not result or result.returncode != 0:
                print(f"⚠️  Warning: Failed to wake screen")
            
            self.slave_mode = False
            print(f"✅ Slave mode disabled on {self.name}")
            print(f"   Device restored to normal mode")
            return True
            
        except Exception as e:
            print(f"❌ Error disabling slave mode: {e}")
            return False
    
    def get_slave_mode_status(self):
        """
        Check if slave mode is enabled
        
        Returns:
            Dict with status information
        """
        if not self.connected:
            return {
                'enabled': False,
                'reason': 'disconnected'
            }
        
        try:
            # Check screen timeout setting
            result = self.run_adb_command(
                ['shell', 'settings', 'get', 'system', 'screen_off_timeout'],
                timeout=5
            )
            
            timeout_value = None
            if result and result.returncode == 0:
                try:
                    timeout_value = int(result.stdout.strip())
                except ValueError:
                    pass
            
            # Check stay awake setting
            result = self.run_adb_command(
                ['shell', 'settings', 'get', 'global', 'stay_on_while_plugged_in'],
                timeout=5
            )
            
            stay_awake = False
            if result and result.returncode == 0:
                try:
                    stay_awake_value = int(result.stdout.strip())
                    stay_awake = stay_awake_value > 0
                except ValueError:
                    pass
            
            # Consider slave mode enabled if timeout is very high (> 1 hour)
            enabled = timeout_value is not None and timeout_value > 3600000
            
            return {
                'enabled': enabled,
                'screen_timeout': timeout_value,
                'stay_awake': stay_awake
            }
            
        except Exception as e:
            print(f"❌ Error checking slave mode status: {e}")
            return {
                'enabled': False,
                'reason': 'error',
                'error': str(e)
            }
    
    def wake_screen(self):
        """Wake the device screen"""
        if not self.connected:
            return False
        
        try:
            result = self.run_adb_command(
                ['shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'],
                timeout=5
            )
            return result and result.returncode == 0
        except Exception as e:
            print(f"❌ Error waking screen: {e}")
            return False
    
    def sleep_screen(self):
        """Turn off the device screen (while keeping device awake in slave mode)"""
        if not self.connected:
            return False
        
        try:
            result = self.run_adb_command(
                ['shell', 'input', 'keyevent', '26'],
                timeout=5
            )
            return result and result.returncode == 0
        except Exception as e:
            print(f"❌ Error sleeping screen: {e}")
            return False


class ADBManager:
    """Manages multiple ADB devices"""
    
    def __init__(self):
        self.devices = [ADBDevice(d["ip"], d["port"], d["name"]) for d in DEVICES]
        
    def check_adb_installed(self):
        """Check if ADB is installed"""
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def connect_all(self):
        """Connect to all configured devices"""
        print("\n" + "="*60)
        print("🔌 CONNECTING TO DEVICES")
        print("="*60)
        
        for device in self.devices:
            device.connect()
            time.sleep(0.5)
        
        print()
    
    def refresh_status(self):
        """Refresh status for all devices"""
        for device in self.devices:
            device.check_connection()
            if device.connected:
                device.check_app_installed()
                device.check_app_running()
    
    def show_devices(self):
        """Display all devices and their status"""
        print("\n" + "="*60)
        print("📱 DEVICE STATUS")
        print("="*60)
        
        self.refresh_status()
        
        for i, device in enumerate(self.devices, 1):
            print(f"\n{device.name} ({device.address})")
            print("-" * 40)
            
            if not device.connected:
                print("  Status: ❌ OFFLINE")
            else:
                print("  Status: ✅ ONLINE")
                
                if device.app_installed:
                    print(f"  App:    ✅ Installed")
                    
                    if device.app_running:
                        print(f"  Running: ✅ YES")
                    else:
                        print(f"  Running: ⚠️  NO")
                else:
                    print(f"  App:    ❌ Not Installed")
        
        print()
    
    def get_online_devices_with_app(self):
        """Get list of devices that are online with app installed"""
        self.refresh_status()
        return [d for d in self.devices if d.connected and d.app_installed]
    
    def pull_sql_from_device(self, device_index):
        """Pull SQL file from a specific device"""
        if device_index < 1 or device_index > len(self.devices):
            print(f"❌ Invalid device number")
            return False
        
        device = self.devices[device_index - 1]
        return device.pull_sql_file()
    
    def pull_sql_from_all(self):
        """Pull SQL files from all available devices"""
        available = self.get_online_devices_with_app()
        
        if not available:
            print("❌ No devices available with app installed")
            return
        
        print("\n" + "="*60)
        print("📥 PULLING SQL FILES FROM ALL DEVICES")
        print("="*60 + "\n")
        
        for device in available:
            device.pull_sql_file()
            print()
    
    def get_apk_path(self):
        """Get the APK file path"""
        os.makedirs(APK_FOLDER, exist_ok=True)
        apk_path = os.path.join(APK_FOLDER, APK_FILENAME)

        if os.path.exists(apk_path):
            if os.path.getsize(apk_path) == 0:
                print(f"⚠️  Found empty APK file at {apk_path}, re-downloading...")
                os.remove(apk_path)
            elif APK_EXPECTED_SHA1:
                existing_sha1 = _compute_sha1(apk_path)
                if existing_sha1.lower() == APK_EXPECTED_SHA1.lower():
                    return apk_path
                print("⚠️  Existing APK checksum mismatch; downloading a fresh copy...")
                os.remove(apk_path)
            else:
                return apk_path

        print(f"🌐 Downloading {APK_FILENAME} from shared storage...")
        if _download_apk(apk_path):
            return apk_path

        print(f"❌ Unable to obtain {APK_FILENAME}. Download it manually from {APK_DOWNLOAD_URL} and place it in '{APK_FOLDER}/'.")
        return None
    
    def install_app_on_device(self, device_index, reinstall=False):
        """Install app on a specific device"""
        if device_index < 1 or device_index > len(self.devices):
            print(f"❌ Invalid device number")
            return False
        
        device = self.devices[device_index - 1]
        apk_path = self.get_apk_path()
        
        if not apk_path or not os.path.exists(apk_path):
            print(f"❌ APK file not available for installation.")
            return False
        
        return device.install_app(apk_path, reinstall)
    
    def install_app_on_all(self, reinstall=False):
        """Install app on all connected devices"""
        apk_path = self.get_apk_path()
        
        if not apk_path or not os.path.exists(apk_path):
            print(f"❌ APK file not available for installation.")
            return
        
        connected = [d for d in self.devices if d.connected]
        
        if not connected:
            print("❌ No devices connected")
            return
        
        print("\n" + "="*60)
        action = "REINSTALLING" if reinstall else "INSTALLING"
        print(f"📦 {action} APP ON ALL DEVICES")
        print("="*60 + "\n")
        
        for device in connected:
            device.install_app(apk_path, reinstall)
            print()
    
    def uninstall_app_from_device(self, device_index):
        """Uninstall app from a specific device"""
        if device_index < 1 or device_index > len(self.devices):
            print(f"❌ Invalid device number")
            return False
        
        device = self.devices[device_index - 1]
        return device.uninstall_app()


def show_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("🤖 ADB DEVICE MANAGER")
    print("="*60)
    print("\n1. Connect to all devices")
    print("2. Show device status")
    print("3. Pull SQL from specific device")
    print("4. Pull SQL from all devices")
    print("5. Install/Reinstall app on device")
    print("6. Install/Reinstall app on all devices")
    print("7. Uninstall app from device")
    print("8. Refresh device status")
    print("0. Exit")
    print("\n" + "="*60)


def main():
    """Main program loop"""
    
    # Check if ADB is installed
    manager = ADBManager()
    
    if not manager.check_adb_installed():
        print("❌ ADB is not installed or not in PATH")
        print("Please install ADB and try again")
        sys.exit(1)
    
    print("\n✅ ADB is installed and ready")
    
    while True:
        show_menu()
        
        try:
            choice = input("\nEnter choice: ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye!")
                break
            
            elif choice == "1":
                manager.connect_all()
            
            elif choice == "2":
                manager.show_devices()
            
            elif choice == "3":
                manager.show_devices()
                available = manager.get_online_devices_with_app()
                
                if not available:
                    print("\n❌ No devices available with app installed")
                    continue
                
                print("\nAvailable devices:")
                for i, device in enumerate(available, 1):
                    print(f"  {i}. {device.name} ({device.address})")
                
                try:
                    device_choice = int(input("\nSelect device number: ").strip())
                    if 1 <= device_choice <= len(available):
                        available[device_choice - 1].pull_sql_file()
                    else:
                        print("❌ Invalid device number")
                except ValueError:
                    print("❌ Please enter a valid number")
            
            elif choice == "4":
                manager.pull_sql_from_all()
            
            elif choice == "5":
                manager.show_devices()
                connected = [d for d in manager.devices if d.connected]
                
                if not connected:
                    print("\n❌ No devices connected")
                    continue
                
                print("\nConnected devices:")
                for i, device in enumerate(connected, 1):
                    status = "✅ Installed" if device.app_installed else "❌ Not installed"
                    print(f"  {manager.devices.index(device) + 1}. {device.name} ({device.address}) - App: {status}")
                
                try:
                    device_choice = int(input("\nSelect device number: ").strip())
                    reinstall = input("Reinstall (keep data)? (y/n): ").strip().lower() == 'y'
                    manager.install_app_on_device(device_choice, reinstall)
                except ValueError:
                    print("❌ Please enter a valid number")
            
            elif choice == "6":
                reinstall = input("\nReinstall (keep data)? (y/n): ").strip().lower() == 'y'
                manager.install_app_on_all(reinstall)
            
            elif choice == "7":
                manager.show_devices()
                available = [d for d in manager.devices if d.connected and d.app_installed]
                
                if not available:
                    print("\n❌ No devices with app installed")
                    continue
                
                print("\nDevices with app installed:")
                for i, device in enumerate(available, 1):
                    print(f"  {manager.devices.index(device) + 1}. {device.name} ({device.address})")
                
                try:
                    device_choice = int(input("\nSelect device number: ").strip())
                    manager.uninstall_app_from_device(device_choice)
                except ValueError:
                    print("❌ Please enter a valid number")
            
            elif choice == "8":
                print("\n🔄 Refreshing device status...")
                manager.refresh_status()
                manager.show_devices()
            
            else:
                print("❌ Invalid choice")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
