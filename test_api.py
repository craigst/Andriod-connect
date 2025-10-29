#!/usr/bin/env python3
"""
Quick API test script
"""

import requests
import json

BASE_URL = "http://10.10.254.13:5020"

print("Testing ADB Device Manager API...")
print("=" * 60)

# Test 1: Health check
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Get devices
print("\n2. Testing devices endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/devices")
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Devices found: {len(data.get('devices', []))}")
    for device in data.get('devices', []):
        print(f"     - {device['name']}: Connected={device['connected']}, App={device['app_installed']}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Database info
print("\n3. Testing database info endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/database/info")
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Database exists: {data.get('exists', False)}")
    if data.get('exists'):
        print(f"   Size: {data.get('size_mb', 0)} MB")
        print(f"   Last modified: {data.get('last_modified_human', 'N/A')}")
except Exception as e:
    print(f"   Error: {e}")

# Test 4: Pull SQL (this is what we're fixing)
print("\n4. Testing SQL pull endpoint (with empty JSON body)...")
try:
    response = requests.post(
        f"{BASE_URL}/api/sql/pull",
        headers={"Content-Type": "application/json"},
        json={}
    )
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Success: {data.get('success', False)}")
    print(f"   Message: {data.get('message', 'N/A')}")
    if 'error' in data:
        print(f"   Error: {data['error']}")
except Exception as e:
    print(f"   Error: {e}")

# Test 5: Get loads
print("\n5. Testing loads endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/loads")
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Success: {data.get('success', False)}")
    if data.get('success'):
        print(f"   Total loads: {data.get('total_loads', 0)}")
    else:
        print(f"   Error: {data.get('error', 'N/A')}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
print("API testing complete!")
