# src/database.py
# BLOB = storing as bytes

import sqlite3
import config
from encryption import EncryptionManager
from auth import hash_password

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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username BLOB UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        first_name BLOB NOT NULL,
        last_name BLOB NOT NULL,
        registration_date TEXT NOT NULL
    )
    """)

    # Insert hardcoded super administrator if not exists
    try:
        encryption_manager = EncryptionManager(config.ENCRYPTION_KEY_FILE)
        encrypted_username = encryption_manager.encrypt('super_admin')
        encrypted_first_name = encryption_manager.encrypt('Super')
        encrypted_last_name = encryption_manager.encrypt('Admin')
        hashed_password = hash_password('Admin_123?')
        
        cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash, role, first_name, last_name, registration_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            encrypted_username,
            hashed_password,
            config.ROLE_SUPER_ADMIN,
            encrypted_first_name,
            encrypted_last_name,
            '2025-06-17'
        ))

        # Insert dummy System Administrator
        encrypted_username = encryption_manager.encrypt('sys_admin')
        encrypted_first_name = encryption_manager.encrypt('System')
        encrypted_last_name = encryption_manager.encrypt('Admin')
        hashed_password = hash_password('SysAdmin_123?')
        cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash, role, first_name, last_name, registration_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            encrypted_username,
            hashed_password,
            config.ROLE_SYSTEM_ADMIN,
            encrypted_first_name,
            encrypted_last_name,
            '2025-06-17'
        ))

        # Insert dummy Service Engineer
        encrypted_username = encryption_manager.encrypt('service_eng')
        encrypted_first_name = encryption_manager.encrypt('Service')
        encrypted_last_name = encryption_manager.encrypt('Engineer')
        hashed_password = hash_password('ServiceEng_123?')
        cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash, role, first_name, last_name, registration_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            encrypted_username,
            hashed_password,
            config.ROLE_SERVICE_ENGINEER,
            encrypted_first_name,
            encrypted_last_name,
            '2025-06-17'
        ))
    except Exception as e:
        print(f"Error during super_admin initialization: {e}")


    # --- Create travellers table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS travellers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name BLOB NOT NULL,
        last_name BLOB NOT NULL,
        birthday BLOB NOT NULL,
        gender BLOB,
        street_name BLOB NOT NULL,
        house_number BLOB NOT NULL,
        zip_code BLOB NOT NULL,
        city BLOB NOT NULL,
        email BLOB NOT NULL,
        mobile_phone BLOB NOT NULL,
        driving_license_number BLOB NOT NULL,
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
        location_lat TEXT,
        location_lon TEXT,
        out_of_service_status INTEGER DEFAULT 0,
        mileage REAL,
        last_maintenance_date TEXT
    )
    """)
    
    # --- Create logs table ---
    # CORRECTED: Changed encrypted columns from TEXT to BLOB
    # ADDED: is_read column for suspicious log alerts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        username BLOB NOT NULL,
        description_of_activity BLOB NOT NULL,
        additional_information BLOB,
        suspicious INTEGER NOT NULL,
        is_read INTEGER DEFAULT 0 NOT NULL
    )
    """)

    # --- Create restore_codes table ---
    # NEW: Table for managing one-time backup restore codes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restore_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        backup_filename TEXT NOT NULL,
        system_admin_username TEXT NOT NULL,
        is_used INTEGER DEFAULT 0 NOT NULL,
        generated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")