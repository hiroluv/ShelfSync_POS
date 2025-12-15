# views/product_card.py
from PyQt6.QtWidgets import QWidget
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
import os


class ProductCard(QWidget):
    # Signal that emits the product ID (int) when the card is clicked
    add_to_cart_clicked = pyqtSignal(int)

    def __init__(self, product):
        super().__init__()
        self.product = product

        # 1. Load the .ui file dynamically
        base_path = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(base_path, 'item_product_card.ui')

        try:
            uic.loadUi(ui_path, self)
        except FileNotFoundError:
            print(f"Error: Could not find UI file at {ui_path}")
            return

        self.setup_ui()

    def setup_ui(self):
        # 2. Populate Labels
        if hasattr(self, 'lbl_name'):
            self.lbl_name.setText(self.product.name)

        if hasattr(self, 'lbl_price'):
            self.lbl_price.setText(f"₱{self.product.selling_price:,.2f}")

        if hasattr(self, 'lbl_stock'):
            self.lbl_stock.setText(f"{self.product.stock} left")

            # Low stock warning (Red text)
            if self.product.stock <= 5:
                self.lbl_stock.setStyleSheet("color: #EF4444; font-weight: bold;")

        # 3. Connect the Button
        # This is the critical fix: We connect to a custom method, NOT directly to emit
        if hasattr(self, 'btn_card'):
            self.btn_card.clicked.connect(self.emit_signal)

    def emit_signal(self):
        """Helper to ensure we send the ID, not the button's boolean state."""
        # This prevents the 'bool' vs 'int' crash
        if hasattr(self, 'product') and hasattr(self.product, 'id'):
            self.add_to_cart_clicked.emit(self.product.id)
        else:
            print("Error: Product object invalid or missing ID")