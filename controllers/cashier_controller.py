from PyQt6.QtWidgets import QMainWindow, QLineEdit
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic
import os


from controllers.product_grid_controller import ProductGrid_Controller
from controllers.cart_controller import Cart_Controller


class CashierController(QMainWindow):

    logout_request = pyqtSignal()

    def __init__(self, user, main_app):
        super().__init__()
        self.user = user
        self.db = main_app.db

        # 1. LOAD UI
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', 'cashier_window.ui')

        try:
            uic.loadUi(ui_path, self)
        except Exception as e:
            print(f"dili ma load ang UI file sa {ui_path}\nbro: {e}")
            return

        # --- Product Grid ---
        if hasattr(self, 'grid_products'):
            self.grid_controller = ProductGrid_Controller(self, self.grid_products, self.db)
            self.grid_controller.refresh_products()
        else:
            print("Error: 'grid_products' widget not found in UI")

        # --- Cart Controller ---
        if hasattr(self, 'scrollArea_cart'):
            self.cart_controller = Cart_Controller(self, self.scrollArea_cart, self.db)

        # VISUALS
        self.setup_ui()
        # CONNECTIONS
        self.setup_connections()

    def setup_ui(self):
        """Sets up ang svg icons"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        #Search Icon
        if hasattr(self, 'input_search'):
            search_icon_path = os.path.join(base_path, 'assets', 'icons', 'search.svg')
            if os.path.exists(search_icon_path):
                search_action = QAction(self)
                search_action.setIcon(QIcon(search_icon_path))
                self.input_search.addAction(search_action, QLineEdit.ActionPosition.LeadingPosition)

        #Cart Icon
        if hasattr(self, 'lbl_cart_title'):
            cart_icon_path = os.path.join(base_path, 'assets', 'icons', 'cart.svg')
            cart_icon_path = cart_icon_path.replace('\\', '/')

            current_text = self.lbl_cart_title.text()
            if "<img" not in current_text and os.path.exists(cart_icon_path):
                self.lbl_cart_title.setText(
                    f'<html><head/><body><p><img src="{cart_icon_path}" width="20" height="20"/>&nbsp;&nbsp;{current_text}</p></body></html>'
                )

    def setup_connections(self):
        """Connects slots."""

        #Product Grid -> Add to Cart
        if hasattr(self, 'grid_controller') and hasattr(self, 'cart_controller'):
            if hasattr(self.grid_controller, 'product_clicked'):
                self.grid_controller.product_clicked.connect(self.handle_add_product)

            if hasattr(self, 'input_search'):
                self.input_search.textChanged.connect(
                    lambda text: self.grid_controller.filter_products(text)
                )

        # 2. Checkout Button
        if hasattr(self, 'btn_checkout'):
            self.btn_checkout.clicked.connect(self.handle_checkout)

        # 3. Exit Button
        if hasattr(self, 'btn_logout'):
            # Connect to handle_logout instead na close() directly
            self.btn_logout.clicked.connect(self.handle_logout)
            print("DEBUG: Exit button connected successfully.")
        else:
            print("WARNING: 'btn_exit' not found in UI. Please check the button name in Qt Designer.")

    # --- ACTIONs cutieeee---

    def handle_logout(self):
        """Handles the exit button click."""
        print("Exit clicked. Logging out...")
        self.logout_request.emit()  # Notify Main.py
        self.close()  # Close this window

    def handle_add_product(self, product_id):
        if hasattr(self, 'cart_controller') and hasattr(self, 'grid_controller'):
            self.cart_controller.add_item(product_id, self.grid_controller.all_products)

    def handle_checkout(self):
        if hasattr(self, 'cart_controller') and hasattr(self, 'grid_controller'):
            user_name = self.user.get('name', 'Unknown') if isinstance(self.user, dict) else getattr(self.user, 'name',
                                                                                                     'Unknown')
            success = self.cart_controller.process_checkout(self.grid_controller.all_products, user_name)
            if success:
                self.grid_controller.refresh_products()

    # --- RESPONS LOGIC ---
    def resizeEvent(self, event):
        width = self.width()
        new_cols = 4
        if width > 1350:
            new_cols = 5
        elif width > 1050:
            new_cols = 4
        else:
            new_cols = 3

        if hasattr(self, 'grid_controller'):
            self.grid_controller.set_columns(new_cols)
        super().resizeEvent(event)