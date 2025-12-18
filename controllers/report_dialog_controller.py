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

        #Database Logic
        self.main_db = DatabaseManager()
        self.db = self.main_db.manager_db
        self.setup_ui()

    def setup_ui(self):
        # Default dates (First of month to Now)
        now = datetime.now()
        self.startDateEdit.setDate(QDate(now.year, now.month, 1))
        self.endDateEdit.setDate(QDate.currentDate())
        self.reportTypeCombo.addItem("All Reports")

        self.exportBtn.clicked.connect(self.handle_export)
        self.cancelBtn.clicked.connect(self.close)

    def handle_export(self):
        rpt_type = self.reportTypeCombo.currentText()
        start = self.startDateEdit.date().toString("yyyy-MM-dd")
        end = self.endDateEdit.date().toString("yyyy-MM-dd")

        # 1. DetermineFilename
        filename = f"{rpt_type.replace(' ', '_')}_{end}.pdf"

        # 2. Ask Where to Save
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", filename, "PDF Files (*.pdf)")

        if not file_path:
            return  # User cancel

        try:
            gen = PDFReportGenerator(file_path)

            #GENERATE EVERYTHING
            if rpt_type == "All Reports":
                # 1. Sales
                gen.add_sales_section(self.db.get_sales_report_data(start, end), start, end)
                # 2. Inventory Valuation
                gen.add_inventory_section(self.db.get_inventory_valuation_data(), "Valuation")
                # 3. Low Stock
                gen.add_inventory_section(self.db.get_low_stock_data(), "LowStock")
                # 4. Audit Logs
                gen.add_audit_section(self.db.get_audit_log_data(start, end), start, end)

            #GENERATE INDIVIDUAL REPORTS
            elif rpt_type == "Sales Report":
                gen.add_sales_section(self.db.get_sales_report_data(start, end), start, end)

            elif rpt_type == "Inventory Valuation":
                gen.add_inventory_section(self.db.get_inventory_valuation_data(), "Valuation")

            elif rpt_type == "Low Stock Alert":
                gen.add_inventory_section(self.db.get_low_stock_data(), "LowStock")

            elif rpt_type == "Audit Logs":
                gen.add_audit_section(self.db.get_audit_log_data(start, end), start, end)

            #Finalize and Write File
            if gen.build():
                QMessageBox.information(self, "Success", "Report Generated Successfully!")
                self.close()
            else:
                QMessageBox.critical(self, "Error", "Failed to compile PDF file.")

        except AttributeError as e:
            QMessageBox.critical(self, "Database Error",
                                 f"Missing method in DatabaseManager.\nError: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")