import mysql.connector
from mysql.connector import Error
from models.entities import User
from models.db_cashier import CashierDB
from models.db_manager import ManagerDB


class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'pos_system'
        }

        self.cashier_db = CashierDB(self)
        self.manager_db = ManagerDB(self)

    def get_connection(self):
        #Centralized connection
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None

    def authenticate_user(self, username, password):
        conn = self.get_connection()
        user_obj = None
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                # In production,
                query = "SELECT id, name, role FROM users WHERE name = %s AND password = %s"
                cursor.execute(query, (username, password))
                result = cursor.fetchone()

                # Return User Obj
                if result:
                    user_obj = User(result['id'], result['name'], result['role'])
            except Error as e:
                print(f"Auth Error: {e}")
            finally:
                conn.close()
        return user_obj

    #Cashier
    def get_all_products(self):
        return self.cashier_db.get_all_products()

    def process_transaction(self, cart, total, cashier):
        return self.cashier_db.process_transaction(cart, total, cashier)

    # --- Manager/Inventory
    def get_all_users(self):
        return self.manager_db.get_all_users()

    def add_user(self, name, pwd, role):
        return self.manager_db.add_user(name, pwd, role)

    def delete_user(self, user_id):
        return self.manager_db.delete_user(user_id)

    def get_inventory_items(self):
        return self.manager_db.get_inventory_items()

    def add_product(self, name, cat, stk, cost, price, thres, exp):
        if hasattr(self.manager_db, 'add_product'):
            return self.manager_db.add_product(name, cat, stk, cost, price, thres, exp)
        return False

    def update_product(self, pid, name, cat, stk, cost, price, thres, exp):
        if hasattr(self.manager_db, 'update_product'):
            return self.manager_db.update_product(pid, name, cat, stk, cost, price, thres, exp)
        return False

    def delete_product(self, pid):
        if hasattr(self.manager_db, 'delete_product'):
            return self.manager_db.delete_product(pid)
        return False

    # Dashboard ways
    def get_dashboard_stats(self):
        return self.manager_db.get_dashboard_stats()

    def get_recent_sales(self, limit=10):
        # Assuming this exists in ManagerDB (or add it if missing)
        if hasattr(self.manager_db, 'get_recent_sales'):
            return self.manager_db.get_recent_sales(limit)
        return []

    def get_top_products(self, limit=5):
        return self.manager_db.get_top_products(limit)

    def get_audit_logs(self):
        logs = []
        conn = self.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                # Fetch logs, newest first
                query = """
                        SELECT timestamp, user_name, action, details
                        FROM audit_logs
                        ORDER BY timestamp DESC
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
