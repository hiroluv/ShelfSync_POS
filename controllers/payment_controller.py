from PyQt6.QtWidgets import QDialog, QButtonGroup
from PyQt6 import uic
import os


class PaymentController(QDialog):
    def __init__(self, parent, total_amount):
        super().__init__(parent)
        self.total_amount = total_amount
        self.payment_details = None

        # Load UI
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Check both paths to be safe
        ui_path = os.path.join(base_path, 'views', 'payment_dialog.ui')
        if not os.path.exists(ui_path):
            ui_path = os.path.join(base_path, 'views', 'ui', 'payment_dialog.ui')

        uic.loadUi(ui_path, self)

        # 1. Setup Data
        self.lbl_total_amount.setText(f"₱{self.total_amount:,.2f}")
        vat = self.total_amount * 0.12  # Example calculation
        self.lbl_vat_breakdown.setText(f"Includes VAT: ₱{vat:,.2f}")

        # 2. Setup Method Buttons Group (Mutually Exclusive)
        self.method_group = QButtonGroup(self)
        self.method_group.addButton(self.btn_cash, 1)
        self.method_group.addButton(self.btn_gcash, 2)
        self.method_group.addButton(self.btn_card, 3)
        self.method_group.buttonClicked.connect(self.on_method_changed)

        # 3. Quick Cash Buttons
        if hasattr(self, 'btn_exact'): self.btn_exact.clicked.connect(self.set_exact)
        if hasattr(self, 'btn_100'): self.btn_100.clicked.connect(lambda: self.add_tender(100))
        if hasattr(self, 'btn_500'): self.btn_500.clicked.connect(lambda: self.add_tender(500))
        if hasattr(self, 'btn_1000'): self.btn_1000.clicked.connect(lambda: self.add_tender(1000))

        # 4. Standard Connections
        self.input_tendered.textChanged.connect(self.calculate_change)
        self.btn_confirm.clicked.connect(self.confirm_payment)
        self.btn_cancel.clicked.connect(self.reject)

        self.input_tendered.setFocus()

    def on_method_changed(self, btn):
        # Toggle Reference Input based on selection
        method = btn.text()
        if method == "Cash":
            self.input_reference.setVisible(False)
        else:
            self.input_reference.setVisible(True)
            self.input_reference.setFocus()
        self.calculate_change(self.input_tendered.text())

    def set_exact(self):
        self.input_tendered.setText(str(self.total_amount))

    def add_tender(self, amount):
        try:
            current = float(self.input_tendered.text() or 0)
        except:
            current = 0.0
        self.input_tendered.setText(str(current + amount))

    def calculate_change(self, text):
        try:
            tendered = float(text)
        except ValueError:
            tendered = 0.0

        change = tendered - self.total_amount

        if change >= 0:
            self.lbl_change_amount.setText(f"₱{change:,.2f}")
            self.lbl_change_amount.setStyleSheet("font-size: 24px; font-weight: 800; color: #15803D;")
            self.btn_confirm.setEnabled(True)
        else:
            self.lbl_change_amount.setText(f"-₱{abs(change):,.2f}")
            self.lbl_change_amount.setStyleSheet("font-size: 24px; font-weight: 800; color: #EF4444;")
            self.btn_confirm.setEnabled(False)

    def confirm_payment(self):
        try:
            tendered = float(self.input_tendered.text())
        except:
            tendered = 0.0

        # Get Checked Button Text
        method = self.method_group.checkedButton().text()
        ref = self.input_reference.text() if method != "Cash" else None

        self.payment_details = {
            'method': method,
            'tendered': tendered,
            'change': tendered - self.total_amount,
            'reference': ref
        }
        self.accept()