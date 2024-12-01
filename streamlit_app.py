from collections import defaultdict
from pathlib import Path
import sqlite3
import os

import streamlit as st
import altair as alt
import pandas as pd

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="Wrenchman Service Provider",
    page_icon=":wrench:",  # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

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
                    ("Engine Oil Change", 600.00, 100.00, 400.00, 35, 10, 10, "Engine oil replacement"),
                    ("Brake Pad Replacement", 1000.00, 200.00, 600.00, 20, 8, 10, "Brake pad replacement service"),
                    ("Spark Plug Replacement", 200.00, 50.00, 100.00, 30, 12, 5, "Replacement of spark plug"),
                    ("Tire Replacement (Front)", 1200.00, 100.00, 900.00, 12, 5, 5, "Replacement of front tire"),
                    ("Tire Replacement (Rear)", 1500.00, 100.00, 1100.00, 10, 5, 5, "Replacement of rear tire"),
                    ("Battery Replacement", 2500.00, 150.00, 2000.00, 8, 3, 3, "Replacement of battery"),
                    ("Chain Replacement", 800.00, 100.00, 500.00, 15, 7, 5, "Chain replacement service"),
                    ("Headlight Replacement", 600.00, 50.00, 400.00, 10, 5, 5, "Headlight replacement"),
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

# Balance Sheet Tables for Assets, Liabilities, and Equity

# Initial data for the tables
def get_database_connection():
    """
    Create and return a new SQLite connection.
    """
    return sqlite3.connect("finance_data.db")

def create_balance_sheet_tables():
    """
    Create tables in the database if they do not already exist.
    """
    conn = get_database_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            value REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Liabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            value REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Equity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            value REAL
        )
    """)
    conn.commit()
    conn.close()

def update_balance_sheet_data():
    """
    Save Assets, Liabilities, and Equity data to the database.
    """
    conn = get_database_connection()
    cursor = conn.cursor()

    # Update Assets data
    cursor.execute("DELETE FROM Assets")
    for _, row in st.session_state.assets_data.iterrows():
        cursor.execute("INSERT INTO Assets (name, value) VALUES (?, ?)", (row["Asset Name"], row["Value (₹)"]))

    # Update Liabilities data
    cursor.execute("DELETE FROM Liabilities")
    for _, row in st.session_state.liabilities_data.iterrows():
        cursor.execute("INSERT INTO Liabilities (name, value) VALUES (?, ?)", (row["Liability Name"], row["Value (₹)"]))

    # Update Equity data
    cursor.execute("DELETE FROM Equity")
    for _, row in st.session_state.equity_data.iterrows():
        cursor.execute("INSERT INTO Equity (name, value) VALUES (?, ?)", (row["Equity Name"], row["Value (₹)"]))

    conn.commit()
    conn.close()
    st.success("Balance sheet data saved successfully!")

# Initialize database
create_balance_sheet_tables()

# Initial data for the tables
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
        {"Equity Name": ["Capital", "Net Profit of CY", "Reserves"], "Value (₹)": [ 50000 ,  467000,  2636060]}
    )

if "profit_loss_data" not in st.session_state:
    st.session_state.profit_loss_data = pd.DataFrame(
        {
            "Particulars": [
                "Opening Stock of Spare Parts", "Purchase of Spare Parts", "Gross Profit",
                "Revenue from Services", "Closing stock of Spare Parts", "License fees",
                "Electricity", "Waste water treatment", "Salary and Wages", "Depreciation",
                "Scrap disposal and Misc", "Net Profit"
            ],
            "Value (₹)": [
                1150000, 3118500, 2229000, 5197500, 1300000, 275000, 280000, 187000, 828000,
                72000, 120000, 467000
            ]
        }
    )

st.subheader("Manage Balance Sheet")

st.info(
    """
    Use the  Balance Sheet to add, remove, and edit asset, equities & liabilities.
    """
)

# Editable Assets Table
st.write("### Assets")
st.session_state.assets_data = st.data_editor(
    st.session_state.assets_data,
    key="assets_table",
    num_rows="dynamic",
    use_container_width=True,
    column_config={"Value (₹)": st.column_config.NumberColumn(format="₹%.2f")},
)

# Editable Liabilities Table
st.write("### Liabilities")
st.session_state.liabilities_data = st.data_editor(
    st.session_state.liabilities_data,
    key="liabilities_table",
    num_rows="dynamic",
    use_container_width=True,
    column_config={"Value (₹)": st.column_config.NumberColumn(format="₹%.2f")},
)

# Editable Equity Table
st.write("### Equity")
st.session_state.equity_data = st.data_editor(
    st.session_state.equity_data,
    key="equity_table",
    num_rows="dynamic",
    use_container_width=True,
    column_config={"Value (₹)": st.column_config.NumberColumn(format="₹%.2f")},
)

def format_currency(value):
    """Format a number as Indian currency with commas."""
    return f"₹{value:,.2f}"

# -----------------------------------------------------------------------------
# Final Table: Relation Between Assets, Liabilities, and Equity

def validate_balance_sheet():
    """
    Function to validate the balance sheet and return the summary data.
    """
    total_assets = st.session_state.assets_data["Value (₹)"].sum()
    total_liabilities = st.session_state.liabilities_data["Value (₹)"].sum()
    total_equity = st.session_state.equity_data["Value (₹)"].sum()

    # Calculate the difference for validation
    difference = total_assets - (total_liabilities + total_equity)

    summary_table = pd.DataFrame(
        {
            "Category": ["Total Assets", "Total Liabilities", "Total Equity", "Difference"],
            "Value (₹)": [total_assets, total_liabilities, total_equity, difference],
        }
    )

    return summary_table, difference

st.subheader("Financial Summary")

# Generate validation summary table
summary_table, difference = validate_balance_sheet()
st.table(summary_table)

# Display validation results
if difference != 0:
    st.warning(f"There is a mismatch of ₹{difference:,.2f} between Assets and the sum of Liabilities and Equity.")
else:
    st.success("The Balance Sheet is balanced: Assets = Liabilities + Equity")

# -----------------------------------------------------------------------------
# Save Changes Buttons
if st.button("Save Balance Sheet Changes"):
    update_balance_sheet_data()


st.write("### Profit and Loss Statement")
profit_loss_display = st.session_state.profit_loss_data.copy()
profit_loss_display["Value (₹)"] = profit_loss_display["Value (₹)"].apply(format_currency)
st.table(profit_loss_display)

excel_file_path = 'balanceSheet.xlsx' 

# Function to allow users to download the Excel file
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


# Allow the user to download the Excel file
allow_download_excel(excel_file_path)

st.title("Inventory Details")

# Connect to database and create table if needed
conn, db_was_just_created = connect_db()

# Initialize data if the database was just created
if db_was_just_created:
    initialize_data(conn)

# Load data from database
df = load_data(conn)

# Display data with editable table
edited_df = st.data_editor(
    df,
    disabled=["id"],  # Don't allow editing the 'id' column.
    num_rows="dynamic",  # Allow appending/deleting rows.
    column_config={
        "price": st.column_config.NumberColumn(format="₹%.2f"),
        "labor_cost": st.column_config.NumberColumn(format="₹%.2f"),
        "parts_cost": st.column_config.NumberColumn(format="₹%.2f"),
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

# -----------------------------------------------------------------------------
# Now some charts for insights.

st.subheader("Inventory to reorder")

need_to_reorder = df[df["units_left"] < df["reorder_point"]].loc[:, "item_name"]

if len(need_to_reorder) > 0:
    items = "\n".join(f"* {name}" for name in need_to_reorder)
    st.error(f"We're running low on the following items:\n {items}")

st.altair_chart(
    alt.Chart(df)
    .mark_bar(orient="horizontal")
    .encode(
        x="units_left",
        y="item_name",
    )
    + alt.Chart(df)
    .mark_point(
        shape="diamond",
        filled=True,
        size=50,
        color="salmon",
        opacity=1,
    )
    .encode(
        x="reorder_point",
        y="item_name",
    ),
    use_container_width=True,
)

st.caption("NOTE: The :diamonds: location shows the reorder point.")

# -----------------------------------------------------------------------------
# Top services chart

st.subheader("Top Services")

st.altair_chart(
    alt.Chart(df)
    .mark_bar(orient="horizontal")
    .encode(
        x="units_used",
        y=alt.Y("item_name", sort="-x")
    ),
    use_container_width=True,
)

# Footer 
st.markdown(
    """
    ### Shop Details
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