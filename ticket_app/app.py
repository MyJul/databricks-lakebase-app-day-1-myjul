"""
Professional IT Ticketing System
Databricks App with Lakebase (Postgres)
"""

import streamlit as st
from lakebase import get_connection
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="IT Support Ticketing System",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .ticket-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    .priority-critical {
        background: #ff4444;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .priority-high {
        background: #ff8800;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .priority-medium {
        background: #ffbb33;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .priority-low {
        background: #00C851;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .status-open {
        background: #2196F3;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
    }
    .status-in-progress {
        background: #ff9800;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
    }
    .status-resolved {
        background: #4CAF50;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
    }
    .status-closed {
        background: #9E9E9E;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# Database functions with priority support
def ensure_priority_column():
    """Add priority column if it doesn't exist"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            ALTER TABLE tickets 
            ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'Medium'
        """)
        conn.commit()
        cursor.close()


def get_tickets(status_filter=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if status_filter and status_filter != "All":
            cursor.execute("""
                SELECT ticket_id, title, status, priority, created_by, created_at
                FROM tickets
                WHERE status = %s
                ORDER BY 
                    CASE priority
                        WHEN 'Critical' THEN 1
                        WHEN 'High' THEN 2
                        WHEN 'Medium' THEN 3
                        WHEN 'Low' THEN 4
                    END,
                    created_at DESC
            """, (status_filter,))
        else:
            cursor.execute("""
                SELECT ticket_id, title, status, priority, created_by, created_at
                FROM tickets
                ORDER BY 
                    CASE priority
                        WHEN 'Critical' THEN 1
                        WHEN 'High' THEN 2
                        WHEN 'Medium' THEN 3
                        WHEN 'Low' THEN 4
                    END,
                    created_at DESC
            """)
        
        tickets = cursor.fetchall()
        cursor.close()
        return tickets


def get_ticket_stats():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Open' THEN 1 END) as open,
                COUNT(CASE WHEN status = 'In Progress' THEN 1 END) as in_progress,
                COUNT(CASE WHEN status = 'Resolved' THEN 1 END) as resolved,
                COUNT(CASE WHEN priority = 'Critical' THEN 1 END) as critical
            FROM tickets
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        return stats


def get_messages(ticket_id):
    with get_connection() as conn:
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


def create_ticket(title, status, priority, created_by, description=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tickets
            (title, status, priority, created_by)
            VALUES (%s, %s, %s, %s)
            RETURNING ticket_id
        """, (title, status, priority, created_by))
        ticket_id = cursor.fetchone()['ticket_id']
        
        # Add initial message if description provided
        if description:
            cursor.execute("""
                INSERT INTO ticket_messages
                (ticket_id, message_text, author)
                VALUES (%s, %s, %s)
            """, (ticket_id, description, created_by))
        
        conn.commit()
        cursor.close()
        return ticket_id


def add_message(ticket_id, message_text, author):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ticket_messages
            (ticket_id, message_text, author)
            VALUES (%s, %s, %s)
        """, (ticket_id, message_text, author))
        conn.commit()
        cursor.close()


def update_ticket(ticket_id, status=None, priority=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if status and priority:
            cursor.execute("""
                UPDATE tickets
                SET status = %s, priority = %s
                WHERE ticket_id = %s
            """, (status, priority, ticket_id))
        elif status:
            cursor.execute("""
                UPDATE tickets
                SET status = %s
                WHERE ticket_id = %s
            """, (status, ticket_id))
        elif priority:
            cursor.execute("""
                UPDATE tickets
                SET priority = %s
                WHERE ticket_id = %s
            """, (priority, ticket_id))
        conn.commit()
        cursor.close()


def get_priority_color(priority):
    colors = {
        "Critical": "priority-critical",
        "High": "priority-high",
        "Medium": "priority-medium",
        "Low": "priority-low"
    }
    return colors.get(priority, "priority-medium")


def get_status_color(status):
    colors = {
        "Open": "status-open",
        "In Progress": "status-in-progress",
        "Resolved": "status-resolved",
        "Closed": "status-closed"
    }
    return colors.get(status, "status-open")


# Initialize database
ensure_priority_column()

# Sidebar
with st.sidebar:
    st.title("🎫 IT Support")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "➕ Create Ticket", "🔍 View Ticket"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Filters")
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Open", "In Progress", "Resolved", "Closed"]
    )


# Main content
if "📊 Dashboard" in page:
    st.title("📊 IT Support Dashboard")
    
    # Statistics
    stats = get_ticket_stats()
    if stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Tickets", stats['total'])
        with col2:
            st.metric("Open", stats['open'], delta=None)
        with col3:
            st.metric("In Progress", stats['in_progress'])
        with col4:
            st.metric("Resolved", stats['resolved'])
        with col5:
            st.metric("🔥 Critical", stats['critical'])
    
    st.markdown("---")
    
    # Ticket list
    st.subheader(f"Tickets {f'({status_filter})' if status_filter != 'All' else ''}")
    
    tickets = get_tickets(status_filter)
    
    if tickets:
        for ticket in tickets:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"### 🎫 #{ticket['ticket_id']} - {ticket['title']}")
                    st.caption(f"Created by {ticket['created_by']} • {ticket['created_at'].strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    st.markdown(
                        f"<span class='{get_status_color(ticket['status'])}'>{ticket['status']}</span>",
                        unsafe_allow_html=True
                    )
                
                with col3:
                    st.markdown(
                        f"<span class='{get_priority_color(ticket['priority'])}'>{ticket['priority']}</span>",
                        unsafe_allow_html=True
                    )
                
                st.markdown("---")
    else:
        st.info("No tickets found.")


elif "➕ Create Ticket" in page:
    st.title("➕ Create New Ticket")
    
    with st.form("create_ticket_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Ticket Title *", placeholder="Brief description of the issue")
            created_by = st.text_input("Your Name *", placeholder="John Doe")
            priority = st.selectbox(
                "Priority *",
                ["Low", "Medium", "High", "Critical"],
                index=1
            )
        
        with col2:
            status = st.selectbox(
                "Initial Status",
                ["Open", "In Progress"],
                index=0
            )
        
        description = st.text_area(
            "Description",
            placeholder="Provide detailed information about the issue...",
            height=200
        )
        
        submitted = st.form_submit_button("🎫 Create Ticket", use_container_width=True)
        
        if submitted:
            if title and created_by:
                ticket_id = create_ticket(title, status, priority, created_by, description)
                st.success(f"✅ Ticket #{ticket_id} created successfully!")
                st.balloons()
            else:
                st.error("Please fill in all required fields (marked with *)")


elif "🔍 View Ticket" in page:
    st.title("🔍 View Ticket Details")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticket_id = st.number_input(
            "Enter Ticket ID",
            min_value=1,
            step=1,
            help="Enter the ticket number you want to view"
        )
    
    if st.button("🔍 Load Ticket", use_container_width=False):
        tickets = get_tickets()
        ticket = next((t for t in tickets if t['ticket_id'] == ticket_id), None)
        
        if ticket:
            st.markdown("---")
            
            # Ticket header
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"## 🎫 #{ticket['ticket_id']} - {ticket['title']}")
            with col2:
                st.markdown(
                    f"<span class='{get_status_color(ticket['status'])}'>{ticket['status']}</span>",
                    unsafe_allow_html=True
                )
            with col3:
                st.markdown(
                    f"<span class='{get_priority_color(ticket['priority'])}'>{ticket['priority']}</span>",
                    unsafe_allow_html=True
                )
            
            st.caption(f"Created by {ticket['created_by']} • {ticket['created_at'].strftime('%Y-%m-%d %H:%M')}")
            
            # Update section
            st.markdown("---")
            st.subheader("Update Ticket")
            
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox(
                    "Update Status",
                    ["Open", "In Progress", "Resolved", "Closed"],
                    index=["Open", "In Progress", "Resolved", "Closed"].index(ticket['status'])
                )
            with col2:
                new_priority = st.selectbox(
                    "Update Priority",
                    ["Low", "Medium", "High", "Critical"],
                    index=["Low", "Medium", "High", "Critical"].index(ticket['priority'])
                )
            
            if st.button("💾 Update Ticket"):
                update_ticket(ticket_id, new_status, new_priority)
                st.success("Ticket updated successfully!")
                st.rerun()
            
            # Messages section
            st.markdown("---")
            st.subheader("💬 Conversation")
            
            messages = get_messages(ticket_id)
            
            if messages:
                for msg in messages:
                    with st.chat_message("user"):
                        st.markdown(f"**{msg['author']}** • {msg['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.markdown(msg['message_text'])
            else:
                st.info("No messages yet.")
            
            # Add message
            st.markdown("---")
            with st.form("add_message_form"):
                st.subheader("➕ Add Message")
                author = st.text_input("Your Name")
                message_text = st.text_area("Message", height=100)
                
                if st.form_submit_button("📤 Send Message"):
                    if author and message_text:
                        add_message(ticket_id, message_text, author)
                        st.success("Message added!")
                        st.rerun()
                    else:
                        st.error("Please fill in all fields")
        else:
            st.error(f"Ticket #{ticket_id} not found.")
