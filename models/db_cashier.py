from mysql.connector import Error
from models.entities import Product


class CashierDB:
    def __init__(self, db_manager):
        self.main_db = db_manager  # Access to get_connection()

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

    def process_transaction(self, cart_dict, total_amount, cashier_name, payment_info=None):
        """
        Saves the sale AND the payment details (Method, Tendered, Change).
        """
        conn = self.main_db.get_connection()
        if not conn or not conn.is_connected():
            return False

        try:
            conn.start_transaction()
            cursor = conn.cursor()

            # 1. Prepare Payment Data
            p_method = 'Cash'
            p_tendered = 0.0
            p_change = 0.0
            p_ref = None

            if payment_info:
                p_method = payment_info.get('method', 'Cash')
                p_tendered = payment_info.get('tendered', 0.0)
                p_change = payment_info.get('change', 0.0)
                p_ref = payment_info.get('reference', None)

            # 2. Insert into sales (UPDATED with new columns)
            items_count = sum(cart_dict.values())
            insert_sale = """
                INSERT INTO sales 
                (total_amount, items_count, cashier_name, sale_timestamp, 
                 payment_method, amount_tendered, change_amount, reference_number)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s)
            """
            cursor.execute(insert_sale, (total_amount, items_count, cashier_name,
                                         p_method, p_tendered, p_change, p_ref))
            sale_id = cursor.lastrowid

            # 3. Insert items and update stock
            for pid, qty in cart_dict.items():
                # Get current price to lock it in history
                cursor.execute("SELECT selling_price FROM inventory WHERE id = %s", (pid,))
                res = cursor.fetchone()
                price = res[0] if res else 0.0

                insert_item = """
                    INSERT INTO sale_items (sale_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_item, (sale_id, pid, qty, price))

                # Deduct Stock
                update_stock = "UPDATE inventory SET stock = stock - %s WHERE id = %s"
                cursor.execute(update_stock, (qty, pid))

            conn.commit()
            return True

        except Exception as e:
            print(f"Transaction Failed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()