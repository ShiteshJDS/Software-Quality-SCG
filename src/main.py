# src/main.py

import database, auth, config, services, models

def print_header(title: str):
    """Prints a formatted header."""
    print("\n" + "=" * 40)
    print(f" {title.center(38)} ")
    print("=" * 40)

def show_service_engineer_menu(current_user: models.User):
    """Displays the menu for Service Engineers."""
    print_header("Service Engineer Menu")
    while True:
        print("1. Update Scooter Location")
        print("2. Search for Scooter")
        print("9. Logout")
        choice = input("Enter your choice, send a number to choose. ")
        
        if choice == '1':
            # Example of calling a service with authorization check
            services.update_scooter_location(current_user, scooter_id=123, new_lat=51.92, new_lon=4.47)
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
    print_header("System Administrator Menu")
    while True:
        print("--- Traveller Management ---")
        print("1. Add New Traveller")
        print("2. Search for Traveller")
        print("--- User Management ---")
        print("3. Add New User (Service Engineer)")
        print("--- Scooter Management ---")
        print("4. Update Scooter Information")
        print("--- System ---")
        print("8. View System Logs")
        print("9. Logout")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            # Example of calling a service
            mock_traveller = {"email": "test@example.com"}
            services.add_new_traveller(current_user, mock_traveller)
        elif choice == '3':
            services.add_new_user(current_user, "new_engineer", "Password123!", config.ROLE_SERVICE_ENGINEER, "John", "Doe")
        elif choice == '8':
            print_header("System Logs")
            logs = services.secure_logger.get_logs()
            if not logs:
                print("No logs found.")
            else:
                for log in logs:
                    print(log)
        elif choice == '9':
            print("Logging out...")
            services.secure_logger.log(current_user.username, "Logged out")
            break
        else:
            print("Invalid choice. Please try again.")


def show_super_admin_menu(current_user: models.User):
    """Displays the menu for the Super Administrator."""
    print_header("Super Administrator Menu")
    print("Super Admin has all the permissions of a System Admin and more.")
    # For this boilerplate, we'll just show the System Admin menu
    show_system_admin_menu(current_user)

def main():
    """Main application entry point."""
    # Initialize the database on startup
    database.initialize_database()
    
    current_user = None
    
    while True:
        if current_user is None:
            print_header("Urban Mobility Backend - Login")
            current_user = auth.login()
            if current_user:
                # Log the successful login
                services.secure_logger.log(current_user.username, "Logged in")
        else:
            # Route to the correct menu based on user role
            if current_user.role == config.ROLE_SUPER_ADMIN:
                show_super_admin_menu(current_user)
            elif current_user.role == config.ROLE_SYSTEM_ADMIN:
                show_system_admin_menu(current_user)
            elif current_user.role == config.ROLE_SERVICE_ENGINEER:
                show_service_engineer_menu(current_user)
            
            # After the menu function returns (on logout), reset the user
            current_user = None

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication shutting down.")