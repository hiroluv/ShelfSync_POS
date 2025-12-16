import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from models.database_manager import DatabaseManager

# Import Controllers
from controllers.login_controller import LoginController
from controllers.main_controller import MainController
from controllers.cashier_controller import CashierController


class AppOrchestrator:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # Initialize Database ONCE here, share it with everyone
        self.db = DatabaseManager()
        self.show_login()

    def show_login(self):
        self.login_window = LoginController(self.db)
        self.login_window.login_success.connect(self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user):
        print(f"Logged in as: {user.name} ({user.role})")

        try:
            if user.role == "Manager":
                # --- [FIX] Pass user to open_manager_window ---
                self.open_manager_window(user)
            elif user.role == "Cashier":
                self.open_cashier_window(user)

            # Close login only if the new window launched successfully
            self.login_window.close()

        except Exception:
            print("CRITICAL ERROR LAUNCHING WINDOW:")
            traceback.print_exc()

    def open_manager_window(self, user):
        # --- [FIX] Pass the user object to MainController ---
        self.main_window = MainController(self.db, user_data=user)
        self.main_window.logout_request.connect(self.on_logout)
        self.main_window.show()

    def open_cashier_window(self, user):
        # Pass user and self (orchestrator) which contains .db
        self.cashier_window = CashierController(user, self)
        self.cashier_window.logout_request.connect(self.on_logout)
        self.cashier_window.show()

    def on_logout(self):
        print("Logout received. Returning to Login Screen.")

        # Close Cashier Window if it exists and is open
        if hasattr(self, 'cashier_window') and self.cashier_window:
            self.cashier_window.close()
            self.cashier_window = None  # Clear the reference

        # Close Manager Window if it exists and is open
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.close()
            self.main_window = None  # Clear the reference

        self.show_login()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    orchestrator = AppOrchestrator()
    orchestrator.run()
