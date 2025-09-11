from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp

import pandas as pd
from datetime import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ===============================
# Load Data
# ===============================
STUDENT_FILE = "students.xlsx"
FEES_FILE = "fees.xlsx"

if not os.path.exists(FEES_FILE):
    pd.DataFrame(columns=["StudentID","Name","AmountPaid","Date"]).to_excel(FEES_FILE,index=False)

students_df = pd.read_excel(STUDENT_FILE)
fees_df = pd.read_excel(FEES_FILE)

# ===============================
# Kivy Layout
# ===============================
KV = """
BoxLayout:
    orientation: "vertical"
    padding: dp(10)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.95,0.95,0.95,1
        Rectangle:
            pos: self.pos
            size: self.size

    MDLabel:
        text: "🏫 Student Fees Management System"
        halign: "center"
        font_style: "H4"
        size_hint_y: None
        height: self.texture_size[1]+20

    MDCard:
        orientation: "vertical"
        padding: dp(10)
        spacing: dp(10)
        size_hint_y: None
        height: dp(150)
        md_bg_color: 1,1,1,1
        radius: [10,10,10,10]
        elevation: 10

        BoxLayout:
            spacing: dp(10)
            MDLabel:
                text: "Select Student:"
                size_hint_x: 0.3
                halign: "right"
            MDTextField:
                id: student_input
                hint_text: "Enter student name or ID"
                size_hint_x:0.7

        BoxLayout:
            spacing: dp(10)
            MDLabel:
                text: "Amount Paid:"
                size_hint_x:0.3
                halign: "right"
            MDTextField:
                id: amount_input
                hint_text: "Enter amount"
                input_filter: "float"
                size_hint_x:0.7

    BoxLayout:
        spacing: dp(10)
        size_hint_y: None
        height: dp(50)
        MDRaisedButton:
            text: "Submit Payment"
            on_release: app.submit_payment()
        MDRaisedButton:
            text: "View Balance"
            on_release: app.view_balance()
        MDRaisedButton:
            text: "View All Records"
            on_release: app.view_all_records()
        MDRaisedButton:
            text: "Export PDF"
            on_release: app.export_pdf_button()

    MDBoxLayout:
        id: table_box
        orientation: "vertical"
"""

# ===============================
# Main App
# ===============================
class FeesApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "BlueGray"
        self.root = Builder.load_string(KV)
        return self.root

    # -------------------------------
    # Submit Payment
    # -------------------------------
    def submit_payment(self):
        student_text = self.root.ids.student_input.text.strip()
        amount_text = self.root.ids.amount_input.text.strip()
        if not student_text or not amount_text:
            self.show_dialog("Error","Enter student and amount.")
            return
        try:
            amount = float(amount_text)
        except:
            self.show_dialog("Error","Amount must be a number.")
            return

        # Find student
        student_row = students_df[(students_df.StudentID.astype(str)==student_text)|(students_df.Name.str.lower()==student_text.lower())]
        if student_row.empty:
            self.show_dialog("Error","Student not found.")
            return
        student_id = student_row.iloc[0].StudentID
        student_name = student_row.iloc[0].Name

        global fees_df
        new_record = {"StudentID":student_id,"Name":student_name,"AmountPaid":amount,"Date":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        fees_df = pd.concat([fees_df,pd.DataFrame([new_record])],ignore_index=True)
        fees_df.to_excel(FEES_FILE,index=False)
        self.show_dialog("Success",f"Payment of {amount} recorded for {student_name}.")
        self.root.ids.amount_input.text = ""

    # -------------------------------
    # View Balance
    # -------------------------------
    def view_balance(self):
        student_text = self.root.ids.student_input.text.strip()
        if not student_text:
            self.show_dialog("Error","Enter student name or ID.")
            return
        student_row = students_df[(students_df.StudentID.astype(str)==student_text)|(students_df.Name.str.lower()==student_text.lower())]
        if student_row.empty:
            self.show_dialog("Error","Student not found.")
            return
        student_id = student_row.iloc[0].StudentID
        total_fees = student_row.iloc[0].TotalFees
        paid_amount = fees_df[fees_df.StudentID==student_id]["AmountPaid"].sum()
        balance = total_fees - paid_amount
        self.show_dialog("Balance",f"Total Fees: {total_fees}\nPaid: {paid_amount}\nBalance: {balance}")

    # -------------------------------
    # View All Records
    # -------------------------------
    def view_all_records(self):
        box = self.root.ids.table_box
        box.clear_widgets()
        if fees_df.empty:
            self.show_dialog("Info","No fee records yet.")
            return
        table = MDDataTable(
            size_hint=(1,1),
            column_data=[
                ("Student ID", dp(30)),
                ("Name", dp(30)),
                ("Amount Paid", dp(30)),
                ("Date", dp(50))
            ],
            row_data=[(r.StudentID,r.Name,r.AmountPaid,r.Date) for idx,r in fees_df.iterrows()],
            use_pagination=True,
            rows_per_page=10
        )
        box.add_widget(table)

    # -------------------------------
    # Export PDF
    # -------------------------------
    def export_pdf_button(self):
        student_text = self.root.ids.student_input.text.strip()
        if not student_text:
            self.show_dialog("Error","Enter student name or ID.")
            return
        student_row = students_df[(students_df.StudentID.astype(str)==student_text)|(students_df.Name.str.lower()==student_text.lower())]
        if student_row.empty:
            self.show_dialog("Error","Student not found.")
            return
        student_id = student_row.iloc[0].StudentID
        self.export_pdf(student_id)

    def export_pdf(self, student_id):
        folder = "fee_receipts"
        if not os.path.exists(folder):
            os.makedirs(folder)
        student = students_df[students_df.StudentID==student_id].iloc[0]
        payments = fees_df[fees_df.StudentID==student_id]
        pdf_file = os.path.join(folder,f"{student.Name}_Fees.pdf")
        c = canvas.Canvas(pdf_file,pagesize=A4)
        c.setFont("Helvetica",12)
        c.drawString(50,800,f"Fee Report for {student.Name} (ID: {student.StudentID})")
        c.drawString(50,780,f"Grade: {student.Grade}")
        c.drawString(50,760,f"Total Fees: {student.TotalFees}")
        total_paid = payments["AmountPaid"].sum()
        balance = student.TotalFees - total_paid
        c.drawString(50,740,f"Total Paid: {total_paid}")
        c.drawString(50,720,f"Balance: {balance}")
        c.drawString(50,700,"Payment History:")
        y = 680
        for idx,row in payments.iterrows():
            c.drawString(60,y,f"{row.Date} - {row.AmountPaid}")
            y -= 20
            if y<50:
                c.showPage()
                c.setFont("Helvetica",12)
                y=800
        c.save()
        self.show_dialog("PDF Saved",f"PDF saved in '{folder}' as {student.Name}_Fees.pdf")

    # -------------------------------
    # Show Dialog
    # -------------------------------
    def show_dialog(self,title,text):
        dialog = MDDialog(title=title,text=text,size_hint=(0.6,None),auto_dismiss=True)
        dialog.open()

# ===============================
# Run App
# ===============================
if __name__=="__main__":
    Window.size = (1000,650)
    FeesApp().run()
