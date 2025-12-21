from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QWidget, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import QPropertyAnimation, QTimer, QPoint


class ToastNotification(QWidget):
    def __init__(self, parent, message, type="success"):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.SubWindow)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        # Colors based on type
        if type == "success":
            bg_color = "#ECFDF5"  # Green-50
            text_color = "#059669"  # Green-600
            border_color = "#10B981"  # Green-500
            icon = "✓"
        elif type in "error":
            bg_color = "#FEF2F2"  # Red-50
            text_color = "#DC2626"  # Red-600
            border_color = "#EF4444"  # Red-500
            icon = "✕"
        else:  # Info
            bg_color = "#F0F9FF"
            text_color = "#DC2626"
            border_color = "#06B6D4"
            icon = "ℹ"

        # Style
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color}; 
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QLabel {{
                color: {text_color};
                font-family: "Segoe UI";
                font-weight: bold;
                font-size: 14px;
                border: none;
                background: transparent;
            }}
        """)

        # Layout
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Icon Label
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {text_color};")
        layout.addWidget(lbl_icon)

        # Message Label
        lbl_msg = QLabel(message)
        layout.addWidget(lbl_msg)

        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setYOffset(5)
        shadow.setColor(QtGui.QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        # Animation Setup
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.timer = QTimer()
        self.timer.timeout.connect(self.fade_out)

    def show_toast(self):
        self.show()
        self.raise_()

        # Position: Bottom Center of Parent
        parent_rect = self.parent().rect()
        self.adjustSize()
        x = (parent_rect.width() - self.width()) // 2
        y = parent_rect.height() - 100  # 100px from bottom
        self.move(x, y)

        # Fade In
        self.setWindowOpacity(0.0)
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.start()

        # Start timer to fade out
        self.timer.start(2500)  # Show for 2.5 seconds

    def fade_out(self):
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self.close)
        self.opacity_anim.start()


# Helper function to easily call it
def show_toast(parent, message, type="success"):
    toast = ToastNotification(parent, message, type)
    toast.show_toast()