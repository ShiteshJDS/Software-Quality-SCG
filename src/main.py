# src/main.py

import getpass
import database, auth, config, services, models, validation
from datetime import datetime

# --- UI Helper Functions ---

def print_header(title: str):
    """Prints a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title.center(58)} ")
    print("=" * 60)

def display_results(results: list[dict]):
    """Displays a list of dictionaries in a formatted table."""
    if not results:
        print("No results found.")
        return
    
    headers = results[0].keys()
    # Simple dynamic column width, with a max
    col_widths = {h: max(len(h), max((len(str(r.get(h, ''))) for r in results), default=0)) for h in headers}
    for h in col_widths:
        col_widths[h] = min(col_widths[h], 30) # Max width to prevent overly wide columns

    header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
    print("\n" + header_line)
    print("-" * len(header_line))
    
    for row in results:
        row_line = " | ".join(str(row.get(h, '')).ljust(col_widths[h]) for h in headers)
        print(row_line)
    print()

# --- Input Validation and Prompting ---

def prompt_with_validation(prompt_text: str, validation_func, error_message: str, optional: bool = False, transform_func=None):
    """Prompts user for input and validates it using the provided function. Loops until valid input is given."""
    while True:
        user_input = input(prompt_text)
        if optional and not user_input:
            return None
        
        if validation_func(user_input):
            return transform_func(user_input) if transform_func else user_input
        else:
            print(f"Invalid input: {error_message}")

def prompt_for_float(prompt_text: str, min_val=None, max_val=None, optional: bool = False):
    """Prompts user for a float and validates range. Loops until valid input is given."""
    while True:
        user_input = input(prompt_text)
        if optional and not user_input:
            return None
        try:
            value = float(user_input)
            if (min_val is not None and value < min_val) or \
               (max_val is not None and value > max_val):
                range_msg = []
                if min_val is not None: range_msg.append(f"at least {min_val}")
                if max_val is not None: range_msg.append(f"at most {max_val}")
                print(f"Value is out of range. Please enter a value {' and '.join(range_msg)}.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a number.")

def prompt_for_int(prompt_text: str, min_val=None, max_val=None, optional: bool = False):
    """Prompts user for an integer and validates range. Loops until valid input is given."""
    while True:
        user_input = input(prompt_text)
        if optional and not user_input:
            return None
        try:
            value = int(user_input)
            if (min_val is not None and value < min_val) or \
               (max_val is not None and value > max_val):
                range_msg = []
                if min_val is not None: range_msg.append(f"at least {min_val}")
                if max_val is not None: range_msg.append(f"at most {max_val}")
                print(f"Value is out of range. Please enter a value {' and '.join(range_msg)}.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a number.")


# --- Input Prompt Functions ---

def prompt_for_new_user(creator_role):
    """Gets data for a new user from the console with immediate validation."""
    print_header("Add New User")
    print_user_syntax_rules()

    username = prompt_with_validation(
        "Enter username: ",
        validation.is_valid_username,
        "Username must be 8-10 chars, start with letter/_, and contain only letters, numbers, _, ', '.",
        optional=False
    )
    
    while True:
        password = getpass.getpass("Enter password: ")
        if validation.is_valid_password(password):
            break
        else:
            print("Password does not meet requirements. Please try again.")
    
    allowed_roles = []
    if creator_role == config.ROLE_SUPER_ADMIN:
        allowed_roles = [config.ROLE_SYSTEM_ADMIN, config.ROLE_SERVICE_ENGINEER]
    elif creator_role == config.ROLE_SYSTEM_ADMIN:
        allowed_roles = [config.ROLE_SERVICE_ENGINEER]

    if not allowed_roles:
        print("You are not authorized to create new users.")
        return None

    role = None
    while role is None:
        print("Allowed roles to create: " + ", ".join(allowed_roles))
        role_input = input(f"Enter role ({'/'.join(r.split()[0] for r in allowed_roles)}): ").strip().lower()
        if 'system' in role_input and config.ROLE_SYSTEM_ADMIN in allowed_roles:
            role = config.ROLE_SYSTEM_ADMIN
        elif 'service' in role_input and config.ROLE_SERVICE_ENGINEER in allowed_roles:
            role = config.ROLE_SERVICE_ENGINEER
        else:
            print("Invalid role selected.")

    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")
    
    return {
        "username": username, "password": password, "role": role,
        "first_name": first_name, "last_name": last_name
    }

def print_user_syntax_rules():
    print("""
User Account Syntax Rules:
- Username:
  - Length: 8-10 characters.
  - Starts with a letter or underscore.
  - Allowed characters: letters, numbers, underscore, apostrophe, period.
  - Case-insensitive.
- Password:
  - Length: 12-30 characters.
  - Must contain at least one lowercase letter, one uppercase letter, one digit, and one special character (~!@#$%&_-+=`|\(){}[]:;'<>,.?/).
""")

def print_traveller_syntax_rules():
    print("""
Traveller Data Attribute Syntax Rules:
- First Name: Only letters, 2-30 characters.
- Last Name: Only letters, 2-30 characters.
- Birthday: Format YYYY-MM-DD (e.g., 1990-12-31).
- Gender: 'male' or 'female'.
- Street Name: Letters and spaces, 2-50 characters.
- House Number: 1-6 digits.
- Zip Code: DDDDXX (e.g., 1234AB).
- City: Must be one of the predefined list.
- Email Address: Standard email format (e.g., user@example.com).
- Mobile Phone: 8 digits (e.g., 12345678, will be stored as +31-6-12345678).
- Driving License Number: XXDDDDDDD or XDDDDDDDD (e.g., AB1234567 or A12345678).
""")

def prompt_for_new_traveller():
    """Gets data for a new traveller from the console with immediate validation."""
    print_header("Add New Traveller")
    print_traveller_syntax_rules()
    data = {}
    data['first_name'] = prompt_with_validation("Enter first name: ", validation.is_valid_first_name, "Only letters, 2-30 characters.")
    data['last_name'] = prompt_with_validation("Enter last name: ", validation.is_valid_last_name, "Only letters, 2-30 characters.")
    data['birthday'] = prompt_with_validation("Enter birthday (YYYY-MM-DD): ", validation.is_valid_iso_date, "Format must be YYYY-MM-DD.")
    data['gender'] = prompt_with_validation("Enter gender (male/female): ", validation.is_valid_gender, "Must be 'male' or 'female'.", str.lower)
    data['street_name'] = prompt_with_validation("Enter street name: ", validation.is_valid_street_name, "Letters and spaces, 2-50 characters.")
    data['house_number'] = prompt_with_validation("Enter house number: ", validation.is_valid_house_number, "1-6 digits.")
    data['zip_code'] = prompt_with_validation("Enter zip code (e.g., 1234AB): ", validation.is_valid_zip_code, "Format must be DDDDXX.", str.upper)
    
    print("--- Predefined Cities ---")
    for i, city in enumerate(config.PREDEFINED_CITIES, 1):
        print(f"{i}. {city}")
    
    city_choice = prompt_for_int("Choose a city (number): ", 1, len(config.PREDEFINED_CITIES))
    data['city'] = config.PREDEFINED_CITIES[city_choice - 1]

    data['email'] = prompt_with_validation("Enter email address: ", validation.is_valid_email, "Standard email format (e.g., user@example.com).")
    data['mobile_phone'] = prompt_with_validation("Enter 8-digit mobile number (e.g., 12345678): ", validation.is_valid_phone_digits, "8 digits required.")
    data['driving_license_number'] = prompt_with_validation("Enter driving license (e.g., AB1234567): ", validation.is_valid_driving_license, "XXDDDDDDD or XDDDDDDDD.", str.upper)
    return data

def print_scooter_syntax_rules():
    print("""
Scooter Data Attribute Syntax Rules:
- Serial Number: 10 to 17 alphanumeric characters.
- Top Speed: Number (e.g., 25.5).
- Battery Capacity: Number (e.g., 1000).
- State of Charge (SoC): Percentage (0-100).
- Target SoC Min/Max: Percentage (0-100).
- Location (Lat/Lon): Real-world coordinates with at least 5 decimal places (e.g., 51.92250, 4.47917) In rotterdam between 51.8, 52.0
    MIN_LON, MAX_LON = 4.3, 4.6.
- Out-of-service Status: 0 for In-Service, 1 for Out-of-Service.
- Mileage: Number (e.g., 150.7).
- Last Maintenance Date: Format YYYY-MM-DD (e.g., 2025-06-18).
""")

def prompt_for_new_scooter():
    """Gets data for a new scooter from the console with immediate validation."""
    print_header("Add New Scooter")
    print_scooter_syntax_rules()
    data = {}

    data['serial_number'] = prompt_with_validation(
        "Enter serial number (10-17 alphanumeric): ",
        validation.is_valid_scooter_serial,
        "Must be 10 to 17 alphanumeric characters."
    )
    data['brand'] = input("Enter brand: ")
    data['model'] = input("Enter model: ")
    data['top_speed'] = prompt_for_float("Enter top speed (km/h): ", min_val=0)
    data['battery_capacity'] = prompt_for_float("Enter battery capacity (Wh): ", min_val=0)
    data['state_of_charge'] = prompt_for_float("Enter initial State of Charge (%): ", min_val=0, max_val=100)
    
    while True:
        min_soc = prompt_for_float("Enter Target SoC Min (%): ", min_val=0, max_val=100)
        max_soc = prompt_for_float(f"Enter Target SoC Max (%): ", min_val=min_soc, max_val=100)
        if max_soc >= min_soc:
            data['target_range_soc_min'] = min_soc
            data['target_range_soc_max'] = max_soc
            break
        else:
            print("Max SoC cannot be less than Min SoC.")

    while True:
        location_lat = prompt_with_validation(
            "Enter initial latitude (e.g., 51.92250): ",
            validation.is_valid_location_coordinate,
            "Must be a valid coordinate with at least 5 decimal places."
        )
        location_lon = prompt_with_validation(
            "Enter initial longitude (e.g., 4.47917): ",
            validation.is_valid_location_coordinate,
            "Must be a valid coordinate with at least 5 decimal places."
        )
        if validation.is_in_rotterdam_region(float(location_lat), float(location_lon)):
            data['location_lat'] = location_lat
            data['location_lon'] = location_lon
            break
        else:
            print("Location is outside of the Rotterdam region. Please enter coordinates within the valid range.")

    data['mileage'] = prompt_for_float("Enter initial mileage (km): ", min_val=0)
    data['last_maintenance_date'] = prompt_with_validation(
        "Enter last maintenance date (YYYY-MM-DD): ",
        validation.is_valid_iso_date,
        "Format must be YYYY-MM-DD."
    )
    return data

def prompt_for_scooter_update(current_user: models.User):
    """Gets data for updating a scooter with immediate validation."""
    print_header("Update Scooter Details")
    
    scooter_id = prompt_for_int("Enter Scooter ID to update: ")
    if scooter_id is None:
        return None, None

    # Fetch current scooter data to validate location updates
    current_scooter = services.get_scooter_details(current_user, scooter_id)
    if not current_scooter:
        return None, None # Error already printed by service

    print("Enter new data. Press Enter to skip a field.")
    print_scooter_syntax_rules()
    
    update_data = {}
    
    # Define editable fields based on role
    is_admin = current_user.role in [config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN]
    
    # --- Admin Fields ---
    if is_admin:
        brand = input("New brand: ")
        if brand: update_data['brand'] = brand
        
        model = input("New model: ")
        if model: update_data['model'] = model

        serial = prompt_with_validation("New serial_number: ", validation.is_valid_scooter_serial, "Must be 10-17 alphanumeric.", optional=True)
        if serial: update_data['serial_number'] = serial

        top_speed = prompt_for_float("New top_speed: ", min_val=0, optional=True)
        if top_speed is not None: update_data['top_speed'] = top_speed

        battery_capacity = prompt_for_float("New battery_capacity: ", min_val=0, optional=True)
        if battery_capacity is not None: update_data['battery_capacity'] = battery_capacity

    # --- Shared Fields ---
    soc = prompt_for_float("New state_of_charge: ", min_val=0, max_val=100, optional=True)
    if soc is not None: update_data['state_of_charge'] = soc

    min_soc = prompt_for_float("New target_range_soc_min: ", min_val=0, max_val=100, optional=True)
    if min_soc is not None: update_data['target_range_soc_min'] = min_soc
    
    # Ensure max_soc is >= min_soc if both are updated
    max_soc_min = update_data.get('target_range_soc_min', 0)
    max_soc = prompt_for_float(f"New target_range_soc_max: ", min_val=max_soc_min, max_val=100, optional=True)
    if max_soc is not None: update_data['target_range_soc_max'] = max_soc

    # --- Location Update ---
    # Loop until valid coordinates in the Rotterdam region are provided, or the user skips.
    while True:
        lat = prompt_with_validation("New location_lat (optional): ", validation.is_valid_location_coordinate, "Must be a valid coordinate.", optional=True)
        lon = prompt_with_validation("New location_lon (optional): ", validation.is_valid_location_coordinate, "Must be a valid coordinate.", optional=True)

        # If user provides neither, we break and move on.
        if not lat and not lon:
            break

        # Determine the final coordinates for validation. Use existing if new is not provided.
        final_lat = float(lat) if lat else float(current_scooter['location_lat'])
        final_lon = float(lon) if lon else float(current_scooter['location_lon'])

        if validation.is_in_rotterdam_region(final_lat, final_lon):
            # If valid, add the provided values to the update dictionary.
            if lat: update_data['location_lat'] = lat
            if lon: update_data['location_lon'] = lon
            break  # Exit the loop on success.
        else:
            print("Error: Location is outside of the Rotterdam region. Both latitude and longitude must be corrected or left blank.")
            # Loop continues, prompting for both again.

    status = prompt_for_int("New out_of_service_status (0 or 1): ", min_val=0, max_val=1, optional=True)
    if status is not None: update_data['out_of_service_status'] = status

    mileage = prompt_for_float("New mileage: ", min_val=0, optional=True)
    if mileage is not None: update_data['mileage'] = mileage

    maint_date = prompt_with_validation("New last_maintenance_date (YYYY-MM-DD): ", validation.is_valid_iso_date, "Format must be YYYY-MM-DD.", optional=True)
    if maint_date: update_data['last_maintenance_date'] = maint_date
            
    if not update_data:
        print("No changes specified.")
        return None, None
            
    return scooter_id, update_data

# --- Handler Functions for Menu Choices ---

def handle_view_logs(current_user: models.User):
    """Handles viewing system logs and marking them as read."""
    print_header("System Logs")
    logs = services.secure_logger.get_logs(limit=25)
    display_results(logs)
    
    # Mark the viewed suspicious logs as read
    suspicious_log_ids = [log['id'] for log in logs if log['is_suspicious'] == 'Yes' and log['is_read'] == 'No']
    if suspicious_log_ids:
        services.mark_logs_as_read(suspicious_log_ids)
        print("\nUnread suspicious logs have been marked as read.")

def handle_update_own_password(current_user: models.User):
    print_header("Update My Password")
    print_user_syntax_rules()
    old_password = getpass.getpass("Enter your current password: ")
    new_password = getpass.getpass("Enter your new password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    if new_password != confirm_password:
        print("New passwords do not match.")
        return
    services.update_own_password(current_user, old_password, new_password)

# --- Role-Specific Menus ---

def show_service_engineer_menu(current_user: models.User):
    """Displays the menu for Service Engineers."""
    while True:
        print_header(f"Service Engineer Menu | Logged in as: {current_user.username}")
        print("\n--- Scooter Management ---")
        print("1. Update Scooter Details")
        print("2. Search for Scooter")
        print("\n--- Self-Service ---")
        print("3. Update My Password")
        print("4. Logout")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            scooter_id, update_data = prompt_for_scooter_update(current_user)
            if scooter_id and update_data:
                services.update_scooter(current_user, scooter_id, update_data)
        elif choice == '2':
            print_scooter_syntax_rules()
            key = input("Enter search key (brand, model, or serial number): ")
            results = services.search_scooters(current_user, key)
            display_results(results)
        elif choice == '3':
            handle_update_own_password(current_user)
        elif choice == '4':
            print("Logging out...")
            services.secure_logger.log(current_user.username, "Logged out")
            break
        else:
            print("Invalid choice. Please try again.")


def show_super_admin_menu(current_user: models.User):
    """Displays the menu for the Super Administrator."""
    while True:
        print_header(f"Super Admin Menu | Logged in as: {current_user.username}")
        print("\n--- Traveller Management ---")
        print("1. Add New Traveller - Register a new traveller with all required personal and contact details.")
        print("2. Search for Traveller - Find travellers by any information (name, email, etc.).")
        print("3. Update Traveller - Modify details of an existing traveller.")
        print("4. Delete Traveller - Remove a traveller from the system.")

        print("\n--- Scooter Management ---")
        print("5. Add New Scooter - Register a new scooter with technical and location details.")
        print("6. Update Scooter Details - Change information or status of a scooter.")
        print("7. Delete Scooter - Remove a scooter from the fleet.")
        print("8. Search for Scooter - Find scooters by brand, model, or serial number.")

        print("\n--- User Management ---")
        print("9. Add New User (Service Engineer) - Create a new Service Engineer account.")
        print("10. Reset User Password - Reset the password for an existing user.")
        print("11. Add New User (System Admin or Service Engineer) - Create a new System Admin or Service Engineer account.")

        print("\n--- System & Self-Service ---")
        print("12. View System Logs - Display recent system logs and mark suspicious logs as read.")
        print("13. Create Backup - Generate a backup of the system database.")
        print("14. Restore From Backup - Restore the system from a backup file.")
        print("15. Generate Restore Code for System Admin - Generate a one-time restore code for a System Admin user.")
        print("16. Revoke Restore Code for System Admin - Revoke an active, unused restore code.")
        print("17. Logout - Log out of the system and return to the login screen.")

        choice = input("Enter your choice: ")
        # Map new numbers to old logic
        if choice == '1':
            traveller_data = prompt_for_new_traveller()
            if traveller_data:
                services.add_new_traveller(current_user, **traveller_data)
        elif choice == '2':
            print_traveller_syntax_rules()
            key = input("Enter search key (any traveller info): ")
            results = services.search_travellers(current_user, key)
            display_results(results)
        elif choice == '3':
            try:
                trav_id = int(input("Enter Traveller ID to update: "))
                new_data = prompt_for_new_traveller()
                if new_data:
                    services.update_traveller(current_user, trav_id, new_data)
            except ValueError:
                print("Invalid ID.")
        elif choice == '4':
            try:
                trav_id = int(input("Enter Traveller ID to delete: "))
                services.delete_traveller(current_user, trav_id)
            except ValueError:
                print("Invalid ID.")
        elif choice == '5':
            scooter_data = prompt_for_new_scooter()
            if scooter_data:
                services.add_new_scooter(current_user, **scooter_data)
        elif choice == '6':
            scooter_id, update_data = prompt_for_scooter_update(current_user)
            if scooter_id and update_data:
                services.update_scooter(current_user, scooter_id, update_data)
        elif choice == '7':
            try:
                scooter_id = int(input("Enter Scooter ID to delete: "))
                services.delete_scooter(current_user, scooter_id)
            except ValueError:
                print("Invalid ID.")
        elif choice == '8':
            print_scooter_syntax_rules()
            key = input("Enter search key (brand, model, or serial number): ")
            results = services.search_scooters(current_user, key)
            display_results(results)
        elif choice == '9':
            user_data = prompt_for_new_user(current_user.role)
            if user_data:
                services.add_new_user(current_user, **user_data)
        elif choice == '10':
            print_user_syntax_rules()
            target_user = input("Enter username to reset password for: ")
            services.reset_user_password(current_user, target_user)
        elif choice == '11':
            user_data = prompt_for_new_user(current_user.role)
            if user_data:
                services.add_new_user(current_user, **user_data)
        elif choice == '12':
            handle_view_logs(current_user)
        elif choice == '13':
            services.create_backup(current_user)
        elif choice == '14':
            filename = input("Enter backup filename (e.g., backup_20250617_103000.zip): ")
            code = input("Enter one-time restore code (press Enter if not required): ")
            services.restore_from_backup(current_user, filename, code or None)
        elif choice == '15':
            target_user = input("Enter System Admin username to generate code for: ")
            backup_file = input("Enter the exact backup filename the code is for: ")
            services.generate_restore_code(current_user, target_user, backup_file)
        elif choice == '16':
            code_to_revoke = input("Enter the exact restore code to revoke: ")
            if code_to_revoke:
                services.revoke_restore_code(current_user, code_to_revoke)
        elif choice == '17':
            print("Logging out...")
            services.secure_logger.log(current_user.username, "Logged out")
            break
        else:
            print("Invalid choice. Please try again.")

def show_system_admin_menu(current_user: models.User):
    """Displays the menu for System Administrators."""
    while True:
        print_header(f"System Admin Menu | Logged in as: {current_user.username}")
        print("\n--- Traveller Management ---")
        print("1. Add New Traveller - Register a new traveller with all required personal and contact details.")
        print("2. Search for Traveller - Find travellers by any information (name, email, etc.).")
        print("3. Update Traveller - Modify details of an existing traveller.")
        print("4. Delete Traveller - Remove a traveller from the system.")

        print("\n--- Scooter Management ---")
        print("5. Add New Scooter - Register a new scooter with technical and location details.")
        print("6. Update Scooter Details - Change information or status of a scooter.")
        print("7. Delete Scooter - Remove a scooter from the fleet.")
        print("8. Search for Scooter - Find scooters by brand, model, or serial number.")

        print("\n--- User Management ---")
        print("9. Add New User (Service Engineer) - Create a new Service Engineer account.")
        print("10. Reset User Password - Reset the password for an existing user.")

        print("\n--- System & Self-Service ---")
        print("11. View System Logs - Display recent system logs and mark suspicious logs as read.")
        print("12. Create Backup - Generate a backup of the system database.")
        print("13. Restore From Backup - Restore the system from a backup file.")
        print("14. Update My Password - Change your own account password.")
        print("15. Logout - Log out of the system and return to the login screen.")

        choice = input("Enter your choice: ")
        # Map new numbers to old logic
        if choice == '1':
            traveller_data = prompt_for_new_traveller()
            if traveller_data:
                services.add_new_traveller(current_user, **traveller_data)
        elif choice == '2':
            print_traveller_syntax_rules()
            key = input("Enter search key (any traveller info): ")
            results = services.search_travellers(current_user, key)
            display_results(results)
        elif choice == '3':
            try:
                trav_id = int(input("Enter Traveller ID to update: "))
                new_data = prompt_for_new_traveller()
                if new_data:
                    services.update_traveller(current_user, trav_id, new_data)
            except ValueError:
                print("Invalid ID.")
        elif choice == '4':
            try:
                trav_id = int(input("Enter Traveller ID to delete: "))
                services.delete_traveller(current_user, trav_id)
            except ValueError:
                print("Invalid ID.")
        elif choice == '5':
            scooter_data = prompt_for_new_scooter()
            if scooter_data:
                services.add_new_scooter(current_user, **scooter_data)
        elif choice == '6':
            scooter_id, update_data = prompt_for_scooter_update(current_user)
            if scooter_id and update_data:
                services.update_scooter(current_user, scooter_id, update_data)
        elif choice == '7':
            try:
                scooter_id = int(input("Enter Scooter ID to delete: "))
                services.delete_scooter(current_user, scooter_id)
            except ValueError:
                print("Invalid ID.")
        elif choice == '8':
            print_scooter_syntax_rules()
            key = input("Enter search key (brand, model, or serial number): ")
            results = services.search_scooters(current_user, key)
            display_results(results)
        elif choice == '9':
            user_data = prompt_for_new_user(current_user.role)
            if user_data:
                services.add_new_user(current_user, **user_data)
        elif choice == '10':
            print_user_syntax_rules()
            target_user = input("Enter username to reset password for: ")
            services.reset_user_password(current_user, target_user)
        elif choice == '11':
            handle_view_logs(current_user)
        elif choice == '12':
            services.create_backup(current_user)
        elif choice == '13':
            filename = input("Enter backup filename (e.g., backup_20250617_103000.zip): ")
            code = input("Enter one-time restore code (press Enter if not required): ")
            services.restore_from_backup(current_user, filename, code or None)
        elif choice == '14':
            handle_update_own_password(current_user)
        elif choice == '15':
            print("Logging out...")
            services.secure_logger.log(current_user.username, "Logged out")
            break
        else:
            print("Invalid choice. Please try again.")

def temp_system_admin_handler(choice, current_user):
    """Temporary function to route choices for Super Admin to the System Admin logic."""
    # This avoids duplicating all the handler code in the Super Admin menu
    
    # Traveller Actions
    if choice == '1':
        traveller_data = prompt_for_new_traveller()
        if traveller_data:
            services.add_new_traveller(current_user, **traveller_data)
    elif choice == '2':
        print_traveller_syntax_rules()
        key = input("Enter search key (any traveller info): ")
        results = services.search_travellers(current_user, key)
        display_results(results)
    elif choice == '3':
        try:
            trav_id = int(input("Enter Traveller ID to update: "))
            new_data = prompt_for_new_traveller()
            if new_data:
                services.update_traveller(current_user, trav_id, new_data)
        except ValueError:
            print("Invalid ID.")
    elif choice == '4':
        try:
            trav_id = int(input("Enter Traveller ID to delete: "))
            services.delete_traveller(current_user, trav_id)
        except ValueError:
            print("Invalid ID.")
    # Scooter Actions
    elif choice == '10':
        scooter_data = prompt_for_new_scooter()
        if scooter_data:
            services.add_new_scooter(current_user, **scooter_data)
    elif choice == '11':
        scooter_id, update_data = prompt_for_scooter_update(current_user)
        if scooter_id and update_data:
            services.update_scooter(current_user, scooter_id, update_data)
    elif choice == '12':
        try:
            scooter_id = int(input("Enter Scooter ID to delete: "))
            services.delete_scooter(current_user, scooter_id)
        except ValueError:
            print("Invalid ID.")
    elif choice == '13':
        key = input("Enter search key (brand, model, or serial number): ")
        results = services.search_scooters(current_user, key)
        display_results(results)
    # User Actions
    elif choice == '20': # This is handled by the Super Admin's '30'
        print("Please use option 30 from the Super Admin menu to add users.")
    elif choice == '21':
        target_user = input("Enter username to reset password for: ")
        services.reset_user_password(current_user, target_user)
    # System Actions
    elif choice == '80':
        handle_view_logs(current_user)
    elif choice == '81':
        services.create_backup(current_user)
    elif choice == '82':
        filename = input("Enter backup filename (e.g., backup_20250617_103000.zip): ")
        # Super admin does not need a code
        services.restore_from_backup(current_user, filename, restore_code=None)

def main():
    """Main application entry point."""
    database.initialize_database()
    current_user = None
    
    while True:
        if current_user is None:
            print_header("Urban Mobility Backend - Login")
            current_user = auth.login()
            if current_user:
                services.secure_logger.log(current_user.username, "Logged in")
        else:
            if current_user.role == config.ROLE_SUPER_ADMIN:
                show_super_admin_menu(current_user)
            elif current_user.role == config.ROLE_SYSTEM_ADMIN:
                show_system_admin_menu(current_user)
            elif current_user.role == config.ROLE_SERVICE_ENGINEER:
                show_service_engineer_menu(current_user)
            
            # After the menu function returns (on logout), reset user and loop to login
            current_user = None

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication shutting down.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")