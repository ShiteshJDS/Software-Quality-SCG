# src/backup_manager.py

import os
import shutil
import zipfile
import secrets
from datetime import datetime
import database

BACKUP_DIR = 'backups'

def _initialize_backup_dir():
    """Ensures the backup directory exists."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def create_backup():
    """
    Creates a compressed zip archive of the database file.
    The backup is timestamped and stored in the backup directory.
    """
    _initialize_backup_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup-{timestamp}.zip"
    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)
    db_file = database.config.DATABASE_FILE

    if not os.path.exists(db_file):
        print(f"Error: Database file '{db_file}' not found.")
        return None

    try:
        with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_file, os.path.basename(db_file))
        print(f"Successfully created backup: {backup_filepath}")
        return backup_filepath
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def list_backups():
    """Returns a list of available backup files."""
    _initialize_backup_dir()
    try:
        return sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith('.zip')])
    except FileNotFoundError:
        return []

def restore_backup(backup_filename: str):
    """
    Restores the database from a specified backup zip file.
    WARNING: This overwrites the current database.
    """
    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)
    db_file = database.config.DATABASE_FILE

    if not os.path.exists(backup_filepath):
        print("Error: Backup file not found.")
        return False

    try:
        # It's crucial that any active database connections are closed before this.
        # The service layer will handle this.
        with zipfile.ZipFile(backup_filepath, 'r') as zf:
            zf.extractall(path='.') # Extracts to the root project directory
        print(f"Successfully restored database from {backup_filename}")
        # Re-initialize the database to ensure tables are created if the backup was empty
        database.initialize_database()
        return True
    except Exception as e:
        print(f"An error occurred during restore: {e}")
        return False

def generate_restore_code(username: str, backup_filename: str):
    """
    Generates a secure, one-time restore code for a specific user and backup.
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    try:
        one_time_code = secrets.token_hex(16)
        cursor.execute(
            """
            INSERT INTO restore_codes (code, username, backup_filename, expires_at, is_used)
            VALUES (?, ?, ?, ?, ?)
            """,
            (one_time_code, username, backup_filename, datetime.now(), 0) # Expiry not implemented as per spec, but can be added
        )
        conn.commit()
        print(f"Generated restore code for user '{username}'.")
        return one_time_code
    except Exception as e:
        print(f"Error generating restore code: {e}")
        return None
    finally:
        conn.close()

def verify_and_use_code(code: str, username: str):
    """
    Verifies a restore code for a user. Marks the code as used if valid.
    Returns the associated backup filename on success, None on failure.
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT backup_filename FROM restore_codes WHERE code = ? AND username = ? AND is_used = 0",
            (code, username)
        )
        result = cursor.fetchone()

        if result:
            backup_filename = result['backup_filename']
            # Mark code as used
            cursor.execute("UPDATE restore_codes SET is_used = 1 WHERE code = ?", (code,))
            conn.commit()
            print("Restore code verified and invalidated.")
            return backup_filename
        else:
            print("Invalid or already used restore code.")
            return None
    except Exception as e:
        print(f"Error verifying code: {e}")
        return None
    finally:
        conn.close()