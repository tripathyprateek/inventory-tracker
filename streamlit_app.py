from collections import defaultdict
from pathlib import Path
import sqlite3

import streamlit as st
import altair as alt
import pandas as pd


# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="2-Wheeler Service Provider",
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
    """Initializes the repair shop database with some data."""
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

    cursor.execute(
        """
        INSERT INTO repairs
            (item_name, price, labor_cost, parts_cost, units_used, units_left, reorder_point, description)
        VALUES
            -- Common Repair Items
            ('Engine Oil Change', 600.00, 100.00, 400.00, 35, 10, 10, 'Engine oil replacement'),
            ('Brake Pad Replacement', 1000.00, 200.00, 600.00, 20, 8, 10, 'Brake pad replacement service'),
            ('Spark Plug Replacement', 200.00, 50.00, 100.00, 30, 12, 5, 'Replacement of spark plug'),
            ('Tire Replacement (Front)', 1200.00, 100.00, 900.00, 12, 5, 5, 'Replacement of front tire'),
            ('Tire Replacement (Rear)', 1500.00, 100.00, 1100.00, 10, 5, 5, 'Replacement of rear tire'),
            ('Battery Replacement', 2500.00, 150.00, 2000.00, 8, 3, 3, 'Replacement of battery'),
            ('Chain Replacement', 800.00, 100.00, 500.00, 15, 7, 5, 'Chain replacement service'),
            ('Headlight Replacement', 600.00, 50.00, 400.00, 10, 5, 5, 'Headlight replacement')
        """
    )
    conn.commit()


def load_data(conn):
    """Loads the repair shop data from the database."""
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM repairs")
        data = cursor.fetchall()
    except:
        return None

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


def update_data(conn, df, changes):
    """Updates the repair shop data in the database."""
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
                (id, item_name, price, labor_cost, parts_cost, units_used, units_left, reorder_point, description)
            VALUES
                (:id, :item_name, :price, :labor_cost, :parts_cost, :units_used, :units_left, :reorder_point, :description)
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
"""
# :wrench: The Wrenchman Repair Shop :wrench:

**Welcome to the cost accounting tracker for Bosch 2-wheeler repair shop!**"""
"""
This project provides practical insights into the operational aspects of 
running a small service business in the two-wheeler industry.
"""
"""
So lets go to know a little bit more about this tiny shop called The Wrenchman located in
District Center, Chandrashekharpur, Bhubaneswar.
This shop is owned and operated by Lal Rajesh Shah Deo and he's in this
business for the last 29 years. He has been providing services to all brands of 2 wheelers under
his expertise and has built his reputation over time in this industry.
"""


st.image("image.jpeg", caption="The Wrenchman Repair Shop", use_container_width=True)


st.info(
    """
    Use the Cost Balance Sheet to add, remove, and edit repair items and costs.
    And don't forget to commit your changes when you're done.
    """
)

# Connect to database and create table if needed
conn, db_was_just_created = connect_db()

# Initialize data.
if db_was_just_created:
    initialize_data(conn)
    st.toast("Database initialized with some sample data.")

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

# Add some space
""
""
""


st.subheader("Inventory Level and Reordering", divider="red")

need_to_reorder = df[df["units_left"] < df["reorder_point"]].loc[:, "item_name"]

if len(need_to_reorder) > 0:
    items = "\n".join(f"* {name}" for name in need_to_reorder)

    st.error(f"We're running low on the following items:\n {items}")

""
""

st.altair_chart(
    # Layer 1: Bar chart.
    alt.Chart(df)
    .mark_bar(orient="horizontal")
    .encode(
        x="units_left",
        y="item_name",
    )
    # Layer 2: Chart showing the reorder point.
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

""
""
""

# -----------------------------------------------------------------------------

st.subheader("Top Services", divider="orange")

""
""

st.altair_chart(
    alt.Chart(df)
    .mark_bar(orient="horizontal")
    .encode(
        x="units_used",
       y=alt.Y("item_name", sort="-x")
    ),
    use_container_width=True,
)

