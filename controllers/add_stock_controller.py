# controllers/add_stock_controller.py
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDialog, QPushButton, QLineEdit, QDateEdit, QMessageBox
from PyQt6.QtCore import Qt, QPoint, QDate
import os
import datetime

try:
    from utils.ui_helper import add_drop_shadow
except ImportError:
    def add_drop_shadow(*args, **kwargs):
        pass


class AddStockDialogController(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        if parent and hasattr(parent, 'db'):
            self.db = parent.db

        self.old_pos = None

        # For passing back to inventory controller
        self.accepted_product_name = ""
        self.accepted_action = "Product Added"

        # Load UI
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(current_dir, '..', 'views', 'add_stock_dialog.ui')

        if not os.path.exists(ui_path):
            QMessageBox.critical(None, "Error", f"Add Stock UI file not found:\n{ui_path}")
            self.reject()
            return

        uic.loadUi(ui_path, self)

        # Frameless + draggable
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Drop shadow
        dialog_content = self.findChild(QtWidgets.QFrame, 'dialog_content')
        if dialog_content:
            add_drop_shadow(dialog_content)

        # Get widgets — exact names from your UI
        self.txt_barcode = self.findChild(QLineEdit, 'txt_barcode')
        self.txt_name = self.findChild(QLineEdit, 'txt_name')
        self.txt_category = self.findChild(QLineEdit, 'txt_category')
        self.txt_cost = self.findChild(QLineEdit, 'txt_cost')
        self.txt_price = self.findChild(QLineEdit, 'txt_price')
        self.txt_stock = self.findChild(QLineEdit, 'txt_stock')
        self.date_expiry = self.findChild(QDateEdit, 'date_expiry')
        self.btn_save = self.findChild(QPushButton, 'btn_save')
        self.btn_cancel = self.findChild(QPushButton, 'btn_cancel')

        # Safety check
        missing = []
        if not self.txt_name: missing.append("txt_name")
        if not self.txt_category: missing.append("txt_category")
        if not self.txt_cost: missing.append("txt_cost")
        if not self.txt_price: missing.append("txt_price")
        if not self.txt_stock: missing.append("txt_stock")
        if not self.date_expiry: missing.append("date_expiry")
        if not self.btn_save: missing.append("btn_save")
        if not self.btn_cancel: missing.append("btn_cancel")

        if missing:
            QMessageBox.critical(self, "UI Error", f"Missing widgets:\n{', '.join(missing)}")
            self.reject()
            return

        # Connect buttons
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.btn_cancel.clicked.connect(self.reject)

        # Default values
        self.txt_stock.setText("0")
        self.date_expiry.setDate(QDate.currentDate())
        self.date_expiry.setCalendarPopup(True)
        self.date_expiry.setDisplayFormat("yyyy-MM-dd")

    def on_save_clicked(self):
        try:
            # Get and validate inputs
            name = self.txt_name.text().strip()
            category = self.txt_category.text().strip()
            cost_text = self.txt_cost.text().strip()
            price_text = self.txt_price.text().strip()
            stock_text = self.txt_stock.text().strip()

            if not name:
                QMessageBox.warning(self, "Required", "Product Name is required.")
                return
            if not category:
                QMessageBox.warning(self, "Required", "Category is required.")
                return
            if not cost_text or not price_text or not stock_text:
                QMessageBox.warning(self, "Required", "Please fill Cost Price, Selling Price, and Initial Stock.")
                return

            cost_price = float(cost_text)
            selling_price = float(price_text)
            stock = int(stock_text)

            if cost_price < 0 or selling_price < 0 or stock < 0:
                QMessageBox.warning(self, "Invalid", "Prices and stock cannot be negative.")
                return

            # Expiry date - optional
            expiry_qdate = self.date_expiry.date()
            expiry_date = expiry_qdate.toPyDate()
            expiry_date_str = expiry_date.strftime("%Y-%m-%d") if expiry_qdate >= QDate.currentDate() else None

            # Barcode is optional
            barcode = self.txt_barcode.text().strip() if self.txt_barcode else None

            # Insert into database
            if not self.db:
                QMessageBox.critical(self, "Error", "Database not available.")
                return

            conn = self.db.get_connection()
            if not conn:
                QMessageBox.critical(self, "Error", "Cannot connect to database.")
                return

            cursor = conn.cursor()
            query = """
                INSERT INTO inventory 
                (name, category, cost_price, selling_price, stock, expiry_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, category, cost_price, selling_price, stock, expiry_date_str))
            conn.commit()
            cursor.close()
            conn.close()

            # Success
            self.accepted_product_name = name
            self.accept()

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for prices and stock.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save product:\n{e}")
            print(f"Error saving product: {e}")

    # Window drag support
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