from PyQt6.QtWidgets import QSpacerItem, QSizePolicy, QFrame, QLabel, QPushButton
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os
from views.product_card import ProductCard


class ProductGrid_Controller:
    def __init__(self, parent_controller, grid_layout, db):
        self.parent = parent_controller
        self.layout = grid_layout
        self.db = db
        self.all_products = []
        self.current_columns = 4

    def refresh_products(self):
        self.all_products = self.db.get_all_products()
        self.populate_grid(self.all_products)

    def set_columns(self, new_columns):
        if new_columns != self.current_columns:
            self.current_columns = new_columns
            self.populate_grid(self.all_products)

    def populate_grid(self, products):
        self.clear_layout(self.layout)
        row, col = 0, 0
        max_cols = self.current_columns

        for product in products:
            card = ProductCard(product)

            #  1. SETUP & TRANSPARENCy
            card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            card.setStyleSheet("background-color: transparent; border: none;")

            #  2. POPULATE DATA
            # --- NAME ---
            lbl_name = card.findChild(QLabel, 'lbl_name')
            if lbl_name:
                lbl_name.setText(str(product.name))
                lbl_name.setWordWrap(True)

            # --- PRICE ---
            lbl_price = card.findChild(QLabel, 'lbl_price')
            if lbl_price:
                lbl_price.setText(f"₱{product.selling_price:,.2f}")

            # --- IMAGE ---
            lbl_image = card.findChild(QLabel, 'lbl_image')
            # Fallback
            if not lbl_image and hasattr(card, 'lbl_image'):
                lbl_image = card.lbl_image

            if lbl_image:
                if product.image_path and os.path.exists(product.image_path):
                    pixmap = QPixmap(product.image_path)
                    lbl_image.setPixmap(pixmap.scaled(
                        lbl_image.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                else:
                    lbl_image.setText("No Image")
                    lbl_image.setStyleSheet("color: #94A3B8; font-size: 10px;")

            #Click
            card.add_to_cart_clicked.connect(self.parent.handle_add_product)


            #  3. STOCK STATUS
            # Find button only, para dili ma highlight ang card
            btn_card = card.findChild(QPushButton, 'btn_card')
            if btn_card:
                btn_card.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            lbl_stock = card.findChild(QLabel, 'lbl_stock')
            threshold = getattr(product, 'threshold', 10)

            if product.stock == 0:
                # === OUT OF STOCK ===
                if lbl_stock:
                    lbl_stock.setText("Out of Stock")
                    # Style ONLY the label
                    lbl_stock.setStyleSheet(
                        "background-color: #FEE2E2; color: #DC2626; border-radius: 4px; font-weight: 700; font-size: 10px; padding: 2px; border: none;")

            elif product.stock <= threshold:
                # === LOW STOCK ===
                if lbl_stock:
                    lbl_stock.setText(f"{product.stock} left")
                    # Style ONLY the label
                    lbl_stock.setStyleSheet(
                        "background-color: #FEF3C7; color: #D97706; border-radius: 4px; font-weight: 700; font-size: 10px; padding: 2px; border: none;")

            else:
                # === IN STOCK ===
                if lbl_stock:
                    lbl_stock.setText(f"{product.stock} left")
                    # Standard Green Badge
                    lbl_stock.setStyleSheet(
                        "background-color: #ECFEFF; color: #0E7490; padding: 2px; border-radius: 4px; font-weight: 700; font-size: 10px; border: none;")

            self.layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout.addItem(spacer, row + 1, 0, 1, max_cols)

    def filter_products(self, search_text):
        """Filters the currently loaded products."""
        text = search_text.lower().strip()
        filtered = [p for p in self.all_products if text in p.name.lower()]
        self.populate_grid(filtered)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()