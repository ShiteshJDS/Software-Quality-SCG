# src/models.py

from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
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
    in_service_date: str
    top_speed: int
    battery_capacity: int
    state_of_charge: int
    target_range_soc_min: int
    target_range_soc_max: int
    location_lat: str
    location_lon: str
    out_of_service_status: bool
    mileage: int
    last_maintenance_date: str

@dataclass
class Log:
    id: int
    date: str
    time: str
    username: str
    description_of_activity: str
    additional_information: str
    suspicious: str