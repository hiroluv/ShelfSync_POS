from mysql.connector import Error
from models.entities import Product

class CashierDB:
    def __init__(self, db_manager):
        self.main_db = db_manager # Access to get_connection()

    def get_all_products(self):
        """Used by CASHIER: Returns Product objects."""
        products = []
        conn = self.main_db.get_connection()
        if conn and conn.is_connected():
            try:
                cursor = conn.cursor(dictionary=True)
                query = """
                    SELECT id, name, category, cost_price, selling_price, 
                           stock, threshold, expiry_date 
                    FROM inventory 
                    ORDER BY name DESC
                """
                cursor.execute(query)
                for row in cursor.fetchall():
                    # Create Product objects (Safe for CashierController)
                    p = Product(
                        id=row['id'],
                        name=row['name'],
                        category=row['category'],
                        cost_price=row['cost_price'],
                        selling_price=row['selling_price'],
                        stock=row['stock'],
                        threshold=row['threshold'],
                        expiry_date=row['expiry_date']
                    )
                    products.append(p)
            except Error as e:
                print(f"Error fetching products for cashier: {e}")
            finally:
                conn.close()
        return products

    def process_transaction(self, cart_dict, total_amount, cashier_name):
        conn = self.main_db.get_connection()
        if not conn or not conn.is_connected():
            return False

        try:
            conn.start_transaction()
            cursor = conn.cursor()

            # 1. Insert into sales
            items_count = sum(cart_dict.values())
            insert_sale = """
                INSERT INTO sales (total_amount, items_count, cashier_name, sale_timestamp)
                VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(insert_sale, (total_amount, items_count, cashier_name))
            sale_id = cursor.lastrowid

            # 2. Insert items and update stock
            for pid, qty in cart_dict.items():
                cursor.execute("SELECT selling_price FROM inventory WHERE id = %s", (pid,))
                res = cursor.fetchone()
                price = res[0] if res else 0.0

                insert_item = """
                    INSERT INTO sale_items (sale_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_item, (sale_id, pid, qty, price))

                update_stock = "UPDATE inventory SET stock = stock - %s WHERE id = %s"
                cursor.execute(update_stock, (qty, pid))

            conn.commit()
            return True
        except Error as e:
            print(f"Transaction Failed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()