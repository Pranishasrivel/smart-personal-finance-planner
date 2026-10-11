import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

st.set_page_config(page_title="Smart Budget Planner", layout="wide")

# Helper functions for database operations
def run_query(query, params=()):
    with sqlite3.connect("budget_tracker.db") as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_db_command(command, params=()):
    with sqlite3.connect("budget_tracker.db") as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(command, params)
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

# --- 🔐 STREAMLIT SESSION STATE LOGIN HANDLING ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'Login' # Default view

# View 1: Authentication Screen (Login / Sign Up)
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Toggle buttons between Login and Sign Up
        auth_toggle = st.segmented_control(
            "Select Action", 
            options=["Login", "Sign Up"], 
            default=st.session_state['auth_mode']
        )
        if auth_toggle:
            st.session_state['auth_mode'] = auth_toggle

        if st.session_state['auth_mode'] == 'Login':
            st.markdown("<h2 style='text-align: center;'>🔐 Secure Portal Login</h2>", unsafe_allow_html=True)
            username_input = st.text_input("Username", key="login_user")
            password_input = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Sign In", type="primary", use_container_width=True):
                user_check = run_query(
                    "SELECT * FROM users WHERE username=? AND password=?", 
                    (username_input, password_input)
                )
                if not user_check.empty:
                    st.session_state['logged_in'] = True
                    st.success("Access Granted! Loading your dashboard...")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password. Please try again.")
                    
        else: # Sign Up View
            st.markdown("<h2 style='text-align: center;'>📝 Create New Account</h2>", unsafe_allow_html=True)
            new_user = st.text_input("Choose Username", key="reg_user")
            new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm")
            
            if st.button("Register Account", type="primary", use_container_width=True):
                if not new_user or not new_pass:
                    st.warning("Username and Password fields cannot be empty.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match. Please re-enter.")
                else:
                    # Insert the new user into the database
                    success = execute_db_command(
                        "INSERT INTO users (username, password) VALUES (?, ?)",
                        (new_user, new_pass)
                    )
                    if success:
                        st.success("Registration Successful! You can now switch to the 'Login' tab to sign in.")
                        st.session_state['auth_mode'] = 'Login'
                    else:
                        st.error("This username is already taken. Please pick another one.")
                        
    st.stop() # Stops execution here if the user is not authenticated

# --- View 2: Your Original Budget Dashboard (Runs only if logged_in is True) ---

col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("💰 Smart Personal Finance & Budget Planner")
with col_logout:
    st.write("") 
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

st.markdown("---")

# Fetch Categories for the dropdown selection
categories_df = run_query("SELECT id, name, monthly_limit FROM categories")
category_list = categories_df['name'].tolist()

tab1, tab2 = st.tabs(["📊 Live Analytics Dashboard", "➕ Log New Expenditure"])

with tab1:
    st.subheader("Your Monthly Summary")
    
    expenses_df = run_query('''
        SELECT e.id, c.name as Category, e.amount as [Amount (₹)], e.date as Date, e.description as Description 
        FROM expenses e 
        JOIN categories c ON e.category_id = c.id
        ORDER BY e.date DESC
    ''')
    
    if not expenses_df.empty:
        total_spent = expenses_df['Amount (₹)'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Expenses Logged", value=f"₹{total_spent:,.2f}")
        with col2:
            st.metric(label="Active Tracking Categories", value=len(category_list))
            
        st.markdown("### Spending Analytics")
        col_chart, col_table = st.columns([1, 1])
        
        with col_chart:
            fig = px.pie(
                expenses_df, 
                values='Amount (₹)', 
                names='Category', 
                title="Distribution of Expenses by Category",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        with col_table:
            st.markdown("##### Detailed Transaction History")
            st.dataframe(expenses_df[["Date", "Category", "Amount (₹)", "Description"]], use_container_width=True, hide_index=True)
            
            # Export to CSV feature
            csv_buffer = io.StringIO()
            expenses_df[["Date", "Category", "Amount (₹)", "Description"]].to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode('utf-8')
            
            st.download_button(
                label="📥 Export Expense Report (CSV)",
                data=csv_bytes,
                file_name=f"Budget_Report_{datetime.today().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("No expenses recorded yet. Switch to the 'Log New Expenditure' tab to add your first transaction!")

with tab2:
    st.subheader("Log a New Expenditure")
    
    selected_cat = st.selectbox("Select Category", category_list)
    amount = st.number_input("Amount (INR)", min_value=0.0, step=50.0, format="%.2f")
    date_selected = st.date_input("Date of Expense", datetime.today())
    description = st.text_input("Short Description")
    
    if st.button("Save Transaction", type="primary"):
        if amount > 0:
            cat_id = int(categories_df[categories_df['name'] == selected_cat]['id'].values[0])
            execute_db_command(
                "INSERT INTO expenses (category_id, amount, date, description) VALUES (?, ?, ?, ?)",
                (cat_id, amount, str(date_selected), description)
            )
            st.success(f"Successfully saved ₹{amount:,.2f} under '{selected_cat}'!")
            st.balloons()
        else:
            st.warning("Please enter an amount greater than zero.")