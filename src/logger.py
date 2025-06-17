# src/logger.py

from datetime import datetime
from src import database, config
from src.encryption import EncryptionManager

class SecureLogger:
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager

    def log(self, username: str, activity_desc: str, additional_info: str = "", is_suspicious: bool = False):
        """
        Creates a formatted log entry, encrypts it, and saves it to the database.
        """
        timestamp = datetime.now().isoformat()
        
        # Format the log entry as a structured string before encryption
        log_entry_string = f"{timestamp}|{username}|{activity_desc}|{additional_info}|{is_suspicious}"
        
        # Encrypt the entire log string
        encrypted_log_data = self.encryption_manager.encrypt(log_entry_string)
        
        # Store the encrypted blob in the database
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (timestamp, log_data, is_suspicious) VALUES (?, ?, ?)",
            (timestamp, encrypted_log_data, 1 if is_suspicious else 0)
        )
        conn.commit()
        conn.close()

    def get_logs(self, limit: int = 100) -> list[str]:
        """
        Retrieves and decrypts the most recent log entries.
        """
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT log_data FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        
        decrypted_logs = []
        rows = cursor.fetchall()
        for row in rows:
            encrypted_data = row['log_data']
            decrypted_log = self.encryption_manager.decrypt(encrypted_data)
            decrypted_logs.append(decrypted_log)
            
        conn.close()
        return decrypted_logs