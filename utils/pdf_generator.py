from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime


class PDFReportGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=30, leftMargin=30,
            topMargin=30, bottomMargin=30
        )
        self.elements = []
        self.styles = getSampleStyleSheet()

        # Define Custom Styles
        self.styles.add(
            ParagraphStyle(name='HeaderTitle', parent=self.styles['Heading1'], fontSize=18, alignment=1, spaceAfter=10,
                           textColor=colors.HexColor("#2C3E50")))
        self.styles.add(ParagraphStyle(name='SubHeader', parent=self.styles['Normal'], fontSize=10, alignment=1,
                                       textColor=colors.HexColor("#7F8C8D")))

    def _add_header(self, title, start_date=None, end_date=None):
        """Adds the standard company header"""
        self.elements.append(Paragraph(title, self.styles['HeaderTitle']))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_range = f"Period: {start_date} to {end_date}" if start_date else "Report Date: " + datetime.now().strftime(
            "%Y-%m-%d")

        info_text = f"""
        <b>ShelfSync POS System</b><br/>
        {date_range}<br/>
        Generated On: {timestamp}
        """
        self.elements.append(Paragraph(info_text, self.styles['SubHeader']))
        self.elements.append(Spacer(1, 0.25 * inch))

    def _create_table(self, data, col_widths):
        """Creates a striped table with professional styling"""
        t = Table(data, colWidths=col_widths)

        # Base Style
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2980b9")),  # Blue Header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]

        # Zebra Striping
        for i in range(1, len(data)):
            bg = colors.whitesmoke if i % 2 == 0 else colors.white
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

        t.setStyle(TableStyle(style_cmds))
        return t

    def generate_sales_report(self, data, start_date, end_date):
        self._add_header("Sales Performance Report", start_date, end_date)

        # Summary Section
        total_rev = sum(float(x['total_amount']) for x in data)
        summary = f"<b>Total Revenue:</b> P {total_rev:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Transactions:</b> {len(data)}"
        self.elements.append(Paragraph(summary, self.styles['Normal']))
        self.elements.append(Spacer(1, 0.15 * inch))

        # Table Data
        table_data = [['Inv #', 'Date/Time', 'Cashier', 'Items', 'Total']]
        for row in data:
            dt = row['date'].strftime("%Y-%m-%d %H:%M") if hasattr(row['date'], 'strftime') else str(row['date'])
            table_data.append([
                str(row['invoice_id']), dt, row['cashier'], str(row['items_count']),
                f"P {float(row['total_amount']):,.2f}"
            ])

        self.elements.append(self._create_table(table_data, [0.8 * inch, 2 * inch, 2 * inch, 1 * inch, 1.5 * inch]))
        self.doc.build(self.elements)

    def generate_inventory_report(self, data, report_type="Valuation"):
        title = "Inventory Valuation Report" if report_type == "Valuation" else "Low Stock Alert Report"
        self._add_header(title)

        if report_type == "Valuation":
            headers = ['ID', 'Product Name', 'Category', 'Stock', 'Price', 'Total Value']
            col_widths = [0.6 * inch, 2.2 * inch, 1.5 * inch, 0.8 * inch, 1 * inch, 1.2 * inch]
            table_data = [headers]
            for row in data:
                table_data.append([
                    str(row['id']), row['name'], row['category'], str(row['stock']),
                    f"P {float(row['selling_price']):,.2f}", f"P {float(row['total_value']):,.2f}"
                ])
        else:  # Low Stock
            headers = ['ID', 'Product Name', 'Category', 'Current Stock', 'Threshold']
            col_widths = [0.8 * inch, 2.5 * inch, 2 * inch, 1 * inch, 1 * inch]
            table_data = [headers]
            for row in data:
                table_data.append([
                    str(row['id']), row['name'], row['category'],
                    str(row['stock']), str(row['threshold'])
                ])

        self.elements.append(self._create_table(table_data, col_widths))
        self.doc.build(self.elements)

    def generate_audit_report(self, data, start_date, end_date):
        self._add_header("System Audit Logs", start_date, end_date)

        headers = ['Time', 'User', 'Action', 'Details']
        table_data = [headers]
        for row in data:
            dt = row['timestamp'].strftime("%Y-%m-%d %H:%M") if hasattr(row['timestamp'], 'strftime') else str(
                row['timestamp'])
            # Wrap long text in details
            details = Paragraph(row['details'], self.styles['BodyText'])
            table_data.append([dt, row['user_name'], row['action'], details])

        # Adjust widths for audit logs (more space for details)
        self.elements.append(self._create_table(table_data, [1.5 * inch, 1.2 * inch, 1.5 * inch, 3 * inch]))
        self.doc.build(self.elements)