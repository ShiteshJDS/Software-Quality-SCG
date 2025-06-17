# src/config.py

# --- Hard-coded Super Administrator Credentials ---
# As per assignment requirements, this is intentionally insecure for assessment.
SUPER_ADMIN_USERNAME = 'super_admin'
SUPER_ADMIN_PASSWORD = 'Admin_123?'

# --- File Paths ---
DATABASE_FILE = 'urban_mobility.db'
ENCRYPTION_KEY_FILE = 'secret.key'
LOG_FILE_NAME = 'system.log' # Note: Logging is to the DB, not a plain file.

# --- User Roles ---
ROLE_SUPER_ADMIN = 'Super Administrator'
ROLE_SYSTEM_ADMIN = 'System Administrator'
ROLE_SERVICE_ENGINEER = 'Service Engineer'

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