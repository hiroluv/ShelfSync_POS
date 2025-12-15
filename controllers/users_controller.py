# controllers/users_controller.py
from PyQt6 import QtWidgets, uic, QtCore
import os

from utils.ui_helper import Overlay, add_drop_shadow, set_icon
from utils.toast_notification import show_toast


class UsersController:
    def __init__(self, view, main_controller):
        self.view = view
        self.main_controller = main_controller
        self.db = main_controller.db

        self.setup_ui()
        self.setup_connections()
        self.refresh_data()

    def setup_ui(self):
        # Style Add User button
        if hasattr(self.view, 'btn_add_user'):
            add_drop_shadow(self.view.btn_add_user, color_alpha=100, hex_color="#06B6D4")
            set_icon(self.view.btn_add_user, 'user-plus.svg', size=18)

    def setup_connections(self):
        if hasattr(self.view, 'btn_add_user'):
            self.view.btn_add_user.clicked.connect(self.open_add_user_dialog)

    def refresh_data(self):
        # Correct layout name from user_accounts_window.ui
        layout = self.view.layout_users_list

        # Clear existing items
        while layout.count() > 1:
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Fetch users
        users = []
        try:
            users = self.db.get_all_users()
        except Exception as e:
            print(f"Error fetching users: {e}")

        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', 'item_user.ui')

        if not os.path.exists(ui_path):
            print(f"Error: item_user.ui not found at {ui_path}")
            return

        for user in users:
            try:
                row_widget = uic.loadUi(ui_path)

                # Labels from your item_user.ui — exact names
                row_widget.lbl_name.setText(user.name)
                row_widget.lbl_role.setText(user.role)

                # No lbl_initial — use the circle frame or skip
                # If you have a circle QLabel for initial, name it lbl_initial in UI
                # For now, we skip it since it's not in your current UI

                # Remove button
                btn_remove = row_widget.findChild(QtWidgets.QPushButton, 'btn_remove')
                if btn_remove:
                    btn_remove.clicked.connect(lambda checked, uid=user.id: self.remove_user(uid))

                layout.insertWidget(0, row_widget)

            except Exception as e:
                print(f"Error loading user row: {e}")

    def open_add_user_dialog(self):
        try:
            overlay = Overlay(self.main_controller)
            overlay.show()

            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dialog_path = os.path.join(base_path, 'views', 'add_user_dialog.ui')

            if not os.path.exists(dialog_path):
                show_toast(self.main_controller, "Add User dialog not found!", type="error")
                overlay.close()
                return

            dialog = uic.loadUi(dialog_path)
            dialog.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
            dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

            content = dialog.findChild(QtWidgets.QFrame, 'dialog_content')
            if content:
                add_drop_shadow(content)

            result = dialog.exec()
            overlay.close()

            if result == QtWidgets.QDialog.DialogCode.Accepted:
                name = dialog.input_name.text().strip()
                password = dialog.input_password.text().strip()
                role = dialog.input_role.currentText()

                if not name or not password:
                    show_toast(self.main_controller, "Name and password required!", type="error")
                    return

                success = self.db.add_user(name, password, role)
                if success:
                    show_toast(self.main_controller, f"User '{name}' added!", type="success")
                    self.refresh_data()
                else:
                    show_toast(self.main_controller, "Failed to add user.", type="error")

        except Exception as e:
            print(f"Error in add user dialog: {e}")
            show_toast(self.main_controller, "Failed to open Add User dialog.", type="error")

    def remove_user(self, user_id):
        reply = QtWidgets.QMessageBox.question(
            self.view, "Confirm Remove",
            "Are you sure you want to remove this user?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            success = self.db.remove_user(user_id)
            if success:
                show_toast(self.main_controller, "User removed successfully!", type="success")
                self.refresh_data()
            else:
                show_toast(self.main_controller, "Cannot remove last Manager.", type="error")