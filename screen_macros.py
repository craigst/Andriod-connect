#!/usr/bin/env python3
"""
Screen Macros - Execute automated actions on Android devices
Supports various action types: tap, swipe, text, keyevent, wait, etc.
"""

import subprocess
import time
import json
import sqlite3
from typing import List, Dict, Optional
from pathlib import Path

# Database path
DB_PATH = "data/screen_control.db"


def execute_adb_command(device_address: str, command: List[str]) -> bool:
    """Execute an ADB command on a device"""
    try:
        full_command = ['adb', '-s', device_address] + command
        result = subprocess.run(
            full_command,
            capture_output=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error executing ADB command: {e}")
        return False


def execute_tap(device_address: str, x: int, y: int) -> bool:
    """Execute a tap action at coordinates (x, y)"""
    return execute_adb_command(device_address, ['shell', 'input', 'tap', str(x), str(y)])


def execute_swipe(device_address: str, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
    """Execute a swipe action from (x1, y1) to (x2, y2)"""
    return execute_adb_command(
        device_address, 
        ['shell', 'input', 'swipe', str(x1), str(y1), str(x2), str(y2), str(duration)]
    )


def execute_text(device_address: str, text: str, delay_ms: int = 150) -> bool:
    """
    Execute text input character-by-character with delays
    
    Args:
        device_address: ADB device address
        text: Text to input
        delay_ms: Delay between characters in milliseconds (default: 150ms)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Type each character individually with delay
        for char in text:
            # Handle special characters
            if char == ' ':
                escaped_char = '%s'
            elif char == '&':
                escaped_char = '\\&'
            elif char == '"':
                escaped_char = '\\"'
            elif char == "'":
                escaped_char = "\\'"
            elif char == '`':
                escaped_char = '\\`'
            elif char == '$':
                escaped_char = '\\$'
            elif char == '(':
                escaped_char = '\\('
            elif char == ')':
                escaped_char = '\\)'
            else:
                escaped_char = char
            
            # Send character
            success = execute_adb_command(device_address, ['shell', 'input', 'text', escaped_char])
            
            if not success:
                print(f"Failed to input character: {char}")
                return False
            
            # Delay between characters
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
        
        return True
    except Exception as e:
        print(f"Error executing text input: {e}")
        return False


def execute_text_with_retry(device_address: str, text: str, delay_ms: int = 150, max_retries: int = 2) -> bool:
    """
    Execute text input with retry logic
    
    Args:
        device_address: ADB device address
        text: Text to input
        delay_ms: Delay between characters in milliseconds
        max_retries: Maximum number of retry attempts
    
    Returns:
        True if successful, False otherwise
    """
    for attempt in range(max_retries + 1):
        if execute_text(device_address, text, delay_ms):
            return True
        
        if attempt < max_retries:
            print(f"Text input failed, retrying ({attempt + 1}/{max_retries})...")
            time.sleep(0.5)
    
    print(f"Text input failed after {max_retries + 1} attempts")
    return False


def execute_keyevent(device_address: str, keycode: int) -> bool:
    """Execute a key event"""
    return execute_adb_command(device_address, ['shell', 'input', 'keyevent', str(keycode)])


def execute_long_press(device_address: str, x: int, y: int, duration: int = 2000) -> bool:
    """Execute a long press at coordinates (x, y)"""
    # Long press is a swipe from point to itself with duration
    return execute_swipe(device_address, x, y, x, y, duration)


def execute_back(device_address: str) -> bool:
    """Execute back button"""
    return execute_keyevent(device_address, 4)


def execute_home(device_address: str) -> bool:
    """Execute home button"""
    return execute_keyevent(device_address, 3)


def execute_wait(seconds: float) -> bool:
    """Wait for specified seconds"""
    try:
        time.sleep(seconds)
        return True
    except Exception as e:
        print(f"Error during wait: {e}")
        return False


def get_device_settings(device_address: str) -> Dict:
    """
    Get device settings from database
    
    Args:
        device_address: ADB device address
    
    Returns:
        Dict with device settings or defaults
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT match_threshold, keystroke_delay_ms, post_login_wait_seconds
            FROM device_settings
            WHERE device_address = ?
        """, (device_address,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'match_threshold': row['match_threshold'],
                'keystroke_delay_ms': row['keystroke_delay_ms'],
                'post_login_wait_seconds': row['post_login_wait_seconds']
            }
        else:
            # Return defaults
            return {
                'match_threshold': 0.7,
                'keystroke_delay_ms': 150,
                'post_login_wait_seconds': 4
            }
    except Exception as e:
        print(f"Error getting device settings: {e}")
        # Return defaults on error
        return {
            'match_threshold': 0.7,
            'keystroke_delay_ms': 150,
            'post_login_wait_seconds': 4
        }


def execute_action(device_address: str, action: Dict, device_settings: Dict = None) -> bool:
    """
    Execute a single action
    
    Args:
        device_address: ADB device address
        action: Dict with action type and parameters
        device_settings: Optional device settings dict (will fetch if not provided)
    
    Returns:
        True if successful, False otherwise
    """
    action_type = action.get('type')
    
    # Get device settings if not provided
    if device_settings is None:
        device_settings = get_device_settings(device_address)
    
    if action_type == 'tap':
        return execute_tap(device_address, action['x'], action['y'])
    
    elif action_type == 'swipe':
        duration = action.get('duration', 300)
        return execute_swipe(
            device_address, 
            action['x1'], action['y1'], 
            action['x2'], action['y2'], 
            duration
        )
    
    elif action_type == 'text':
        # Use device-specific keystroke delay
        delay_ms = action.get('delay_ms', device_settings['keystroke_delay_ms'])
        use_retry = action.get('retry', True)
        
        if use_retry:
            return execute_text_with_retry(device_address, action['value'], delay_ms)
        else:
            return execute_text(device_address, action['value'], delay_ms)
    
    elif action_type == 'keyevent':
        return execute_keyevent(device_address, action['code'])
    
    elif action_type == 'long_press':
        duration = action.get('duration', 2000)
        return execute_long_press(device_address, action['x'], action['y'], duration)
    
    elif action_type == 'back':
        return execute_back(device_address)
    
    elif action_type == 'home':
        return execute_home(device_address)
    
    elif action_type == 'wait':
        return execute_wait(action['seconds'])
    
    else:
        print(f"Unknown action type: {action_type}")
        return False


def execute_macro(device_address: str, actions: List[Dict]) -> Dict:
    """
    Execute a sequence of actions (macro)
    
    Args:
        device_address: ADB device address
        actions: List of action dictionaries
    
    Returns:
        Dict with execution results
    """
    results = {
        'success': True,
        'total_actions': len(actions),
        'executed_actions': 0,
        'failed_actions': [],
        'execution_log': []
    }
    
    # Get device settings once for all actions
    device_settings = get_device_settings(device_address)
    
    for i, action in enumerate(actions):
        action_type = action.get('type', 'unknown')
        
        try:
            success = execute_action(device_address, action, device_settings)
            
            if success:
                results['executed_actions'] += 1
                results['execution_log'].append({
                    'step': i + 1,
                    'action': action_type,
                    'status': 'success'
                })
            else:
                results['success'] = False
                results['failed_actions'].append({
                    'step': i + 1,
                    'action': action_type,
                    'error': 'Execution failed'
                })
                results['execution_log'].append({
                    'step': i + 1,
                    'action': action_type,
                    'status': 'failed'
                })
                # Continue executing remaining actions
        except Exception as e:
            results['success'] = False
            results['failed_actions'].append({
                'step': i + 1,
                'action': action_type,
                'error': str(e)
            })
            results['execution_log'].append({
                'step': i + 1,
                'action': action_type,
                'status': 'error',
                'error': str(e)
            })
    
    return results


def save_macro(name: str, description: str, actions: List[Dict]) -> bool:
    """Save a macro to the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Convert actions to JSON
        actions_json = json.dumps(actions)
        
        # Insert or update macro
        cursor.execute("""
            INSERT INTO macros (name, description, actions)
            VALUES (?, ?, ?)
            ON CONFLICT(name) 
            DO UPDATE SET description=?, actions=?, created_at=CURRENT_TIMESTAMP
        """, (name, description, actions_json, description, actions_json))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error saving macro: {e}")
        return False


def get_macro(name: str) -> Optional[Dict]:
    """Get a macro from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, actions, created_at 
            FROM macros 
            WHERE name = ?
        """, (name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'actions': json.loads(row['actions']),
                'created_at': row['created_at']
            }
        return None
    except Exception as e:
        print(f"Error getting macro: {e}")
        return None


def get_macro_by_id(macro_id: int) -> Optional[Dict]:
    """Get a macro by ID from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, actions, created_at 
            FROM macros 
            WHERE id = ?
        """, (macro_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'actions': json.loads(row['actions']),
                'created_at': row['created_at']
            }
        return None
    except Exception as e:
        print(f"Error getting macro by ID: {e}")
        return None


def list_macros() -> List[Dict]:
    """List all macros"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, created_at 
            FROM macros
            ORDER BY name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error listing macros: {e}")
        return []


def delete_macro(name: str) -> bool:
    """Delete a macro"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM macros WHERE name = ?", (name,))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error deleting macro: {e}")
        return False


def link_template_to_macro(template_id: int, macro_id: int) -> bool:
    """Link a template to a macro for auto-execution"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO template_macro_links (template_id, macro_id)
            VALUES (?, ?)
        """, (template_id, macro_id))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error linking template to macro: {e}")
        return False


def unlink_template_from_macro(template_id: int, macro_id: int) -> bool:
    """Unlink a template from a macro"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM template_macro_links 
            WHERE template_id = ? AND macro_id = ?
        """, (template_id, macro_id))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error unlinking template from macro: {e}")
        return False


def get_macros_for_template(template_id: int) -> List[Dict]:
    """Get all macros linked to a template"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.id, m.name, m.description
            FROM macros m
            JOIN template_macro_links tml ON m.id = tml.macro_id
            WHERE tml.template_id = ?
        """, (template_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting macros for template: {e}")
        return []


if __name__ == "__main__":
    # Test the module
    print("Testing screen macros...")
    
    # Create a test macro
    print("\n1. Creating test macro...")
    test_actions = [
        {"type": "tap", "x": 500, "y": 500},
        {"type": "wait", "seconds": 1},
        {"type": "text", "value": "Hello World"},
        {"type": "keyevent", "code": 61},
        {"type": "wait", "seconds": 0.5}
    ]
    
    save_macro("test_macro", "A test macro", test_actions)
    
    # List macros
    print("\n2. Listing all macros...")
    macros = list_macros()
    for macro in macros:
        print(f"   - {macro['name']}: {macro['description']}")
    
    # Get macro
    print("\n3. Getting test macro...")
    macro = get_macro("test_macro")
    if macro:
        print(f"   Name: {macro['name']}")
        print(f"   Description: {macro['description']}")
        print(f"   Actions: {len(macro['actions'])}")
    
    print("\nTest complete!")
