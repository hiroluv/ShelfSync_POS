# models/db_manager.py
from mysql.connector import Error
from models.entities import User, InventoryItem, DashboardStats


class ManagerDB:
    def __init__(self, db_manager):
        self.main_db = db_manager  # Access to get_connection()

    # ================= USER MANAGEMENT =================
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
                cursor = conn.cursor()
                query = "INSERT INTO users (name, password, role) VALUES (%s, %s, %s)"
                cursor.execute(query, (name, password, role))
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
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
                return True
            except Error as e:
                print(f"Error deleting user: {e}")
                return False
            finally:
                conn.close()
        return False

    # ================= INVENTORY MANAGEMENT =================
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
        """
        Fetches items that have stock > 0 AND are expiring within 'days_threshold' (or expired).
        """
        items = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                # SQL LOGIC:
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

    # ================= DASHBOARD & ANALYTICS =================
    def get_dashboard_stats(self):
        conn = self.main_db.get_connection()
        stats = DashboardStats(0, 0, 0)

        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)

                # 1. Revenue
                cursor.execute("SELECT SUM(total_amount) as rev FROM sales WHERE DATE(sale_timestamp) = CURDATE()")
                res_rev = cursor.fetchone()
                revenue = res_rev['rev'] if res_rev and res_rev['rev'] else 0.0

                # 2. Low Stock (UPDATED)
                # Count items where stock <= threshold BUT ignore items with 0 stock
                cursor.execute("""
                    SELECT COUNT(*) as cnt 
                    FROM inventory 
                    WHERE stock <= threshold 
                    AND stock > 0
                """)
                low_stock = cursor.fetchone()['cnt']

                # 3. Expiring Soon
                # Also ignores items with 0 stock
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
        """
        Fetches individual ITEMS sold recently by joining sales, sale_items, and inventory tables.
        This provides the product name, individual price, and quantity for the dashboard list.
        """
        sales = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)

                # UPDATED QUERY: Joins tables to get specific item details instead of generic totals
                query = """
                        SELECT i.name as product_name, \
                               si.price, \
                               si.quantity, \
                               s.cashier_name, \
                               s.sale_timestamp
                        FROM sale_items si
                                 JOIN sales s ON si.sale_id = s.id
                                 JOIN inventory i ON si.product_id = i.id
                        ORDER BY s.sale_timestamp DESC
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