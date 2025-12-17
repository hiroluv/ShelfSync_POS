from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDialog, QMessageBox, QLineEdit, QComboBox, QDateEdit, QPushButton
from PyQt6.QtCore import Qt, QDate
import os

# Import Utils
try:
    from utils.ui_helper import add_drop_shadow
except ImportError:
    def add_drop_shadow(*args, **kwargs):
        pass


class AddStockDialogController(QDialog):
    def __init__(self, main_controller=None):
        super().__init__()
        self.main_controller = main_controller
        self.db = main_controller.db if main_controller else None
        self.old_pos = None

        # Load UI
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', 'add_stock_dialog.ui')

        if not os.path.exists(ui_path):
            QMessageBox.critical(None, "Error", f"UI file not found: {ui_path}")
            self.reject()
            return

        uic.loadUi(ui_path, self)

        # UI Setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        dialog_content = self.findChild(QtWidgets.QFrame, 'dialog_content')
        if dialog_content:
            add_drop_shadow(dialog_content)

        # --- 1. Get Widgets using IDs from your XML ---
        self.txt_name = self.findChild(QLineEdit, 'txt_name')

        # [NEW] Get the new text input
        self.txt_new_category = self.findChild(QLineEdit, 'txt_new_category')

        self.cmb_category = self.findChild(QComboBox, 'cmb_category')


        self.txt_cost = self.findChild(QLineEdit, 'txt_cost')
        self.txt_price = self.findChild(QLineEdit, 'txt_price')
        self.txt_stock = self.findChild(QLineEdit, 'txt_stock')
        self.date_expiry = self.findChild(QDateEdit, 'date_expiry')
        self.txt_barcode = self.findChild(QLineEdit, 'txt_barcode')

        self.btn_save = self.findChild(QPushButton, 'btn_save')
        self.btn_cancel = self.findChild(QPushButton, 'btn_cancel')

        # --- 2. Setup Defaults ---
        self.populate_categories()

        if self.date_expiry:
            self.date_expiry.setDate(QDate.currentDate())
            self.date_expiry.setCalendarPopup(True)

        # --- 3. Connections ---
        if self.btn_save: self.btn_save.clicked.connect(self.save_product)
        if self.btn_cancel: self.btn_cancel.clicked.connect(self.reject)

        # [NEW] Connect the "Seesaw" logic
        if self.txt_new_category:
            self.txt_new_category.textChanged.connect(self.handle_category_input_change)

    def populate_categories(self):
        """Fetches categories from DB to fill the ComboBox."""
        if not self.cmb_category: return

        # 1. Clear existing items
        self.cmb_category.clear()

        # 2. Add Default Option
        self.cmb_category.addItem("Select from list...", None)

        # 3. Fetch from Database
        if self.db:
            try:
                categories = self.db.get_all_categories()

                # Debug print to verify data
                print(f"DEBUG: Categories fetched from DB: {categories}")

                if categories:
                    self.cmb_category.addItems(categories)
            except Exception as e:
                print(f"Error loading categories: {e}")

        # 4. Final UI Adjustments
        self.cmb_category.setEditable(False)

        # FORCE SELECTION: Ensure the first item ("Select from list...") is selected
        if self.cmb_category.count() > 0:
            self.cmb_category.setCurrentIndex(0)

        # Ensure it is enabled
        self.cmb_category.setEnabled(True)

    def handle_category_input_change(self, text):
        """
        If text is typed in 'New Category', disable the Dropdown.
        If 'New Category' is empty, enable the Dropdown.
        """
        if not self.cmb_category: return

        if text.strip():
            # User is typing a new category -> Disable dropdown
            self.cmb_category.setEnabled(False)
            self.cmb_category.setCurrentIndex(0)  # Reset dropdown selection
        else:
            # User cleared the text -> Enable dropdown
            self.cmb_category.setEnabled(True)

    def save_product(self):
        """Validates inputs and saves via ManagerDB."""
        try:
            # 1. Gather Inputs
            name = self.txt_name.text().strip() if self.txt_name else ""

            # [UPDATED LOGIC] Determine which Category to use
            final_category = ""

            # Check 'New Category' Box first
            new_cat_text = self.txt_new_category.text().strip() if self.txt_new_category else ""

            # Check Dropdown second
            dropdown_text = ""
            if self.cmb_category and self.cmb_category.isEnabled():
                # We use currentText() but we ignore the placeholder "Select from list..."
                current = self.cmb_category.currentText()
                if current != "Select from list...":
                    dropdown_text = current

            # Decision Matrix
            if new_cat_text:
                final_category = new_cat_text
            elif dropdown_text:
                final_category = dropdown_text

            # Numbers (QLineEdit)
            cost_text = self.txt_cost.text().strip() if self.txt_cost else "0"
            price_text = self.txt_price.text().strip() if self.txt_price else "0"
            stock_text = self.txt_stock.text().strip() if self.txt_stock else "0"

            # Expiry (QDateEdit)
            expiry_str = ""
            if self.date_expiry:
                expiry_str = self.date_expiry.date().toString("yyyy-MM-dd")

            # 2. Validation
            if not name:
                QMessageBox.warning(self, "Validation", "Product Name is required.")
                return

            if not final_category:
                QMessageBox.warning(self, "Validation", "Please select an existing category OR type a new one.")
                return

            try:
                cost = float(cost_text)
                price = float(price_text)
                stock = int(stock_text)
            except ValueError:
                QMessageBox.warning(self, "Validation", "Stock and Price must be valid numbers.")
                return

            # 3. Save to Database
            if self.db:
                # Use final_category here
                success = self.db.add_product(name, final_category, stock, cost, price, 10, expiry_str)

                if success:
                    self.accept()  # Close dialog on success
                else:
                    QMessageBox.critical(self, "Database Error", "The database returned an error.")
            else:
                QMessageBox.critical(self, "Error", "Database connection missing.")

        except Exception as e:
            print(f"Error in save_product: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{e}")

    # --- Dragging Logic ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None