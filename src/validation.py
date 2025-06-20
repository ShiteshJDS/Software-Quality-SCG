# src/validation.py

import re
from datetime import datetime

def _is_safe_string(s: str) -> bool:
    """
    Internal check for unsafe characters, starting with null bytes, to prevent injection attacks.
    Returns False if the string is unsafe.
    """
    if '\0' in str(s):
        return False
    return True

def is_valid_username(username: str) -> bool:
    """
    Validates a username based on assignment rules.
    - Length: 8-10 characters.
    - Starts with a letter or underscore.
    - Can contain letters, numbers, underscores, apostrophes, and periods.
    """
    if not _is_safe_string(username): return False
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_'.]{7,9}$"
    return re.match(pattern, username) is not None

def is_valid_password(password: str) -> bool:
    """
    Validates a password based on assignment rules.
    - Length: 12-30 characters.
    - Must contain at least one lowercase letter, one uppercase letter,
      one digit, and one special character.
    """
    if not _is_safe_string(password): return False
    if not 12 <= len(password) <= 30:
        return False
    
    patterns = [
        r"(?=.*[a-z])",        
        r"(?=.*[A-Z])",        
        r"(?=.*\d)",           
        r"(?=.*[~!@#$%^&*()_+=\`{}\[\]:;'<>,.?/|\\-])" 
    ]
    
    full_pattern = "".join(patterns) + r".{12,30}$"
    return re.match(full_pattern, password) is not None

def is_valid_zip_code(zip_code: str) -> bool:
    """Validates Zip Code format: DDDDXX."""
    if not _is_safe_string(zip_code): return False
    pattern = r"^\d{4}[A-Z]{2}$"
    return re.match(pattern, zip_code) is not None

def is_valid_phone_digits(digits: str) -> bool:
    """Validates phone number digits: DDDDDDDD."""
    if not _is_safe_string(digits): return False
    pattern = r"^\d{8}$"
    return re.match(pattern, digits) is not None

def is_valid_driving_license(license_num: str) -> bool:
    """Validates Driving License: XXDDDDDDD or XDDDDDDDD."""
    if not _is_safe_string(license_num): return False
    pattern = r"^(?:[A-Z]{1}\d{8}|[A-Z]{2}\d{7})$"
    return re.match(pattern, license_num.upper()) is not None

def is_valid_scooter_serial(serial: str) -> bool:
    """Validates Scooter Serial Number: 10 to 17 alphanumeric characters."""
    if not _is_safe_string(serial): return False
    pattern = r"^[a-zA-Z0-9]{10,17}$"
    return re.match(pattern, serial) is not None


def is_valid_location_coordinate(coord: str) -> bool:
    """Validates GPS coordinate format (a number with an optional sign and at least 5 decimal places for 2-meter accuracy)."""
    if not _is_safe_string(coord): return False
    pattern = r"^[+-]?\d+\.\d{5,}$"
    return re.match(pattern, str(coord)) is not None


def is_in_rotterdam_region(latitude: float, longitude: float) -> bool:
    """
    Validates if the given GPS coordinates are within the Rotterdam region.
    """
    # Bounding box
    MIN_LAT, MAX_LAT = 51.8, 52.0
    MIN_LON, MAX_LON = 4.3, 4.6

    if not (MIN_LAT <= latitude <= MAX_LAT):
        return False
    if not (MIN_LON <= longitude <= MAX_LON):
        return False
    return True


def is_valid_iso_date(date_string: str) -> bool:
    """Validates date format: YYYY-MM-DD and ensures it's not in the future."""
    if not _is_safe_string(date_string): return False
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d').date()
        if date_obj > datetime.now().date():
            return False
        return True
    except ValueError:
        return False

def is_valid_first_name(name: str) -> bool:
    """Validates first name: only letters, 2-30 chars."""
    if not _is_safe_string(name): return False
    return bool(re.match(r"^[A-Za-z]{2,30}$", name))

def is_valid_last_name(name: str) -> bool:
    """Validates last name: only letters, 2-30 chars."""
    if not _is_safe_string(name): return False
    return bool(re.match(r"^[A-Za-z]{2,30}$", name))

def is_valid_email(email: str) -> bool:
    """Validates email address format."""
    if not _is_safe_string(email): return False
    pattern = r"^[\w.-]+@[\w.-]+\.\w{2,}$"
    return re.match(pattern, email) is not None

def is_valid_gender(gender: str) -> bool:
    """Validates gender: must be 'male' or 'female'."""
    if not _is_safe_string(gender): return False
    return gender.lower() in ['male', 'female']

def is_valid_house_number(house_number: str) -> bool:
    """Validates house number: 1-6 digits."""
    if not _is_safe_string(house_number): return False
    return bool(re.match(r"^\d{1,6}$", str(house_number)))

def is_valid_street_name(street: str) -> bool:
    """Validates street name: letters, spaces, 2-50 chars."""
    if not _is_safe_string(street): return False
    return bool(re.match(r"^[A-Za-z ]{2,50}$", street))