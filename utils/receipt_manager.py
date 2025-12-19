from reportlab.lib.pagesizes import A6
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import os
import subprocess
import platform

from datetime import datetime


class ReceiptManager:
    def __init__(self):
        self.width = 80 * mm  # Standard Thermal Printer Width (80mm)
        self.height = 200 * mm  # Total height
        self.file_name = "latest_receipt.pdf"

        # Determine paths for assets relative to this file
        # Assuming receipt_manager.py is in /utils or /controllers and logo is in /assets
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logo_path = os.path.join(self.base_path, 'assets', 'logo.png')

    def generate_receipt(self, transaction_data):
        c = canvas.Canvas(self.file_name, pagesize=(self.width, self.height))

        # --- 1. Header with Logo ---
        y = self.height - 10 * mm

        # Add Logo at the top center
        if os.path.exists(self.logo_path):
            logo_size = 15 * mm  # Adjusted size for 80mm receipt
            c.drawImage(self.logo_path, (self.width - logo_size) / 2, y - 10 * mm,
                        width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')
            y -= 18 * mm  # Push text down further to make room for logo
        else:
            y -= 2 * mm  # Minor spacing if no logo

        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(self.width / 2, y, "ShelfSync")
        y -= 5 * mm
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.width / 2, y, "Davao City, Philippines")
        y -= 4 * mm
        c.drawCentredString(self.width / 2, y, "Tel: (+63) 6767-6767")

        y -= 6 * mm
        c.line(5 * mm, y, self.width - 5 * mm, y)  # Separator Line
        y -= 5 * mm

        # --- 2. Transaction Info ---
        c.setFont("Helvetica", 7)  # Slightly smaller font for info
        c.drawString(5 * mm, y, f"Date: {transaction_data['date'].strftime('%Y-%m-%d %H:%M')}")
        y -= 4 * mm
        c.drawString(5 * mm, y, f"Cashier: {transaction_data['cashier']}")
        y -= 4 * mm
        c.drawString(5 * mm, y, f"Ref #: {transaction_data['sale_id']}")

        y -= 5 * mm
        c.line(5 * mm, y, self.width - 5 * mm, y)
        y -= 5 * mm

        # --- 3. Items Header ---
        c.setFont("Helvetica-Bold", 8)
        c.drawString(5 * mm, y, "Item")
        c.drawString(45 * mm, y, "Qty")
        c.drawRightString(self.width - 5 * mm, y, "Price")
        y -= 5 * mm

        # --- 4. Item List ---
        c.setFont("Helvetica", 8)
        for item in transaction_data['items']:
            # Handle wrapping or truncating long names
            raw_name = item['name']
            name = raw_name[:18] + ".." if len(raw_name) > 18 else raw_name

            c.drawString(5 * mm, y, name)
            c.drawString(46 * mm, y, str(item['qty']))
            total_price = item['qty'] * item['price']
            c.drawRightString(self.width - 5 * mm, y, f"{total_price:,.2f}")
            y -= 4 * mm

        y -= 2 * mm
        c.line(5 * mm, y, self.width - 5 * mm, y)
        y -= 5 * mm

        # --- 5. Totals ---
        c.setFont("Helvetica-Bold", 8)
        c.drawString(30 * mm, y, "Subtotal:")
        c.drawRightString(self.width - 5 * mm, y, f"{transaction_data['subtotal']:,.2f}")
        y -= 4 * mm

        c.drawString(30 * mm, y, "VAT (12%):")
        c.drawRightString(self.width - 5 * mm, y, f"{transaction_data['vat']:,.2f}")
        y -= 6 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(15 * mm, y, "TOTAL:")
        c.drawRightString(self.width - 5 * mm, y, f"{transaction_data['total']:,.2f}")
        y -= 8 * mm

        # --- 6. Payment Details ---
        c.setFont("Helvetica", 7)
        pay_info = transaction_data['payment']
        c.drawString(5 * mm, y, f"Paid via {pay_info['method']}")
        y -= 3.5 * mm
        c.drawString(5 * mm, y, f"Tendered: {pay_info['tendered']:,.2f}")
        y -= 3.5 * mm
        c.drawString(5 * mm, y, f"Change: {pay_info['change']:,.2f}")

        # --- 7. Footer ---
        y -= 12 * mm
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(self.width / 2, y, "Thank you for shopping!")

        c.save()
        self.open_pdf()

    def open_pdf(self):
        """Automatically opens the PDF to simulate printing"""
        current_os = platform.system()
        try:
            if current_os == "Windows":
                os.startfile(self.file_name)
            elif current_os == "Darwin":  # macOS
                subprocess.call(["open", self.file_name])
            else:  # Linux
                subprocess.call(["xdg-open", self.file_name])
        except Exception as e:
            print(f"Error opening receipt: {e}")