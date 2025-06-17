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
        cursor.execute(
            # New logs are suspicious and unread by default
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
        cursor.execute("SELECT * FROM logs ORDER BY date DESC, time DESC LIMIT ?", (limit,))
        
        decrypted_logs = []
        log_ids_to_mark_read = []
        rows = cursor.fetchall()
        for row in rows:
            decrypted_log = {
                "id": row["id"],
                "date": row["date"],
                "time": row["time"],
                "username": self.encryption_manager.decrypt(row["username"]),
                "activity_description": self.encryption_manager.decrypt(row["description_of_activity"]),
                "additional_info": self.encryption_manager.decrypt(row["additional_information"]),
                "is_suspicious": "Yes" if row["suspicious"] == 1 else "No"
            }
            decrypted_logs.append(decrypted_log)
            log_ids_to_mark_read.append(row["id"])
        
        conn.close()

        # Mark the fetched logs as read
        if log_ids_to_mark_read:
            self.mark_logs_as_read(log_ids_to_mark_read)

        return decrypted_logs

    def mark_logs_as_read(self, log_ids: list[int]):
        """Marks a list of log entries as read."""
        if not log_ids:
            return
        conn = database.get_db_connection()
        cursor = conn.cursor()
        try:
            placeholders = ','.join('?' for _ in log_ids)
            cursor.execute(f"UPDATE logs SET is_read = 1 WHERE id IN ({placeholders})", log_ids)
            conn.commit()
        finally:
            conn.close()

    def check_unread_alerts(self) -> int:
        """Counts the number of unread suspicious log entries."""
        conn = database.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM logs WHERE suspicious = 1 AND is_read = 0")
            result = cursor.fetchone()
            return result['count'] if result else 0
        finally:
            conn.close()