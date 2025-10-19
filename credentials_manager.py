#!/usr/bin/env python3
"""
Credentials Manager - Encrypted storage for device credentials
Uses Fernet symmetric encryption for password storage
"""

import sqlite3
import os
from cryptography.fernet import Fernet
from pathlib import Path

# Database path
DB_PATH = "data/screen_control.db"

# Encryption key file
KEY_FILE = "data/.screen_control_key"


def get_or_create_key():
    """Get existing encryption key or create a new one"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        # Generate new key
        key = Fernet.generate_key()
        
        # Save key securely
        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(KEY_FILE, 0o600)
        
        return key


def get_cipher():
    """Get Fernet cipher instance"""
    key = get_or_create_key()
    return Fernet(key)


def encrypt_password(password: str) -> str:
    """Encrypt a password string"""
    cipher = get_cipher()
    encrypted = cipher.encrypt(password.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt an encrypted password"""
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_password.encode('utf-8'))
    return decrypted.decode('utf-8')


def store_credentials(device_address: str, username: str, password: str) -> bool:
    """Store encrypted credentials for a device"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Encrypt password
        encrypted_pwd = encrypt_password(password)
        
        # Insert or update credentials
        cursor.execute("""
            INSERT INTO credentials (device_address, username, encrypted_password)
            VALUES (?, ?, ?)
            ON CONFLICT(device_address) 
            DO UPDATE SET username=?, encrypted_password=?, created_at=CURRENT_TIMESTAMP
        """, (device_address, username, encrypted_pwd, username, encrypted_pwd))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error storing credentials: {e}")
        return False


def get_credentials(device_address: str) -> dict:
    """Get decrypted credentials for a device"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, encrypted_password 
            FROM credentials 
            WHERE device_address = ?
        """, (device_address,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Decrypt password
            password = decrypt_password(row['encrypted_password'])
            return {
                'username': row['username'],
                'password': password
            }
        else:
            return None
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None


def delete_credentials(device_address: str) -> bool:
    """Delete credentials for a device"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM credentials 
            WHERE device_address = ?
        """, (device_address,))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error deleting credentials: {e}")
        return False


def list_devices_with_credentials() -> list:
    """List all devices that have stored credentials"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT device_address, username, created_at 
            FROM credentials
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error listing credentials: {e}")
        return []


if __name__ == "__main__":
    # Test the module
    print("Testing credentials manager...")
    
    # Store test credentials
    print("\n1. Storing credentials...")
    store_credentials("10.10.254.13:5555", "testuser", "testpass123")
    
    # Retrieve credentials
    print("\n2. Retrieving credentials...")
    creds = get_credentials("10.10.254.13:5555")
    if creds:
        print(f"   Username: {creds['username']}")
        print(f"   Password: {creds['password']}")
    
    # List all devices
    print("\n3. Listing all devices with credentials...")
    devices = list_devices_with_credentials()
    for device in devices:
        print(f"   - {device['device_address']}: {device['username']}")
    
    # Delete credentials
    print("\n4. Deleting credentials...")
    delete_credentials("10.10.254.13:5555")
    
    print("\nTest complete!")
