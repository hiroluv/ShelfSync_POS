# controllers/main_controller.py
from PyQt6 import QtWidgets, uic, QtGui, QtCore
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal
import os
import sys

from controllers.add_stock_controller import AddStockDialogController
from controllers.dashboard_controller import DashboardController
from controllers.inventory_controller import InventoryController
from controllers.perishables_controller import PerishablesController
from controllers.reports_controller import ReportsController
from controllers.users_controller import UsersController
from models.database_manager import DatabaseManager
from utils.ui_helper import center_window


class MainController(QMainWindow):
    logout_request = pyqtSignal()

    def __init__(self, db_manager, user_data=None):
        super().__init__()

        self.setWindowOpacity(0.0)

        self.db = db_manager
        self.user = user_data  # Store the logged-in user

        self.load_main_ui()
        self.setup_sidebar()

        # Display the user name immediately
        self.update_user_display()

        # Initialize pages
        self.init_pages()

        # Connect Navigation
        if hasattr(self, 'btn_nav_dashboard'):
            self.btn_nav_dashboard.clicked.connect(lambda: self.switch_page(0))
        if hasattr(self, 'btn_nav_inventory'):
            self.btn_nav_inventory.clicked.connect(lambda: self.switch_page(1))
        if hasattr(self, 'btn_nav_perishables'):
            self.btn_nav_perishables.clicked.connect(lambda: self.switch_page(2))
        if hasattr(self, 'btn_nav_reports'):
            self.btn_nav_reports.clicked.connect(lambda: self.switch_page(3))
        if hasattr(self, 'btn_nav_users'):
            self.btn_nav_users.clicked.connect(lambda: self.switch_page(4))

        if hasattr(self, 'btn_logout'):
            self.btn_logout.clicked.connect(self.handle_logout)

        # Force size for the Manager Dashboard
        self.resize(1200, 700)

        center_window(self)
        self.fade_in()

    def update_user_display(self):
        """Updates the sidebar label with the current user's name and role."""
        if hasattr(self, 'lbl_user'):
            if self.user:
                # Handle both dictionary and object access
                if isinstance(self.user, dict):
                    name = self.user.get('name', 'Unknown')
                    role = self.user.get('role', '')
                else:
                    name = getattr(self.user, 'name', 'Unknown')
                    role = getattr(self.user, 'role', '')

                if role:
                    self.lbl_user.setText(f"{name}\n({role})")
                else:
                    self.lbl_user.setText(name)
            else:
                self.lbl_user.setText("System Admin")

    def fade_in(self):
        self.anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(600)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def handle_logout(self):
        print("Logging out...")
        self.logout_request.emit()
        self.close()

    def load_main_ui(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', 'dashboard_window.ui')
        if not os.path.exists(ui_path):
            print("CRITICAL: dashboard_window.ui not found!")
            sys.exit(1)
        uic.loadUi(ui_path, self)

    def setup_sidebar(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icon_folder_normal = os.path.join(base_path, 'assets', 'side_panel_icons')
        self.icon_folder_active = os.path.join(self.icon_folder_normal, 'active')

        self.sidebar_buttons = []
        if hasattr(self, 'btn_nav_dashboard'): self.sidebar_buttons.append((self.btn_nav_dashboard, "dashboard.svg"))
        if hasattr(self, 'btn_nav_inventory'): self.sidebar_buttons.append((self.btn_nav_inventory, "inventory.svg"))
        if hasattr(self, 'btn_nav_perishables'): self.sidebar_buttons.append(
            (self.btn_nav_perishables, "perishables.svg"))
        if hasattr(self, 'btn_nav_reports'): self.sidebar_buttons.append((self.btn_nav_reports, "bar-chart.svg"))
        if hasattr(self, 'btn_nav_users'): self.sidebar_buttons.append((self.btn_nav_users, "users.svg"))

        for btn, filename in self.sidebar_buttons:
            self.configure_button(btn, filename)

        logout_filename = "log-out.svg"
        if hasattr(self, 'btn_logout'):
            self.configure_button(self.btn_logout, logout_filename)
            self.btn_logout.setStyleSheet("""
                QPushButton {
                    text-align: left; padding: 12px 20px; border: none;
                    color: #EF4444; background-color: transparent;
                    font-size: 14px; border-radius: 10px; margin: 4px 10px; font-weight: bold;
                }
                QPushButton:hover { background-color: #EF4444; color: white; }
                QPushButton:pressed { background-color: #DC2626; }
            """)

        if self.sidebar_buttons:
            first_btn = self.sidebar_buttons[0][0]
            first_btn.setChecked(True)
            self.set_btn_icon(first_btn, first_btn.path_active)

    def configure_button(self, btn, filename):
        normal_path = os.path.join(self.icon_folder_normal, filename)
        active_path = os.path.join(self.icon_folder_active, filename)
        btn.path_normal = normal_path
        btn.path_active = active_path
        self.set_btn_icon(btn, normal_path)
        btn.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)
        btn.setMouseTracking(True)
        btn.installEventFilter(self)

    def set_btn_icon(self, btn, path):
        if os.path.exists(path):
            btn.setIcon(QIcon(path))
            btn.setIconSize(QtCore.QSize(20, 20))

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.Type.Enter:
            if hasattr(source, 'path_active'):
                self.set_btn_icon(source, source.path_active)
        elif event.type() == QtCore.QEvent.Type.Leave:
            if hasattr(source, 'path_normal'):
                if source.isCheckable() and source.isChecked():
                    pass
                else:
                    self.set_btn_icon(source, source.path_normal)
        return super().eventFilter(source, event)

    def switch_page(self, index):
        self.main_stack.setCurrentIndex(index)
        for btn, _ in self.sidebar_buttons:
            if btn.isChecked():
                self.set_btn_icon(btn, btn.path_active)
            else:
                self.set_btn_icon(btn, btn.path_normal)

        # Refresh Data when mag switch page (no more re-running yay)
        if index == 0:
            self.dashboard_controller.refresh_data()
        elif index == 1:
            self.inventory_controller.refresh_data("all")
        elif index == 2:
            self.perishables_controller.refresh_data()
        elif index == 3:
            self.reports_controller.refresh_data()
        elif index == 4:
            self.users_controller.refresh_data()

    def init_pages(self):
        # 1. Dashboard
        self.dashboard_controller = DashboardController(self.page_dashboard, self)

        # 2. Inventory (CORRECT: inventory_window.ui)
        self.page_inventory = self.load_and_add_page('inventory_window.ui')
        self.inventory_controller = InventoryController(self.page_inventory, self)

        # 3. Perishables (CORRECT: perishables_window.ui)
        self.page_perishables = self.load_and_add_page('perishables_window.ui')
        self.perishables_controller = PerishablesController(self.page_perishables, self)

        # 4. Reports (CORRECT: reports_window.ui)
        self.page_reports = self.load_and_add_page('reports_window.ui')
        self.reports_controller = ReportsController(self.page_reports, self)

        # 5. Users (CORRECT: user_accounts_window.ui)
        self.page_users = self.load_and_add_page('user_accounts_window.ui')
        self.users_controller = UsersController(self.page_users, self)

    def load_and_add_page(self, filename):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', filename)

        if not os.path.exists(ui_path):
            print(f"CRITICAL ERROR: UI file not found: {filename}")
            widget = QtWidgets.QWidget()  # Fallback to empty widget to prevent crash
        else:
            try:
                widget = uic.loadUi(ui_path)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                widget = QtWidgets.QWidget()

        self.main_stack.addWidget(widget)
        return widget

    def open_add_stock_dialog(self):
        dialog = AddStockDialogController()
        if dialog.exec():
            if hasattr(self, 'inventory_controller'):
                self.inventory_controller.refresh_data("all")