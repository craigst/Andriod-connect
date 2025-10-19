#!/usr/bin/env python3
"""
Initialize screen_control database with schema and default data
"""

import sqlite3
import os

DB_PATH = "data/screen_control.db"

def init_database():
    """Initialize the screen control database"""
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
    
    # Credentials table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_address TEXT UNIQUE,
            username TEXT,
            encrypted_password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Screen templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screen_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            filename TEXT,
            confidence_threshold REAL DEFAULT 0.7,
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Macros table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS macros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            actions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Template-macro links table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS template_macro_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER,
            macro_id INTEGER,
            FOREIGN KEY (template_id) REFERENCES screen_templates(id),
            FOREIGN KEY (macro_id) REFERENCES macros(id)
        )
    """)
    
    # Vehicle overrides table (stores manual make/model corrections)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration TEXT UNIQUE,
            make_model TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Timesheet entries table (stores daily work hours)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timesheet_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_ending_date TEXT,
            day_name TEXT,
            entry_date TEXT,
            start_time TEXT,
            finish_time TEXT,
            total_hours TEXT,
            driver TEXT,
            fleet_reg TEXT,
            start_mileage TEXT,
            end_mileage TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(week_ending_date, day_name)
        )
    """)
    
    print("Tables created successfully!")
    
    # Insert default templates
    print("Inserting default templates...")
    
    templates = [
        ('login', 'Login.png', 0.7, 5),
        ('bionag', 'bionag.png', 0.7, 8),
        ('noload', 'noload.png', 0.7, 10),
        ('firstloadnag', 'firstloadnag.png', 0.7, 7),
        ('nagload2', 'nagload2.png', 0.7, 6),
        ('nagload3', 'nagload3.png', 0.7, 6),
        ('loadlist', 'loadlist.png', 0.7, 3),
        ('cartoload', 'cartoload.png', 0.7, 4)
    ]
    
    for name, filename, threshold, priority in templates:
        cursor.execute("""
            INSERT OR IGNORE INTO screen_templates 
            (name, filename, confidence_threshold, priority) 
            VALUES (?, ?, ?, ?)
        """, (name, filename, threshold, priority))
    
    # Get count
    cursor.execute("SELECT COUNT(*) FROM screen_templates")
    count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully!")
    print(f"Templates in database: {count}")
    print(f"Database location: {DB_PATH}")

if __name__ == "__main__":
    init_database()
