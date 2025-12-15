from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget, QLabel, QFrame, QPushButton
from PyQt6.QtCore import QObject, QEvent, QPropertyAnimation, QEasingCurve, QPoint, Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QBrush, QIcon, QGuiApplication, QPixmap
import os


class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
        if parent: self.resize(parent.size())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QBrush(QColor(15, 23, 42, 120)))

    def resizeEvent(self, event):
        if self.parent(): self.resize(self.parent().size())


def add_drop_shadow(widget, blur=20, y_offset=5, color_alpha=30, hex_color="#000000"):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setYOffset(y_offset)
    c = QColor(hex_color)
    c.setAlpha(color_alpha)
    shadow.setColor(c)
    widget.setGraphicsEffect(shadow)


# --- UPDATED SET_ICON WITH COLOR SUPPORT ---
def set_icon(widget, icon_name, size=20, color=None):
    """
    Sets an icon on a QLabel or QPushButton.
    Supports recoloring (tinting) the icon.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_path, 'assets', 'icons', icon_name)

    if not os.path.exists(icon_path):
        print(f"Warning: Icon not found at {icon_path}")
        return

    # 1. Load the original Pixmap
    pixmap = QPixmap(icon_path)

    # 2. Apply Color Tint (if color is provided)
    if color:
        # Create a blank transparent pixmap of the same size
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)

        # Initialize Painter
        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw the original icon
        painter.drawPixmap(0, 0, pixmap)

        # Change composition mode to keep alpha but change color
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), QColor(color))
        painter.end()

        # Replace original with colored version
        pixmap = colored_pixmap

    # 3. Scale it smoothly to the requested size
    scaled_pixmap = pixmap.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )

    # 4. Apply to Widget
    if isinstance(widget, QLabel):
        # QLabel Logic
        widget.setText("")
        widget.setPixmap(scaled_pixmap)
        # Optional: Lock size if you want strictly that size
        # widget.setFixedSize(size, size)
        widget.setScaledContents(False)  # We already scaled it manually for better quality
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

    elif isinstance(widget, QPushButton):
        # QPushButton Logic
        widget.setIcon(QIcon(scaled_pixmap))
        widget.setIconSize(QSize(size, size))


def center_window(window):
    screen = QGuiApplication.primaryScreen()
    if not screen: return
    screen_geometry = screen.availableGeometry()
    window_geometry = window.frameGeometry()
    window_geometry.moveCenter(screen_geometry.center())
    window.move(window_geometry.topLeft())


# --- IMPROVED HOVER EFFECT ---

class HoverShadowEffect(QObject):
    def __init__(self, widget: QWidget, move_dy=-5):
        super().__init__(widget)
        self.widget = widget
        self.move_dy = move_dy

        # 1. Setup Shadow
        self.shadow = self.widget.graphicsEffect()
        if not isinstance(self.shadow, QGraphicsDropShadowEffect):
            self.shadow = QGraphicsDropShadowEffect(self.widget)
            self.widget.setGraphicsEffect(self.shadow)

        self.normal_blur = 20
        self.normal_offset = 5
        self.normal_color = QColor(0, 0, 0, 30)

        self.hover_blur = 35
        self.hover_offset = 8
        self.hover_color = QColor(0, 0, 0, 100)

        self.shadow.setBlurRadius(self.normal_blur)
        self.shadow.setYOffset(self.normal_offset)
        self.shadow.setColor(self.normal_color)

        # 2. Setup Animation
        self.anim_pos = QPropertyAnimation(self.widget, b"pos")
        self.anim_pos.setDuration(150)
        self.anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 3. Install Event Filter
        self.widget.installEventFilter(self)
        self.original_pos = None

    def eventFilter(self, obj, event):
        if obj == self.widget:
            if event.type() == QEvent.Type.Enter:
                self.on_enter()
            elif event.type() == QEvent.Type.Leave:
                self.on_leave()
            elif event.type() == QEvent.Type.Move:
                # CRITICAL FIX: Update original_pos when layout moves the widget (e.g. resize)
                # But ignore moves caused by our own animation
                if self.anim_pos.state() == QPropertyAnimation.State.Stopped:
                    self.original_pos = self.widget.pos()
        return super().eventFilter(obj, event)

    def on_enter(self):
        # Shadow
        self.shadow.setColor(self.hover_color)
        self.shadow.setBlurRadius(self.hover_blur)
        self.shadow.setYOffset(self.hover_offset)

        # Update position reference if missing
        if self.original_pos is None:
            self.original_pos = self.widget.pos()

        # Float Up (from current pos to target)
        self.anim_pos.setStartValue(self.widget.pos())
        self.anim_pos.setEndValue(QPoint(self.original_pos.x(), self.original_pos.y() + self.move_dy))
        self.anim_pos.start()

    def on_leave(self):
        # Restore Shadow
        self.shadow.setColor(self.normal_color)
        self.shadow.setBlurRadius(self.normal_blur)
        self.shadow.setYOffset(self.normal_offset)

        # Return to original position
        if self.original_pos:
            self.anim_pos.setStartValue(self.widget.pos())
            self.anim_pos.setEndValue(self.original_pos)
            self.anim_pos.start()


def apply_hover_effect(widget):
    if widget:
        # Prevent double application
        if hasattr(widget, '_hover_effect'):
            return
        effect = HoverShadowEffect(widget)
        widget._hover_effect = effect