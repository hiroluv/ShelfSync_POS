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
        layout = self.view.layout_users_list

        # Clear existing items (Keeping > 1 preserves the bottom spacer if you have one)
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

                # Set Labels
                if hasattr(row_widget, 'lbl_name'):
                    row_widget.lbl_name.setText(user.name)
                if hasattr(row_widget, 'lbl_role'):
                    row_widget.lbl_role.setText(user.role)

                # Connect Delete Button
                # FIX: Capture 'uid' in the lambda so it doesn't default to the last loop item
                btn_remove = row_widget.findChild(QtWidgets.QPushButton, 'btn_remove')
                if btn_remove:
                    btn_remove.clicked.connect(lambda checked, uid=user.id: self.delete_user_action(uid))

                # Insert at top (index 0) to show new users first?
                # Or use layout.addWidget(row_widget) if you want ID order.
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

    def delete_user_action(self, user_id):
        # 1. Create the dialog instance manually (instead of using static .question)
        msg_box = QtWidgets.QMessageBox(self.view)
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setText("Are you sure you want to delete this user?")
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)

        # 2. Apply a specific style to fix the visibility issue
        # We force a dark background and ensure buttons are visible
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #1F2937;  /* Dark Grey Background */
            }
            QLabel {
                color: white;               /* White Text */
                font-size: 14px;
                background: none;
            }
            QPushButton {
                background-color: #374151;  /* Button Color */
                color: white;
                border: 1px solid #4B5563;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4B5563;  /* Lighter on Hover */
            }
        """)

        # 3. Show the dialog
        overlay = Overlay(self.main_controller)
        overlay.show()
        reply = msg_box.exec()
        overlay.close()

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            success = self.db.delete_user(user_id)

            if success:
                show_toast(self.main_controller, "User deleted successfully!", type="success")
                self.refresh_data()
            else:
                show_toast(self.main_controller, "Cannot delete the last Manager account.", type="error")