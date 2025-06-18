# src/auth.py

import bcrypt
import getpass # Dit is een standaard-python library: zorgt ervoor dat de wachtwoord niet vertoont wordt tijdens het invullen
import time
import config, services, models

# In-memory dictionary to track login attempts.
# In a real-world application, this should be a more persistent store like Redis or a database table.
login_attempts = {}

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
                # Lockout has expired, reset attempts
                del login_attempts[username.lower()]

    password = getpass.getpass("Enter password: (When entering the password it is hidden by getpass, you are still typing) ") # Hides password input

    # --- Handle User Login (from Database) ---
    # This process is necessarily slow as it requires decrypting all usernames.
    # This is a security tradeoff: protects usernames at rest but impacts login performance.
    all_users_from_db = services.get_all_users_raw() # Gets all raw user data
    
    user_found = False
    for user_row in all_users_from_db:
        decrypted_username = services.encryption_manager.decrypt(user_row['username'])
        
        # Case-insensitive comparison for username
        if decrypted_username.lower() == username.lower():
            user_found = True
            # Username match found, now verify the password
            if verify_password(password, user_row['password_hash']):
                print(f"Welcome, {decrypted_username}!")

                # Reset failed login attempts for this user
                if username.lower() in login_attempts:
                    del login_attempts[username.lower()]

                logged_in_user = models.User(
                    id=user_row['id'],
                    username=decrypted_username,
                    role=user_row['role'],
                    first_name=services.encryption_manager.decrypt(user_row['first_name']),
                    last_name=services.encryption_manager.decrypt(user_row['last_name']),
                    registration_date=user_row['registration_date']
                )

                # --- NEW: Check for unread suspicious logs for admins ---
                if logged_in_user.role in [config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN]:
                    services.check_for_unread_suspicious_logs()

                return logged_in_user
            else:
                # Password incorrect for this username, break and handle failure
                break

    # --- Handle Failed Login ---
    print("Invalid username or password.")
    
    # Log a failed attempt
    log_message = "Wrong password" if user_found else "Username not found"
    services.secure_logger.log(username, "Unsuccessful login", log_message, is_suspicious=True)

    # Update failed login attempts
    attempts, _ = login_attempts.get(username.lower(), (0, 0))
    login_attempts[username.lower()] = (attempts + 1, time.time())
    
    if attempts + 1 >= config.MAX_LOGIN_ATTEMPTS:
        print(f"Account locked for {config.LOCKOUT_TIME_SECONDS / 60:.0f} minutes due to multiple failed attempts.")

    return None