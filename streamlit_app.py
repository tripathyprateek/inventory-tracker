import os
import sqlite3
from pathlib import Path
from collections import defaultdict
import pandas as pd
import streamlit as st
import altair as alt

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="Wrenchman Service Provider",
    page_icon=":wrench:",  # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Draw the actual page, starting with the repair items table.

# Set the title that appears at the top of the page.
st.title(":wrench: The Wrenchman Service Provider :wrench:")

st.write("**Welcome to the cost accounting tracker for Bosch 2-wheeler Service Provider!**")
st.write("""
This project provides insights into the cost and operational aspects of running a 2 wheeler service business in the repair industry.

The Wrenchman is located in District Center, Chandrashekharpur, Bhubaneswar.

This shop is owned and operated by Lal Rajesh Shah Deo and he's in this
business for the last 29 years. He has been providing services to all brands of 2 wheelers under
his expertise and has built his reputation over time in this industry.

""")

# Check if image exists before loading
if os.path.exists("image.jpeg"):
    st.image("image.jpeg", caption="The Wrenchman Service Provider", use_container_width=True)
else:
    st.warning("Image file 'image.jpeg' not found.")

# -----------------------------------------------------------------------------
# Database Management Functions

DB_FILENAME = "repair_shop.db"


def connect_db():
    """Connects to the sqlite database."""
    DB_FILENAME = Path(__file__).parent / "repair_shop.db"
    db_already_exists = DB_FILENAME.exists()

    conn = sqlite3.connect(DB_FILENAME)
    db_was_just_created = not db_already_exists

    return conn, db_was_just_created


def initialize_data(conn):
    """Initializes the Service Provider database with some data if it's newly created."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                price REAL,
                labor_cost REAL,
                parts_cost REAL,
                units_used INTEGER,
                units_left INTEGER,
                reorder_point INTEGER,
                description TEXT
            )
            """
        )

        # Check if sample data already exists to avoid duplication
        cursor.execute("SELECT COUNT(*) FROM repairs")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                """
                INSERT INTO repairs
                    (item_name, price, labor_cost, parts_cost, units_used, units_left, reorder_point, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("Engine Oil Change", 600, 100, 400, 35, 10, 10, "Engine oil replacement"),
                    ("Brake Pad Replacement", 1000, 200, 600, 20, 8, 10, "Brake pad replacement service"),
                    ("Spark Plug Replacement", 200, 50, 100, 30, 12, 5, "Replacement of spark plug"),
                    ("Tire Replacement (Front)", 1200, 100, 900, 12, 5, 5, "Replacement of front tire"),
                    ("Tire Replacement (Rear)", 1500, 100, 1100, 10, 5, 5, "Replacement of rear tire"),
                    ("Battery Replacement", 2500, 150, 2000, 8, 3, 3, "Replacement of battery"),
                    ("Chain Replacement", 800, 100, 500, 15, 7, 5, "Chain replacement service"),
                    ("Headlight Replacement", 600, 50, 400, 10, 5, 5, "Headlight replacement"),
                ],
            )
            conn.commit()
            st.toast("Database initialized with sample data.")
    except Exception as e:
        st.error(f"Error initializing database: {e}")

def load_data(conn):
    """Loads the Service Provider data from the database."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repairs")
        data = cursor.fetchall()
        df = pd.DataFrame(
            data,
            columns=[
                "id",
                "item_name",
                "price",
                "labor_cost",
                "parts_cost",
                "units_used",
                "units_left",
                "reorder_point",
                "description",
            ],
        )
        return df
    except Exception as e:
        st.error(f"Error loading data from database: {e}")
        return pd.DataFrame()

def update_data(conn, df, changes):
    """Updates the Service Provider data in the database."""
    cursor = conn.cursor()

    if changes["edited_rows"]:
        deltas = st.session_state.repair_table["edited_rows"]
        rows = []

        for i, delta in deltas.items():
            row_dict = df.iloc[i].to_dict()
            row_dict.update(delta)
            rows.append(row_dict)

        cursor.executemany(
            """
            UPDATE repairs
            SET
                item_name = :item_name,
                price = :price,
                labor_cost = :labor_cost,
                parts_cost = :parts_cost,
                units_used = :units_used,
                units_left = :units_left,
                reorder_point = :reorder_point,
                description = :description
            WHERE id = :id
            """,
            rows,
        )

    if changes["added_rows"]:
        cursor.executemany(
            """
            INSERT INTO repairs
                (item_name, price, labor_cost, parts_cost, units_used, units_left, reorder_point, description)
            VALUES
                (:item_name, :price, :labor_cost, :parts_cost, :units_used, :units_left, :reorder_point, :description)
            """,
            (defaultdict(lambda: None, row) for row in changes["added_rows"]),
        )

    if changes["deleted_rows"]:
        cursor.executemany(
            "DELETE FROM repairs WHERE id = :id",
            ({"id": int(df.loc[i, "id"])} for i in changes["deleted_rows"]),
        )

    conn.commit()

# ---------------------------------------------------------------------
# Manage Balance Sheet Tab
def manage_balance_sheet():

    if "assets_data" not in st.session_state:
        st.session_state.assets_data = pd.DataFrame(
            {"Asset Name": ["Land", "Building", "Machinery", "Inventory of Service Parts", "Trade Receivables", "Cash and Cash Equivalents"], 
             "Value (₹)": [200000,  288000,  1440000,  1300000,  311850,  548760]}
        )

    if "liabilities_data" not in st.session_state:
        st.session_state.liabilities_data = pd.DataFrame(
            {"Liability Name": ["Creditors"], "Value (₹)": [ 935550]}
        )

    if "equity_data" not in st.session_state:
        st.session_state.equity_data = pd.DataFrame(
            {"Equity Name": ["Capital", "Net Profit of CY", "Reserves"], "Value (₹)": [ 50000 , 467000, 2636060]}
        )

    st.write("### Assets")
    st.session_state.assets_data = st.data_editor(
        st.session_state.assets_data,
        key="assets_table",
        num_rows="dynamic",
        use_container_width=True,
    )

    st.write("### Liabilities")
    st.session_state.liabilities_data = st.data_editor(
        st.session_state.liabilities_data,
        key="liabilities_table",
        num_rows="dynamic",
        use_container_width=True,
    )

    st.write("### Equity")
    st.session_state.equity_data = st.data_editor(
        st.session_state.equity_data,
        key="equity_table",
        num_rows="dynamic",
        use_container_width=True,
    )

    # Validation and financial summary
    total_assets = st.session_state.assets_data["Value (₹)"].sum()
    total_liabilities = st.session_state.liabilities_data["Value (₹)"].sum()
    total_equity = st.session_state.equity_data["Value (₹)"].sum()
    difference = total_assets - (total_liabilities + total_equity)

    summary_table = pd.DataFrame(
        {"Category": ["Total Assets", "Total Liabilities", "Total Equity", "Difference"],
         "Value (₹)": [total_assets, total_liabilities, total_equity, difference]})

    st.table(summary_table)

    if difference != 0:
        st.warning(f"There is a mismatch of ₹{difference:,.0f} between Assets and the sum of Liabilities and Equity.")
    else:
        st.success("The Balance Sheet is balanced: Assets = Liabilities + Equity")

excel_file_path = 'balanceSheet.xlsx' 
def allow_download_excel(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)
    
    # Provide a download button for the file
    with open(file_path, 'rb') as file:
        st.download_button(
            label="Download Balance Sheet Excel file", 
            data=file, 
            file_name="balanceSheet.xlsx",  # You can change the filename here
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
allow_download_excel(excel_file_path)
        


# ---------------------------------------------------------------------
# Inventory Details Tab
def inventory_details():
    st.subheader("Inventory Details")

    conn, _ = connect_db()
    df = load_data(conn)

    edited_df = st.data_editor(
        df,
        disabled=["id"],  # Don't allow editing the 'id' column.
        num_rows="dynamic",  # Allow appending/deleting rows.
        column_config={
            "price": st.column_config.NumberColumn(format="₹%.0f"),
            "labor_cost": st.column_config.NumberColumn(format="₹%.0f"),
            "parts_cost": st.column_config.NumberColumn(format="₹%.0f"),
        },
        key="repair_table",
    )

    has_uncommitted_changes = any(len(v) for v in st.session_state.repair_table.values())

    st.button(
        "Commit changes",
        type="primary",
        disabled=not has_uncommitted_changes,
        # Update data in database
        on_click=update_data,
        args=(conn, df, st.session_state.repair_table),
    )

    


# ---------------------------------------------------------------------
# Shop Details Tab
def shop_details():

    st.markdown(
        """
        📞 **Contact**: [09338474750](tel:09338474750)  -  Lal Rajesh Shah Deo 
        
        📍 **Location**: [View on Google Maps](https://www.google.com/maps/place/The+WrenchMan+Honda+Service/@20.3253636,85.819295,17.83z/data=!4m6!3m5!1s0x3a190987b1b7c1c5:0xbe6d62beda1b73b1!8m2!3d20.3253846!4d85.8192934!16s%2Fg%2F11j9f6xh5f?entry=ttu&g_ep=EgoyMDI0MTEwNi4wIKXMDSoASAFQAw%3D%3D)  
        
        👥 **Group Members**:
        - Ankita Priyadarshini (UM24329)
        - Hrushikesh Wasudeo Umalkar (UM24350)
        - Kshatriya Ameya Anil (UM24353)
        - Kulkarni Prathamesh Milind (UM24354)
        - Prateek Tripathy (UM24360)
        """
    )

    # Embed Google Maps iframe with the pinned location
    st.components.v1.iframe(
        src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d609.915711848547!2d85.8192934!3d20.3253846!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3a190987b1b7c1c5%3A0xbe6d62beda1b73b1!2sThe%20WrenchMan%20Honda%20Service!5e0!3m2!1sen!2sin!4v1699618898505!5m2!1sen!2sin",
        width=700,
        height=400,
        scrolling=False,
    )

# Function to generate the Profit and Loss Statement
def display_profit_and_loss():
    # Create a sample Profit and Loss Statement data
    profit_loss_data = pd.DataFrame({
        "Particulars": [
            "Opening Stock of Spare Parts", "Purchase of  Spare Parts", "Gross profit","Total",
            "", "License fees", "Electricity", "Waste water treatment", "Salary and Wages", "Depreciation",
            "Scrap disposal and Misc", "", "Net Profit", "Total"
        ],
        "Value (₹)": [
            1150000, 3118500, 2229000, 6497500, " ",  275000,  280000,  187000,  828000,  72000,  120000, " ",  467000,  2229000
        ]
    })

    revenues = pd.DataFrame({
        "Particulars":[
            "Revenue from Services", "Closing stock of Spare Parts", "Total","Gross Profit c/d", "Total"
        ],
        "Value (₹)":[
             5197500, 1300000, 6497500,  2229000,  2229000
        ]
    })

    # Display the data as a table
    st.write("Below is the detailed Profit and Loss Statement:")
    st.table(profit_loss_data)
    st.table(revenues)

# ---------------------------------------------------------------------
# Main Application Logic

# Tabs for the different sections
tab1, tab2, tab3, tab4 = st.tabs(["Manage Balance Sheet", "Profit & Loss","Inventory Details", "Shop Details"])

with tab1:
    manage_balance_sheet()

with tab2:
    display_profit_and_loss()

with tab3:
    inventory_details()

with tab4:
    shop_details()