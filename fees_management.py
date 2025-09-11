import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

STUDENT_FILE = "students.xlsx"
FEES_FILE = "fees.xlsx"

if not os.path.exists(FEES_FILE):
    df = pd.DataFrame(columns=["StudentID", "Name", "AmountPaid", "Date"])
    df.to_excel(FEES_FILE, index=False)

students_df = pd.read_excel(STUDENT_FILE)
fees_df = pd.read_excel(FEES_FILE)

class FeesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Fees Management System")
        self.root.geometry("900x550")
        tk.Label(root, text="Select Student:").pack(pady=5)
        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(root, textvariable=self.student_var)
        self.student_combo['values'] = [f"{row.StudentID} - {row.Name}" for idx, row in students_df.iterrows()]
        self.student_combo.pack(pady=5)
        tk.Label(root, text="Amount Paid:").pack(pady=5)
        self.amount_entry = tk.Entry(root)
        self.amount_entry.pack(pady=5)
        tk.Button(root, text="Submit Payment", command=self.submit_payment).pack(pady=5)
        tk.Button(root, text="View Balance", command=self.view_balance).pack(pady=5)
        tk.Button(root, text="View All Records", command=self.view_all_records).pack(pady=5)
        tk.Button(root, text="Export PDF", command=self.export_pdf_button).pack(pady=5)
        self.tree = ttk.Treeview(root)
        self.tree.pack(pady=10, fill="both", expand=True)

    def submit_payment(self):
        student_selection = self.student_var.get()
        amount = self.amount_entry.get()
        if not student_selection or not amount:
            messagebox.showwarning("Input Error", "Select a student and enter amount.")
            return
        try:
            amount = float(amount)
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a number.")
            return
        student_id = int(student_selection.split(" - ")[0])
        student_name = student_selection.split(" - ")[1]
        global fees_df
        new_record = {"StudentID": student_id, "Name": student_name, "AmountPaid": amount, "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        fees_df = pd.concat([fees_df, pd.DataFrame([new_record])], ignore_index=True)
        fees_df.to_excel(FEES_FILE, index=False)
        messagebox.showinfo("Success", f"Payment of {amount} recorded for {student_name}.")
        self.amount_entry.delete(0, tk.END)

    def view_balance(self):
        student_selection = self.student_var.get()
        if not student_selection:
            messagebox.showwarning("Input Error", "Select a student.")
            return
        student_id = int(student_selection.split(" - ")[0])
        student_row = students_df[students_df.StudentID == student_id].iloc[0]
        total_fees = student_row.TotalFees
        paid_amount = fees_df[fees_df.StudentID == student_id]["AmountPaid"].sum()
        balance = total_fees - paid_amount
        messagebox.showinfo("Balance", f"Total Fees: {total_fees}\nPaid: {paid_amount}\nBalance: {balance}")

    def view_all_records(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.tree["columns"] = ("StudentID", "Name", "AmountPaid", "Date")
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=0, stretch=False)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        for idx, row in fees_df.iterrows():
            self.tree.insert("", "end", values=(row.StudentID, row.Name, row.AmountPaid, row.Date))

    def export_pdf_button(self):
        student_selection = self.student_var.get()
        if not student_selection:
            messagebox.showwarning("Input Error", "Select a student.")
            return
        student_id = int(student_selection.split(" - ")[0])
        self.export_pdf(student_id)

    def export_pdf(self, student_id):
        student = students_df[students_df.StudentID == student_id].iloc[0]
        payments = fees_df[fees_df.StudentID == student_id]
        pdf_file = f"{student.Name}_Fees.pdf"
        c = canvas.Canvas(pdf_file, pagesize=A4)
        c.setFont("Helvetica", 12)
        c.drawString(50, 800, f"Fee Report for {student.Name} (ID: {student.StudentID})")
        c.drawString(50, 780, f"Grade: {student.Grade}")
        c.drawString(50, 760, f"Total Fees: {student.TotalFees}")
        total_paid = payments["AmountPaid"].sum()
        balance = student.TotalFees - total_paid
        c.drawString(50, 740, f"Total Paid: {total_paid}")
        c.drawString(50, 720, f"Balance: {balance}")
        c.drawString(50, 700, "Payment History:")
        y = 680
        for idx, row in payments.iterrows():
            c.drawString(60, y, f"{row.Date} - {row.AmountPaid}")
            y -= 20
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 800
        c.save()
        messagebox.showinfo("PDF Saved", f"PDF saved as {pdf_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FeesApp(root)
    root.mainloop()
