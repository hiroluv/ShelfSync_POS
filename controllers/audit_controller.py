from PyQt6 import uic, QtWidgets
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QPoint
import os

from utils.ui_helper import set_icon, add_drop_shadow, Overlay


class AuditWindowController(QDialog):
    def __init__(self, main_controller):
        # 1. Parent MUST be main_controller
        super().__init__(parent=main_controller)
        self.main_controller = main_controller
        self.db = main_controller.db

        # Variable for dragging
        self.old_pos = None


        self.overlay = Overlay(self.main_controller)
        self.overlay.hide()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Load UI
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', 'audit_window.ui')

        try:
            uic.loadUi(ui_path, self)

            # Apply Shadow to the internal frame named 'dialog_content'
            # This ensures the white box pops out, while the rest is transparent
            content = self.findChild(QFrame, 'dialog_content')
            if content:
                add_drop_shadow(content)
            else:
                # Fallback: if 'dialog_content' isn't found, try the first frame
                # (You should ensure your .ui file has a main QFrame wrapping everything)
                frames = self.findChildren(QFrame)
                if frames: add_drop_shadow(frames[0])

        except Exception as e:
            print(f"Error loading audit_window.ui: {e}")
            self.resize(800, 600)

        self.setup_ui()
        self.load_data()

    def showEvent(self, event):
        """When dialog opens, show the dim overlay on the main window."""
        if self.overlay:
            # 1. Resize overlay to cover the Main Window
            self.overlay.resize(self.main_controller.size())
            # 2. Show the overlay
            self.overlay.show()


        self.raise_()
        self.activateWindow()

        super().showEvent(event)

    def closeEvent(self, event):
        """When dialog closes, hide the overlay."""
        if self.overlay:
            self.overlay.hide()
        super().closeEvent(event)

    def setup_ui(self):
        if hasattr(self, 'btn_close'):
            self.btn_close.clicked.connect(self.close)

    def load_data(self):
        layout = self.findChild(QVBoxLayout, 'layout_audit_list')
        if not layout: return

        # Clear existing items
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        logs = self.db.get_audit_logs()

        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        item_ui_path = os.path.join(base_path, 'views', 'item_audit.ui')

        if not os.path.exists(item_ui_path): return

        for log in logs:
            try:
                row_widget = uic.loadUi(item_ui_path)

                # Populate Text
                if hasattr(row_widget, 'lbl_action'): row_widget.lbl_action.setText(str(log.get('action', '')))
                if hasattr(row_widget, 'lbl_details'): row_widget.lbl_details.setText(str(log.get('details', '')))
                if hasattr(row_widget, 'lbl_user'): row_widget.lbl_user.setText(str(log.get('user_name', 'System')))
                if hasattr(row_widget, 'lbl_time'): row_widget.lbl_time.setText(str(log.get('timestamp', '')))

                # Icon Logic
                action_text = str(log.get('action', '')).lower()
                icon_color = "#64748B"
                icon_name = "activity.svg"

                if "add" in action_text or "create" in action_text or "stock" in action_text:
                    icon_color = "#059669"
                    icon_name = "plus-circle.svg"
                elif "delete" in action_text or "remove" in action_text:
                    icon_color = "#DC2626"
                    icon_name = "trash-2.svg"
                elif "update" in action_text or "edit" in action_text:
                    icon_color = "#2563EB"
                    icon_name = "edit.svg"
                elif "login" in action_text:
                    icon_color = "#7C3AED"
                    icon_name = "log-in.svg"

                if hasattr(row_widget, 'lbl_icon'):
                    set_icon(row_widget.lbl_icon, icon_name, color=icon_color)
                    row_widget.lbl_icon.setStyleSheet(
                        f"border: 2px solid {icon_color}; border-radius: 20px; background-color: white;"
                    )

                layout.addWidget(row_widget)
            except Exception as e:
                print(f"Error rendering audit row: {e}")

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum,
                                       QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)

