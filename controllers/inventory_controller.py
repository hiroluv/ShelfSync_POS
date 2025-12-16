# controllers/inventory_controller.py
from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget, QScrollArea
import os

from utils.ui_helper import Overlay, add_drop_shadow, set_icon
from utils.toast_notification import show_toast

# Import Sub-Controllers
from controllers.add_stock_controller import AddStockDialogController
from controllers.edit_product_controller import EditProductDialogController
from controllers.audit_controller import AuditWindowController


class InventoryController:
    def __init__(self, view, main_controller):
        self.view = view
        self.main_controller = main_controller
        self.db = main_controller.db

        self.active_filter_button = None

        self.setup_ui()
        self.setup_connections()

        # Start with All Items active
        if hasattr(self.view, 'btn_filter_all'):
            self.set_active_filter(self.view.btn_filter_all)

        # Load data safely
        self.refresh_data("all")

    def setup_ui(self):
        # 1. Setup Add Stock Button
        if hasattr(self.view, 'btn_add_stock'):
            add_drop_shadow(self.view.btn_add_stock, color_alpha=100, hex_color="#06B6D4")
            set_icon(self.view.btn_add_stock, 'plus.svg', size=18)
            self.view.btn_add_stock.setText(" Add Stock")

        # 2. Setup View Logs Button
        if hasattr(self.view, 'btn_view_logs'):
            set_icon(self.view.btn_view_logs, 'clipboard.svg', size=18)
            self.view.btn_view_logs.setText(" Audit Logs")

        # 3. Setup Filter Button Styles
        style_active = """
            QPushButton {
                background-color: #06B6D4; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                font-weight: bold; 
                padding: 5px 15px;
            }
        """
        style_default = """
            QPushButton {
                background-color: #F1F5F9; 
                color: #64748B; 
                border: 1px solid #E2E8F0; 
                border-radius: 8px; 
                font-weight: bold; 
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """

        buttons = ['btn_filter_all', 'btn_filter_low', 'btn_filter_out', 'btn_filter_expiring']
        for btn_name in buttons:
            if hasattr(self.view, btn_name):
                btn = getattr(self.view, btn_name)
                btn.active_style = style_active
                btn.default_style = style_default
                btn.setStyleSheet(style_default)

    def setup_connections(self):
        if hasattr(self.view, 'btn_add_stock'):
            self.view.btn_add_stock.clicked.connect(self.open_add_stock_dialog)

        if hasattr(self.view, 'btn_view_logs'):
            self.view.btn_view_logs.clicked.connect(self.open_audit_logs)

        # Filters
        if hasattr(self.view, 'btn_filter_all'):
            self.view.btn_filter_all.clicked.connect(
                lambda: [self.set_active_filter(self.view.btn_filter_all), self.refresh_data("all")])
        if hasattr(self.view, 'btn_filter_low'):
            self.view.btn_filter_low.clicked.connect(
                lambda: [self.set_active_filter(self.view.btn_filter_low), self.refresh_data("low")])
        if hasattr(self.view, 'btn_filter_out'):
            self.view.btn_filter_out.clicked.connect(
                lambda: [self.set_active_filter(self.view.btn_filter_out), self.refresh_data("out")])

        # Search
        if hasattr(self.view, 'input_search'):
            self.view.input_search.textChanged.connect(self.handle_search)

    def set_active_filter(self, button):
        if self.active_filter_button and hasattr(self.active_filter_button, 'default_style'):
            self.active_filter_button.setStyleSheet(self.active_filter_button.default_style)

        self.active_filter_button = button
        if hasattr(button, 'active_style'):
            button.setStyleSheet(button.active_style)

    def refresh_data(self, filter_type="all"):

        if not hasattr(self.view, 'layout_inventory_list'):
            print("CRITICAL ERROR: 'layout_inventory_list' not found in UI.")
            return

        layout = self.view.layout_inventory_list

        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # === FETCH DATA ===
        products = self.db.get_inventory_items()

        # Filter Data
        filtered_products = []
        if filter_type == "all":
            filtered_products = products
        elif filter_type == "low":
            filtered_products = [p for p in products if p.stock <= p.threshold and p.stock > 0]
        elif filter_type == "out":
            filtered_products = [p for p in products if p.stock == 0]

        # Sort (Newest First)
        filtered_products.sort(key=lambda x: x.id, reverse=True)

        # ROWS
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        row_ui_path = os.path.join(base_path, 'views', 'item_inventory.ui')

        for product in filtered_products:
            try:
                row_widget = uic.loadUi(row_ui_path)

                # Set Data
                if hasattr(row_widget, 'lbl_name'): row_widget.lbl_name.setText(product.name)
                if hasattr(row_widget, 'lbl_category'): row_widget.lbl_category.setText(product.category)
                if hasattr(row_widget, 'lbl_stock'):row_widget.lbl_stock.setText(str(product.stock))
                if hasattr(row_widget, 'lbl_price'): row_widget.lbl_price.setText(f"₱{product.selling_price:,.2f}")

                # Status Badge
                if hasattr(row_widget, 'lbl_status'):
                    if product.stock == 0:
                        row_widget.lbl_status.setText("Out of Stock")
                        row_widget.lbl_status.setStyleSheet(
                            "background-color: #FEE2E2; color: #DC2626; border-radius: 12px; font-weight: bold;")
                    elif product.stock <= product.threshold:
                        row_widget.lbl_status.setText("Low Stock")
                        row_widget.lbl_status.setStyleSheet(
                            "background-color: #FEF3C7; color: #D97706; border-radius: 12px; font-weight: bold;")
                    else:
                        row_widget.lbl_status.setText("In Stock")
                        row_widget.lbl_status.setStyleSheet(
                            "background-color: #ECFDF5; color: #059669; border-radius: 12px; font-weight: bold;")

                #Edit Button
                if hasattr(row_widget, 'btn_edit'):
                    row_widget.btn_edit.clicked.connect(lambda _, p=product: self.open_edit_dialog(p))
                spacer_index = layout.count() - 1   # Always insert at (count() - 1) to keep the spacer at the bottom
                layout.insertWidget(spacer_index, row_widget)

            except Exception as e:
                print(f"Error loading row: {e}")

    def handle_search(self, text):
        self.refresh_data("all")

    def open_add_stock_dialog(self):
        try:
            overlay = Overlay(self.main_controller)
            overlay.show()

            dialog = AddStockDialogController(parent=self.main_controller)
            dialog.setModal(True)
            if dialog.exec():
                show_toast(self.main_controller, "Stock Added Successfully!", type="success")
                self.refresh_data("all")

            overlay.close()
        except Exception as e:
            print(f"Error opening add stock: {e}")

    def open_edit_dialog(self, product):
        try:
            overlay = Overlay(self.main_controller)
            overlay.show()

            #USER CHECK
            if hasattr(self.main_controller, 'user') and self.main_controller.user:
                current_user = self.main_controller.user.name
            else:
                current_user = "System Admin"

            dialog = EditProductDialogController(self.main_controller, product, current_user)
            dialog.setModal(True)
            if dialog.exec():
                self.refresh_data("all")
                show_toast(self.main_controller, "Product updated & logged.", type="success")

            overlay.close()

        except Exception as e:
            print(f"Error opening edit dialog: {e}")

    def open_audit_logs(self):
        try:
            window = AuditWindowController(self.main_controller)
            window.exec()
        except Exception as e:
            print(f"Error opening audit logs: {e}")