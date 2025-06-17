# src/database.py

import sqlite3
import config

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(config.DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def initialize_database():
    """
    Creates the database and all necessary tables if they don't already exist.
    This function is safe to run multiple times.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- Create users table ---
    # Usernames are encrypted, so they are stored as TEXT.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        registration_date TEXT NOT NULL
    )
    """)

    # --- Create travellers table ---
    # All personally identifiable information (PII) is encrypted and stored as TEXT.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS travellers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        birthday TEXT NOT NULL,
        gender TEXT,
        address TEXT NOT NULL,
        email TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        driving_license TEXT NOT NULL,
        registration_date TEXT NOT NULL
    )
    """)

    # --- Create scooters table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scooters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        serial_number TEXT UNIQUE NOT NULL,
        brand TEXT,
        model TEXT,
        in_service_date TEXT NOT NULL,
        top_speed REAL,
        battery_capacity REAL,
        state_of_charge REAL,
        target_range_soc_min REAL,
        target_range_soc_max REAL,
        location_lat REAL,
        location_lon REAL,
        out_of_service_status INTEGER DEFAULT 0, -- 0 = In Service, 1 = Out of Service
        mileage REAL,
        last_maintenance_date TEXT
    )
    """)
    
    # --- Create logs table ---
    # Log entries are fully encrypted and stored as a single BLOB.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        log_data BLOB NOT NULL,
        is_suspicious INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")