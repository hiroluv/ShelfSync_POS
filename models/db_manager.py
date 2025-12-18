from mysql.connector import Error
from models.entities import User, InventoryItem, DashboardStats
from models.user_model import UserModel  # Added for password hashing


# Manager's side DB
class ManagerDB:
    def __init__(self, db_manager):
        self.main_db = db_manager  # Access to get_connection()

    # --- USER MANAGEMENT ---

    def authenticate_user(self, username, password):
        """
        Authenticates a user by name and password hash.
        Moved here from DatabaseManager for better MVC separation.
        """
        conn = self.main_db.get_connection()
        user_obj = None

        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)

                # 1. Fetch user by name
                query = "SELECT id, name, role, password FROM users WHERE name = %s"
                cursor.execute(query, (username,))
                result = cursor.fetchone()

                # 2. Verify password
                if result:
                    stored_hash = result['password']
                    # Use the Model to verify the hash
                    if UserModel.verify_password(password, stored_hash):
                        user_obj = User(result['id'], result['name'], result['role'])

            except Error as e:
                print(f"Auth Error: {e}")
            finally:
                conn.close()

        return user_obj

    def get_all_users(self):
        users = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id, name, role FROM users ORDER BY id ASC")
                for row in cursor.fetchall():
                    users.append(User(row['id'], row['name'], row['role']))
            except Error as e:
                print(f"Error fetching users: {e}")
            finally:
                conn.close()
        return users

    def add_user(self, name, password, role):
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                # UPDATED: Hash the password before inserting into DB
                hashed_pw = UserModel.hash_password(password)

                cursor = conn.cursor()
                query = "INSERT INTO users (name, password, role) VALUES (%s, %s, %s)"

                # Use hashed_pw instead of plain password
                cursor.execute(query, (name, hashed_pw, role))
                conn.commit()
                return True
            except Error as e:
                print(f"Error adding user: {e}")
                return False
            finally:
                conn.close()
        return False

    def delete_user(self, user_id):
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor()
                # prevent deleting last manager's profile
                cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
                if row and row[0] == 'Manager':
                    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Manager'")
                    manager_count = cursor.fetchone()[0]
                    if manager_count <= 1:
                        print("Cannot delete the last Manager account.")
                        return False

                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
                return True
            except Error as e:
                print(f"cant delete user: {e}")
                return False
            finally:
                conn.close()
        return False

    # --- INVENTORY MANAGEMENT ---
    def get_inventory_items(self):
        items = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT * FROM inventory ORDER BY id DESC"
                cursor.execute(query)
                for row in cursor.fetchall():
                    item = InventoryItem(
                        id=row['id'],
                        name=row['name'],
                        category=row['category'],
                        stock=row['stock'],
                        cost_price=row['cost_price'],
                        selling_price=row['selling_price'],
                        threshold=row['threshold'],
                        expiry_date=row['expiry_date']
                    )
                    items.append(item)
            except Error as e:
                print(f"Error fetching inventory: {e}")
            finally:
                conn.close()
        return items

    def get_expiring_products_in_stock(self, days_threshold=30):
        # get items that have more than 1 stock and are expiring
        items = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                # explanation oh
                # 1. stock > 0: Only available items (Perishables view Requirement)
                # 2. expiry_date IS NOT NULL: Must have an expiry
                # 3. expiry_date <= ...: Date is today or in the past (expired) OR within next 30 days
                query = """
                        SELECT * \
                        FROM inventory
                        WHERE stock > 0
                          AND expiry_date IS NOT NULL
                          AND expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                        ORDER BY expiry_date ASC
                        """
                cursor.execute(query, (days_threshold,))

                for row in cursor.fetchall():
                    item = InventoryItem(
                        id=row['id'],
                        name=row['name'],
                        category=row['category'],
                        stock=row['stock'],
                        cost_price=row['cost_price'],
                        selling_price=row['selling_price'],
                        threshold=row['threshold'],
                        expiry_date=row['expiry_date']
                    )
                    items.append(item)
            except Error as e:
                print(f"Error fetching perishables: {e}")
            finally:
                conn.close()
        return items

    def add_product(self, name, category, stock, cost, price, threshold, expiry):
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor()
                query = """
                        INSERT INTO inventory
                        (name, category, stock, cost_price, selling_price, threshold, expiry_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) \
                        """
                if expiry == "": expiry = None
                cursor.execute(query, (name, category, stock, cost, price, threshold, expiry))
                conn.commit()
                return True
            except Error as e:
                print(f"Error adding product: {e}")
                return False
            finally:
                conn.close()
        return False

    def update_product(self, pid, name, category, stock, cost, price, threshold, expiry):
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor()
                query = """
                        UPDATE inventory
                        SET name=%s, \
                            category=%s, \
                            stock=%s, \
                            cost_price=%s,
                            selling_price=%s, \
                            threshold=%s, \
                            expiry_date=%s
                        WHERE id = %s \
                        """
                if expiry == "": expiry = None
                cursor.execute(query, (name, category, stock, cost, price, threshold, expiry, pid))
                conn.commit()
                return True
            except Error as e:
                print(f"Error updating product: {e}")
                return False
            finally:
                conn.close()
        return False

    def delete_product(self, pid):
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM inventory WHERE id=%s", (pid,))
                conn.commit()
                return True
            except Error as e:
                print(f"Error deleting product: {e}")
                return False
            finally:
                conn.close()
        return False

    def get_all_categories(self):
        # Get unique category
        categories = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor()
                # distinct selects only unique values
                cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category ASC")
                for row in cursor.fetchall():
                    if row[0]:  # Ensure not None/Empty
                        categories.append(row[0])
            except Exception as e:
                print(f"Error fetching categories: {e}")
            finally:
                conn.close()
        return categories

    # --- ANALYTICS & REPORTS ---

    def get_dashboard_stats(self):
        conn = self.main_db.get_connection()
        stats = DashboardStats(0, 0, 0)

        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)

                # Revenue
                cursor.execute("SELECT SUM(total_amount) as rev FROM sales WHERE DATE(sale_timestamp) = CURDATE()")
                res_rev = cursor.fetchone()
                revenue = res_rev['rev'] if res_rev and res_rev['rev'] else 0.0

                # Low Stock (Ignore 0 stock)
                cursor.execute("""
                    SELECT COUNT(*) as cnt 
                    FROM inventory 
                    WHERE stock <= threshold 
                    AND stock > 0
                """)
                low_stock = cursor.fetchone()['cnt']

                # Expiring Soon (Ignore 0 stock)
                cursor.execute("""
                               SELECT COUNT(*) as cnt
                               FROM inventory
                               WHERE expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                                 AND stock > 0
                               """)
                expiring = cursor.fetchone()['cnt']

                stats = DashboardStats(revenue, low_stock, expiring)
            except Error as e:
                print(f"Stats Error: {e}")
            finally:
                conn.close()
        return stats

    def get_recent_sales(self, limit=10):
        # UPDATED: Added payment_method to the select
        sales = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                    SELECT 
                        total_amount, 
                        items_count, 
                        cashier_name, 
                        sale_timestamp,
                        payment_method 
                    FROM sales 
                    ORDER BY sale_timestamp DESC 
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
                sales = cursor.fetchall()
            except Error as e:
                print(f"Error fetching recent sales: {e}")
            finally:
                conn.close()
        return sales

    def get_top_products(self, limit=5):
        items = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                        SELECT i.name, SUM(si.quantity) as total_qty
                        FROM sale_items si
                                 JOIN inventory i ON si.product_id = i.id
                        GROUP BY si.product_id
                        ORDER BY total_qty DESC
                            LIMIT %s \
                        """
                cursor.execute(query, (limit,))
                items = cursor.fetchall()
            except Error as e:
                print(f"Error fetching top products: {e}")
            finally:
                conn.close()
        return items

    def get_sales_report_data(self, start_date, end_date):
        # UPDATED: Added payment_method and reference_number
        data = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                SELECT 
                    id as invoice_id,
                    sale_timestamp as date,
                    cashier_name as cashier,
                    items_count,
                    total_amount,
                    payment_method,
                    reference_number
                FROM sales 
                WHERE DATE(sale_timestamp) BETWEEN %s AND %s
                ORDER BY sale_timestamp DESC
                """
                cursor.execute(query, (start_date, end_date))
                data = cursor.fetchall()
                cursor.close()
            except Error as e:
                print(f"Error fetching sales report: {e}")
            finally:
                conn.close()
        return data

    def get_inventory_valuation_data(self):
        # calculate total value sa stock
        data = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                SELECT 
                    id, name, category, stock, cost_price, selling_price,
                    (stock * selling_price) as total_value
                FROM inventory
                ORDER BY category, name
                """
                cursor.execute(query)
                data = cursor.fetchall()
                cursor.close()
            except Error as e:
                print(f"cant grab inventory valuations: {e}")
            finally:
                conn.close()
        return data

    def get_low_stock_data(self):
        # get items below threshold (always <=10)
        data = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                SELECT id, name, category, stock, threshold
                FROM inventory
                WHERE stock <= threshold
                ORDER BY stock ASC
                """
                cursor.execute(query)
                data = cursor.fetchall()
                cursor.close()
            except Error as e:
                print(f"Ecant grab low stocks: {e}")
            finally:
                conn.close()
        return data

    def get_audit_log_data(self, start_date, end_date):
        data = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                SELECT timestamp, user_name, action, details
                FROM audit_logs
                WHERE DATE(timestamp) BETWEEN %s AND %s
                ORDER BY timestamp DESC
                """
                cursor.execute(query, (start_date, end_date))
                data = cursor.fetchall()
                cursor.close()
            except Error as e:
                print(f"Error fetching audit logs: {e}")
            finally:
                conn.close()
        return data