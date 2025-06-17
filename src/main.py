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
    role_input = input(f"Enter role ({'/'.join(r.split()[0] for r in allowed_roles)}): ").strip().lower()
    
    role = None
    if role_input == 'system' and config.ROLE_SYSTEM_ADMIN in allowed_roles:
        role = config.ROLE_SYSTEM_ADMIN
    elif role_input == 'service' and config.ROLE_SERVICE_ENGINEER in allowed_roles:
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
    try:
        city_choice = int(input("Choose a city (number): "))
        if 1 <= city_choice <= len(config.PREDEFINED_CITIES):
            data['city'] = config.PREDEFINED_CITIES[city_choice - 1]
        else:
            print("Invalid city choice.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None

    data['email'] = input("Enter email address: ")
    data['mobile_phone'] = input("Enter 8-digit mobile number (e.g., 12345678): ")
    data['driving_license_number'] = input("Enter driving license (e.g., AB1234567): ")
    return data

def prompt_for_new_scooter():
    """Gets data for a new scooter from the console."""
    print_header("Add New Scooter")
    data = {}
    data['serial_number'] = input("Enter serial number (10-17 alphanumeric): ")
    data['brand'] = input("Enter brand: ")
    data['model'] = input("Enter model: ")
    # Simplified for this example. A real app would prompt for all fields.
    data['top_speed'] = 60.0
    data['battery_capacity'] = 1000.0
    data['state_of_charge'] = 100.0
    data['target_range_soc_min'] = 20.0
    data['target_range_soc_max'] = 90.0
    data['location_lat'] = 51.9225
    data['location_lon'] = 4.47917
    data['mileage'] = 0.0
    data['last_maintenance_date'] = datetime.now().strftime("%Y-%m-%d")
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

# --- Display Functions ---
def display_travellers(travellers: list[models.Traveller]):
    if not travellers:
        print("No travellers found.")
        return
    print_header("Traveller Search Results")
    for t in travellers:
        print(f"ID: {t.id} | Name: {t.first_name} {t.last_name} | Email: {t.email} | Phone: {t.mobile_phone}")
    print("-" * 50)

def display_scooters(scooters: list[models.Scooter]):
    if not scooters:
        print("No scooters found.")
        return
    print_header("Scooter Search Results")
    for s in scooters:
        print(f"ID: {s.id} | Serial: {s.serial_number} | Brand: {s.brand} {s.model} | Location: ({s.location_lat}, {s.location_lon})")
    print("-" * 50)


# --- Role-Specific Menus ---

def show_service_engineer_menu(current_user: models.User):
    """Displays the menu for Service Engineers."""
    while True:
        print_header(f"Service Engineer Menu | Logged in as: {current_user.username}")
        print("1. Update Scooter Location")
        print("2. Search for Scooter")
        print("9. Logout")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            location_data = prompt_for_scooter_location()
            if location_data:
                services.update_scooter_location(current_user, **location_data)
        elif choice == '2':
            term = input("Enter search term for scooter (serial, brand, model): ")
            scooters = services.search_scooters(current_user, term)
            display_scooters(scooters)
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
        print("2. Search for Traveller")
        print("--- User Management ---")
        print("3. Add New User (Service Engineer)")
        print("--- Scooter Management ---")
        print("4. Add New Scooter")
        print("5. Search for Scooter")
        print("6. Update Scooter Location")
        print("--- System ---")
        print("7. Create Backup")
        print("8. Restore from Backup (requires code)")
        print("9. View System Logs")
        print("0. Logout")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            traveller_data = prompt_for_new_traveller()
            if traveller_data:
                services.add_new_traveller(current_user, traveller_data)
        elif choice == '2':
            term = input("Enter search term for traveller (name, email, etc.): ")
            travellers = services.search_travellers(current_user, term)
            display_travellers(travellers)
        elif choice == '3':
            user_data = prompt_for_new_user(current_user.role)
            if user_data:
                services.add_new_user(current_user, **user_data)
        elif choice == '4':
            scooter_data = prompt_for_new_scooter()
            if scooter_data:
                services.add_new_scooter(current_user, scooter_data)
        elif choice == '5':
            term = input("Enter search term for scooter (serial, brand, model): ")
            scooters = services.search_scooters(current_user, term)
            display_scooters(scooters)
        elif choice == '6':
            location_data = prompt_for_scooter_location()
            if location_data:
                services.update_scooter_location(current_user, **location_data)
        elif choice == '7':
            services.create_system_backup(current_user)
        elif choice == '8':
            code = input("Enter one-time restore code: ")
            services.restore_with_one_time_code(current_user, code)
        elif choice == '9':
            print_header("System Logs (Last 10)")
            logs = services.secure_logger.get_logs(limit=10)
            if not logs:
                print("No logs found.")
            else:
                for log in logs:
                    print(f"[{log.get('date', '?')} {log.get('time', '?')}] User: {log.get('username', '?')}, Action: {log.get('activity_description', '?')}, Suspicious: {log.get('is_suspicious', '?')}")
        elif choice == '0':
            print("Logging out...")
            services.secure_logger.log(current_user.username, "Logged out")
            break
        else:
            print("Invalid choice. Please try again.")

def show_super_admin_menu(current_user: models.User):
    """Displays the menu for the Super Administrator."""
    while True:
        print_header(f"Super Admin Menu | Logged in as: {current_user.username}")
        # Super admin has all system admin rights, plus more
        print("--- Traveller Management ---")
        print("1. Add New Traveller")
        print("2. Search for Traveller")
        print("--- User Management ---")
        print("3. Add New User (Admin/Engineer)")
        print("--- Scooter Management ---")
        print("4. Add New Scooter")
        print("5. Search for Scooter")
        print("--- Backup & Restore ---")
        print("6. Create Backup")
        print("7. Restore from Backup (Directly)")
        print("8. Generate Restore Code for System Admin")
        print("--- System ---")
        print("9. View System Logs")
        print("0. Logout")
        choice = input("Enter your choice: ")

        if choice == '1':
            traveller_data = prompt_for_new_traveller()
            if traveller_data:
                services.add_new_traveller(current_user, traveller_data)
        elif choice == '2':
            term = input("Enter search term for traveller (name, email, etc.): ")
            travellers = services.search_travellers(current_user, term)
            display_travellers(travellers)
        elif choice == '3':
            user_data = prompt_for_new_user(current_user.role)
            if user_data:
                services.add_new_user(current_user, **user_data)
        elif choice == '4':
            scooter_data = prompt_for_new_scooter()
            if scooter_data:
                services.add_new_scooter(current_user, scooter_data)
        elif choice == '5':
            term = input("Enter search term for scooter (serial, brand, model): ")
            scooters = services.search_scooters(current_user, term)
            display_scooters(scooters)
        elif choice == '6':
            services.create_system_backup(current_user)
        elif choice == '7':
            backups = services.get_available_backups()
            if not backups:
                print("No backups available to restore.")
                continue
            print("Available backups:")
            for i, b in enumerate(backups):
                print(f"{i+1}. {b}")
            try:
                backup_choice = int(input("Choose a backup to restore: "))
                if 1 <= backup_choice <= len(backups):
                    if input("This will overwrite the current database. Are you sure? [y/n]: ").lower() == 'y':
                         services.restore_system_backup(current_user, backups[backup_choice-1])
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Invalid input.")
        elif choice == '8':
            admin_user = input("Enter username of System Admin to generate code for: ")
            backups = services.get_available_backups()
            if not backups:
                print("No backups available.")
                continue
            print("Available backups:")
            for i, b in enumerate(backups):
                print(f"{i+1}. {b}")
            try:
                backup_choice = int(input("Choose a backup file for the code: "))
                if 1 <= backup_choice <= len(backups):
                    backup_file = backups[backup_choice-1]
                    code = services.generate_one_time_code(current_user, admin_user, backup_file)
                    if code:
                        print(f"\nSUCCESS! One-time code for {admin_user} is: {code}")
                        print("Provide this code to the System Administrator. It is valid for one use only.")
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Invalid input.")

        elif choice == '9':
            print_header("System Logs (Last 10)")
            logs = services.secure_logger.get_logs(limit=10)
            if not logs:
                print("No logs found.")
            else:
                for log in logs:
                     print(f"[{log.get('date', '?')} {log.get('time', '?')}] User: {log.get('username', '?')}, Action: {log.get('activity_description', '?')}, Suspicious: {log.get('is_suspicious', '?')}")
        elif choice == '0':
            print("Logging out...")
            services.secure_logger.log(current_user.username, "Logged out")
            break
        else:
            print("Invalid choice. Please try again.")


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
                # Check for suspicious activity alerts
                if current_user.role in [config.ROLE_SUPER_ADMIN, config.ROLE_SYSTEM_ADMIN]:
                    unread_alerts = services.secure_logger.check_unread_alerts()
                    if unread_alerts > 0:
                        print("\n" + "!" * 50)
                        print(f"!! You have {unread_alerts} unread suspicious activity alerts. !!".center(48))
                        print("!! View system logs to review and clear this notice. !!".center(48))
                        print("!" * 50)


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