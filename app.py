import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import groq
import os
from dotenv import load_dotenv


# ================================
# 1. DATABASE SETUP
# ================================
def init_db():
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     date
                     TEXT,
                     category
                     TEXT,
                     amount
                     REAL,
                     description
                     TEXT
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
                 SET date=?,
                     category=?,
                     amount=?,
                     description=?
                 WHERE id = ?""",
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
# 2. DASHBOARD HELPER FUNCTION
# ================================
def generate_dashboard(df):
    """Generates and displays the metrics and charts for a given dataframe."""
    # --- METRICS ---
    total_spent = df["amount"].sum()
    st.metric("Total Spent for Period", f"${total_spent:,.2f}")

    st.divider()

    # --- VISUALIZATION DASHBOARD ---
    st.subheader("📈 Data Visualization")

    # Layout for charts
    col1, col2 = st.columns(2)

    with col1:
        # Bar chart for spending by category
        st.write("#### Spending by Category")
        category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        fig_bar = px.bar(category_spending,
                         x=category_spending.index,
                         y=category_spending.values,
                         labels={'y': 'Total Amount', 'x': 'Category'},
                         color=category_spending.index)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        # Pie chart for spending distribution
        st.write("#### Spending Distribution")
        fig_pie = px.pie(df,
                         names='category',
                         values='amount',
                         hole=.3)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Line chart for spending over time
    st.write("#### Spending Over Time")
    # Ensure date column is datetime for grouping
    df['date'] = pd.to_datetime(df['date'])
    daily_spending = df.groupby(df['date'].dt.date)['amount'].sum()
    fig_line = px.line(daily_spending,
                       x=daily_spending.index,
                       y=daily_spending.values,
                       labels={'y': 'Total Amount', 'x': 'Date'},
                       markers=True)
    st.plotly_chart(fig_line, use_container_width=True)


# ================================
# 3. STREAMLIT UI
# ================================
st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("💰 Expense Tracker (CRUD App)")

menu = ["Add Expense", "View Expenses", "Update Expense", "Delete Expense", "Ask AI"]
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
    st.subheader("📊 All Expenses & Dashboard")
    df = view_expenses()
    if not df.empty:
        # Always display the full data table at the top
        st.dataframe(df, use_container_width=True)

        # Convert date column for filtering and plotting
        df['date'] = pd.to_datetime(df['date'])

        st.divider()

        # --- VIEW MODE SELECTION ---
        view_mode = st.radio("Select View", ["Overall Summary", "Monthly Breakdown"], horizontal=True)

        if view_mode == "Overall Summary":
            generate_dashboard(df)

        elif view_mode == "Monthly Breakdown":
            st.subheader("Monthly Analysis")
            # Create filter widgets
            years = sorted(df['date'].dt.year.unique(), reverse=True)
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                      "November", "December"]

            col1, col2 = st.columns(2)
            with col1:
                selected_year = st.selectbox("Select Year", years)
            with col2:
                selected_month_name = st.selectbox("Select Month", months)

            # Convert month name to number
            selected_month_num = months.index(selected_month_name) + 1

            # Filter DataFrame for the selected month and year
            monthly_df = df[(df['date'].dt.year == selected_year) & (df['date'].dt.month == selected_month_num)]

            if monthly_df.empty:
                st.warning(f"No expenses found for {selected_month_name}, {selected_year}.")
            else:
                st.write(f"### Dashboard for {selected_month_name}, {selected_year}")
                generate_dashboard(monthly_df)

    else:
        st.warning("No expenses found! Add some data to see the dashboard.")

elif choice == "Update Expense":
    st.subheader("✏️ Update Expense")
    df = view_expenses()
    if not df.empty:
        # Get a list of IDs for the selectbox
        expense_ids = df["id"].tolist()
        expense_id_to_update = st.selectbox("Select Expense to Update (by ID)", expense_ids)

        # Get the selected expense's data
        selected_expense = df[df["id"] == expense_id_to_update].iloc[0]

        # Pre-fill the form with the selected expense's data
        default_date = datetime.strptime(selected_expense["date"], "%Y-%m-%d").date()
        category_options = ["Food", "Transport", "Shopping", "Bills", "Other"]
        default_index = category_options.index(selected_expense["category"]) if selected_expense[
                                                                                    "category"] in category_options else 0

        with st.form("update_form"):
            date = st.date_input("Date", value=default_date)
            category = st.selectbox("Category", category_options, index=default_index)
            amount = st.number_input("Amount", value=float(selected_expense["amount"]), format="%.2f")
            description = st.text_area("Description", value=selected_expense["description"])

            if st.form_submit_button("Update Expense"):
                update_expense(expense_id_to_update, str(date), category, amount, description)
                st.success("Expense updated successfully!")
                st.rerun()

    else:
        st.warning("No expenses available to update.")

elif choice == "Delete Expense":
    st.subheader("🗑️ Delete Expense")
    df = view_expenses()
    if not df.empty:
        expense_ids = df["id"].tolist()
        expense_id_to_delete = st.selectbox("Select Expense to Delete (by ID)", expense_ids)

        st.warning(f"**Warning:** You are about to delete expense ID {expense_id_to_delete}.")

        if st.button("Confirm Deletion"):
            delete_expense(expense_id_to_delete)
            st.success("Expense deleted successfully!")
            st.rerun()

    else:
        st.warning("No expenses available to delete.")

elif choice == "Ask AI":
    st.subheader("🤖 Ask AI About Your Expenses")

    # --- API Key and Client Initialization ---
    load_dotenv()  # Load variables from .env file
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        st.warning("Groq API key not found. Please create a `.env` file and add `GROQ_API_KEY='your-key-here'`.")
        st.info("Alternatively, you can paste your key below for this session.")
        groq_api_key = st.text_input("Enter your Groq API Key:", type="password")
        if not groq_api_key:
            st.stop()

    client = groq.Groq(api_key=groq_api_key)

    # --- Data Loading and Chat Interface ---
    df = view_expenses()
    if df.empty:
        st.warning("No expense data found. Please add some expenses first before asking the AI.")
    else:
        # Convert dataframe to string format for the AI
        data_string = df.to_csv(index=False)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if prompt := st.chat_input("What is my biggest expense?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)

            # --- AI Response Generation ---
            with st.chat_message("assistant"):
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": f"""You are an expert financial analyst.
                                Your task is to answer questions about the user's expense data.
                                Analyze the following expense data, provided in CSV format, and answer the user's question based ONLY on this data.
                                Be helpful and provide clear, concise insights. Do not make up information.

                                Here is the expense data:
                                ```csv
                                {data_string}
                                ```
                                """
                            },
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        model="llama-3.3-70b-versatile",
                    )
                    response = chat_completion.choices[0].message.content
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"An error occurred: {e}")


