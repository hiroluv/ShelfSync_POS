from PyQt6 import uic, QtCore
import os

from utils.ui_helper import add_drop_shadow, set_icon, apply_hover_effect


class DashboardController(QtCore.QObject):
    def __init__(self, view, main_controller):
        super().__init__()
        self.view = view
        self.main_controller = main_controller
        self.db = main_controller.db

        self.setup_ui()
        self.refresh_data()

    # mga ao na design pu
    def setup_ui(self):
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

        while layout.count() > 1:
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        sales = self.db.get_recent_sales()

        ui_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'views', 'item_sale.ui'
        )

        if not os.path.exists(ui_path):
            print(f"Error: item_sale.ui not found at {ui_path}")
            return

        for sale in sales:
            try:
                widget = uic.loadUi(ui_path)

                if hasattr(widget, 'lbl_product_name'):
                    widget.lbl_product_name.setText(sale.get('product_name', 'Unknown Item'))
                if hasattr(widget, 'lbl_price'):
                    widget.lbl_price.setText(f"₱{float(sale.get('price', 0)):.2f}")
                if hasattr(widget, 'lbl_quantity'):
                    widget.lbl_quantity.setText(f"Qty: {sale.get('quantity', 0)}")
                if hasattr(widget, 'lbl_cashier_name'):
                    widget.lbl_cashier_name.setText(f"Cashier: {sale.get('cashier_name', 'N/A')}")
                if hasattr(widget, 'lbl_time'):
                    time_val = sale.get('sale_timestamp')
                    if time_val:
                        widget.lbl_time.setText(time_val.strftime("%b %d, %I:%M %p"))

                layout.insertWidget(0, widget)

            except Exception as e:
                print(f"Error loading sale row: {e}")