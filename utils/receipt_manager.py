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
        self.height = 200 * mm  # Dynamic height in a real app, fixed for now
        self.file_name = "latest_receipt.pdf"

    def generate_receipt(self, transaction_data):
        #Explanation of the process of how i generate the receipt
        """
        transaction_data = {
            'sale_id': 123,
            'cashier': 'Name',
            'items': [{'name': 'Soap', 'qty': 2, 'price': 50.00}],
            'subtotal': 100.00,
            'vat': 12.00,
            'total': 112.00,
            'payment': {'method': 'Cash', 'tendered': 120.00, 'change': 8.00},
            'date': datetime.now()
        }
        """
        c = canvas.Canvas(self.file_name, pagesize=(self.width, self.height))

        # 1. Header
        y = self.height - 10 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(self.width / 2, y, "ShelfSync POS")
        y -= 5 * mm
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.width / 2, y, "Davao City, Philippines")
        y -= 5 * mm
        c.drawCentredString(self.width / 2, y, "Tel: (082) 555-1234")

        y -= 10 * mm
        c.line(5 * mm, y, self.width - 5 * mm, y)  # Separator Line
        y -= 5 * mm

        # 2. Transaction Info
        c.setFont("Helvetica", 8)
        c.drawString(5 * mm, y, f"Date: {transaction_data['date'].strftime('%Y-%m-%d %H:%M')}")
        y -= 4 * mm
        c.drawString(5 * mm, y, f"Cashier: {transaction_data['cashier']}")
        y -= 4 * mm
        c.drawString(5 * mm, y, f"Ref #: {transaction_data['sale_id']}")

        y -= 6 * mm
        c.line(5 * mm, y, self.width - 5 * mm, y)
        y -= 5 * mm

        # 3. Items Header
        c.setFont("Helvetica-Bold", 8)
        c.drawString(5 * mm, y, "Item")
        c.drawString(45 * mm, y, "Qty")
        c.drawRightString(self.width - 5 * mm, y, "Price")
        y -= 5 * mm

        # 4. Item List
        c.setFont("Helvetica", 8)
        for item in transaction_data['items']:
            name = item['name'][:15] + "..." if len(item['name']) > 15 else item['name']
            c.drawString(5 * mm, y, name)
            c.drawString(48 * mm, y, str(item['qty']))
            total_price = item['qty'] * item['price']
            c.drawRightString(self.width - 5 * mm, y, f"{total_price:,.2f}")
            y -= 4 * mm

        y -= 2 * mm
        c.line(5 * mm, y, self.width - 5 * mm, y)
        y -= 5 * mm

        # 5. Totals
        c.setFont("Helvetica-Bold", 9)

        c.drawString(25 * mm, y, "Subtotal:")
        c.drawRightString(self.width - 5 * mm, y, f"{transaction_data['subtotal']:,.2f}")
        y -= 4 * mm

        c.drawString(25 * mm, y, "VAT (12%):")
        c.drawRightString(self.width - 5 * mm, y, f"{transaction_data['vat']:,.2f}")
        y -= 6 * mm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(15 * mm, y, "TOTAL:")
        c.drawRightString(self.width - 5 * mm, y, f"{transaction_data['total']:,.2f}")
        y -= 8 * mm

        # 6. Payment Details
        c.setFont("Helvetica", 8)
        pay_info = transaction_data['payment']
        c.drawString(5 * mm, y, f"Paid via {pay_info['method']}")
        y -= 4 * mm
        c.drawString(5 * mm, y, f"Tendered: {pay_info['tendered']:,.2f}")
        y -= 4 * mm
        c.drawString(5 * mm, y, f"Change: {pay_info['change']:,.2f}")

        # 7. Footer
        y -= 15 * mm
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