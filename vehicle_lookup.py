#!/usr/bin/env python3
"""
Vehicle Lookup Module
Scrapes motorcheck.co.uk to retrieve vehicle make and model information
"""

import re
import sqlite3
import logging
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

DB_PATH = "data/screen_control.db"

logger = logging.getLogger(__name__)


def normalize_registration(reg):
    """Normalize vehicle registration (remove spaces, dashes, uppercase)"""
    if not reg:
        return None
    return str(reg).upper().replace(' ', '').replace('-', '').replace('_', '').strip()


def scrape_motorcheck(registration):
    """
    Scrape motorcheck.co.uk for vehicle make and model
    Returns: dict with 'make', 'model', 'year', 'makeModel' or None if failed
    """
    try:
        clean_reg = normalize_registration(registration)
        if not clean_reg:
            logger.error("Invalid registration provided")
            return None
        
        url = f"https://www.motorcheck.co.uk/free-car-check/?vrm={clean_reg}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        html = response.text
        
        # Extract VRM
        vrm_match = re.search(r'vrm=\"([A-Z0-9]+)\"', html, re.IGNORECASE)
        vrm = vrm_match.group(1) if vrm_match else None
        
        # Extract make from logo path
        make = None
        make_match = re.search(r'images/make-logos/([a-z0-9-]+)/', html, re.IGNORECASE)
        if make_match:
            make = title_case(make_match.group(1))
        else:
            # Alternative: extract from "for this <strong>MAKE.</strong>"
            make_alt = re.search(r'for this\s*<strong>\s*([A-Za-z0-9\- ]+?)\.\s*</strong>', html, re.IGNORECASE)
            if make_alt:
                make = title_case(make_alt.group(1).replace('.', '').strip())
        
        # Extract title HTML (contains full vehicle description)
        title_match = re.search(
            r'<h[34][^>]*class="[^"]*vehicle-title[^"]*"[^>]*>([\s\S]*?)</h[34]>',
            html,
            re.IGNORECASE
        )
        
        if not title_match:
            logger.warning(f"Could not find vehicle title for {registration}")
            return None
        
        title_html = title_match.group(1)
        title_text = strip_tags(title_html)
        
        # Remove VRM from title if present
        if vrm and title_text.upper().startswith(vrm.upper() + ' '):
            title_text = title_text[len(vrm) + 1:].strip()
        
        # Extract year
        year = None
        year_match = re.search(r',\s*(\d{4})\b', title_text)
        if year_match:
            year = int(year_match.group(1))
            # Remove year from title
            title_text = re.sub(r',\s*\d{4}\b', '', title_text).strip()
        
        model = title_text or None
        
        # Remove make from model if it starts with make
        if make and model and model.lower().startswith(make.lower() + ' '):
            model = model[len(make) + 1:].strip()
        
        # Construct make_model
        if make:
            make_model = f"{make} {model}".strip() if model else make
        else:
            make_model = model
        
        if not make_model:
            logger.warning(f"Could not extract make/model for {registration}")
            return None
        
        return {
            'make': make,
            'model': model,
            'year': year,
            'makeModel': make_model
        }
        
    except requests.RequestException as e:
        logger.error(f"HTTP error scraping motorcheck for {registration}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error scraping motorcheck for {registration}: {e}")
        return None


def strip_tags(html):
    """Remove HTML tags and normalize whitespace"""
    if not html:
        return ''
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def title_case(slug):
    """Convert slug to Title Case (e.g., 'ford-focus' -> 'Ford Focus')"""
    if not slug:
        return ''
    words = re.split(r'[\-\s]+', slug)
    return ' '.join(w.capitalize() if w else '' for w in words).strip()


def get_vehicle_override(registration):
    """Get saved override for a registration"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        clean_reg = normalize_registration(registration)
        
        cursor.execute("""
            SELECT registration, make_model, created_date, last_used_date
            FROM vehicle_overrides
            WHERE registration = ?
        """, (clean_reg,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
        
    except Exception as e:
        logger.error(f"Error getting vehicle override: {e}")
        return None


def save_vehicle_override(registration, make_model):
    """Save or update vehicle override"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        clean_reg = normalize_registration(registration)
        
        cursor.execute("""
            INSERT INTO vehicle_overrides (registration, make_model, last_used_date)
            VALUES (?, ?, ?)
            ON CONFLICT(registration) DO UPDATE SET
                make_model = excluded.make_model,
                last_used_date = excluded.last_used_date
        """, (clean_reg, make_model, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving vehicle override: {e}")
        return False


def cleanup_old_overrides(days=14):
    """Delete vehicle overrides older than specified days"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            DELETE FROM vehicle_overrides
            WHERE last_used_date < ?
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} old vehicle overrides (older than {days} days)")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old overrides: {e}")
        return 0


def lookup_vehicle(registration):
    """
    Lookup vehicle make/model with override priority:
    1. Check for saved override
    2. Scrape motorcheck.co.uk
    3. Return None if both fail
    """
    clean_reg = normalize_registration(registration)
    if not clean_reg:
        return {'error': 'Invalid registration'}
    
    # Check for override first
    override = get_vehicle_override(clean_reg)
    if override:
        # Update last_used_date
        save_vehicle_override(clean_reg, override['make_model'])
        return {
            'registration': clean_reg,
            'makeModel': override['make_model'],
            'source': 'override',
            'saved_date': override['created_date']
        }
    
    # Scrape motorcheck
    result = scrape_motorcheck(clean_reg)
    
    if result:
        return {
            'registration': clean_reg,
            'makeModel': result['makeModel'],
            'make': result.get('make'),
            'model': result.get('model'),
            'year': result.get('year'),
            'source': 'motorcheck'
        }
    
    return {'error': 'Could not find vehicle information', 'registration': clean_reg}
