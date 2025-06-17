# src/auth.py

import bcrypt
import getpass # Dit is een standaard-python library: zorgt ervoor dat de wachtwoord niet vertoont wordt tijdens het invullen
import config, services, models

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
    Handles the user login process.
    Returns a User object on success, None on failure.
    """
    username = input("Enter username: ").strip()
    password = getpass.getpass("Enter password: ") # Hides password input

    # --- Handle Super Administrator Login (Hard-coded) ---
    if username == config.SUPER_ADMIN_USERNAME:
        if password == config.SUPER_ADMIN_PASSWORD:
            print("Super Administrator logged in successfully.")
            # Create a mock User object for the super admin
            return models.User(
                id=0,
                username=config.SUPER_ADMIN_USERNAME,
                role=config.ROLE_SUPER_ADMIN,
                first_name="Super",
                last_name="Admin",
                registration_date="N/A"
            )
        else:
            print("Invalid credentials for Super Administrator.")
            return None

    # --- Handle Regular User Login (from Database) ---
    # This process is necessarily slow as it requires decrypting all usernames.
    # This is a security tradeoff: protects usernames at rest but impacts login performance.
    all_users_from_db = services.get_all_users_raw() # Gets all raw user data
    
    for user_row in all_users_from_db:
        decrypted_username = services.encryption_manager.decrypt(user_row['username'])
        
        # Case-insensitive comparison for username
        if decrypted_username.lower() == username.lower():
            # Username match found, now verify the password
            if verify_password(password, user_row['password_hash']):
                print(f"Welcome, {decrypted_username}!")
                return models.User(
                    id=user_row['id'],
                    username=decrypted_username,
                    role=user_row['role'],
                    first_name=user_row['first_name'],
                    last_name=user_row['last_name'],
                    registration_date=user_row['registration_date']
                )
            else:
                # Password incorrect for this username
                print("Invalid username or password.")
                # Log a failed attempt
                services.secure_logger.log(username, "Unsuccessful login", "Wrong password", is_suspicious=True)
                return None # Stop after first username match

    print("Invalid username or password.")
    services.secure_logger.log(username, "Unsuccessful login", "Username not found", is_suspicious=True)
    return None