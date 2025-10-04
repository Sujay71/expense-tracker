import streamlit as st
import sqlite3
import pandas as pd

# ================================
# 1. DATABASE SETUP
# ================================
def init_db():
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    category TEXT,
                    amount REAL,
                    description TEXT
                )''')
    conn.commit()
    conn.close()

def add_expense(date, category, amount, description):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)",
              (date, category, amount, description))
    conn.commit()
    conn.close()

def view_expenses():
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql("SELECT * FROM expenses", conn)
    conn.close()
    return df

def update_expense(expense_id, date, category, amount, description):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("""UPDATE expenses 
                 SET date=?, category=?, amount=?, description=? 
                 WHERE id=?""",
              (date, category, amount, description, expense_id))
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()


# ================================
# 2. STREAMLIT UI
# ================================
st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("💰 Expense Tracker (CRUD App)")

menu = ["Add Expense", "View Expenses", "Update Expense", "Delete Expense"]
choice = st.sidebar.radio("Menu", menu)

init_db()

if choice == "Add Expense":
    st.subheader("➕ Add New Expense")
    date = st.date_input("Date")
    category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Other"])
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    description = st.text_area("Description")
    if st.button("Add Expense"):
        add_expense(str(date), category, amount, description)
        st.success("Expense added successfully!")

elif choice == "View Expenses":
    st.subheader("📊 All Expenses")
    df = view_expenses()
    if not df.empty:
        st.dataframe(df)
        st.write("### Total Spent: ", df["amount"].sum())
    else:
        st.warning("No expenses found!")

elif choice == "Update Expense":
    st.subheader("✏️ Update Expense")
    df = view_expenses()
    if not df.empty:
        expense_id = st.selectbox("Select Expense ID", df["id"])
        row = df[df["id"] == expense_id].iloc[0]

        date = st.date_input("Date", pd.to_datetime(row["date"]))
        category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Other"], index=["Food", "Transport", "Shopping", "Bills", "Other"].index(row["category"]) if row["category"] in ["Food", "Transport", "Shopping", "Bills", "Other"] else 0)
        amount = st.number_input("Amount", value=float(row["amount"]))
        description = st.text_area("Description", row["description"])

        if st.button("Update Expense"):
            update_expense(expense_id, str(date), category, amount, description)
            st.success("Expense updated successfully!")
    else:
        st.warning("No expenses available to update.")

elif choice == "Delete Expense":
    st.subheader("🗑️ Delete Expense")
    df = view_expenses()
    if not df.empty:
        expense_id = st.selectbox("Select Expense ID", df["id"])
        if st.button("Delete Expense"):
            delete_expense(expense_id)
            st.success("Expense deleted successfully!")
    else:
        st.warning("No expenses available to delete.")
