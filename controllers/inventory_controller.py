from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox
import os

# Utils
try:
    from utils.ui_helper import Overlay, add_drop_shadow, set_icon
    from utils.toast_notification import show_toast
except ImportError:
    pass

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

        # Load data
        self.refresh_data("all")

    def setup_ui(self):
        """Configure UI elements."""

        # Setup Add Stock Button
        if hasattr(self.view, 'btn_add_stock'):
            add_drop_shadow(self.view.btn_add_stock, color_alpha=100, hex_color="#06B6D4")
            set_icon(self.view.btn_add_stock, 'plus.svg', size=18)
            self.view.btn_add_stock.setText(" Add Stock")

        # Setup View Logs Button
        if hasattr(self.view, 'btn_view_logs'):
            set_icon(self.view.btn_view_logs, 'clipboard.svg', size=18)
            self.view.btn_view_logs.setText(" Audit Logs")

        # Setup Filter Button Styles
        style_active = """
            QPushButton {
                background-color: #06B6D4; color: white; border: none; border-radius: 18px; font-weight: bold; font-size: 13px;
            }
        """
        style_default = """
            QPushButton {
                background-color: white; color: #64748B; border: 1px solid #E2E8F0; border-radius: 18px; font-weight: 600; font-size: 13px;
            }
            QPushButton:hover { background-color: #F8FAFC; }
        """

        buttons = ['btn_filter_all', 'btn_filter_low', 'btn_filter_out']
        for btn_name in buttons:
            if hasattr(self.view, btn_name):
                btn = getattr(self.view, btn_name)
                btn.active_style = style_active
                btn.default_style = style_default
                # Reset to default initially (logic handles activation)
                btn.setStyleSheet(style_default)

    def setup_connections(self):
        """Connect buttons and inputs."""

        # Main Actions
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

        # Search Bar Connection
        # Note: Updated name to 'lineEdit_search' based on your latest UI file
        if hasattr(self.view, 'lineEdit_search'):
            self.view.lineEdit_search.textChanged.connect(self.handle_search)

    def set_active_filter(self, button):
        """Highlight the active filter button."""
        if self.active_filter_button and hasattr(self.active_filter_button, 'default_style'):
            self.active_filter_button.setStyleSheet(self.active_filter_button.default_style)

        self.active_filter_button = button
        if hasattr(button, 'active_style'):
            button.setStyleSheet(button.active_style)

    def get_current_username(self):
        """Safely retrieves the name of the currently logged-in user."""
        if not hasattr(self.main_controller, 'user') or not self.main_controller.user:
            return "System Admin"
        user_data = self.main_controller.user
        if isinstance(user_data, dict):
            return user_data.get('name', 'Unknown User')
        return getattr(user_data, 'name', 'Unknown User')

    def refresh_data(self, filter_type="all"):
        """Refreshes the inventory list based on filters AND search text."""
        if not hasattr(self.view, 'layout_inventory_list'):
            return

        layout = self.view.layout_inventory_list

        # Clear existing items
        while layout.count() > 1:  # Keep the spacer
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # === FETCH DATA ===
        products = self.db.get_inventory_items()

        # === GET SEARCH TEXT ===
        search_text = ""
        if hasattr(self.view, 'lineEdit_search'):
            search_text = self.view.lineEdit_search.text().lower().strip()

        filtered_products = []

        for p in products:
            # 1. Search Filter
            if search_text:
                name_match = search_text in p.name.lower()
                cat_match = search_text in p.category.lower()
                if not (name_match or cat_match):
                    continue

                    # 2. Category/Status Filter
            # (Note: In a real app, you might track 'current_filter' state rather than passing string)
            # But for now, we rely on the button click passing the string,
            # or if called from search, we default to "all" (or we should track the active state).
            # *Improvement*: You might want to save self.current_filter_state = "all" in init

            if filter_type == "low":
                if not (p.stock <= p.threshold and p.stock > 0): continue
            elif filter_type == "out":
                if p.stock != 0: continue

            filtered_products.append(p)

        # Sort (Newest First)
        filtered_products.sort(key=lambda x: x.id, reverse=True)

        # === RENDER ROWS ===
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        row_ui_path = os.path.join(base_path, 'views', 'item_inventory.ui')

        for product in filtered_products:
            try:
                row_widget = uic.loadUi(row_ui_path)

                # Set Data
                if hasattr(row_widget, 'lbl_name'): row_widget.lbl_name.setText(product.name)
                if hasattr(row_widget, 'lbl_category'): row_widget.lbl_category.setText(product.category)
                if hasattr(row_widget, 'lbl_stock'): row_widget.lbl_stock.setText(str(product.stock))
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

                # Edit Button
                if hasattr(row_widget, 'btn_edit'):
                    row_widget.btn_edit.clicked.connect(lambda _, p=product: self.open_edit_dialog(p))

                # Insert row before the spacer
                spacer_index = layout.count() - 1
                layout.insertWidget(spacer_index, row_widget)

            except Exception as e:
                print(f"Error loading row: {e}")

    def handle_search(self, text):
        """Called when text changes in search bar."""
        # We assume the user wants to search across 'all' or the current view.
        # For simplicity, we refresh current view.
        # Ideally, you check which button is active.
        filter_mode = "all"
        if self.active_filter_button == getattr(self.view, 'btn_filter_low', None):
            filter_mode = "low"
        elif self.active_filter_button == getattr(self.view, 'btn_filter_out', None):
            filter_mode = "out"

        self.refresh_data(filter_mode)

    def open_add_stock_dialog(self):
        try:
            overlay = Overlay(self.main_controller)
            overlay.show()

            # Pass main_controller so it can access self.main_controller.db
            dialog = AddStockDialogController(main_controller=self.main_controller)
            dialog.setModal(True)
            if dialog.exec():
                show_toast(self.main_controller, "Stock Added Successfully!", type="success")
                self.refresh_data("all")

            overlay.close()
        except Exception as e:
            print(f"Error opening add stock: {e}")
            # Ensure overlay closes if error
            try:
                overlay.close()
            except:
                pass

    def open_edit_dialog(self, product):
        try:
            overlay = Overlay(self.main_controller)
            overlay.show()

            current_user = self.get_current_username()

            dialog = EditProductDialogController(self.main_controller, product, current_user)
            dialog.setModal(True)
            if dialog.exec():
                self.refresh_data("all")
                show_toast(self.main_controller, "Product updated & logged.", type="success")

            overlay.close()

        except Exception as e:
            print(f"Error opening edit dialog: {e}")
            try:
                overlay.close()
            except:
                pass

    def open_audit_logs(self):
        try:
            overlay = Overlay(self.main_controller)
            overlay.show()

            window = AuditWindowController(self.main_controller)
            window.exec()

            overlay.close()
        except Exception as e:
            print(f"Error opening audit logs: {e}")
            try:
                overlay.close()
            except:
                pass