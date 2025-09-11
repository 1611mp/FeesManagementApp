from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
import pandas as pd
from datetime import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from kivy.uix.screenmanager import Screen

# file names (change if you prefer)
STUDENT_FILE = "students.xlsx"
PAYMENTS_FILE = "payments.xlsx"

KV = """
BoxLayout:
    orientation: "vertical"
    padding: dp(15)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.97, 0.97, 0.97, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDLabel:
        text: "🏫 MIS Fees Management Portal"
        halign: "center"
        font_style: "H4"
        size_hint_y: None
        height: self.texture_size[1] + dp(10)

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)

        MDTextField:
            id: srn_input
            hint_text: "Enter SRN Number"
            size_hint_x: 0.6

        MDRaisedButton:
            text: "Fetch Student Info"
            size_hint_x: 0.4
            on_release: app.on_fetch()

    MDSeparator:

    MDLabel:
        text: "Student Information"
        halign: "center"
        bold: True
        size_hint_y: None
        height: dp(30)

    GridLayout:
        cols: 2
        size_hint_y: None
        height: dp(120)
        row_default_height: dp(28)
        row_force_default: True

        MDLabel:
            text: "Name:"
            halign: "right"
        MDLabel:
            id: name_label
            text: ""

        MDLabel:
            text: "Class / Section:"
            halign: "right"
        MDLabel:
            id: class_label
            text: ""

        MDLabel:
            text: "Total Fees:"
            halign: "right"
        MDLabel:
            id: total_label
            text: ""

        MDLabel:
            text: "Paid / Balance:"
            halign: "right"
        MDLabel:
            id: paid_balance_label
            text: ""

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)

        MDTextField:
            id: amount_input
            hint_text: "Enter Amount Paid"
            input_filter: "float"
            size_hint_x: 0.5

        MDRaisedButton:
            text: "Submit Payment"
            size_hint_x: 0.5
            on_release: app.submit_payment()

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)

        MDRaisedButton:
            text: "View Records"
            on_release: app.view_records()

        MDRaisedButton:
            text: "Export PDF"
            on_release: app.export_pdf_button()

    MDBoxLayout:
        id: table_box
        orientation: "vertical"
        size_hint_y: 1
"""


class MISFeesApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "BlueGray"
        self.root = Builder.load_string(KV)
        Window.size = (1000, 650)
        self.load_data()
        return self.root

    def load_data(self):
        try:
            self.students_df = pd.read_excel(STUDENT_FILE, dtype={'SRN': str})
        except Exception:
            self.students_df = pd.DataFrame(columns=["SRN", "Name", "Class", "Section", "TotalFees"])
            self.students_df.to_excel(STUDENT_FILE, index=False)
            self.show_dialog("Template created", f"{STUDENT_FILE} not found. A template was created. Fill it and restart.")
            self.payments_df = pd.DataFrame(columns=["SRN", "Name", "AmountPaid", "Date"])
            self.payments_df.to_excel(PAYMENTS_FILE, index=False)
            return

        if not os.path.exists(PAYMENTS_FILE):
            pd.DataFrame(columns=["SRN", "Name", "AmountPaid", "Date"]).to_excel(PAYMENTS_FILE, index=False)

        self.payments_df = pd.read_excel(PAYMENTS_FILE, dtype={'SRN': str})

    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=str(text),
            buttons=[MDRaisedButton(text="OK", on_release=lambda x: dialog.dismiss())],
            size_hint=(0.8, None)
        )
        dialog.open()

    def on_fetch(self):
        srn = self.root.ids.srn_input.text.strip()
        if not srn:
            self.show_dialog("Input Error", "Enter SRN.")
            return

        student = self.students_df[self.students_df['SRN'].astype(str) == srn]
        if student.empty:
            self.show_dialog("Not found", f"SRN {srn} not found in {STUDENT_FILE}.")
            return

        s = student.iloc[0]
        self.root.ids.name_label.text = str(s.get('Name', ''))
        self.root.ids.class_label.text = f"{s.get('Class', '')} / {s.get('Section', '')}"
        self.root.ids.total_label.text = str(s.get('TotalFees', ''))

        self.update_financials(srn)

    def update_financials(self, srn):
        try:
            student = self.students_df[self.students_df['SRN'].astype(str) == srn]
            if student.empty:
                total = 0.0
            else:
                total = float(student.iloc[0].get('TotalFees', 0) or 0)

            if self.payments_df is None or self.payments_df.empty:
                paid = 0.0
            else:
                paid = self.payments_df[self.payments_df['SRN'].astype(str) == srn]['AmountPaid'].sum()

            balance = total - paid
            self.root.ids.paid_balance_label.text = f"{paid}  /  {balance}"
        except Exception as e:
            self.show_dialog("Error", f"Failed to update financials: {e}")

    def submit_payment(self, instance=None):
        srn = self.root.ids.srn_input.text.strip()
        amount_text = self.root.ids.amount_input.text.strip()

        if not srn or not amount_text:
            self.show_dialog("Error", "Enter SRN and Amount!")
            return

        try:
            amount_paid = float(amount_text)
        except ValueError:
            self.show_dialog("Error", "Amount must be a valid number!")
            return

        student = self.students_df[self.students_df['SRN'].astype(str) == srn]
        if student.empty:
            self.show_dialog("Error", "SRN not found.")
            return

        name = student.iloc[0].get('Name', '')

        new_record = {
            "SRN": srn,
            "Name": name,
            "AmountPaid": amount_paid,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.payments_df = pd.concat([self.payments_df, pd.DataFrame([new_record])], ignore_index=True)
        self.payments_df["AmountPaid"] = pd.to_numeric(self.payments_df["AmountPaid"], errors="coerce").fillna(0)

        try:
            self.payments_df.to_excel(PAYMENTS_FILE, index=False)
        except Exception as e:
            self.show_dialog("Error", f"Failed to save payment data: {e}")
            return

        self.root.ids.amount_input.text = ""
        self.update_financials(srn)
        self.show_dialog("Success", f"Payment of {amount_paid} received successfully for {name}.")

    def view_records(self, instance=None):
        if self.payments_df is None or self.payments_df.empty:
            self.show_dialog("No Records", "No payment records to display.")
            return

        self.root.ids.table_box.clear_widgets()

        table = MDDataTable(
            size_hint=(1, 1),
            use_pagination=True,
            check=False,
            column_data=[
                ("SRN", dp(30)),
                ("Name", dp(50)),
                ("Amount Paid", dp(40)),
                ("Date", dp(70)),
            ],
            row_data=[
                (str(row["SRN"]), str(row["Name"]), str(row["AmountPaid"]), str(row["Date"]))
                for _, row in self.payments_df.iterrows()
            ],
        )

        self.root.ids.table_box.add_widget(table)

    def export_pdf_button(self):
        srn = self.root.ids.srn_input.text.strip()
        if not srn:
            self.show_dialog("Error", "Enter SRN first.")
            return

        student = self.students_df[self.students_df['SRN'].astype(str) == srn]
        if student.empty:
            self.show_dialog("Error", "SRN not found.")
            return

        self.export_pdf(srn)

    def export_pdf(self, srn):
        student_df = self.students_df[self.students_df['SRN'].astype(str) == srn]
        if student_df.empty:
            self.show_dialog("Error", "Student data not found for PDF.")
            return

        student = student_df.iloc[0]
        payments = self.payments_df[self.payments_df['SRN'].astype(str) == srn] if not self.payments_df.empty else pd.DataFrame()

        folder = "fee_receipts"
        os.makedirs(folder, exist_ok=True)
        name = student.get('Name', '').replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(folder, f"{srn}_{name}_{timestamp}.pdf")

        c = canvas.Canvas(filename, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 800, "SCHOOL NAME")
        c.setFont("Helvetica", 12)
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
                c.setFont("Helvetica", 12)
                y = 800
        c.save()
        self.show_dialog("PDF Saved", f"Saved to: {filename}")

if __name__ == "__main__":
    MISFeesApp().run()
