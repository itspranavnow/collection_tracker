import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="Ganesh Chavithi Chanda Tracker",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for festive styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B35, #F7931E, #FFD700, #FF6B35);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .summary-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .summary-card h3 {
        color: #FFD700;
        margin-bottom: 0.5rem;
    }
    
    .summary-card .amount {
        font-size: 2rem;
        font-weight: bold;
        color: #FFD700;
    }
    
    .status-paid {
        background-color: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-due {
        background-color: #f44336;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .type-badge {
        background: linear-gradient(45deg, #FF6B35, #F7931E);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        color: #262730;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #FF6B35, #F7931E);
        color: white;
    }
    
    .search-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #FF6B35;
        margin-bottom: 1rem;
    }
    
    .filter-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🕉️ Ganesh Chavithi Chanda Tracker 🕉️</div>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load data from Excel files. collections.xlsx is required; expenses.xlsx is optional."""
    # Required: collections.xlsx
    try:
        collections_df = pd.read_excel('collections.xlsx')
    except FileNotFoundError:
        st.error("collections.xlsx not found. Please place 'collections.xlsx' next to app.py and rerun the app.")
        return None, pd.DataFrame()

    # Optional: expenses.xlsx
    try:
        expenses_df = pd.read_excel('expenses.xlsx')
    except FileNotFoundError:
        expenses_df = pd.DataFrame(columns=['Expense Name', 'Cost'])

    return collections_df, expenses_df

def format_currency(amount):
    """Format amount as Indian currency"""
    return f"₹{amount:,.2f}"

def create_summary_cards(collections_df):
    """Create summary cards for collections"""
    if collections_df is None or collections_df.empty:
        return
    
    total_collected = collections_df[collections_df['Status'] == 'Paid']['Amount'].sum()
    total_due = collections_df[collections_df['Status'] == 'Due']['Amount'].sum()
    paid_count = len(collections_df[collections_df['Status'] == 'Paid'])
    due_count = len(collections_df[collections_df['Status'] == 'Due'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="summary-card">
            <h3>💰 Total Collected</h3>
            <div class="amount">{format_currency(total_collected)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="summary-card">
            <h3>⏳ Total Due</h3>
            <div class="amount">{format_currency(total_due)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="summary-card">
            <h3>✅ Paid Donors</h3>
            <div class="amount">{paid_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="summary-card">
            <h3>❌ Due Donors</h3>
            <div class="amount">{due_count}</div>
        </div>
        """, unsafe_allow_html=True)

def create_charts(collections_df):
    """Create visualization charts"""
    if collections_df is None or collections_df.empty:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Amount by Type
        type_amount = collections_df.groupby('Type')['Amount'].sum().reset_index()
        fig_type = px.pie(
            type_amount, 
            values='Amount', 
            names='Type',
            title='💰 Amount Distribution by Type',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_type.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_type, use_container_width=True)
    
    with col2:
        # Paid vs Due Summary
        status_amount = collections_df.groupby('Status')['Amount'].sum().reset_index()
        fig_status = px.bar(
            status_amount,
            x='Status',
            y='Amount',
            title='📊 Paid vs Due Amount',
            color='Status',
            color_discrete_map={'Paid': '#4CAF50', 'Due': '#f44336'}
        )
        fig_status.update_layout(showlegend=False)
        st.plotly_chart(fig_status, use_container_width=True)

def collections_tab(collections_df):
    """Collections tab content"""
    if collections_df is None or collections_df.empty:
        st.warning("No collections data available.")
        return
    
    # Summary cards
    create_summary_cards(collections_df)
    
    # Charts
    with st.expander("📊 View Charts", expanded=False):
        create_charts(collections_df)
    
    # Search and filters
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    st.subheader("🔍 Search & Filter")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("Search by Name:", placeholder="Enter donor name...")
    
    with col2:
        filter_type = st.selectbox(
            "Filter by Type:",
            ["All"] + list(collections_df['Type'].unique())
        )
    
    with col3:
        filter_status = st.selectbox(
            "Filter by Status:",
            ["All"] + list(collections_df['Status'].unique())
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_df = collections_df.copy()
    
    if search_name:
        filtered_df = filtered_df[filtered_df['Name'].str.contains(search_name, case=False, na=False)]
    
    if filter_type != "All":
        filtered_df = filtered_df[filtered_df['Type'] == filter_type]
    
    if filter_status != "All":
        filtered_df = filtered_df[filtered_df['Status'] == filter_status]
    
    # Display filtered data
    if not filtered_df.empty:
        st.subheader(f"📋 Donor Records ({len(filtered_df)} records)")
        
        # Format the dataframe for display
        display_df = filtered_df.copy()
        display_df['Amount'] = display_df['Amount'].apply(format_currency)
        display_df['Status_Display'] = display_df['Status'].apply(
            lambda x: f'<span class="status-paid">✅ {x}</span>' if x == 'Paid' else f'<span class="status-due">❌ {x}</span>'
        )
        display_df['Type_Display'] = display_df['Type'].apply(
            lambda x: f'<span class="type-badge">{x}</span>'
        )
        
        # Reorder columns for display
        display_df = display_df[['Name', 'Amount', 'Type_Display', 'Status_Display']]
        display_df.columns = ['Name', 'Amount', 'Type', 'Status']
        
        # Display as HTML for styling
        st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f'ganesh_chavithi_collections_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv'
        )
    else:
        st.info("No records found matching the current filters.")

def expenses_tab(expenses_df):
    """Expenses tab content"""
    if expenses_df is None or expenses_df.empty:
        st.warning("No expenses data available.")
        return
    
    st.subheader("💰 Expense Summary")
    
    # Calculate total expenses
    total_expenses = expenses_df['Cost'].sum()
    
    # Display total in a card
    st.markdown(f"""
    <div class="summary-card">
        <h3>💸 Total Expenses</h3>
        <div class="amount">{format_currency(total_expenses)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display expenses table
    st.subheader("📋 Expense Details")
    
    # Format the dataframe for display
    display_expenses = expenses_df.copy()
    display_expenses['Cost'] = display_expenses['Cost'].apply(format_currency)
    
    st.dataframe(display_expenses, use_container_width=True)
    
    # Create expense chart
    if len(expenses_df) > 1:
        fig_expenses = px.bar(
            expenses_df,
            x='Expense Name',
            y='Cost',
            title='📊 Expense Breakdown',
            color='Cost',
            color_continuous_scale='viridis'
        )
        fig_expenses.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_expenses, use_container_width=True)
    
    # Download button
    csv = expenses_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Expenses as CSV",
        data=csv,
        file_name=f'ganesh_chavithi_expenses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv'
    )

def main():
    """Main application function"""
    # Load data
    collections_df, expenses_df = load_data()
    
    if collections_df is None:
        st.stop()
    
    # Create tabs
    tab1, tab2 = st.tabs(["🧾 Chanda Collections", "💰 Expenses"])
    
    with tab1:
        collections_tab(collections_df)
    
    with tab2:
        expenses_tab(expenses_df)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "🕉️ Ganesh Chavithi Chanda Tracker | Built with Streamlit 🕉️"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
