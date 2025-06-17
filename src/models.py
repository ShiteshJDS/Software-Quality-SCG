# src/models.py

from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str # This will hold the DECRYPTED username for in-memory use
    role: str
    first_name: str
    last_name: str
    registration_date: str

@dataclass
class Traveller:
    id: int
    customer_id: str
    first_name: str
    last_name: str
    birthday: str
    gender: str
    address: str
    email: str
    phone_number: str
    driving_license: str
    registration_date: str

@dataclass
class Scooter:
    id: int
    serial_number: str
    brand: str
    model: str
    # Add all other scooter fields from the DB schema