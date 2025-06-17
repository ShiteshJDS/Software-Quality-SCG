# src/main.py

import database, auth, config, services, models, validation
from datetime import datetime

def print_header(title: str):
    """Prints a formatted header."""
    print("\n" + "=" * 50)
    print(f" {title.center(48)} ")
    print("=" * 50)

# --- UI Helper Functions for Input ---

def prompt_for_new_user(creator_role):
    """Gets data for a new user from the console."""
    print_header("Add New User")
    username = input("Enter username (8-10 chars, starts with letter/_): ")
    password = input("Enter password (12-30 chars, mix of cases, num, special): ")
    
    allowed_roles = []
    if creator_role == config.ROLE_SUPER_ADMIN:
        allowed_roles = [config.ROLE_SYSTEM_ADMIN, config.ROLE_SERVICE_ENGINEER]
    elif creator_role == config.ROLE_SYSTEM_ADMIN:
        allowed_roles = [config.ROLE_SERVICE_ENGINEER]

    if not allowed_roles:
        print("You are not authorized to create new users.")
        return None

    print("Allowed roles to create: " + ", ".join(allowed_roles))
    role = input(f"Enter role ({'/'.join(r.split()[0] for r in allowed_roles)}): ").strip()
    # Simplified role selection
    if role.lower() == 'system' and config.ROLE_SYSTEM_ADMIN in allowed_roles:
        role = config.ROLE_SYSTEM_ADMIN
    elif role.lower() == 'service' and config.ROLE_SERVICE_ENGINEER in allowed_roles:
        role = config.ROLE_SERVICE_ENGINEER
    else:
        print("Invalid role selected.")
        return None

    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")
    
    return {
        "username": username, "password": password, "role": role,
        "first_name": first_name, "last_name": last_name
    }

def prompt_for_new_traveller():
    """Gets data for a new traveller from the console."""
    print_header("Add New Traveller")
    data = {}
    data['first_name'] = input("Enter first name: ")
    data['last_name'] = input("Enter last name: ")
    data['birthday'] = input("Enter birthday (YYYY-MM-DD): ")
    data['gender'] = input("Enter gender: ")
    data['street_name'] = input("Enter street name: ")
    data['house_number'] = input("Enter house number: ")
    data['zip_code'] = input("Enter zip code (e.g., 1234AB): ")
    
    print("--- Predefined Cities ---")
    for i, city in enumerate(config.PREDEFINED_CITIES, 1):
        print(f"{i}. {city}")
    city_choice = int(input("Choose a city (number): "))
    if 1 <= city_choice <= len(config.PREDEFINED_CITIES):
        data['city'] = config.PREDEFINED_CITIES[city_choice - 1]
    else:
        print("Invalid city choice.")
        return None

    data['email'] = input("Enter email address: ")
    data['mobile_phone'] = input("Enter 8-digit mobile number (e.g., 12345678): ")
    data['driving_license_number'] = input("Enter driving license (e.g., AB1234567): ")
    return data

def prompt_for_scooter_location():
    """Gets data for updating a scooter's location."""
    print_header("Update Scooter Location")
    try:
        scooter_id = int(input("Enter Scooter ID to update: "))
        new_lat = float(input("Enter new latitude (e.g., 51.9225): "))
        new_lon = float(input("Enter new longitude (e.g., 4.47917): "))
        return {"scooter_id": scooter_id, "new_lat": new_lat, "new_lon": new_lon}
    except ValueError:
        print("Invalid input. Please enter numbers.")
        return None

# --- Role-Specific Menus ---

def show_service_engineer_menu(current_user: models.User):
    """Displays the menu for Service Engineers."""
    while True:
        print_header(f"Service Engineer Menu | Logged in as: {current_user.username}")
        print("1. Update Scooter Location")
        print("2. Search for Scooter (Not Implemented)")
        print("9. Logout")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            location_data = prompt_for_scooter_location()
            if location_data:
                services.update_scooter_location(current_user, **location_data)
        elif choice == '2':
            print("Search functionality not implemented yet.")
        elif choice == '9':
            print("Logging out...")
            services.secure_logger.log(current_user.username, "Logged out")
            break
        else:
            print("Invalid choice. Please try again.")

def show_system_admin_menu(current_user: models.User):
    """Displays the menu for System Administrators."""
    while True:
        print_header(f"System Admin Menu | Logged in as: {current_user.username}")
        print("--- Traveller Management ---")
        print("1. Add New Traveller")
        print("2. Search for Traveller (Not Implemented)")
        print("--- User Management ---")
        print("3. Add New User (Service Engineer)")
        print("--- Scooter Management ---")
        print("4. Update Scooter Location")
        print("--- System ---")
        print("8. View System Logs")
        print("9. Logout")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            traveller_data = prompt_for_new_traveller()
            if traveller_data:
                services.add_new_traveller(current_user, traveller_data)
        elif choice == '3':
            user_data = prompt_for_new_user(current_user.role)
            if user_data:
                services.add_new_user(current_user, **user_data)
        elif choice == '4':
            location_data = prompt_for_scooter_location()
            if location_data:
                services.update_scooter_location(current_user, **location_data)
        elif choice == '8':
            print_header("System Logs (Last 10)")
            logs = services.secure_logger.get_logs(limit=10)
            if not logs:
                print("No logs found.")
            else:
                for log in logs:
                    # Debug: print log structure
                    print(f"DEBUG LOG ENTRY: {log}")
                    # Use .get() to avoid KeyError
                    print(f"[{log.get('date', '?')} {log.get('time', '?')}] User: {log.get('username', '?')}, Action: {log.get('activity_description', '?')}, Suspicious: {log.get('is_suspicious', '?')}")
        elif choice == '9':
            print("Logging out...")
            services.secure_logger.log(current_user.username, "Logged out")
            break
        else:
            print("Invalid choice. Please try again.")

def show_super_admin_menu(current_user: models.User):
    """Displays the menu for the Super Administrator."""
    # For this implementation, the Super Admin has the same menu as System Admin,
    # but with more permissions enforced by the services layer.
    show_system_admin_menu(current_user)


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