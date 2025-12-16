from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime


class PDFReportGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=40, leftMargin=40,
            topMargin=40, bottomMargin=40
        )
        self.elements = []
        self.styles = getSampleStyleSheet()

        # --- Custom Professional Styles ---
        # Main Title (Large, Dark Blue)
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1E3A8A"),  # Dark Royal Blue
            spaceAfter=5
        ))

        # Section Headers (Medium, Slate Grey)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor("#334155"),  # Slate 700
            spaceBefore=20,
            spaceAfter=10,
        ))

        # [FIX] Renamed from 'BodyText' to 'ReportBody' to avoid conflict
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#475569"),  # Slate 600
            leading=14
        ))

        # KPI/Card Label (Small, Uppercase)
        self.styles.add(ParagraphStyle(
            name='CardLabel',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor("#64748B"),
            alignment=1  # Center
        ))

        # KPI/Card Value (Large, Bold)
        self.styles.add(ParagraphStyle(
            name='CardValue',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor("#0F172A"),
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        ))

    def _add_header_info(self, title, start_date, end_date):
        """Creates a professional 2-column header block"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Left Side: Report Title & Company Name
        title_para = Paragraph(title, self.styles['ReportTitle'])
        # [FIX] Updated style reference
        company_para = Paragraph("<b>ShelfSync POS System</b>", self.styles['ReportBody'])

        # Right Side: Meta Data (Date Range, Generated Time)
        period_text = f"<b>Period:</b> {start_date} to {end_date}"
        gen_text = f"<b>Generated:</b> {timestamp}"
        # [FIX] Updated style reference
        meta_para = Paragraph(f"{period_text}<br/>{gen_text}", self.styles['ReportBody'])

        # Layout Table for Header
        header_data = [[[title_para, company_para], meta_para]]
        t = Table(header_data, colWidths=[4.5 * inch, 2.5 * inch])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        self.elements.append(t)
        self.elements.append(Spacer(1, 0.3 * inch))

    def _create_kpi_cards(self, kpi_data):
        """
        Creates a row of 'cards' for high-level metrics.
        kpi_data list of tuples: [("Label", "Value"), ("Label", "Value")]
        """
        card_cells = []
        for label, value in kpi_data:
            # Each card is a mini-table with background color
            l_para = Paragraph(label.upper(), self.styles['CardLabel'])
            v_para = Paragraph(value, self.styles['CardValue'])

            # Inner table for the card content
            card_content = [[l_para], [v_para]]
            inner_t = Table(card_content, colWidths=[1.5 * inch])
            inner_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),  # Light Grey Background
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),  # Border
                ('ROUNDEDCORNERS', [4, 4, 4, 4]),
            ]))
            card_cells.append(inner_t)

        # Container table to hold the cards horizontally
        container = Table([card_cells], colWidths=[1.7 * inch] * len(card_cells))
        container.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        self.elements.append(container)
        self.elements.append(Spacer(1, 0.2 * inch))

    def _create_data_table(self, data, col_widths, col_alignments=None):
        if not data: return Spacer(1, 1)

        t = Table(data, colWidths=col_widths, repeatRows=1)

        # Base Style
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),  # Dark Blue Header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),  # Header Align Left
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),

            # Row Styles
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#334155")),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),  # Subtle Grid
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Apply Column Alignments if provided (e.g., Numbers to the RIGHT)
        if col_alignments:
            for i, align in enumerate(col_alignments):
                style_cmds.append(('ALIGN', (i, 1), (i, -1), align))

        # Zebra Striping
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#F8FAFC")))  # Very Light Grey
            else:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), colors.white))

        t.setStyle(TableStyle(style_cmds))
        return t

    # --- SECTION BUILDERS ---

    def add_sales_section(self, data, start_date, end_date):
        if self.elements: self.elements.append(PageBreak())

        # 1. Header
        self._add_header_info("Sales Report", start_date, end_date)

        if not data:
            # [FIX] Updated style reference
            self.elements.append(Paragraph("No sales data found for this period.", self.styles['ReportBody']))
            return

        # 2. KPI Cards
        total_rev = sum(float(x['total_amount']) for x in data)
        txn_count = len(data)
        avg_ticket = total_rev / txn_count if txn_count > 0 else 0

        self._create_kpi_cards([
            ("Total Revenue", f"P {total_rev:,.2f}"),
            ("Transactions", str(txn_count)),
            ("Avg Ticket", f"P {avg_ticket:,.2f}")
        ])

        # 3. Data Table
        headers = ['Inv #', 'Date/Time', 'Cashier', 'Items', 'Total']
        table_data = [headers]
        for row in data:
            dt = row['date'].strftime("%Y-%m-%d %H:%M") if hasattr(row['date'], 'strftime') else str(row['date'])
            table_data.append([
                str(row['invoice_id']),
                dt,
                row['cashier'],
                str(row['items_count']),
                f"P {float(row['total_amount']):,.2f}"
            ])

        # Alignments: Left, Left, Left, Center, Right
        self.elements.append(self._create_data_table(
            table_data,
            [1 * inch, 2 * inch, 2 * inch, 1 * inch, 1.5 * inch],
            ['LEFT', 'LEFT', 'LEFT', 'CENTER', 'RIGHT']
        ))

    def add_inventory_section(self, data, report_type="Valuation"):
        if self.elements: self.elements.append(PageBreak())

        title = "Inventory Valuation" if report_type == "Valuation" else "Low Stock Alerts"
        today = datetime.now().strftime("%Y-%m-%d")
        self._add_header_info(title, today, today)

        if not data:
            # [FIX] Updated style reference
            self.elements.append(Paragraph("No records found.", self.styles['ReportBody']))
            return

        # KPI Cards for Inventory
        if report_type == "Valuation":
            total_value = sum(float(x['total_value']) for x in data)
            total_items = sum(int(x['stock']) for x in data)
            self._create_kpi_cards([
                ("Total Asset Value", f"P {total_value:,.2f}"),
                ("Total Items in Stock", str(total_items))
            ])

            headers = ['ID', 'Product Name', 'Category', 'Stock', 'Price', 'Value']
            col_widths = [0.8 * inch, 2.2 * inch, 1.5 * inch, 0.8 * inch, 1 * inch, 1.2 * inch]
            alignments = ['LEFT', 'LEFT', 'LEFT', 'CENTER', 'RIGHT', 'RIGHT']

            table_data = [headers]
            for row in data:
                table_data.append([
                    str(row['id']), row['name'], row['category'], str(row['stock']),
                    f"P {float(row['selling_price']):,.2f}", f"P {float(row['total_value']):,.2f}"
                ])

        else:  # Low Stock
            low_stock_count = len(data)
            self._create_kpi_cards([
                ("Items Low on Stock", str(low_stock_count)),
                ("Action Required", "Restock ASAP")
            ])

            headers = ['ID', 'Product Name', 'Category', 'Stock', 'Threshold']
            col_widths = [0.8 * inch, 2.5 * inch, 2 * inch, 1 * inch, 1 * inch]
            alignments = ['LEFT', 'LEFT', 'LEFT', 'CENTER', 'CENTER']

            table_data = [headers]
            for row in data:
                table_data.append([
                    str(row['id']), row['name'], row['category'],
                    str(row['stock']), str(row['threshold'])
                ])

        self.elements.append(self._create_data_table(table_data, col_widths, alignments))

    def add_audit_section(self, data, start_date, end_date):
        if self.elements: self.elements.append(PageBreak())
        self._add_header_info("System Audit Logs", start_date, end_date)

        if not data:
            # [FIX] Updated style reference
            self.elements.append(Paragraph("No audit logs found.", self.styles['ReportBody']))
            return

        headers = ['Time', 'User', 'Action', 'Details']
        table_data = [headers]
        for row in data:
            dt = row['timestamp'].strftime("%Y-%m-%d %H:%M") if hasattr(row['timestamp'], 'strftime') else str(
                row['timestamp'])
            # Wrap detail text
            # [FIX] Updated style reference
            details = Paragraph(row['details'], self.styles['ReportBody'])
            table_data.append([dt, row['user_name'], row['action'], details])

        self.elements.append(self._create_data_table(
            table_data,
            [1.5 * inch, 1.2 * inch, 1.5 * inch, 3.2 * inch],
            ['LEFT', 'LEFT', 'LEFT', 'LEFT']
        ))

    def build(self):
        try:
            self.doc.build(self.elements)
            return True
        except Exception as e:
            print(f"PDF Build Error: {e}")
            return False