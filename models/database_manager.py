import mysql.connector
from mysql.connector import Error

# Import Entity for Auth
from models.entities import User


# Import the new modular DBs
from models.db_cashier import CashierDB
from models.db_manager import ManagerDB


class DatabaseManager:
    def __init__(self):
        # Configuration
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'pos_system'
        }

        # Initialize sub-managers, passing 'self' to give them access to get_connection()
        self.cashier_db = CashierDB(self)
        self.manager_db = ManagerDB(self)

    def get_connection(self):
        """Centralized connection factory used by sub-managers."""
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None

    # ================= CORE AUTH =================
    def authenticate_user(self, username, password):
        conn = self.get_connection()
        user_obj = None
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                # In production, use hashed passwords!
                query = "SELECT id, name, role FROM users WHERE name = %s AND password = %s"
                cursor.execute(query, (username, password))
                result = cursor.fetchone()
                if result:
                    user_obj = User(result['id'], result['name'], result['role'])
            except Error as e:
                print(f"Auth Error: {e}")
            finally:
                conn.close()
        return user_obj

    # =========================================================
    # PROXY METHODS - These ensure Controllers don't break
    # =========================================================

    # --- Cashier Routes ---
    def get_all_products(self):
        return self.cashier_db.get_all_products()

    def process_transaction(self, cart, total, cashier):
        return self.cashier_db.process_transaction(cart, total, cashier)

    # --- Manager/Inventory Routes ---
    def get_all_users(self):
        return self.manager_db.get_all_users()

    def add_user(self, name, pwd, role):
        return self.manager_db.add_user(name, pwd, role)

    def delete_user(self, uid):
        return self.manager_db.delete_user(uid)

    def get_inventory_items(self):
        return self.manager_db.get_inventory_items()

    def add_product(self, name, cat, stk, cost, price, thres, exp):
        return self.manager_db.add_product(name, cat, stk, cost, price, thres, exp)

    def update_product(self, pid, name, cat, stk, cost, price, thres, exp):
        return self.manager_db.update_product(pid, name, cat, stk, cost, price, thres, exp)

    def delete_product(self, pid):
        return self.manager_db.delete_product(pid)

    # --- Dashboard Routes ---
    def get_dashboard_stats(self):
        return self.manager_db.get_dashboard_stats()

    def get_recent_sales(self, limit=10):
        return self.manager_db.get_recent_sales(limit)

    def get_top_products(self, limit=5):
        return self.manager_db.get_top_products(limit)

    # === AUDIT LOG METHODS ===

    def get_audit_logs(self):
        logs = []
        # Note: Use self.get_connection() if DatabaseManager holds the connection logic
        conn = self.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                # Fetch logs, newest first
                query = """
                        SELECT timestamp, user_name, action, details
                        FROM audit_logs
                        ORDER BY timestamp DESC \
                        """
                cursor.execute(query)
                logs = cursor.fetchall()
            except Error as e:
                print(f"Error fetching audit logs: {e}")
            finally:
                conn.close()
        return logs

    def log_audit(self, user_name, action, details):
        conn = self.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor()
                query = "INSERT INTO audit_logs (user_name, action, details) VALUES (%s, %s, %s)"
                cursor.execute(query, (user_name, action, details))
                conn.commit()
            except Error as e:
                print(f"Error saving audit log: {e}")
            finally:
                conn.close()