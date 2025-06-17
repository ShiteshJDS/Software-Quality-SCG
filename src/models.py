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
    first_name: str
    last_name: str
    birthday: str
    gender: str
    street_name: str
    house_number: str
    zip_code: str
    city: str
    email: str
    mobile_phone: str
    driving_license_number: str
    registration_date: str

@dataclass
class Scooter:
    id: int
    serial_number: str
    brand: str
    model: str
    # Add all other scooter fields from the DB schema

@dataclass
class Log:
    id: int
    date: str
    time: str
    username: str
    description_of_activity: str
    additional_information: str
    suspicious: str