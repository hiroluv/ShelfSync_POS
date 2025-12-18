from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.widgets.markers import makeMarker


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
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1E3A8A"),  # Dark Royal Blue
            spaceAfter=5
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor("#334155"),  # Slate 700
            spaceBefore=20,
            spaceAfter=10,
        ))

        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#475569"),  # Slate 600
            leading=14
        ))

        self.styles.add(ParagraphStyle(
            name='CardLabel',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor("#64748B"),
            alignment=1
        ))

        self.styles.add(ParagraphStyle(
            name='CardValue',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor("#0F172A"),
            alignment=1,
            fontName='Helvetica-Bold'
        ))

    def _header_footer(self, canvas, doc):
        """Draws the Header and Footer on every page."""
        canvas.saveState()

        # --- HEADER ---
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColor(colors.HexColor("#1E3A8A"))
        canvas.drawString(40, A4[1] - 35, "ShelfSync POS System")

        # Divider Line
        canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
        canvas.setLineWidth(1)
        canvas.line(40, A4[1] - 45, A4[0] - 40, A4[1] - 45)

        # --- FOOTER ---
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#64748B"))

        # Left: Generation Time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        canvas.drawString(40, 30, f"Generated: {timestamp}")

        # Right: Page Number
        page_num = canvas.getPageNumber()
        text = "Page %s" % page_num
        canvas.drawRightString(A4[0] - 40, 30, text)

        canvas.restoreState()

    def _add_report_metadata(self, title, start_date, end_date):
        title_para = Paragraph(title, self.styles['ReportTitle'])
        period_text = f"<b>Reporting Period:</b> {start_date} to {end_date}"
        meta_para = Paragraph(period_text, self.styles['ReportBody'])

        self.elements.append(title_para)
        self.elements.append(meta_para)
        self.elements.append(Spacer(1, 0.3 * inch))

    def _create_kpi_cards(self, kpi_data):
        card_cells = []
        for label, value in kpi_data:
            l_para = Paragraph(label.upper(), self.styles['CardLabel'])
            v_para = Paragraph(value, self.styles['CardValue'])
            card_content = [[l_para], [v_para]]
            inner_t = Table(card_content, colWidths=[1.5 * inch])
            inner_t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ('ROUNDEDCORNERS', [4, 4, 4, 4]),
            ]))
            card_cells.append(inner_t)

        container = Table([card_cells], colWidths=[1.7 * inch] * len(card_cells))
        container.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        self.elements.append(container)
        self.elements.append(Spacer(1, 0.2 * inch))

    def _create_line_chart(self, data, title="Sales Trend"):
        if not data: return Spacer(1, 1)

        drawing = Drawing(400, 200)

        lc = HorizontalLineChart()
        lc.x = 50
        lc.y = 50
        lc.height = 125
        lc.width = 300

        # Data must be a list of lists [[val1, val2...]]
        lc.data = [[x[1] for x in data]]

        # Axis Config
        lc.categoryAxis.categoryNames = [x[0] for x in data]
        lc.categoryAxis.labels.boxAnchor = 'n'
        lc.categoryAxis.labels.dy = -10
        lc.categoryAxis.labels.fontName = 'Helvetica'

        lc.valueAxis.valueMin = 0
        lc.valueAxis.gridStrokeColor = colors.HexColor("#E2E8F0")
        lc.valueAxis.gridStrokeWidth = 0.5
        lc.valueAxis.visibleGrid = 1

        # Line Style
        lc.lines[0].strokeColor = colors.HexColor("#1E3A8A")
        lc.lines[0].strokeWidth = 2

        # --- FIX: Use makeMarker instead of tuple ---
        lc.lines[0].symbol = makeMarker('FilledCircle')
        lc.lines[0].symbol.size = 4
        lc.lines[0].symbol.fillColor = colors.HexColor("#0891B2")
        lc.lines[0].symbol.strokeColor = colors.white

        drawing.add(lc)

        self.elements.append(Paragraph(f"<b>{title}</b>", self.styles['ReportBody']))
        self.elements.append(drawing)
        self.elements.append(Spacer(1, 0.2 * inch))

    def _create_horizontal_bar_chart(self, data, title="Inventory Value by Category"):
        if not data: return Spacer(1, 1)

        # Sort descending
        sorted_data = sorted(data, key=lambda x: x[1])
        names = [x[0] for x in sorted_data]
        values = [x[1] for x in sorted_data]

        chart_height = 50 + (len(names) * 20)
        drawing = Drawing(400, chart_height)

        bc = HorizontalBarChart()
        bc.x = 80
        bc.y = 20
        bc.height = chart_height - 30
        bc.width = 300
        bc.data = [values]
        bc.strokeColor = colors.white
        bc.valueAxis.valueMin = 0
        bc.categoryAxis.categoryNames = names
        bc.categoryAxis.labels.boxAnchor = 'e'
        bc.categoryAxis.labels.dx = -5
        bc.categoryAxis.labels.fontName = 'Helvetica'
        bc.bars[0].fillColor = colors.HexColor("#0891B2")

        drawing.add(bc)

        self.elements.append(Paragraph(f"<b>{title}</b>", self.styles['ReportBody']))
        self.elements.append(drawing)
        self.elements.append(Spacer(1, 0.2 * inch))

    def _create_data_table(self, data, col_widths, col_alignments=None):
        if not data: return Spacer(1, 1)

        t = Table(data, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#334155")),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        if col_alignments:
            for i, align in enumerate(col_alignments):
                style_cmds.append(('ALIGN', (i, 1), (i, -1), align))

        for i in range(1, len(data)):
            bg = colors.HexColor("#F8FAFC") if i % 2 == 0 else colors.white
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

        t.setStyle(TableStyle(style_cmds))
        return t

    # --- MAIN REPORT SECTIONS ---

    def add_sales_section(self, data, start_date, end_date):
        if self.elements: self.elements.append(PageBreak())

        self._add_report_metadata("Sales Report", start_date, end_date)

        if not data:
            self.elements.append(Paragraph("No sales data found.", self.styles['ReportBody']))
            return

        # Metrics
        total_rev = sum(float(x['total_amount']) for x in data)
        txn_count = len(data)
        net_sales = total_rev / 1.12
        tax_amount = total_rev - net_sales

        self._create_kpi_cards([
            ("Gross Revenue", f"P {total_rev:,.2f}"),
            ("Net Sales", f"P {net_sales:,.2f}"),
            ("VAT (12%)", f"P {tax_amount:,.2f}"),
            ("Transactions", str(txn_count))
        ])

        # Chart: Sales Trend (Using Line Chart)
        chart_data = {}
        for row in data:
            dt_str = row['date'].strftime("%m-%d") if hasattr(row['date'], 'strftime') else str(row['date'])[:5]
            chart_data[dt_str] = chart_data.get(dt_str, 0) + float(row['total_amount'])
        sorted_chart = sorted(chart_data.items())[-7:]

        self._create_line_chart(sorted_chart, title="Revenue Trend")

        # Detailed Table
        self.elements.append(Paragraph("<b>Transaction Details</b>", self.styles['SectionHeader']))
        headers = ['Inv #', 'Date', 'Cashier', 'Total', 'Net', 'Tax']
        table_data = [headers]
        for row in data:
            dt = row['date'].strftime("%Y-%m-%d %H:%M") if hasattr(row['date'], 'strftime') else str(row['date'])
            total = float(row['total_amount'])
            net = total / 1.12
            tax = total - net

            table_data.append([
                str(row['invoice_id']),
                dt,
                row['cashier'],
                f"{total:,.2f}",
                f"{net:,.2f}",
                f"{tax:,.2f}"
            ])

        self.elements.append(self._create_data_table(
            table_data,
            [0.8 * inch, 1.8 * inch, 1.5 * inch, 1.2 * inch, 1.1 * inch, 1.1 * inch],
            ['LEFT', 'LEFT', 'LEFT', 'RIGHT', 'RIGHT', 'RIGHT']
        ))

    def add_inventory_section(self, data, report_type="Valuation"):
        if self.elements: self.elements.append(PageBreak())

        title = "Inventory Valuation" if report_type == "Valuation" else "Low Stock Alerts"
        today = datetime.now().strftime("%Y-%m-%d")
        self._add_report_metadata(title, today, today)

        if not data:
            self.elements.append(Paragraph("No records found.", self.styles['ReportBody']))
            return

        if report_type == "Valuation":
            total_value = sum(float(x['total_value']) for x in data)
            total_items = sum(int(x['stock']) for x in data)

            self._create_kpi_cards([
                ("Total Asset Value", f"P {total_value:,.2f}"),
                ("Total Items", str(total_items)),
                ("Unique SKUs", str(len(data)))
            ])

            # Chart: Category Value (Horizontal Bar)
            cat_data = {}
            for row in data:
                cat = row['category']
                val = float(row['total_value'])
                cat_data[cat] = cat_data.get(cat, 0) + val
            self._create_horizontal_bar_chart(list(cat_data.items()))

            # Table with Cost and Margin
            headers = ['Name', 'Stock', 'Cost', 'Price', 'Margin', 'Value']
            table_data = [headers]

            for row in data:
                # Handle potential missing cost_price if DB wasn't updated
                cost = float(row.get('cost_price', 0))
                price = float(row['selling_price'])
                stock = int(row['stock'])

                if price > 0:
                    margin = ((price - cost) / price) * 100
                    margin_str = f"{margin:.0f}%"
                else:
                    margin_str = "0%"

                table_data.append([
                    row['name'][:25],
                    str(stock),
                    f"{cost:,.2f}",
                    f"{price:,.2f}",
                    margin_str,
                    f"{float(row['total_value']):,.2f}"
                ])

            self.elements.append(self._create_data_table(
                table_data,
                [2.5 * inch, 0.8 * inch, 1 * inch, 1 * inch, 0.8 * inch, 1.2 * inch],
                ['LEFT', 'CENTER', 'RIGHT', 'RIGHT', 'CENTER', 'RIGHT']
            ))

        else:  # Low Stock Report
            low_count = len(data)
            self._create_kpi_cards([("Low Stock Items", str(low_count)), ("Action", "Restock")])

            headers = ['Name', 'Category', 'Stock', 'Threshold', 'Status']
            table_data = [headers]
            for row in data:
                stock = int(row['stock'])
                thresh = int(row['threshold'])
                status = "CRITICAL" if stock == 0 else "LOW"

                table_data.append([
                    row['name'],
                    row['category'],
                    str(stock),
                    str(thresh),
                    status
                ])

            self.elements.append(self._create_data_table(
                table_data,
                [2.5 * inch, 2 * inch, 1 * inch, 1 * inch, 1 * inch],
                ['LEFT', 'LEFT', 'CENTER', 'CENTER', 'CENTER']
            ))

    def add_audit_section(self, data, start_date, end_date):
        if self.elements: self.elements.append(PageBreak())
        self._add_report_metadata("System Audit Logs", start_date, end_date)

        if not data:
            self.elements.append(Paragraph("No audit logs found.", self.styles['ReportBody']))
            return

        headers = ['Time', 'User', 'Action', 'Details']
        table_data = [headers]
        for row in data:
            dt = row['timestamp'].strftime("%Y-%m-%d %H:%M") if hasattr(row['timestamp'], 'strftime') else str(
                row['timestamp'])
            details = Paragraph(row['details'], self.styles['ReportBody'])
            table_data.append([dt, row['user_name'], row['action'], details])

        self.elements.append(self._create_data_table(
            table_data,
            [1.5 * inch, 1.2 * inch, 1.5 * inch, 3.2 * inch],
            ['LEFT', 'LEFT', 'LEFT', 'LEFT']
        ))

    def build(self):
        try:
            self.doc.build(self.elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
            return True
        except Exception as e:
            print(f"PDF Build Error: {e}")
            return False