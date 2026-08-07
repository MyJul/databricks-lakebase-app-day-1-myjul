"""

Databricks App boilerplate:
- Reads/writes to Lakebase (Databricks-managed Postgres) via lakebase.py

Run locally:
    python app.py
Deploy as a Databricks App using app.yaml.
"""

import streamlit as st
from lakebase import get_connection


# Create database connection
conn = get_connection()


def get_tickets():
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ticket_id, title, status, created_by, created_at
        FROM tickets
        ORDER BY ticket_id
    """)

    tickets = cursor.fetchall()
    cursor.close()

    return tickets


def get_messages(ticket_id):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT author, message_text, created_at
        FROM ticket_messages
        WHERE ticket_id = %s
        ORDER BY created_at
    """, (ticket_id,))

    messages = cursor.fetchall()
    cursor.close()

    return messages


def create_ticket(title, status, created_by):
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tickets
        (title, status, created_by)
        VALUES (%s, %s, %s)
    """,
    (title, status, created_by))

    conn.commit()
    cursor.close()


def add_message(ticket_id, message_text, author):
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ticket_messages
        (ticket_id, message_text, author)
        VALUES (%s, %s, %s)
    """,
    (ticket_id, message_text, author))

    conn.commit()
    cursor.close()


def update_status(ticket_id, status):
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status = %s
        WHERE ticket_id = %s
    """,
    (status, ticket_id))

    conn.commit()
    cursor.close()



# -----------------------------
# Streamlit App
# -----------------------------

st.title("Support Ticket App")


# View tickets

st.header("All Tickets")

tickets = get_tickets()

for ticket in tickets:
    st.write(
        f"#{ticket[0]} - {ticket[1]} - {ticket[2]}"
    )


# Select ticket

st.header("View Ticket Messages")

ticket_id = st.number_input(
    "Enter Ticket ID",
    min_value=1,
    step=1
)

if st.button("View Messages"):

    messages = get_messages(ticket_id)

    for message in messages:
        st.write(
            f"{message[0]}: {message[1]}"
        )



# Create ticket

st.header("Create New Ticket")

title = st.text_input("Ticket Title")

created_by = st.text_input("Created By")


if st.button("Create Ticket"):

    create_ticket(
        title,
        "Open",
        created_by
    )

    st.success("Ticket created!")



# Add message

st.header("Add Message")

message_ticket = st.number_input(
    "Ticket ID",
    min_value=1,
    step=1,
    key="message"
)

author = st.text_input("Author")

message_text = st.text_area("Message")


if st.button("Submit Message"):

    add_message(
        message_ticket,
        message_text,
        author
    )

    st.success("Message added!")



# Update status

st.header("Update Ticket Status")

status_ticket = st.number_input(
    "Ticket ID",
    min_value=1,
    step=1,
    key="status"
)

new_status = st.selectbox(
    "New Status",
    [
        "Open",
        "In Progress",
        "Resolved",
        "Closed"
    ]
)


if st.button("Update Status"):

    update_status(
        status_ticket,
        new_status
    )

    st.success("Status updated!")
