# 🏫 MIS Fees Management Portal

A **desktop-based Fees Management System** built with **Python (PySide6)**.  
This app helps schools/colleges manage **student fee records, payments, and PDF receipts**.

---

## 🚀 Features

✅ **Student Data Management**  
- Loads student data from `students.xlsx` (SRN, Name, Class, Section, Total Fees).  
- Auto-generates a **template Excel file** if missing.  

✅ **Payment Tracking**  
- Submit and store student payments in `payments.xlsx`.  
- Shows **total fees, paid amount, and balance** dynamically.  

✅ **Record Viewer**  
- Displays all payment records in a **searchable table**.  

✅ **PDF Receipt Generator**  
- Generates a **professional PDF receipt** per student.  
- Auto-saves in `fee_receipts/` folder.  

✅ **User-Friendly GUI (PySide6)**  
- Built using **Qt Widgets** (`QLineEdit`, `QTableWidget`, `QPushButton`).  
- Clean and simple layout for school staff usage.  

---

## 📂 File Structure

MIS-Fees-App/
│── mis_fees_app.py # Main application code
│── students.xlsx # Student details (auto-created if missing)
│── payments.xlsx # Payment history (auto-created if missing)
│── fee_receipts/ # Folder for generated PDF receipts
│── README.md # Documentation (this file)



---

## ⚙️ Requirements

Install the required libraries using **pip**:

```bash
pip install PySide6 pandas openpyxl reportlab

python fees_mis_portal.py
