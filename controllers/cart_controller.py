from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSizePolicy,
                             QFrame, QAbstractScrollArea, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from PyQt6 import uic
import os
from datetime import datetime  # <--- NEW IMPORT

from utils.toast_notification import show_toast
from controllers.payment_controller import PaymentController
from utils.receipt_manager import ReceiptManager  # <--- NEW IMPORT


class Cart_Controller:
    def __init__(self, parent_controller, scroll_area, db):
        self.parent = parent_controller
        self.scroll_area = scroll_area
        self.db = db
        self.cart_data = {}

        # ui edits
        self.scroll_area.setVisible(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow)

        # Container
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background-color: transparent;")
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(8)
        self.scroll_area.setWidget(self.container_widget)
        self.scroll_area.setWidgetResizable(True)
        # Initial Button State
        self.update_checkout_button_state()

    def add_item(self, product_id, all_products):
        product = next((p for p in all_products if p.id == product_id), None)
        if not product: return

        current_qty = self.cart_data.get(product_id, 0)
        if current_qty + 1 > product.stock:
            show_toast(self.parent, "Not enough stock!", type="warning")
            return

        self.cart_data[product_id] = current_qty + 1
        self.render_cart(all_products)

    def update_quantity(self, product_id, change, all_products):
        if product_id not in self.cart_data: return
        product = next((p for p in all_products if p.id == product_id), None)
        new_qty = self.cart_data[product_id] + change

        if new_qty <= 0:
            del self.cart_data[product_id]
        elif product and new_qty > product.stock:
            show_toast(self.parent, f"Max stock is {product.stock}", type="warning")
            return

        if product_id in self.cart_data:
            self.cart_data[product_id] = new_qty
        self.render_cart(all_products)  # refresh cart every add

    def render_cart(self, all_products):
        self.clear_layout(self.container_layout)
        subtotal = 0.0
        total_items = 0
        is_empty = len(self.cart_data) == 0

        # Update Button State
        self.update_checkout_button_state()
        # empty state
        if hasattr(self.parent, 'lbl_empty_title'):
            self.parent.lbl_empty_title.setVisible(False)

        if is_empty:
            lbl_empty = QLabel("Cart is Empty")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty.setStyleSheet("color: #94A3B8; font-size: 14px; margin-top: 20px;")
            self.container_layout.addWidget(lbl_empty)
            self._update_totals(0, 0, 0, 0)
            return

        # Render Rows
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Added fallback check for robustness
        row_ui_path = os.path.join(base_path, 'views', 'item_cart_row.ui')
        if not os.path.exists(row_ui_path):
            row_ui_path = os.path.join(base_path, 'views', 'ui', 'item_cart_row.ui')

        for pid, qty in self.cart_data.items():
            product = next((p for p in all_products if p.id == pid), None)
            if not product: continue

            total_items += qty
            row_price = product.selling_price * qty
            subtotal += row_price

            row_widget = QWidget()
            try:
                uic.loadUi(row_ui_path, row_widget)
                row_widget.setMinimumHeight(70)
                row_widget.setMinimumWidth(0)

                if hasattr(row_widget, 'lbl_product_name'): row_widget.lbl_product_name.setText(product.name)
                if hasattr(row_widget, 'lbl_price'): row_widget.lbl_price.setText(f"₱{row_price:,.2f}")
                if hasattr(row_widget, 'lbl_qty'): row_widget.lbl_qty.setText(str(qty))

                if hasattr(row_widget, 'btn_plus'):
                    row_widget.btn_plus.clicked.connect(lambda _, p=pid: self.update_quantity(p, 1, all_products))
                if hasattr(row_widget, 'btn_minus'):
                    row_widget.btn_minus.clicked.connect(lambda _, p=pid: self.update_quantity(p, -1, all_products))
                if hasattr(row_widget, 'btn_remove'):
                    row_widget.btn_remove.clicked.connect(lambda _, p=pid: self.update_quantity(p, -999, all_products))

                self.container_layout.addWidget(row_widget)

            except Exception as e:
                print(f"Error loading row: {e}")

        self.container_layout.addStretch()

        vat = subtotal * 0.12
        grand_total = subtotal + vat
        self._update_totals(subtotal, vat, grand_total, total_items)

    def update_checkout_button_state(self):
        if not hasattr(self.parent, 'btn_checkout'): return

        btn = self.parent.btn_checkout
        is_empty = len(self.cart_data) == 0

        if is_empty:
            btn.setEnabled(False)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    color: #94A3B8;
                    border-radius: 12px;
                    font-weight: 800;
                    font-size: 15px;
                    border: 1px solid #E2E8F0;
                }
            """)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setOffset(0, 8)
            color = QColor("#06B6D4")
            color.setAlpha(100)
            shadow.setColor(color)
            btn.setGraphicsEffect(shadow)
        else:
            btn.setEnabled(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0891B2;
                    color: white;
                    border-radius: 12px;
                    font-weight: 800;
                    font-size: 15px;
                    border: none;
                }
                QPushButton:hover { background-color: #0E7490; }
                QPushButton:pressed { background-color: #155E75; }
            """)
            btn.setGraphicsEffect(None)

    def _update_totals(self, sub, vat, total, count):
        if hasattr(self.parent, 'lbl_val_subtotal'): self.parent.lbl_val_subtotal.setText(f"₱{sub:,.2f}")
        if hasattr(self.parent, 'lbl_val_vat'): self.parent.lbl_val_vat.setText(f"₱{vat:,.2f}")
        if hasattr(self.parent, 'lbl_val_total'): self.parent.lbl_val_total.setText(f"₱{total:,.2f}")
        if hasattr(self.parent, 'lbl_cart_count'): self.parent.lbl_cart_count.setText(f"{count} Items")

    def process_checkout(self, all_products, user_name):
        if not self.cart_data: return False

        #Calculate Totals & Prep Receipt Data
        subtotal = 0.0
        items_list = [] #collect for receipt

        for pid, qty in self.cart_data.items():
            product = next((p for p in all_products if p.id == pid), None)
            if product:
                price = product.selling_price
                subtotal += price * qty
                items_list.append({
                    'name': product.name,
                    'qty': qty,
                    'price': price
                })

        vat = subtotal * 0.12
        grand_total = subtotal + vat

        #open paymen dial
        try:
            dialog = PaymentController(self.parent, grand_total)
            if dialog.exec():
                # when cashier confirms the pay
                payment_info = dialog.payment_details

                # save payments to DB
                success = self.db.process_transaction(self.cart_data, grand_total, user_name, payment_info)

                if success:
                    show_toast(self.parent, "Transaction Successful!", type="success")

                    #this will pass data to generate receipt
                    try:
                        receipt_mgr = ReceiptManager()
                        receipt_data = {
                            'sale_id': 'NEW',  # Ideally this comes from DB return
                            'cashier': user_name,
                            'items': items_list,
                            'subtotal': subtotal,
                            'vat': vat,
                            'total': grand_total,
                            'payment': payment_info,
                            'date': datetime.now()
                        }
                        receipt_mgr.generate_receipt(receipt_data)
                    except Exception as e:
                        print(f"Receipt Error: {e}")
                        show_toast(self.parent, "Receipt Printing Failed", type="warning")

                    # 6. Clear Cart
                    self.cart_data = {}
                    self.render_cart(all_products)
                    return True
                else:
                    show_toast(self.parent, "Transaction Failed.", type="error")
                    return False
        except Exception as e:
            print(f"Payment Error: {e}")
            show_toast(self.parent, "Error processing payment", type="error")
            return False

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())