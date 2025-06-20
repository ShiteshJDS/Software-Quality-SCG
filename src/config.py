# src/config.py

# --- Hard-coded Super Administrator Credentials ---
SUPER_ADMIN_USERNAME = 'super_admin'
SUPER_ADMIN_PASSWORD = 'Admin_123?'

# --- File Paths ---
DATABASE_FILE = 'urban_mobility.db'
ENCRYPTION_KEY_FILE = 'secret.key'
LOG_FILE_NAME = 'system.log' # Er wordt gelogt naar DB niet naar een file

# --- User Roles ---
ROLE_SUPER_ADMIN = 'Super Administrator'
ROLE_SYSTEM_ADMIN = 'System Administrator'
ROLE_SERVICE_ENGINEER = 'Service Engineer'

# --- Brute-Force Protection ---
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_TIME_SECONDS = 60

# --- Predefined Cities for Traveller Registration ---
PREDEFINED_CITIES = [
    "Rotterdam",
    "Amsterdam",
    "The Hague",
    "Utrecht",
    "Eindhoven",
    "Groningen",
    "Tilburg",
    "Almere",
    "Breda",
    "Nijmegen"
]