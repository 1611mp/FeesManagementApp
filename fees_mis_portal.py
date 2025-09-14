import sys
import os
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog
)
from PySide6.QtCore import Qt

# File names
STUDENT_FILE = "students.xlsx"
PAYMENTS_FILE = "payments.xlsx"


class MISFeesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏫 MIS Fees Management Portal")
        self.setGeometry(200, 100, 900, 600)

        # Load data
        self.load_data()

        # Widgets
        self.srn_input = QLineEdit()
        self.srn_input.setPlaceholderText("Enter SRN Number")

        fetch_btn = QPushButton("Fetch Student Info")
        fetch_btn.clicked.connect(self.on_fetch)

        self.name_label = QLabel("")
        self.class_label = QLabel("")
        self.total_label = QLabel("")
        self.paid_balance_label = QLabel("")

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter Amount Paid")

        submit_btn = QPushButton("Submit Payment")
        submit_btn.clicked.connect(self.submit_payment)

        view_btn = QPushButton("View Records")
        view_btn.clicked.connect(self.view_records)

        pdf_btn = QPushButton("Export PDF")
        pdf_btn.clicked.connect(self.export_pdf_button)

        # Table for payment history
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["SRN", "Name", "Amount Paid", "Date"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Layout
        layout = QVBoxLayout()

        # SRN Input
        srn_layout = QHBoxLayout()
        srn_layout.addWidget(self.srn_input)
        srn_layout.addWidget(fetch_btn)
        layout.addLayout(srn_layout)

        # Student Info
        layout.addWidget(QLabel("<b>Student Information</b>", alignment=Qt.AlignCenter))
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_label)
        layout.addWidget(QLabel("Class / Section:"))
        layout.addWidget(self.class_label)
        layout.addWidget(QLabel("Total Fees:"))
        layout.addWidget(self.total_label)
        layout.addWidget(QLabel("Paid / Balance:"))
        layout.addWidget(self.paid_balance_label)

        # Payment input
        pay_layout = QHBoxLayout()
        pay_layout.addWidget(self.amount_input)
        pay_layout.addWidget(submit_btn)
        layout.addLayout(pay_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(view_btn)
        btn_layout.addWidget(pdf_btn)
        layout.addLayout(btn_layout)

        # Table
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_data(self):
        try:
            self.students_df = pd.read_excel(STUDENT_FILE, dtype={"SRN": str})
        except Exception:
            self.students_df = pd.DataFrame(columns=["SRN", "Name", "Class", "Section", "TotalFees"])
            self.students_df.to_excel(STUDENT_FILE, index=False)
            QMessageBox.warning(self, "Template Created",
                                f"{STUDENT_FILE} not found. A template was created. Fill it and restart.")
            self.payments_df = pd.DataFrame(columns=["SRN", "Name", "AmountPaid", "Date"])
            self.payments_df.to_excel(PAYMENTS_FILE, index=False)
            return

        if not os.path.exists(PAYMENTS_FILE):
            pd.DataFrame(columns=["SRN", "Name", "AmountPaid", "Date"]).to_excel(PAYMENTS_FILE, index=False)

        self.payments_df = pd.read_excel(PAYMENTS_FILE, dtype={"SRN": str})

    def on_fetch(self):
        srn = self.srn_input.text().strip()
        if not srn:
            QMessageBox.warning(self, "Input Error", "Enter SRN.")
            return

        student = self.students_df[self.students_df["SRN"].astype(str) == srn]
        if student.empty:
            QMessageBox.warning(self, "Not Found", f"SRN {srn} not found.")
            return

        s = student.iloc[0]
        self.name_label.setText(str(s.get("Name", "")))
        self.class_label.setText(f"{s.get('Class', '')} / {s.get('Section', '')}")
        self.total_label.setText(str(s.get("TotalFees", "")))

        self.update_financials(srn)

    def update_financials(self, srn):
        student = self.students_df[self.students_df["SRN"].astype(str) == srn]
        total = float(student.iloc[0].get("TotalFees", 0)) if not student.empty else 0.0

        paid = self.payments_df[self.payments_df["SRN"].astype(str) == srn]["AmountPaid"].sum() \
            if not self.payments_df.empty else 0.0

        balance = total - paid
        self.paid_balance_label.setText(f"{paid} / {balance}")

    def submit_payment(self):
        srn = self.srn_input.text().strip()
        amount_text = self.amount_input.text().strip()

        if not srn or not amount_text:
            QMessageBox.warning(self, "Error", "Enter SRN and Amount!")
            return

        try:
            amount_paid = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Amount must be a valid number!")
            return

        student = self.students_df[self.students_df["SRN"].astype(str) == srn]
        if student.empty:
            QMessageBox.warning(self, "Error", "SRN not found.")
            return

        name = student.iloc[0].get("Name", "")

        new_record = {
            "SRN": srn,
            "Name": name,
            "AmountPaid": amount_paid,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.payments_df = pd.concat([self.payments_df, pd.DataFrame([new_record])], ignore_index=True)
        self.payments_df.to_excel(PAYMENTS_FILE, index=False)

        self.amount_input.clear()
        self.update_financials(srn)
        QMessageBox.information(self, "Success", f"Payment of {amount_paid} received for {name}.")

    def view_records(self):
        if self.payments_df.empty:
            QMessageBox.information(self, "No Records", "No payment records to display.")
            return

        self.table.setRowCount(len(self.payments_df))
        for i, row in self.payments_df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(str(row["SRN"])))
            self.table.setItem(i, 1, QTableWidgetItem(str(row["Name"])))
            self.table.setItem(i, 2, QTableWidgetItem(str(row["AmountPaid"])))
            self.table.setItem(i, 3, QTableWidgetItem(str(row["Date"])))

    def export_pdf_button(self):
        srn = self.srn_input.text().strip()
        if not srn:
            QMessageBox.warning(self, "Error", "Enter SRN first.")
            return

        student = self.students_df[self.students_df["SRN"].astype(str) == srn]
        if student.empty:
            QMessageBox.warning(self, "Error", "SRN not found.")
            return

        self.export_pdf(srn)

    def export_pdf(self, srn):
        student_df = self.students_df[self.students_df["SRN"].astype(str) == srn]
        if student_df.empty:
            QMessageBox.warning(self, "Error", "Student data not found for PDF.")
            return

        student = student_df.iloc[0]
        payments = self.payments_df[self.payments_df["SRN"].astype(str) == srn]

        folder = "fee_receipts"
        os.makedirs(folder, exist_ok=True)
        name = student.get("Name", "").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(folder, f"{srn}_{name}_{timestamp}.pdf")

        c = canvas.Canvas(filename, pagesize=A4)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 800, "SCHOOL NAME")
        c.setFont("Helvetica", 14)
        c.drawString(50, 780, f"Receipt for: {student.get('Name', '')}    SRN: {srn}")
        c.drawString(50, 760, f"Class / Section: {student.get('Class', '')} / {student.get('Section', '')}")
        c.drawString(50, 740, f"Total Fees: {student.get('TotalFees', '')}")
        c.drawString(50, 720, "Payments:")

        y = 700
        for _, p in payments.iterrows():
            c.drawString(60, y, f"{p.Date}  —  {p.AmountPaid}")
            y -= 18
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 14)
                y = 800

        c.save()
        QMessageBox.information(self, "PDF Saved", f"Saved to: {filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MISFeesApp()
    window.show()
    sys.exit(app.exec())
