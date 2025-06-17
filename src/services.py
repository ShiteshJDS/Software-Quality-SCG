# src/services.py

import sqlite3
import database, config, models, auth
from encryption import EncryptionManager
from logger import SecureLogger

# --- Initialize Global Managers ---
# These are instantiated once and used by the services layer.
encryption_manager = EncryptionManager(config.ENCRYPTION_KEY_FILE)
secure_logger = SecureLogger(encryption_manager)


# --- Authorization Decorator ---
def requires_role(allowed_roles: list[str]):
    """
    A decorator to enforce role-based access control on service functions.
    """
    def decorator(func):
        def wrapper(current_user: models.User, *args, **kwargs):
            if current_user.role not in allowed_roles:
                print(f"Access Denied. Required role(s): {', '.join(allowed_roles)}")
                secure_logger.log(current_user.username, "Authorization failed", f"Attempted to use {func.__name__}")
                return None # Or raise a PermissionError
            return func(current_user, *args, **kwargs)
        return wrapper
    return decorator

# --- User Services ---

def get_all_users_raw() -> list[sqlite3.Row]:
    """
    Retrieves all user records from the database with encrypted usernames.
    This is primarily for the login function.
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def add_new_user(current_user: models.User, username, password, role, first_name, last_name):
    """Placeholder for adding a new user. Enforces role permissions."""
    print(f"User '{current_user.username}' is attempting to add a new user '{username}'.")
    #
    # Full implementation would go here:
    # 1. Validate inputs using functions from validation.py
    # 2. Encrypt username
    # 3. Hash password
    # 4. Insert into DB using parameterized query
    # 5. Log the action
    #
    secure_logger.log(current_user.username, "Added new user", f"Username: {username}, Role: {role}")
    print("User added successfully (placeholder).")


# --- Traveller Services ---

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def add_new_traveller(current_user: models.User, traveller_data: dict):
    """Placeholder for adding a new traveller."""
    print(f"User '{current_user.username}' is adding a new traveller.")
    #
    # Full implementation would go here:
    # 1. Validate all traveller_data fields
    # 2. Encrypt all PII fields (name, address, email, etc.)
    # 3. Insert into DB using parameterized query
    # 4. Log the action
    #
    secure_logger.log(current_user.username, "Added new traveller", f"Traveller email: {traveller_data.get('email')}")
    print("Traveller added successfully (placeholder).")


# --- Scooter Services ---

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN, config.ROLE_SERVICE_ENGINEER])
def update_scooter_location(current_user: models.User, scooter_id: int, new_lat: float, new_lon: float):
    """Placeholder for updating scooter location."""
    print(f"User '{current_user.username}' is updating location for scooter ID {scooter_id}.")
    #
    # Full implementation would go here:
    # 1. Validate scooter_id and coordinates
    # 2. UPDATE scooter in DB using parameterized query
    # 3. Log the action
    #
    secure_logger.log(current_user.username, "Updated scooter location", f"Scooter ID: {scooter_id}")
    print("Scooter location updated successfully (placeholder).")