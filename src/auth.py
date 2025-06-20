# src/auth.py

import bcrypt
import getpass # Dit is een standaard-python library: zorgt ervoor dat de wachtwoord niet vertoont wordt tijdens het invullen
import time
import config, services, models, database
from encryption import EncryptionManager

login_attempts = {}
encryption_manager = EncryptionManager(config.ENCRYPTION_KEY_FILE)

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verifies a plain password against a stored bcrypt hash."""
    plain_password_bytes = plain_password.encode('utf-8')
    password_hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(plain_password_bytes, password_hash_bytes)

def decrypt_user_row(user_row):
    """Helper function to decrypt a user row from the database."""
    return models.User(
        id=user_row['id'],
        username=encryption_manager.decrypt(user_row['username']),
        role=user_row['role'],
        first_name=encryption_manager.decrypt(user_row['first_name']),
        last_name=encryption_manager.decrypt(user_row['last_name']),
        registration_date=user_row['registration_date']
    )

def login() -> models.User | None:
    """
    Handles the user login process with brute-force protection.
    Returns a User object on success, None on failure.
    """
    username = input("Enter username: ").strip()

    # --- Brute-Force Protection Check ---
    if username.lower() in login_attempts:
        attempts, last_attempt_time = login_attempts[username.lower()]
        if attempts >= config.MAX_LOGIN_ATTEMPTS:
            time_since_last_attempt = time.time() - last_attempt_time
            if time_since_last_attempt < config.LOCKOUT_TIME_SECONDS:
                remaining_lockout = config.LOCKOUT_TIME_SECONDS - time_since_last_attempt
                print(f"Too many failed login attempts. Please try again in {remaining_lockout:.0f} seconds.")
                return None
            else:
                del login_attempts[username.lower()]

    password = getpass.getpass("Enter password: (When entering the password it is hidden by getpass, you are still typing) ") # Hides password input

    # --- Handle User Login (from Database) ---
    all_users_from_db = services.get_all_users_raw() # Gets all raw user data
    
    user_found = False
    for user_row in all_users_from_db:
        decrypted_username = services.encryption_manager.decrypt(user_row['username'])
        
        if decrypted_username.lower() == username.lower():
            user_found = True
            if verify_password(password, user_row['password_hash']):
                print(f"Welcome, {decrypted_username}!")

                if username.lower() in login_attempts:
                    del login_attempts[username.lower()]

                logged_in_user = decrypt_user_row(user_row)

                # --- NEW: Check for unread suspicious logs for admins ---
                if logged_in_user.role in [config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN]:
                    services.check_for_unread_suspicious_logs()

                return logged_in_user
            else:
                break

    # --- Handle Failed Login ---
    if username.lower() in login_attempts:
        attempts, _ = login_attempts[username.lower()]
        login_attempts[username.lower()] = (attempts + 1, time.time())
    else:
        login_attempts[username.lower()] = (1, time.time())

    print("Invalid username or password.")
    return None

def get_user_by_username(username: str) -> models.User | None:
    """Finds a user by their plaintext username and returns a User object."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    all_users = cursor.fetchall()
    conn.close()

    for user_row in all_users:
        try:
            decrypted_username = encryption_manager.decrypt(user_row['username'])
            if decrypted_username.lower() == username.lower():
                return decrypt_user_row(user_row)
        except Exception:
            continue
    return None