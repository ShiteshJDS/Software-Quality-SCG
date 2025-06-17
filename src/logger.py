# src/logger.py

from datetime import datetime
import database, config
from encryption import EncryptionManager

class SecureLogger:
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager

    def log(self, username: str, activity_desc: str, additional_info: str = "", is_suspicious: bool = False):
        """
        Creates a formatted log entry, encrypts it, and saves it to the database.
        """
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        
        # Encrypt sensitive log data
        encrypted_username = self.encryption_manager.encrypt(username)
        encrypted_activity_desc = self.encryption_manager.encrypt(activity_desc)
        encrypted_additional_info = self.encryption_manager.encrypt(additional_info)

        # Store the encrypted blob in the database
        conn = database.get_db_connection()
        cursor = conn.cursor()
        # MODIFIED: Added the `is_read` column to the INSERT statement
        cursor.execute(
            "INSERT INTO logs (date, time, username, description_of_activity, additional_information, suspicious, is_read) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date, time, encrypted_username, encrypted_activity_desc, encrypted_additional_info, 1 if is_suspicious else 0, 0)
        )
        conn.commit()
        conn.close()

    def get_logs(self, limit: int = 100) -> list[dict]:
        """
        Retrieves and decrypts the most recent log entries.
        """
        conn = database.get_db_connection()
        cursor = conn.cursor()
        # MODIFIED: Select all columns including the new ones
        cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        
        decrypted_logs = []
        rows = cursor.fetchall()
        for row in rows:
            decrypted_log = {
                "id": row["id"],
                "date": row["date"],
                "time": row["time"],
                "username": self.encryption_manager.decrypt(row["username"]),
                "activity_description": self.encryption_manager.decrypt(row["description_of_activity"]),
                "additional_info": self.encryption_manager.decrypt(row["additional_information"]),
                "is_suspicious": "Yes" if row["suspicious"] == 1 else "No",
                "is_read": "Yes" if row["is_read"] == 1 else "No"
            }
            decrypted_logs.append(decrypted_log)
            
        conn.close()
        return decrypted_logs