# src/validation.py

import re
from datetime import datetime

def is_valid_username(username: str) -> bool:
    """
    Validates a username based on assignment rules.
    - Length: 8-10 characters.
    - Starts with a letter or underscore.
    - Can contain letters, numbers, underscores, apostrophes, and periods.
    """
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_'.]{7,9}$"
    return re.match(pattern, username) is not None

def is_valid_password(password: str) -> bool:
    """
    Validates a password based on assignment rules.
    - Length: 12-30 characters.
    - Must contain at least one lowercase letter, one uppercase letter,
      one digit, and one special character.
    """
    if not 12 <= len(password) <= 30:
        return False
    
    # Positive lookaheads to ensure each character type is present
    patterns = [
        r"(?=.*[a-z])",        # At least one lowercase letter
        r"(?=.*[A-Z])",        # At least one uppercase letter
        r"(?=.*\d)",           # At least one digit
        r"(?=.*[~!@#$%^&*()_+=\`{}\[\]:;'<>,.?/|\\-])" # At least one special character
    ]
    
    full_pattern = "".join(patterns) + r".{12,30}$"
    return re.match(full_pattern, password) is not None

def is_valid_zip_code(zip_code: str) -> bool:
    """Validates Zip Code format: DDDDXX."""
    pattern = r"^\d{4}[A-Z]{2}$"
    return re.match(pattern, zip_code) is not None

def is_valid_phone_digits(digits: str) -> bool:
    """Validates phone number digits: DDDDDDDD."""
    pattern = r"^\d{8}$"
    return re.match(pattern, digits) is not None

def is_valid_driving_license(license_num: str) -> bool:
    """Validates Driving License: XXDDDDDDD or XDDDDDDDD."""
    # This pattern precisely matches a 9-character string that is
    # either 1 letter followed by 8 digits, or 2 letters followed by 7 digits.
    pattern = r"^(?:[A-Z]{1}\d{8}|[A-Z]{2}\d{7})$"
    return re.match(pattern, license_num.upper()) is not None

def is_valid_scooter_serial(serial: str) -> bool:
    """Validates Scooter Serial Number: 10 to 17 alphanumeric characters."""
    pattern = r"^[a-zA-Z0-9]{10,17}$"
    return re.match(pattern, serial) is not None

def is_valid_location_coordinate(coord: str) -> bool:
    """Validates GPS coordinate format with 5 decimal places."""
    pattern = r"^-?\d+\.\d{5}$"
    return re.match(pattern, str(coord)) is not None

def is_valid_iso_date(date_string: str) -> bool:
    """Validates date format: YYYY-MM-DD."""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False