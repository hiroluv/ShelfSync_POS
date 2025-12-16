from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt6.QtCore import QDate
from PyQt6.uic import loadUi
from datetime import datetime

from models.database_manager import DatabaseManager
from utils.pdf_generator import PDFReportGenerator


class ReportDialogController(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("views/report_dialog.ui", self)

        # --- FIX: Initialize Database Logic ---
        # 1. Create the main DB connection handler
        self.main_db = DatabaseManager()

        # 2. Access the ManagerDB instance where we wrote the queries (get_sales_report_data, etc.)
        # DatabaseManager automatically creates 'self.manager_db' inside its __init__
        self.db = self.main_db.manager_db

        self.setup_ui()

    def setup_ui(self):
        # Default dates (First of month to Now)
        now = datetime.now()
        self.startDateEdit.setDate(QDate(now.year, now.month, 1))
        self.endDateEdit.setDate(QDate.currentDate())

        self.exportBtn.clicked.connect(self.handle_export)
        self.cancelBtn.clicked.connect(self.close)

    def handle_export(self):
        rpt_type = self.reportTypeCombo.currentText()
        start = self.startDateEdit.date().toString("yyyy-MM-dd")
        end = self.endDateEdit.date().toString("yyyy-MM-dd")

        # 1. Fetch Data
        data = []
        try:
            if rpt_type == "Sales Report":
                data = self.db.get_sales_report_data(start, end)
                filename = f"Sales_Report_{start}_{end}.pdf"
            elif rpt_type == "Inventory Valuation":
                data = self.db.get_inventory_valuation_data()
                filename = f"Inventory_Value_{end}.pdf"
            elif rpt_type == "Low Stock Alert":
                data = self.db.get_low_stock_data()
                filename = f"Low_Stock_{end}.pdf"
            elif rpt_type == "Audit Logs":
                data = self.db.get_audit_log_data(start, end)
                filename = f"Audit_Logs_{start}_{end}.pdf"
        except AttributeError as e:
            QMessageBox.critical(self, "Database Error",
                                 f"Could not find the report method in ManagerDB.\nError: {e}\n\nPlease check models/db_manager.py")
            return
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch data: {str(e)}")
            return

        if not data:
            QMessageBox.warning(self, "No Data", f"No records found for {rpt_type}.")
            return

        # 2. Save Dialog
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", filename, "PDF Files (*.pdf)")

        if file_path:
            try:
                gen = PDFReportGenerator(file_path)
                if rpt_type == "Sales Report":
                    gen.generate_sales_report(data, start, end)
                elif rpt_type == "Inventory Valuation":
                    gen.generate_inventory_report(data, "Valuation")
                elif rpt_type == "Low Stock Alert":
                    gen.generate_inventory_report(data, "LowStock")
                elif rpt_type == "Audit Logs":
                    gen.generate_audit_report(data, start, end)

                QMessageBox.information(self, "Success", "Report Generated Successfully!")
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))