import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

# ===============================
# Load Excel Data
# ===============================
STUDENT_FILE = "students.xlsx"
FEES_FILE = "fees.xlsx"

if not os.path.exists(FEES_FILE):
    df = pd.DataFrame(columns=["StudentID", "Name", "AmountPaid", "Date"])
    df.to_excel(FEES_FILE, index=False)

students_df = pd.read_excel(STUDENT_FILE)
fees_df = pd.read_excel(FEES_FILE)

# ===============================
# Main Application
# ===============================
class FeesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Fees Management System")
        self.root.geometry("1000x650")
        self.root.resizable(False, False)

        # ===============================
        # Gradient Background
        # ===============================
        self.canvas = tb.Canvas(root, width=1000, height=650)
        self.canvas.pack(fill=BOTH, expand=True)
        self.draw_gradient(self.canvas, "#f0f0f0", "#ffffff")

        # ===============================
        # Header with Logo + Title
        # ===============================
        header_frame = tb.Frame(root, bootstyle=PRIMARY, padding=15)
        header_frame.place(relx=0.5, rely=0.05, anchor='n')
        tb.Label(header_frame, text="🏫 Student Fees Management System", font=("Helvetica", 22, "bold"), bootstyle=PRIMARY).pack()

        # ===============================
        # Load Icons
        # ===============================
        self.icons = {}
        for name in ['pdf', 'view', 'balance', 'submit']:
            img = Image.open(f"icons/{name}.png").resize((25,25))
            self.icons[name] = ImageTk.PhotoImage(img)

        # ===============================
        # Student Info Card
        # ===============================
        card_frame = tb.Frame(root, bootstyle=INFO, padding=15, borderwidth=2, relief="ridge")
        card_frame.place(relx=0.5, rely=0.15, anchor='n')

        tb.Label(card_frame, text="Select Student:", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.student_var = tb.StringVar()
        self.student_combo = tb.Combobox(card_frame, textvariable=self.student_var, width=40, bootstyle=INFO)
        self.student_combo['values'] = [f"{row.StudentID} - {row.Name}" for idx, row in students_df.iterrows()]
        self.student_combo.grid(row=0, column=1, padx=5, pady=5)

        tb.Label(card_frame, text="Amount Paid:", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.amount_entry = tb.Entry(card_frame, width=42)
        self.amount_entry.grid(row=1, column=1, padx=5, pady=5)

        # ===============================
        # Buttons Frame
        # ===============================
        btn_frame = tb.Frame(root, padding=10)
        btn_frame.place(relx=0.5, rely=0.32, anchor='n')

        self.submit_btn = tb.Button(btn_frame, text="Submit Payment", bootstyle=SUCCESS, image=self.icons['submit'], compound=LEFT, width=180, command=self.submit_payment)
        self.submit_btn.grid(row=0, column=0, padx=10, pady=5)
        self.add_hover(self.submit_btn, '#28a745', '#218838')

        self.balance_btn = tb.Button(btn_frame, text="View Balance", bootstyle=INFO, image=self.icons['balance'], compound=LEFT, width=180, command=self.view_balance)
        self.balance_btn.grid(row=0, column=1, padx=10, pady=5)
        self.add_hover(self.balance_btn, '#17a2b8', '#138496')

        self.view_btn = tb.Button(btn_frame, text="View All Records", bootstyle=SECONDARY, image=self.icons['view'], compound=LEFT, width=180, command=self.view_all_records)
        self.view_btn.grid(row=0, column=2, padx=10, pady=5)
        self.add_hover(self.view_btn, '#6c757d', '#5a6268')

        self.pdf_btn = tb.Button(btn_frame, text="Export PDF", bootstyle=WARNING, image=self.icons['pdf'], compound=LEFT, width=180, command=self.export_pdf_button)
        self.pdf_btn.grid(row=0, column=3, padx=10, pady=5)
        self.add_hover(self.pdf_btn, '#ffc107', '#e0a800')

        # ===============================
        # Records Table
        # ===============================
        table_frame = tb.Frame(root, padding=10)
        table_frame.place(relx=0.5, rely=0.48, anchor='n')

        style = tb.Style()
        style.configure("Treeview", rowheight=30, font=("Helvetica", 11))
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))

        self.tree = tb.Treeview(table_frame, bootstyle="info")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<Motion>", self.highlight_row)

    # ===============================
    # Gradient Background
    # ===============================
    def draw_gradient(self, canvas, color1, color2):
        for i in range(650):
            ratio = i/650
            r1, g1, b1 = canvas.winfo_rgb(color1)
            r2, g2, b2 = canvas.winfo_rgb(color2)
            nr = int(r1*(1-ratio) + r2*ratio)//256
            ng = int(g1*(1-ratio) + g2*ratio)//256
            nb = int(b1*(1-ratio) + b2*ratio)//256
            canvas.create_line(0, i, 1000, i, fill=f'#{nr:02x}{ng:02x}{nb:02x}')

    # ===============================
    # Hover Animation for Buttons
    # ===============================
    def add_hover(self, btn, color_normal, color_hover):
        def on_enter(e):
            btn.configure(background=color_hover)
        def on_leave(e):
            btn.configure(background=color_normal)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    # ===============================
    # Highlight Table Row on Hover
    # ===============================
    def highlight_row(self, event):
        rowid = self.tree.identify_row(event.y)
        self.tree.selection_set(rowid)

    # ===============================
    # Submit Payment
    # ===============================
    def submit_payment(self):
        student_selection = self.student_var.get()
        amount = self.amount_entry.get()
        if not student_selection or not amount:
            tb.Messagebox.show_warning("Input Error", "Select a student and enter amount.")
            return
        try:
            amount = float(amount)
        except ValueError:
            tb.Messagebox.show_error("Input Error", "Amount must be a number.")
            return
        student_id = int(student_selection.split(" - ")[0])
        student_name = student_selection.split(" - ")[1]

        global fees_df
        new_record = {"StudentID": student_id, "Name": student_name, "AmountPaid": amount, "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        fees_df = pd.concat([fees_df, pd.DataFrame([new_record])], ignore_index=True)
        fees_df.to_excel(FEES_FILE, index=False)

        tb.Messagebox.show_info("Success", f"Payment of {amount} recorded for {student_name}.")
        self.amount_entry.delete(0, tb.END)

    # ===============================
    # View Balance
    # ===============================
    def view_balance(self):
        student_selection = self.student_var.get()
        if not student_selection:
            tb.Messagebox.show_warning("Input Error", "Select a student.")
            return
        student_id = int(student_selection.split(" - ")[0])
        student_row = students_df[students_df.StudentID == student_id].iloc[0]
        total_fees = student_row.TotalFees
        paid_amount = fees_df[fees_df.StudentID == student_id]["AmountPaid"].sum()
        balance = total_fees - paid_amount
        tb.Messagebox.show_info("Balance", f"Total Fees: {total_fees}\nPaid: {paid_amount}\nBalance: {balance}")

    # ===============================
    # View All Records
    # ===============================
    def view_all_records(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.tree
