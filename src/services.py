# src/services.py

import sqlite3
from datetime import datetime
import database, config, models, auth, validation
from encryption import EncryptionManager
from logger import SecureLogger

# --- Initialize Global Managers ---
# These are instantiated once and used by the services layer.
encryption_manager = EncryptionManager(config.ENCRYPTION_KEY_FILE)
secure_logger = SecureLogger(encryption_manager)


# --- Authorization Decorator ---
def requires_role(allowed_roles: list[str]):
    """A decorator to enforce role-based access control on service functions."""
    def decorator(func):
        def wrapper(current_user: models.User, *args, **kwargs):
            if not current_user or current_user.role not in allowed_roles:
                print(f"Access Denied. Your role '{current_user.role if current_user else 'None'}' is not authorized.")
                if current_user:
                    secure_logger.log(current_user.username, "Authorization failed", f"Attempted to use {func.__name__}", is_suspicious=True)
                return None
            return func(current_user, *args, **kwargs)
        return wrapper
    return decorator

# --- User Services ---

def get_all_users_raw() -> list[sqlite3.Row]:
    """Retrieves all user records from the database with encrypted data."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def add_new_user(current_user: models.User, username, password, role, first_name, last_name):
    """Adds a new user to the database after validation and encryption."""
    # 1. Validate inputs
    if not validation.is_valid_username(username):
        print("Invalid username format.")
        return False
    if not validation.is_valid_password(password):
        print("Invalid password format.")
        return False
    if role not in [config.ROLE_SERVICE_ENGINEER, config.ROLE_SYSTEM_ADMIN]:
        print("Invalid role specified.")
        return False
    # A super admin cannot create another super admin
    if role == config.ROLE_SUPER_ADMIN:
        print("Cannot create another Super Administrator.")
        return False
    # A system admin cannot create a super admin or another system admin
    if current_user.role == config.ROLE_SYSTEM_ADMIN and role == config.ROLE_SYSTEM_ADMIN:
        print("System administrators cannot create other system administrators.")
        return False
    
    try:
        # 2. Encrypt username and names
        encrypted_username = encryption_manager.encrypt(username)
        encrypted_first_name = encryption_manager.encrypt(first_name)
        encrypted_last_name = encryption_manager.encrypt(last_name)
        
        # 3. Hash password
        password_hash = auth.hash_password(password)
        
        # 4. Insert into DB
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, first_name, last_name, registration_date) VALUES (?, ?, ?, ?, ?, ?)",
            (encrypted_username, password_hash, role, encrypted_first_name, encrypted_last_name, datetime.now().strftime("%Y-%m-%d"))
        )
        conn.commit()
        
        # 5. Log the action
        secure_logger.log(current_user.username, "Added new user", f"Username: {username}, Role: {role}")
        print("User added successfully.")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Username '{username}' already exists.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- Traveller Services ---

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def add_new_traveller(current_user: models.User, traveller_data: dict):
    """Adds a new traveller to the database after validation and encryption."""
    # 1. Validate all traveller_data fields (example for a few)
    if not validation.is_valid_zip_code(traveller_data['zip_code']):
        print("Invalid Zip Code format.")
        return False
    if not validation.is_valid_phone_digits(traveller_data['mobile_phone']):
        print("Invalid mobile phone format.")
        return False
    if not validation.is_valid_driving_license(traveller_data['driving_license_number']):
        print("Invalid driving license format.")
        return False

    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 2. Encrypt all PII fields
        encrypted_data = {key: encryption_manager.encrypt(str(value)) for key, value in traveller_data.items()}
        
        # 3. Insert into DB using parameterized query
        cursor.execute("""
            INSERT INTO travellers (first_name, last_name, birthday, gender, street_name, house_number, zip_code, city, email, mobile_phone, driving_license_number, registration_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            encrypted_data['first_name'], encrypted_data['last_name'], encrypted_data['birthday'],
            encrypted_data['gender'], encrypted_data['street_name'], encrypted_data['house_number'],
            encrypted_data['zip_code'], encrypted_data['city'], encrypted_data['email'],
            encrypted_data['mobile_phone'], encrypted_data['driving_license_number'],
            datetime.now().strftime("%Y-%m-%d")
        ))
        conn.commit()
        
        # 4. Log the action
        secure_logger.log(current_user.username, "Added new traveller", f"Traveller email: {traveller_data.get('email')}")
        print("Traveller added successfully.")
        return True
    except Exception as e:
        print(f"An error occurred while adding traveller: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- Scooter Services ---

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN, config.ROLE_SERVICE_ENGINEER])
def update_scooter_location(current_user: models.User, scooter_id: int, new_lat: float, new_lon: float):
    """Updates the location of a specific scooter."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 2. UPDATE scooter in DB using parameterized query
        cursor.execute(
            "UPDATE scooters SET location_lat = ?, location_lon = ? WHERE id = ?",
            (new_lat, new_lon, scooter_id)
        )
        if cursor.rowcount == 0:
            print(f"Error: Scooter ID {scooter_id} not found.")
            return False
            
        conn.commit()
        
        # 3. Log the action
        secure_logger.log(current_user.username, "Updated scooter location", f"Scooter ID: {scooter_id}")
        print("Scooter location updated successfully.")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        if conn:
            conn.close()

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def add_new_scooter(current_user: models.User, scooter_data: dict):
    """Adds a new scooter to the fleet."""
    if not validation.is_valid_scooter_serial(scooter_data['serial_number']):
        print("Invalid scooter serial number format.")
        return False
        
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scooters (
                serial_number, brand, model, in_service_date, top_speed, battery_capacity,
                state_of_charge, target_range_soc_min, target_range_soc_max, location_lat,
                location_lon, out_of_service_status, mileage, last_maintenance_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scooter_data['serial_number'], scooter_data['brand'], scooter_data['model'],
            datetime.now().strftime("%Y-%m-%d"), scooter_data['top_speed'], scooter_data['battery_capacity'],
            scooter_data['state_of_charge'], scooter_data['target_range_soc_min'], scooter_data['target_range_soc_max'],
            scooter_data['location_lat'], scooter_data['location_lon'], scooter_data['out_of_service_status'],
            scooter_data['mileage'], scooter_data['last_maintenance_date']
        ))
        conn.commit()
        secure_logger.log(current_user.username, "Added new scooter", f"Serial: {scooter_data['serial_number']}")
        print("Scooter added successfully.")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Scooter with serial number '{scooter_data['serial_number']}' already exists.")
        return False
    except Exception as e:
        print(f"An error occurred while adding scooter: {e}")
        return False
    finally:
        if conn:
            conn.close()