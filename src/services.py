# src/services.py

import sqlite3
import zipfile
import shutil
import os
import secrets
import string
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

def _find_user_by_username(username: str) -> sqlite3.Row | None:
    """Finds a user by their plaintext username by decrypting all usernames."""
    all_users = get_all_users_raw()
    for user_row in all_users:
        try:
            decrypted_username = encryption_manager.decrypt(user_row['username'])
            if decrypted_username.lower() == username.lower():
                return user_row
        except Exception:
            continue # Skip records that fail to decrypt
    return None

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
        if 'conn' in locals() and conn:
            conn.close()

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def update_user_profile(current_user: models.User, target_username: str, new_profile_data: dict):
    """Updates a user's first and last name, enforcing role hierarchy."""
    target_user_record = _find_user_by_username(target_username)
    if not target_user_record:
        print(f"Error: User '{target_username}' not found.")
        return False

    target_user_role = target_user_record['role']
    encrypted_target_username = target_user_record['username']

    # Role-based authorization check
    if current_user.role == config.ROLE_SYSTEM_ADMIN and target_user_role != config.ROLE_SERVICE_ENGINEER:
        print("System Admins can only update Service Engineer profiles.")
        secure_logger.log(current_user.username, "Authorization failed", f"Attempted to update profile of {target_username} ({target_user_role})", is_suspicious=True)
        return False
    
    if not new_profile_data or not any(new_profile_data.values()):
        print("No new data provided for update.")
        return False

    # Build the update query dynamically based on provided data
    update_fields = {}
    if new_profile_data.get('first_name'):
        update_fields['first_name'] = encryption_manager.encrypt(new_profile_data['first_name'])
    if new_profile_data.get('last_name'):
        update_fields['last_name'] = encryption_manager.encrypt(new_profile_data['last_name'])

    if not update_fields:
        print("No valid fields to update.")
        return False

    set_clause = ", ".join([f"{key} = ?" for key in update_fields.keys()])
    params = list(update_fields.values()) + [encrypted_target_username]

    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE users SET {set_clause} WHERE username = ?",
            tuple(params)
        )
        
        if cursor.rowcount == 0:
            print(f"Error: User '{target_username}' not found during update.")
            return False
            
        conn.commit()
        secure_logger.log(current_user.username, "Updated user profile", f"Target Username: {target_username}")
        print("User profile updated successfully.")
        return True
    except Exception as e:
        print(f"An error occurred while updating user profile: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()


@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def delete_user(current_user: models.User, target_username: str):
    """Deletes a user from the system, enforcing role hierarchy."""
    if current_user.username.lower() == target_username.lower():
        print("Error: You cannot delete your own account this way.")
        return False

    target_user_record = _find_user_by_username(target_username)
    if not target_user_record:
        print(f"Error: User '{target_username}' not found.")
        return False

    target_user_role = target_user_record['role']
    encrypted_target_username = target_user_record['username']

    # Role-based authorization check
    if current_user.role == config.ROLE_SYSTEM_ADMIN and target_user_role != config.ROLE_SERVICE_ENGINEER:
        print("System Admins can only delete Service Engineers.")
        secure_logger.log(current_user.username, "Authorization failed", f"Attempted to delete user {target_username} ({target_user_role})", is_suspicious=True)
        return False
    
    if current_user.role == config.ROLE_SUPER_ADMIN and target_user_role == config.ROLE_SUPER_ADMIN:
        print("Error: Super Admins cannot delete other Super Admins.")
        return False

    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (encrypted_target_username,))
        
        if cursor.rowcount == 0:
            print(f"Error: User '{target_username}' not found during deletion.")
            return False
            
        conn.commit()
        secure_logger.log(current_user.username, "Deleted user", f"Target Username: {target_username}", is_suspicious=True)
        print(f"User '{target_username}' deleted successfully.")
        return True
    except Exception as e:
        print(f"An error occurred while deleting user: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def reset_user_password(current_user: models.User, target_username: str):
    """Resets a user's password to a new secure temporary password."""
    target_user_record = _find_user_by_username(target_username)

    if not target_user_record:
        print(f"Error: User '{target_username}' not found.")
        return False

    # Now we have the correct encrypted username from the record
    encrypted_target_username = target_user_record['username']
    
    # Generate a secure temporary password
    alphabet = string.ascii_letters + string.digits + string.punctuation
    temp_password = ''.join(secrets.choice(alphabet) for i in range(14))
    
    new_password_hash = auth.hash_password(temp_password)
    
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (new_password_hash, encrypted_target_username)
    )
    
    conn.commit()
    conn.close()
    
    secure_logger.log(current_user.username, "Reset user password", f"Target Username: {target_username}", is_suspicious=True)
    print(f"Password for user '{target_username}' has been reset.")
    print(f"New Temporary Password: {temp_password}")
    return True

@requires_role([config.ROLE_SYSTEM_ADMIN, config.ROLE_SERVICE_ENGINEER])
def update_own_password(current_user: models.User, old_password: str, new_password: str):
    """Allows a logged-in user to update their own password."""
    if not validation.is_valid_password(new_password):
        print("New password does not meet the security requirements.")
        return False

    conn = database.get_db_connection()
    cursor = conn.cursor()
    # Use the user's ID for a reliable lookup.
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (current_user.id,))
    user_row = cursor.fetchone()

    if not user_row or not auth.verify_password(old_password, user_row['password_hash']):
        print("Incorrect old password.")
        conn.close()
        secure_logger.log(current_user.username, "Failed password change", "Incorrect old password", is_suspicious=True)
        return False
        
    new_password_hash = auth.hash_password(new_password)
    # Update the password using the user's ID.
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_password_hash, current_user.id)
    )
    conn.commit()
    conn.close()
    
    secure_logger.log(current_user.username, "Changed own password")
    print("Password updated successfully.")
    return True

# --- Scooter Services ---

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def add_new_scooter(current_user: models.User, serial_number: str, brand: str, model: str, top_speed: int, battery_capacity: int, state_of_charge: int, target_range_soc_min: int, target_range_soc_max: int, location_lat: float, location_lon: float, mileage: int, last_maintenance_date: str, out_of_service_status: bool = False):
    """Adds a new scooter to the fleet."""
    if not validation.is_valid_scooter_serial(serial_number):
        print("Invalid scooter serial number format. Must be 10 to 17 alphanumeric characters.")
        return False
    if not validation.is_valid_location_coordinate(str(location_lat)):
        print("Invalid latitude format. Must have 5 decimal places (e.g., 51.92250).")
        return False
    if not validation.is_valid_location_coordinate(str(location_lon)):
        print("Invalid longitude format. Must have 5 decimal places (e.g., 4.47917).")
        return False
    if not validation.is_valid_iso_date(last_maintenance_date):
        print("Invalid date format. Must be YYYY-MM-DD.")
        return False

    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        in_service_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO scooters (serial_number, brand, model, in_service_date, top_speed, battery_capacity, state_of_charge, target_range_soc_min, target_range_soc_max, location_lat, location_lon, out_of_service_status, mileage, last_maintenance_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (serial_number, brand, model, in_service_date, top_speed, battery_capacity, state_of_charge, target_range_soc_min, target_range_soc_max, location_lat, location_lon, out_of_service_status, mileage, last_maintenance_date)
        )
        conn.commit()
        secure_logger.log(current_user.username, "Added new scooter", f"Serial: {serial_number}")
        print("Scooter added successfully.")
        return True
    except sqlite3.IntegrityError:
        print("Error: A scooter with this serial number already exists.")
        return False
    except Exception as e:
        print(f"An error occurred while adding the scooter: {e}")
        return False
    finally:
        if conn:
            conn.close()

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN, config.ROLE_SERVICE_ENGINEER])
def update_scooter(current_user: models.User, scooter_id: int, updates: dict):
    """Updates a scooter's information based on the user's role."""
    allowed_updates = {}
    # Define editable fields for each role
    service_engineer_fields = ['state_of_charge', 'target_range_soc_min', 'target_range_soc_max', 'location_lat', 'location_lon', 'out_of_service_status', 'mileage', 'last_maintenance_date']
    admin_fields = service_engineer_fields + ['brand', 'model', 'serial_number', 'top_speed', 'battery_capacity']

    # Determine which fields the current user can edit
    if current_user.role == config.ROLE_SERVICE_ENGINEER:
        editable_fields = service_engineer_fields
    else: # Super Admin and System Admin
        editable_fields = admin_fields

    # Filter the updates dictionary to only include editable fields
    for key, value in updates.items():
        if key in editable_fields:
            # Validate input before adding to allowed_updates
            if key in ['location_lat', 'location_lon'] and not validation.is_valid_location_coordinate(str(value)):
                print(f"Invalid format for {key}. Must have 5 decimal places.")
                return False
            if key == 'last_maintenance_date' and not validation.is_valid_iso_date(value):
                print(f"Invalid date format for {key}. Must be YYYY-MM-DD.")
                return False
            if key == 'serial_number' and not validation.is_valid_scooter_serial(value):
                print(f"Invalid format for {key}. Must be 10 to 17 alphanumeric characters.")
                return False
            allowed_updates[key] = value
        else:
            print(f"Warning: You are not authorized to update the '{key}' field. It will be ignored.")

    if not allowed_updates:
        print("No valid fields to update or all updates were unauthorized.")
        return False

    # Construct the SQL query dynamically
    set_clause = ", ".join([f"{key} = ?" for key in allowed_updates.keys()])
    sql_query = f"UPDATE scooters SET {set_clause} WHERE id = ?"
    params = list(allowed_updates.values()) + [scooter_id]

    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query, params)

        if cursor.rowcount == 0:
            print(f"Error: Scooter with ID '{scooter_id}' not found.")
            return False

        conn.commit()
        secure_logger.log(current_user.username, "Updated scooter", f"ID: {scooter_id}, Updates: {allowed_updates}")
        print("Scooter updated successfully.")
        return True
    except Exception as e:
        print(f"An error occurred while updating the scooter: {e}")
        return False
    finally:
        if conn:
            conn.close()

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def delete_scooter(current_user: models.User, serial_number: str):
    """Deletes a scooter from the system."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scooters WHERE serial_number = ?", (serial_number,))

        if cursor.rowcount == 0:
            print(f"Error: Scooter with serial number '{serial_number}' not found.")
            return False

        conn.commit()
        secure_logger.log(current_user.username, "Deleted scooter", f"Serial: {serial_number}", is_suspicious=True)
        print(f"Scooter '{serial_number}' deleted successfully.")
        return True
    except Exception as e:
        print(f"An error occurred while deleting the scooter: {e}")
        return False
    finally:
        if conn:
            conn.close()


# ---  Services ---

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def add_new_traveller(current_user: models.User, first_name, last_name, birthday, 
                   gender, street_name, house_number, zip_code, city, email, 
                   mobile_phone, driving_license_number):
    """Adds a new traveller to the database after validation and encryption."""
    # Predefined city list
    allowed_cities = [
        "Amsterdam", "Rotterdam", "Utrecht", "Eindhoven", "Groningen",
        "Maastricht", "Haarlem", "Leiden", "Nijmegen", "Zwolle"
    ]
    # Validate all fields
    if not validation.is_valid_first_name(first_name):
        print("Invalid First Name. Only letters, 2-30 characters.")
        return False
    if not validation.is_valid_last_name(last_name):
        print("Invalid Last Name. Only letters, 2-30 characters.")
        return False
    if not validation.is_valid_iso_date(birthday):
        print("Invalid Birthday. Format must be YYYY-MM-DD.")
        return False
    if not validation.is_valid_gender(gender):
        print("Invalid Gender. Must be 'male' or 'female'.")
        return False
    if not validation.is_valid_street_name(street_name):
        print("Invalid Street Name. Letters and spaces, 2-50 characters.")
        return False
    if not validation.is_valid_house_number(house_number):
        print("Invalid House Number. 1-6 digits.")
        return False
    if not validation.is_valid_zip_code(zip_code):
        print("Invalid Zip Code format. DDDDXX (e.g., 1234AB).")
        return False
    if city not in allowed_cities:
        print(f"Invalid City. Must be one of: {', '.join(allowed_cities)}")
        return False
    if not validation.is_valid_email(email):
        print("Invalid Email Address format.")
        return False
    if not validation.is_valid_phone_digits(mobile_phone):
        print("Invalid Mobile Phone. 8 digits required.")
        return False
    if not validation.is_valid_driving_license(driving_license_number):
        print("Invalid Driving License Number. XXDDDDDDD or XDDDDDDDD.")
        return False

    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 2. Encrypt all PII fields
        encrypted_data = {
            "first_name": encryption_manager.encrypt(first_name),
            "last_name": encryption_manager.encrypt(last_name),
            "birthday": encryption_manager.encrypt(birthday),
            "gender": encryption_manager.encrypt(gender),
            "street_name": encryption_manager.encrypt(street_name),
            "house_number": encryption_manager.encrypt(house_number),
            "zip_code": encryption_manager.encrypt(zip_code),
            "city": encryption_manager.encrypt(city),
            "email": encryption_manager.encrypt(email),
            "mobile_phone": encryption_manager.encrypt(mobile_phone),
            "driving_license_number": encryption_manager.encrypt(driving_license_number)
        }
        
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
        secure_logger.log(current_user.username, "Added new traveller", f"Traveller email: {email}")
        print("Traveller added successfully.")
        return True
    except Exception as e:
        print(f"An error occurred while adding traveller: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def search_travellers(current_user: models.User, search_key: str):
    """
    Searches for travellers by a partial key.
    NOTE: This is computationally expensive as it decrypts all records in memory.
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM travellers")
    all_travellers = cursor.fetchall()
    conn.close()

    results = []
    search_key_lower = search_key.lower()

    for row in all_travellers:
        decrypted_row = {key: encryption_manager.decrypt(value) if isinstance(value, bytes) else value for key, value in dict(row).items()}
        
        match = False
        for value in decrypted_row.values():
            if search_key_lower in str(value).lower():
                match = True
                break
        
        if match:
            results.append(decrypted_row)
            
    return results

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def update_traveller(current_user: models.User, traveller_id: int, new_data: dict):
    """Updates an existing traveller's information."""
    allowed_cities = [
        "Amsterdam", "Rotterdam", "Utrecht", "Eindhoven", "Groningen",
        "Maastricht", "Haarlem", "Leiden", "Nijmegen", "Zwolle"
    ]
    # Validate fields if present in update
    if 'first_name' in new_data and not validation.is_valid_first_name(new_data['first_name']):
        print("Invalid First Name. Only letters, 2-30 characters.")
        return False
    if 'last_name' in new_data and not validation.is_valid_last_name(new_data['last_name']):
        print("Invalid Last Name. Only letters, 2-30 characters.")
        return False
    if 'birthday' in new_data and not validation.is_valid_iso_date(new_data['birthday']):
        print("Invalid Birthday. Format must be YYYY-MM-DD.")
        return False
    if 'gender' in new_data and not validation.is_valid_gender(new_data['gender']):
        print("Invalid Gender. Must be 'male' or 'female'.")
        return False
    if 'street_name' in new_data and not validation.is_valid_street_name(new_data['street_name']):
        print("Invalid Street Name. Letters and spaces, 2-50 characters.")
        return False
    if 'house_number' in new_data and not validation.is_valid_house_number(new_data['house_number']):
        print("Invalid House Number. 1-6 digits.")
        return False
    if 'zip_code' in new_data and not validation.is_valid_zip_code(new_data['zip_code']):
        print("Invalid Zip Code format. DDDDXX (e.g., 1234AB).")
        return False
    if 'city' in new_data and new_data['city'] not in allowed_cities:
        print(f"Invalid City. Must be one of: {', '.join(allowed_cities)}")
        return False
    if 'email' in new_data and not validation.is_valid_email(new_data['email']):
        print("Invalid Email Address format.")
        return False
    if 'mobile_phone' in new_data and not validation.is_valid_phone_digits(new_data['mobile_phone']):
        print("Invalid Mobile Phone. 8 digits required.")
        return False
    if 'driving_license_number' in new_data and not validation.is_valid_driving_license(new_data['driving_license_number']):
        print("Invalid Driving License Number. XXDDDDDDD or XDDDDDDDD.")
        return False

    encrypted_data = {key: encryption_manager.encrypt(str(value)) for key, value in new_data.items()}
    
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Dynamically build the SET part of the query
    set_clause = ", ".join([f"{key} = ?" for key in encrypted_data.keys()])
    params = list(encrypted_data.values())
    params.append(traveller_id)
    
    query = f"UPDATE travellers SET {set_clause} WHERE id = ?"
    
    cursor.execute(query, tuple(params))
    
    if cursor.rowcount == 0:
        print(f"Error: Traveller with ID {traveller_id} not found.")
        conn.close()
        return False
        
    conn.commit()
    conn.close()
    secure_logger.log(current_user.username, "Updated traveller info", f"Traveller ID: {traveller_id}")
    print("Traveller information updated successfully.")
    return True

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def delete_traveller(current_user: models.User, traveller_id: int):
    """Deletes a traveller from the system."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM travellers WHERE id = ?", (traveller_id,))
    
    if cursor.rowcount == 0:
        print(f"Error: Traveller with ID {traveller_id} not found.")
        conn.close()
        return False

    conn.commit()
    conn.close()
    secure_logger.log(current_user.username, "Deleted traveller", f"Traveller ID: {traveller_id}", is_suspicious=True)
    print(f"Traveller with ID {traveller_id} deleted successfully.")
    return True

# --- Backup and Restore Services ---

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def create_backup(current_user: models.User):
    """Creates a timestamped zip archive of the database."""
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.zip"
    backup_filepath = os.path.join(backup_dir, backup_filename)
    
    try:
        with zipfile.ZipFile(backup_filepath, 'w') as zf:
            zf.write(config.DATABASE_FILE)
        
        secure_logger.log(current_user.username, "Created backup", f"File: {backup_filename}")
        print(f"Successfully created backup: {backup_filepath}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

@requires_role([config.ROLE_SUPER_ADMIN])
def generate_restore_code(current_user: models.User, target_system_admin_username: str, backup_filename: str):
    """Generates a one-time restore code for a System Administrator."""
    # Verify target user is a System Admin
    # ... (omitted for brevity)

    code = secrets.token_hex(16)
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO restore_codes (code, backup_filename, system_admin_username, generated_at) VALUES (?, ?, ?, ?)",
        (code, backup_filename, target_system_admin_username, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    
    secure_logger.log(current_user.username, "Generated restore code", f"For user {target_system_admin_username}, file {backup_filename}")
    print("\n--- Restore Code Generated ---")
    print(f"Code: {code}")
    print(f"Valid for user: {target_system_admin_username}")
    print(f"Valid for file: {backup_filename}")
    print("This is a one-time use code.")
    print("----------------------------\n")
    return code

@requires_role([config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN])
def restore_from_backup(current_user: models.User, backup_filename: str, restore_code: str = None):
    """Restores the database from a backup zip file."""
    backup_filepath = os.path.join("backups", backup_filename)
    if not os.path.exists(backup_filepath):
        print("Error: Backup file not found.")
        return False

    # System Admin restore logic
    if current_user.role == config.ROLE_SYSTEM_ADMIN:
        if not restore_code:
            print("Error: A restore code is required for System Administrators.")
            return False
            
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM restore_codes WHERE code = ? AND system_admin_username = ? AND backup_filename = ? AND is_used = 0",
            (restore_code, current_user.username, backup_filename)
        )
        code_data = cursor.fetchone()
        
        if not code_data:
            print("Error: Invalid, expired, or incorrect restore code for this backup/user.")
            secure_logger.log(current_user.username, "Failed backup restore", f"Invalid code used for {backup_filename}", is_suspicious=True)
            conn.close()
            return False
            
        # Invalidate the code
        cursor.execute("UPDATE restore_codes SET is_used = 1 WHERE id = ?", (code_data['id'],))
        conn.commit()
        conn.close()

    # Super Admin or validated System Admin can proceed
    try:
        with zipfile.ZipFile(backup_filepath, 'r') as zf:
            zf.extract(config.DATABASE_FILE, path=".")
        
        secure_logger.log(current_user.username, "Restored from backup", f"File: {backup_filename}", is_suspicious=True)
        print("\n!!! --- System Restored --- !!!")
        print("Database has been restored from backup.")
        print("It is recommended to restart the application.")
        print("!!! ----------------------- !!!\n")
        return True
    except Exception as e:
        print(f"An error occurred during restore: {e}")
        return False

# --- Log Services ---
def check_for_unread_suspicious_logs():
    """Checks for and alerts about unread suspicious logs."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logs WHERE suspicious = 1 AND is_read = 0")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count > 0:
        print("\n--- !!! SECURITY ALERT !!! ---")
        print(f"There are {count} unread suspicious activity logs.")
        print("Please review the system logs immediately.")
        print("----------------------------\n")

def mark_logs_as_read(log_ids: list[int]):
    """Marks a list of log IDs as read."""
    if not log_ids:
        return
    conn = database.get_db_connection()
    cursor = conn.cursor()
    # Create a placeholder string like (?, ?, ?)
    placeholders = ', '.join('?' for _ in log_ids)
    query = f"UPDATE logs SET is_read = 1 WHERE id IN ({placeholders}) AND suspicious = 1"
    cursor.execute(query, log_ids)
    conn.commit()
    conn.close()