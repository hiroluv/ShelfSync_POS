# controllers/reports_controller.py
from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtWidgets import QScrollArea, QScrollBar
import os

# Import the ManagerDB wrapper to access helper methods like get_top_products
from models.db_manager import ManagerDB
from utils.ui_helper import add_drop_shadow, set_icon, apply_hover_effect


class ReportsController(QtCore.QObject):
    def __init__(self, view, main_controller):
        super().__init__()
        self.view = view
        self.main_controller = main_controller

        # FIX: Wrap the raw DatabaseManager in ManagerDB
        # This gives us access to self.db.get_top_products() AND self.db.main_db.get_connection()
        self.db = ManagerDB(main_controller.db)

        self.setup_ui()
        self.refresh_data()

    def apply_modern_scrollbar_style(self, scroll_area):
        """Applies a modern, transparent scrollbar style to a QScrollArea."""
        qss = """
        QScrollArea { border: none; background-color: transparent; }
        QScrollBar:vertical { border: none; background: transparent; width: 8px; }
        QScrollBar::groove:vertical { border: none; background: transparent; width: 0px; }
        QScrollBar::handle:vertical { background-color: #94A3B8; border-radius: 4px; min-height: 20px; }
        QScrollBar::handle:vertical:hover { background-color: #64748B; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """
        scroll_area.setStyleSheet(scroll_area.styleSheet() + qss)

    def setup_ui(self):
        # 1. Apply Hover Effect
        if hasattr(self.view, 'card_alert_stock'): apply_hover_effect(self.view.card_alert_stock)
        if hasattr(self.view, 'card_alert_expiry'): apply_hover_effect(self.view.card_alert_expiry)
        if hasattr(self.view, 'card_financial'): apply_hover_effect(self.view.card_financial)

        # 2. Apply Scrollbar Style
        if hasattr(self.view, 'scrollArea_top_selling'):
            self.apply_modern_scrollbar_style(self.view.scrollArea_top_selling)

        # 3. Icons
        if hasattr(self.view, 'icon_stock'): set_icon(self.view.icon_stock, 'alert-triangle.svg', size=24)
        if hasattr(self.view, 'icon_exp'): set_icon(self.view.icon_exp, 'history.svg', size=24)

    def refresh_data(self):
        # --- 1. Financial Overview (Manual Query) ---
        revenue = 0.0
        try:
            # We access .main_db because self.db is now the ManagerDB wrapper
            conn = self.db.main_db.get_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) AS total FROM sales")
                result = cursor.fetchone()
                if result:
                    revenue = float(result['total'])
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"Error fetching revenue: {e}")

        estimated_cost = revenue * 0.70
        estimated_profit = revenue * 0.30

        if hasattr(self.view, 'lbl_val_revenue'): self.view.lbl_val_revenue.setText(f"₱{revenue:,.2f}")
        if hasattr(self.view, 'lbl_val_cost'): self.view.lbl_val_cost.setText(f"₱{estimated_cost:,.2f}")
        if hasattr(self.view, 'lbl_val_profit'): self.view.lbl_val_profit.setText(f"₱{estimated_profit:,.2f}")

        # --- 2. Alerts (Using ManagerDB Method) ---
        try:
            # Assuming get_dashboard_stats exists in ManagerDB (db_manager.py)
            # If not, this block might need a try/except or manual query fallback
            if hasattr(self.db, 'get_dashboard_stats'):
                stats = self.db.get_dashboard_stats()
                if hasattr(self.view, 'lbl_val_alert_stock'):
                    self.view.lbl_val_alert_stock.setText(str(stats.low_stock_count))
                if hasattr(self.view, 'lbl_val_alert_expiry'):
                    self.view.lbl_val_alert_expiry.setText(str(stats.expiring_count))
        except Exception as e:
            print(f"Error fetching stats: {e}")

        # --- 3. Top Selling Items ---
        self.populate_top_selling()

    def populate_top_selling(self):
        if not hasattr(self.view, 'layout_top_selling'): return
        layout = self.view.layout_top_selling

        # Clear layout
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # Fetch Items using ManagerDB method
        items = []
        try:
            # This calls the method in db_manager.py
            results = self.db.get_top_products(limit=5)
            # Convert dictionary result to tuple list [(name, qty), ...]
            items = [(row['name'], row['total_qty']) for row in results]
        except Exception as e:
            print(f"Error loading top products: {e}")
            return

        if not items: return

        max_sold = max(count for _, count in items)

        # Load Row UI
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', 'item_report.ui')

        if not os.path.exists(ui_path): return

        for name, count in items:
            try:
                row_widget = uic.loadUi(ui_path)

                if hasattr(row_widget, 'lbl_name'): row_widget.lbl_name.setText(name)
                if hasattr(row_widget, 'lbl_count'): row_widget.lbl_count.setText(f"{count} sold")

                if hasattr(row_widget, 'progress_bar'):
                    percent = int((count / max_sold) * 100) if max_sold > 0 else 0
                    row_widget.progress_bar.setValue(percent)

                layout.addWidget(row_widget)
            except Exception as e:
                print(f"Error rendering report row: {e}")

        # Add Spacer at bottom
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum,
                                       QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)