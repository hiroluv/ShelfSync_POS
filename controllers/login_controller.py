from PyQt6 import QtWidgets, uic, QtCore, QtGui
from PyQt6.QtWidgets import QMainWindow, QLineEdit, QMessageBox, QApplication
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import pyqtSignal, QTimer
from utils.ui_helper import add_drop_shadow, center_window
import os


class LoginController(QMainWindow):
    login_success = pyqtSignal(object)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(base_path, 'views', 'login_window.ui')
        uic.loadUi(ui_path, self)

        # Start invisible for fade-in
        self.setWindowOpacity(0.0)

        self.setup_ui()
        self.setup_connections()

        # Start with default role
        self.set_role("Cashier")

        # Center and Fade In
        center_window(self)
        self.fade_in()

    def setup_ui(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_path, 'assets', 'logo.png')

        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(250, 250, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                          QtCore.Qt.TransformationMode.SmoothTransformation)
            self.lbl_logo_icon.setPixmap(scaled_pixmap)

        add_drop_shadow(self.btn_login, blur=25, y_offset=8, color_alpha=50, hex_color="#06B6D4")
        add_drop_shadow(self.frame_role_toggle, blur=10, y_offset=2, color_alpha=10, hex_color="#000000")

        self.btn_role_cashier.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)
        self.btn_role_cashier.installEventFilter(self)
        self.btn_role_manager.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)
        self.btn_role_manager.installEventFilter(self)

    def setup_connections(self):
        self.btn_role_cashier.clicked.connect(lambda: self.set_role("Cashier"))
        self.btn_role_manager.clicked.connect(lambda: self.set_role("Manager"))
        self.btn_toggle_pass.clicked.connect(self.toggle_password_visibility)
        self.btn_forgot.clicked.connect(self.handle_forgot_password)

        self.btn_login.clicked.connect(self.handle_login)
        self.input_pass.returnPressed.connect(self.handle_login)
        self.input_user.returnPressed.connect(lambda: self.input_pass.setFocus())

    def fade_in(self):
        self.anim_in = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim_in.setDuration(500)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.start()

    def fade_out(self, user):
        self.anim_out = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim_out.setDuration(400)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.finished.connect(lambda: self.login_success.emit(user))
        self.anim_out.start()

    def set_role(self, role):
        self.current_role = role
        if role == "Cashier":
            self.btn_role_cashier.setChecked(True)
            self.btn_role_manager.setChecked(False)
            add_drop_shadow(self.btn_role_cashier, blur=15, y_offset=4, color_alpha=40, hex_color="#000000")
            self.btn_role_manager.setGraphicsEffect(None)
        else:
            self.btn_role_cashier.setChecked(False)
            self.btn_role_manager.setChecked(True)
            add_drop_shadow(self.btn_role_manager, blur=15, y_offset=4, color_alpha=40, hex_color="#000000")
            self.btn_role_cashier.setGraphicsEffect(None)
        self.lbl_error.setText("")
        self.input_user.setFocus()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.Type.Enter:
            if source in [self.btn_role_cashier, self.btn_role_manager] and not source.isChecked():
                add_drop_shadow(source, blur=10, y_offset=2, color_alpha=20, hex_color="#000000")
        elif event.type() == QtCore.QEvent.Type.Leave:
            if source in [self.btn_role_cashier, self.btn_role_manager] and not source.isChecked():
                source.setGraphicsEffect(None)
        return super().eventFilter(source, event)

    def toggle_password_visibility(self):
        if self.input_pass.echoMode() == QLineEdit.EchoMode.Password:
            self.input_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_pass.setText("🙈")
        else:
            self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_pass.setText("👁️")

    def handle_forgot_password(self):
        QMessageBox.information(self, "Reset Password",
                                "Please contact your System Administrator to reset your password.")

    def handle_login(self):
        username = self.input_user.text().strip()
        password = self.input_pass.text().strip()

        if not username or not password:
            self.lbl_error.setText("Please fill in all fields.")
            self.shake_window()
            return

        original_text = self.btn_login.text()
        self.btn_login.setText("Signing in...")
        self.btn_login.setEnabled(False)
        self.input_user.setEnabled(False)
        self.input_pass.setEnabled(False)
        QApplication.processEvents()

        QTimer.singleShot(500, lambda: self.process_auth(username, password, original_text))

    def process_auth(self, username, password, original_btn_text):
        user = self.db.authenticate_user(username, password)

        if user:
            if user.role.lower() == self.current_role.lower():
                self.fade_out(user)
            else:
                self.lbl_error.setText(f"This account is not authorized as {self.current_role}")
                self.shake_window()
                self.reset_loading_state(original_btn_text)
        else:
            self.lbl_error.setText("Invalid username or password.")
            self.shake_window()
            self.reset_loading_state(original_btn_text)

    def reset_loading_state(self, original_text):
        self.btn_login.setText(original_text)
        self.btn_login.setEnabled(True)
        self.input_user.setEnabled(True)
        self.input_pass.setEnabled(True)
        self.input_pass.clear()
        self.input_pass.setFocus()

    def shake_window(self):
        anim = QtCore.QPropertyAnimation(self.frame_login, b"pos")
        anim.setDuration(100)
        anim.setLoopCount(2)
        pos = self.frame_login.pos()
        x = pos.x()
        y = pos.y()
        anim.setKeyValueAt(0, QtCore.QPoint(x, y))
        anim.setKeyValueAt(0.25, QtCore.QPoint(x + 5, y))
        anim.setKeyValueAt(0.75, QtCore.QPoint(x - 5, y))
        anim.setKeyValueAt(1, QtCore.QPoint(x, y))
        anim.start()