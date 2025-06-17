# src/models.py

from dataclasses import dataclass
import sqlite3
import config
from encryption import EncryptionManager
from auth import hash_password

@dataclass
class User:
    id: int
    username: str # This will hold the DECRYPTED username for in-memory use
    role: str
    first_name: str
    last_name: str
    registration_date: str

@dataclass
class Traveller:
    id: int
    first_name: str
    last_name: str
    birthday: str
    gender: str
    street_name: str
    house_number: str
    zip_code: str
    city: str
    email: str
    mobile_phone: str
    driving_license_number: str
    registration_date: str

@dataclass
class Scooter:
    id: int
    serial_number: str
    brand: str
    model: str
    in_service_date: str
    top_speed: float
    battery_capacity: float
    state_of_charge: float
    target_range_soc_min: float
    target_range_soc_max: float
    location_lat: float
    location_lon: float
    out_of_service_status: int # 0 = In Service, 1 = Out of Service
    mileage: float
    last_maintenance_date: str

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
        first_name TEXT,
        last_name TEXT,
        registration_date TEXT NOT NULL
    )
    """)

    # Insert hardcoded super administrator if not exists
    encryption_manager = EncryptionManager(config.ENCRYPTION_KEY_FILE)
    encrypted_username = encryption_manager.encrypt('super_admin')
    hashed_password = hash_password('Admin_123?')
    cursor.execute("""
    INSERT OR IGNORE INTO users (username, password_hash, role, first_name, last_name, registration_date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        encrypted_username,
        hashed_password,
        config.ROLE_SUPER_ADMIN,  # Use the correct role string
        'Super',
        'Admin',
        '2025-06-17'
    ))

    # --- Create travellers table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS travellers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        birthday TEXT NOT NULL,
        gender TEXT,
        street_name TEXT NOT NULL,
        house_number TEXT NOT NULL,
        zip_code TEXT NOT NULL,
        city TEXT NOT NULL,
        email TEXT NOT NULL,
        mobile_phone TEXT NOT NULL,
        driving_license_number TEXT NOT NULL,
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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        username TEXT NOT NULL,
        description_of_activity TEXT NOT NULL,
        additional_information TEXT,
        suspicious TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")