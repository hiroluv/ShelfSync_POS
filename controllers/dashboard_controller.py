from PyQt6 import uic, QtCore
from PyQt6.QtCore import QTimer, QDateTime  # <--- Added these imports
import os

from utils.ui_helper import add_drop_shadow, set_icon, apply_hover_effect


class DashboardController(QtCore.QObject):
    def __init__(self, view, main_controller):
        super().__init__()
        self.view = view
        self.main_controller = main_controller
        self.db = main_controller.db

        # Default name
        self.current_user_name = "Manager"

        self.setup_ui()
        self.refresh_data()
        self.start_clock()  # <--- Start the clock immediately

    def setup_ui(self):
        # --- 1. GET USER NAME ---
        # We fetch this once during setup so we don't query it every second
        if hasattr(self.main_controller, 'user'):
            current_user = getattr(self.main_controller, 'user', None)
            if current_user:
                # Handle if user is an Object (user.name) or Dictionary (user['name'])
                if hasattr(current_user, 'name'):
                    self.current_user_name = current_user.name
                elif isinstance(current_user, dict):
                    self.current_user_name = current_user.get('name', 'Manager')

        # --- 2. EXISTING UI EFFECTS ---
        # Apply Hover Effect (Floating + Shadow) for cards
        if hasattr(self.main_controller, 'card_revenue'):
            apply_hover_effect(self.main_controller.card_revenue)
        if hasattr(self.main_controller, 'card_stock'):
            apply_hover_effect(self.main_controller.card_stock)
        if hasattr(self.main_controller, 'card_expiring'):
            apply_hover_effect(self.main_controller.card_expiring)

        # Static shadow for the table frame (no floating)
        if hasattr(self.main_controller, 'frame_table'):
            add_drop_shadow(self.main_controller.frame_table)

        # icons for the cards
        if hasattr(self.main_controller, 'lbl_icon_1'):
            set_icon(self.main_controller.lbl_icon_1, 'dollar-sign.svg', size=24)
        if hasattr(self.main_controller, 'lbl_icon_2'):
            set_icon(self.main_controller.lbl_icon_2, 'alert-triangle.svg', size=24)  # Low Stock
        if hasattr(self.main_controller, 'lbl_icon_3'):
            set_icon(self.main_controller.lbl_icon_3, 'history.svg', size=24)  # Expiring

    # --- NEW CLOCK FUNCTIONS ---
    def start_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard_time)
        self.timer.start(1000)  # Update every 1 second
        self.update_dashboard_time()  # Run immediately

    def update_dashboard_time(self):
        # Get current time
        current_time = QDateTime.currentDateTime()

        # Format: Month Day, Year | Hour:Minute:Second AM/PM
        # Example: December 17, 2025 | 09:30:45 AM
        date_display = current_time.toString("MMMM d, yyyy")
        time_display = current_time.toString("hh:mm:ss AP")

        # Combine Welcome Message + Date/Time
        final_text = f"Welcome back, {self.current_user_name}\n{date_display} | {time_display}"

        # Update the label
        if hasattr(self.main_controller, 'label_dash_sub'):
            self.main_controller.label_dash_sub.setText(final_text)

    def refresh_data(self):
        stats = self.db.get_dashboard_stats()

        if stats:
            self.main_controller.lbl_val_revenue.setText(f"₱{stats.revenue:,.2f}")
            self.main_controller.lbl_val_stock.setText(str(stats.low_stock_count))
            self.main_controller.lbl_val_expiring.setText(str(stats.expiring_count))

            self.populate_sales_list()
        else:
            self.main_controller.lbl_val_revenue.setText("₱0.00")
            self.main_controller.lbl_val_stock.setText("0")
            self.main_controller.lbl_val_expiring.setText("0")

    def populate_sales_list(self):
        layout = self.main_controller.layout_sales_list

        # 1. Clear existing items
        while layout.count() > 0:
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 2. Fetch Data
        sales = self.db.get_recent_sales()

        # 3. Load UI
        ui_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'views', 'item_sale.ui'
        )

        if not os.path.exists(ui_path):
            return

        for sale in sales:
            try:
                widget = uic.loadUi(ui_path)

                # 1. TOTAL ITEMS (Matches 'items_count' from DB)
                if hasattr(widget, 'lbl_items'):
                    count = sale.get('items_count', 0)
                    widget.lbl_items.setText(f"{count} Items")

                # 2. TOTAL AMOUNT (Matches 'total_amount' from DB)
                if hasattr(widget, 'lbl_total'):
                    amount = float(sale.get('total_amount', 0))
                    widget.lbl_total.setText(f"₱{amount:,.2f}")

                # 3. CASHIER NAME (Matches 'cashier_name' from DB)
                if hasattr(widget, 'lbl_name'):
                    cashier = sale.get('cashier_name', 'N/A')
                    widget.lbl_name.setText(cashier)

                # 4. TIME
                if hasattr(widget, 'lbl_time'):
                    time_val = sale.get('sale_timestamp')
                    if time_val:
                        widget.lbl_time.setText(time_val.strftime("%b %d, %I:%M %p"))

                # assert isinstance(widget, object)
                layout.addWidget(widget)

            except Exception as e:
                print(f"Error loading sale row: {e}")