from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDialog, QMessageBox, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import Qt, QDate
import os
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

        # UI
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        dialog_content = self.findChild(QtWidgets.QFrame, 'dialog_content')
        if dialog_content:
            add_drop_shadow(dialog_content)

        # Get Widgets
        self.txt_name = self.findChild(QLineEdit, 'txt_name')
        self.txt_category = self.findChild(QLineEdit, 'txt_category')
        self.txt_cost = self.findChild(QLineEdit, 'txt_cost')
        self.txt_price = self.findChild(QLineEdit, 'txt_price')
        self.txt_stock = self.findChild(QLineEdit, 'txt_stock')
        self.date_expiry = self.findChild(QDateEdit, 'date_expiry')
        self.txt_barcode = self.findChild(QLineEdit, 'txt_barcode')

        self.btn_save = self.findChild(QPushButton, 'btn_save')
        self.btn_cancel = self.findChild(QPushButton, 'btn_cancel')
        # defaults
        if self.date_expiry:
            self.date_expiry.setDate(QDate.currentDate())
            self.date_expiry.setCalendarPopup(True)
        # Connections
        if self.btn_save: self.btn_save.clicked.connect(self.save_product)
        if self.btn_cancel: self.btn_cancel.clicked.connect(self.reject)

    def save_product(self):
        #saves in ManagerDB
        try:
            #getInputs
            name = self.txt_name.text().strip() if self.txt_name else ""
            # Read textfrom QLineEdit
            category = self.txt_category.text().strip() if self.txt_category else ""
            cost_text = self.txt_cost.text().strip() if self.txt_cost else "0"
            price_text = self.txt_price.text().strip() if self.txt_price else "0"
            stock_text = self.txt_stock.text().strip() if self.txt_stock else "0"
            expiry_str = ""
            if self.date_expiry:
                expiry_str = self.date_expiry.date().toString("yyyy-MM-dd")
            # 2. Validation
            if not name:
                QMessageBox.warning(self, "Validation", "Product Name is required.")
                return
            if not category:
                QMessageBox.warning(self, "Validation", "Category is required.")
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
                success = self.db.add_product(name, category, stock, cost, price, 10, expiry_str) #10 is the threshold for expiry
                if success:
                    self.accept()  # Close dialog

        except Exception as e:
            print(f"Error in save_product: {e}")
            QMessageBox.critical(self, "Error", f"guba nasad\n{e}")