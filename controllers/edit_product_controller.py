# controllers/edit_product_controller.py
from PyQt6.QtWidgets import QDialog, QMessageBox, QFrame
from PyQt6.QtCore import Qt, QPoint
from PyQt6 import uic
import os

# Import UI Helper for shadow
from utils.ui_helper import add_drop_shadow


class EditProductDialogController(QDialog):
    def __init__(self, parent, product_data, user_name=None):
        super().__init__(parent)
        self.main_controller = parent
        self.product = product_data
        self.db = parent.db

        # Variable for dragging
        self.old_pos = None

        # ========================================================
        #  FRAMELESS WINDOW SETUP
        # ========================================================
        # Frameless + Window Stays on Top (optional, remove StaysOnTop if it's annoying)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ========================================================
        #  USER IDENTITY LOGIC
        # ========================================================
        self.user_name = "System Admin"

        if hasattr(self.main_controller, 'user') and self.main_controller.user:
            user_obj = self.main_controller.user
            if isinstance(user_obj, dict):
                name = user_obj.get('name', 'Unknown')
                role = user_obj.get('role', '')
            else:
                name = getattr(user_obj, 'name', 'Unknown')
                role = getattr(user_obj, 'role', '')

            if role:
                self.user_name = f"{name} ({role})"
            else:
                self.user_name = name
        elif user_name:
            self.user_name = user_name

        # Load UI
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', 'edit_product_dialog.ui')
        try:
            uic.loadUi(ui_path, self)

            # Apply Shadow to the main content frame
            # Ensure your UI has a QFrame named 'dialog_content' wrapping the inputs
            dialog_content = self.findChild(QFrame, 'dialog_content')
            if dialog_content:
                add_drop_shadow(dialog_content)

        except Exception as e:
            print(f"Error loading UI: {e}")

        self.setup_ui()

    def setup_ui(self):
        # 1. Populate Fields
        if hasattr(self, 'input_name'): self.input_name.setText(self.product.name)
        if hasattr(self, 'input_category'): self.input_category.setText(self.product.category)
        if hasattr(self, 'input_cost'): self.input_cost.setValue(self.product.cost_price)
        if hasattr(self, 'input_price'): self.input_price.setValue(self.product.selling_price)
        if hasattr(self, 'input_threshold'): self.input_threshold.setValue(self.product.threshold)

        # 2. Stock Display & Input
        if hasattr(self, 'lbl_current_stock_val'):
            self.lbl_current_stock_val.setText(str(self.product.stock))

        if hasattr(self, 'input_remove_qty'):
            self.input_remove_qty.setValue(0)
            self.input_remove_qty.setMaximum(self.product.stock)

        # Connect Buttons
        if hasattr(self, 'btn_save'): self.btn_save.clicked.connect(self.save_changes)
        if hasattr(self, 'btn_cancel'): self.btn_cancel.clicked.connect(self.reject)

    def save_changes(self):
        new_name = self.input_name.text().strip() if hasattr(self, 'input_name') else self.product.name
        new_category = self.input_category.text().strip() if hasattr(self, 'input_category') else self.product.category
        new_cost = self.input_cost.value() if hasattr(self, 'input_cost') else self.product.cost_price
        new_price = self.input_price.value() if hasattr(self, 'input_price') else self.product.selling_price

        qty_to_remove = 0
        if hasattr(self, 'input_remove_qty'):
            qty_to_remove = self.input_remove_qty.value()

        current_stock = self.product.stock
        new_stock = current_stock - qty_to_remove

        reason = ""
        if hasattr(self, 'input_reason'):
            if hasattr(self.input_reason, 'toPlainText'):
                reason = self.input_reason.toPlainText().strip()
            elif hasattr(self.input_reason, 'text'):
                reason = self.input_reason.text().strip()

        if not new_name:
            QMessageBox.warning(self, "Error", "Product Name is required.")
            return

        if qty_to_remove > 0 and len(reason) < 5:
            QMessageBox.warning(self, "Audit Requirement",
                                "You are removing stock. Please provide a reason (min 5 chars).")
            return

        success = self.db.update_product(
            self.product.id, new_name, new_category, new_stock,
            new_cost, new_price, self.product.threshold, self.product.expiry_date
        )

        if success:
            changes = []
            if new_name != self.product.name: changes.append(f"Name: {self.product.name} -> {new_name}")
            if new_price != self.product.selling_price: changes.append(
                f"Price: {self.product.selling_price} -> {new_price}")
            if new_cost != self.product.cost_price: changes.append(f"Cost: {self.product.cost_price} -> {new_cost}")

            if changes:
                log_details = ", ".join(changes)
                if reason and qty_to_remove == 0: log_details += f". Note: {reason}"
                self.db.log_audit(self.user_name, "Product Edit", log_details)

            if qty_to_remove > 0:
                self.db.log_audit(self.user_name, "Stock Shrinkage",
                                  f"Removed {qty_to_remove}. Old: {current_stock}, New: {new_stock}. Reason: {reason}")

            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to update product.")
