from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QVBoxLayout, QScrollArea
import datetime
import os

# IMPORT THE HELPER CLASS
from models.db_manager import ManagerDB


class PerishablesController:
    def __init__(self, view, main_controller):
        self.view = view
        self.main_controller = main_controller

        # --- FIX: WRAP THE DB CONNECTION ---
        # We wrap the raw connection (main_controller.db) with ManagerDB
        # so we can use the 'get_expiring_products_in_stock' method.
        self.db = ManagerDB(main_controller.db)

        # 1. FIND THE LAYOUT
        self.layout = None
        scroll_area = self.view.findChild(QScrollArea, 'scrollArea_perishables')
        if scroll_area and scroll_area.widget() and scroll_area.widget().layout():
            self.layout = scroll_area.widget().layout()
        if not self.layout:
            self.layout = self.view.findChild(QVBoxLayout, 'layout_list')

        if not self.layout:
            print("CRITICAL: Could not find any layout to add items to in Perishables Window.")

        # 2. Path to Row UI
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.item_ui_path = os.path.join(base_path, 'views', 'item_perishable.ui')

        self.refresh_data()

    def refresh_data(self):
        if not self.layout:
            return

        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered_items = self.db.get_expiring_products_in_stock(days_threshold=30)

        today = datetime.date.today()

        for item in filtered_items:
            try:
                # Calculate days_left for styling
                exp = item.expiry_date
                if isinstance(exp, str):
                    exp = datetime.datetime.strptime(exp, "%Y-%m-%d").date()
                elif isinstance(exp, datetime.datetime):
                    exp = exp.date()

                days_left = (exp - today).days

                # Render Row
                row = uic.loadUi(self.item_ui_path)

                if hasattr(row, 'lbl_name'):
                    row.lbl_name.setText(item.name)
                if hasattr(row, 'lbl_category'):
                    row.lbl_category.setText(item.category)
                if hasattr(row, 'lbl_expiry'):
                    row.lbl_expiry.setText(exp.strftime("%Y-%m-%d"))
                if hasattr(row, 'lbl_stock'):
                    row.lbl_stock.setText(f"Quantity: {item.stock}")

                if days_left < 0:
                    status = f"EXPIRED ({abs(days_left)} days ago)"
                    style = "background-color: #EF4444; color: white; font-weight: bold; border-radius: 13px;"
                elif days_left <= 7:
                    status = f"DISCOUNT NOW ({days_left} days left)"
                    style = "background-color: #FBBF24; color: #475569; font-weight: bold; border-radius: 13px;"
                else:
                    status = "Stock Check"
                    style = "background-color: #E2E8F0; color: #475569; font-weight: bold; border-radius: 13px;"

                if hasattr(row, 'lbl_action'):
                    row.lbl_action.setText(status)
                    row.lbl_action.setStyleSheet(style)

                self.layout.insertWidget(self.layout.count() - 1, row)

            except Exception as e:
                print(f"Error adding perishable row: {e}")