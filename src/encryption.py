# src/encryption.py

import os
from cryptography.fernet import Fernet, InvalidToken

class EncryptionManager:
    """
    Manages loading, generating, and using a Fernet key for symmetric encryption.
    """
    def __init__(self, key_path: str):
        self.key_path = key_path
        self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self):
        """Loads the key from key_path or generates a new one if it doesn't exist."""
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as key_file:
                self.key = key_file.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_path, 'wb') as key_file:
                key_file.write(self.key)
            print(f"Generated new encryption key at: {self.key_path}")

    def encrypt(self, data: str) -> bytes:
        """
        Encrypts a string.
        Args:
            data: The string to encrypt.
        Returns:
            The encrypted bytes.
        """
        if not isinstance(data, str):
            raise TypeError("Data to be encrypted must be a string.")
        encoded_data = data.encode('utf-8')
        return self.cipher.encrypt(encoded_data)

    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Decrypts bytes back into a string.
        Args:
            encrypted_data: The bytes to decrypt.
        Returns:
            The decrypted string.
        """
        if not isinstance(encrypted_data, bytes):
            raise TypeError("Data to be decrypted must be bytes.")
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except InvalidToken:
            # This error occurs if the key is wrong or the data is corrupt
            return "" # Return empty string or handle as a critical error