#!/usr/bin/env python3
"""
Screen Detector - OpenCV-based template matching for Android screen detection
Detects which screen the BCA app is currently displaying
"""

import cv2
import numpy as np
import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Database and templates path
DB_PATH = "data/screen_control.db"
TEMPLATES_DIR = "screen_templates"
SCREENSHOTS_DIR = "screenshots"


def get_device_resolution(device_address: str) -> Optional[Tuple[int, int]]:
    """
    Get device screen resolution via ADB
    
    Args:
        device_address: ADB device address
    
    Returns:
        Tuple of (width, height) or None if failed
    """
    try:
        import subprocess
        
        result = subprocess.run(
            ['adb', '-s', device_address, 'shell', 'wm', 'size'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Output format: "Physical size: 1440x2560"
            output = result.stdout.strip()
            if 'Physical size:' in output:
                size_str = output.split('Physical size:')[1].strip()
                width, height = map(int, size_str.split('x'))
                return (width, height)
        
        return None
    except Exception as e:
        print(f"Error getting device resolution: {e}")
        return None


def load_templates_from_db() -> List[Dict]:
    """Load template definitions from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, filename, confidence_threshold, priority 
            FROM screen_templates
            ORDER BY priority DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        templates = []
        for row in rows:
            template_path = os.path.join(TEMPLATES_DIR, row['filename'])
            if os.path.exists(template_path):
                templates.append({
                    'id': row['id'],
                    'name': row['name'],
                    'filename': row['filename'],
                    'path': template_path,
                    'threshold': row['confidence_threshold'],
                    'priority': row['priority']
                })
        
        return templates
    except Exception as e:
        print(f"Error loading templates from database: {e}")
        return []


def match_template(screenshot_path: str, template_path: str, threshold: float = 0.7) -> Optional[Dict]:
    """
    Match a template against a screenshot using OpenCV
    
    Args:
        screenshot_path: Path to screenshot image
        template_path: Path to template image
        threshold: Confidence threshold (0.0-1.0)
    
    Returns:
        Dict with match info or None if no match
    """
    try:
        # Load images
        screenshot = cv2.imread(screenshot_path)
        template = cv2.imread(template_path)
        
        if screenshot is None or template is None:
            return None
        
        # Convert to grayscale
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # Get best match
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Check if match exceeds threshold
        if max_val >= threshold:
            template_h, template_w = template_gray.shape
            return {
                'confidence': float(max_val),
                'location': {
                    'x': int(max_loc[0]),
                    'y': int(max_loc[1]),
                    'width': int(template_w),
                    'height': int(template_h)
                },
                'matched': True,
                'scale': 1.0
            }
        else:
            return {
                'confidence': float(max_val),
                'matched': False,
                'scale': 1.0
            }
    except Exception as e:
        print(f"Error matching template: {e}")
        return None


def match_template_multiscale(screenshot_path: str, template_path: str, threshold: float = 0.7, 
                               scales: List[float] = None) -> Optional[Dict]:
    """
    Match a template against a screenshot using multi-scale template matching
    
    Args:
        screenshot_path: Path to screenshot image
        template_path: Path to template image
        threshold: Confidence threshold (0.0-1.0)
        scales: List of scales to try (default: [0.8, 0.9, 1.0, 1.1, 1.2])
    
    Returns:
        Dict with best match info or None if no match
    """
    if scales is None:
        scales = [0.8, 0.9, 1.0, 1.1, 1.2]
    
    try:
        # Load images
        screenshot = cv2.imread(screenshot_path)
        template_orig = cv2.imread(template_path)
        
        if screenshot is None or template_orig is None:
            return None
        
        # Convert screenshot to grayscale once
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        best_match = None
        best_confidence = 0.0
        
        # Try each scale
        for scale in scales:
            # Scale template
            template_h, template_w = template_orig.shape[:2]
            new_h, new_w = int(template_h * scale), int(template_w * scale)
            
            # Skip if scaled template is larger than screenshot
            if new_h > screenshot.shape[0] or new_w > screenshot.shape[1]:
                continue
            
            # Resize template
            template_resized = cv2.resize(template_orig, (new_w, new_h), interpolation=cv2.INTER_AREA)
            template_gray = cv2.cvtColor(template_resized, cv2.COLOR_BGR2GRAY)
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            # Get best match for this scale
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Update best match if this is better
            if max_val > best_confidence:
                best_confidence = max_val
                best_match = {
                    'confidence': float(max_val),
                    'location': {
                        'x': int(max_loc[0]),
                        'y': int(max_loc[1]),
                        'width': new_w,
                        'height': new_h
                    },
                    'scale': scale,
                    'matched': max_val >= threshold
                }
        
        return best_match
    except Exception as e:
        print(f"Error in multi-scale template matching: {e}")
        return None


def detect_current_screen(screenshot_path: str, threshold: float = None, use_multiscale: bool = True) -> Optional[Dict]:
    """
    Detect which screen is currently displayed
    
    Args:
        screenshot_path: Path to screenshot image
        threshold: Optional custom confidence threshold (overrides template defaults)
        use_multiscale: Whether to use multi-scale template matching (default: True)
    
    Returns:
        Dict with detection results or None
    """
    try:
        # Load all templates
        templates = load_templates_from_db()
        
        if not templates:
            return {
                'success': False,
                'error': 'No templates available'
            }
        
        # Try to match each template (ordered by priority)
        matches = []
        for template in templates:
            # Use custom threshold if provided, otherwise use template default
            match_threshold = threshold if threshold is not None else template['threshold']
            
            # Choose matching method
            if use_multiscale:
                match_result = match_template_multiscale(
                    screenshot_path, 
                    template['path'], 
                    match_threshold
                )
            else:
                match_result = match_template(
                    screenshot_path, 
                    template['path'], 
                    match_threshold
                )
            
            if match_result and match_result['matched']:
                matches.append({
                    'template_id': template['id'],
                    'template_name': template['name'],
                    'confidence': match_result['confidence'],
                    'location': match_result['location'],
                    'priority': template['priority'],
                    'scale': match_result.get('scale', 1.0)
                })
        
        # Return best match (highest priority and confidence)
        if matches:
            # Sort by priority (desc) then confidence (desc)
            matches.sort(key=lambda x: (x['priority'], x['confidence']), reverse=True)
            best_match = matches[0]
            
            return {
                'success': True,
                'screen': best_match['template_name'],
                'template_id': best_match['template_id'],
                'confidence': best_match['confidence'],
                'location': best_match['location'],
                'scale': best_match['scale'],
                'all_matches': matches
            }
        else:
            return {
                'success': True,
                'screen': None,
                'message': 'No matching screen detected'
            }
    except Exception as e:
        print(f"Error detecting screen: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def capture_screenshot(device_address: str, save_path: Optional[str] = None) -> Optional[str]:
    """
    Capture screenshot from Android device via ADB
    
    Args:
        device_address: ADB device address
        save_path: Optional custom save path
    
    Returns:
        Path to saved screenshot or None
    """
    try:
        import subprocess
        from datetime import datetime
        
        # Create device-specific screenshot directory
        if save_path is None:
            device_dir = os.path.join(SCREENSHOTS_DIR, device_address.replace(':', '_'))
            os.makedirs(device_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(device_dir, f'screenshot_{timestamp}.png')
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Capture screenshot via ADB
        # First capture to device
        result = subprocess.run(
            ['adb', '-s', device_address, 'shell', 'screencap', '-p', '/sdcard/screenshot.png'],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"Error capturing screenshot: {result.stderr.decode()}")
            return None
        
        # Pull screenshot from device
        result = subprocess.run(
            ['adb', '-s', device_address, 'pull', '/sdcard/screenshot.png', save_path],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"Error pulling screenshot: {result.stderr.decode()}")
            return None
        
        # Clean up device screenshot
        subprocess.run(
            ['adb', '-s', device_address, 'shell', 'rm', '/sdcard/screenshot.png'],
            capture_output=True,
            timeout=5
        )
        
        return save_path if os.path.exists(save_path) else None
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None


def get_screenshot_as_base64(screenshot_path: str) -> Optional[str]:
    """Convert screenshot to base64 for web display"""
    try:
        import base64
        
        with open(screenshot_path, 'rb') as f:
            image_data = f.read()
            b64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{b64_data}"
    except Exception as e:
        print(f"Error converting screenshot to base64: {e}")
        return None


if __name__ == "__main__":
    # Test the module
    print("Testing screen detector...")
    
    # Load templates
    print("\n1. Loading templates from database...")
    templates = load_templates_from_db()
    print(f"   Loaded {len(templates)} templates")
    for t in templates:
        print(f"   - {t['name']}: {t['filename']} (priority: {t['priority']})")
    
    # Test template matching (if screenshot exists)
    test_screenshot = "screenshots/test_screenshot.png"
    if os.path.exists(test_screenshot):
        print(f"\n2. Testing detection on {test_screenshot}...")
        result = detect_current_screen(test_screenshot)
        if result['success'] and result.get('screen'):
            print(f"   Detected: {result['screen']}")
            print(f"   Confidence: {result['confidence']:.2%}")
        else:
            print(f"   No screen detected")
    else:
        print(f"\n2. No test screenshot found at {test_screenshot}")
    
    print("\nTest complete!")
