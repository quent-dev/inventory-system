import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

from src.inventory_engine import InventoryEngine
from src.models import EffectiveInventory

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Inventory Management Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = None
    st.session_state.last_refresh = None

def initialize_engine():
    """Initialize the inventory engine with error handling."""
    try:
        engine = InventoryEngine()
        success = engine.load_data()
        if success:
            st.session_state.engine = engine
            st.session_state.last_refresh = datetime.now()
            return True
        else:
            st.error("Failed to load data from APIs")
            return False
    except Exception as e:
        st.error(f"Error initializing inventory engine: {e}")
        return False

def display_system_status():
    """Display system connection status."""
    if not st.session_state.engine:
        st.warning("System not initialized")
        return
    
    status = st.session_state.engine.get_system_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = "🟢" if status['shopify_connected'] else "🔴"
        st.metric("Shopify", f"{status_color} {'Connected' if status['shopify_connected'] else 'Disconnected'}")
    
    with col2:
        status_color = "🟢" if status['sheets_connected'] else "🔴"
        st.metric("Google Sheets", f"{status_color} {'Connected' if status['sheets_connected'] else 'Disconnected'}")
    
    with col3:
        st.metric("Products Loaded", status['products_loaded'])
    
    with col4:
        st.metric("Kits Configured", status['kits_loaded'])
    
    if status['data_issues']:
        st.warning("Data Issues Detected:")
        for issue in status['data_issues']:
            st.write(f"⚠️ {issue}")

def display_effective_inventory():
    """Display effective inventory calculations."""
    if not st.session_state.engine:
        st.warning("Please initialize the system first")
        return
    
    st.subheader("Effective Inventory Analysis")
    
    # Calculate effective inventory
    effective_inventory = st.session_state.engine.calculate_effective_inventory()
    
    if not effective_inventory:
        st.info("No kit inventory data available")
        return
    
    # Convert to DataFrame for display
    df_data = []
    for inv in effective_inventory:
        df_data.append({
            'Kit SKU': inv.kit_sku,
            'Kit Name': inv.kit_name,
            'Max Kits Possible': inv.max_kits_possible,
            'Bottleneck Component': inv.bottleneck_component or 'None',
            'Status': inv.status
        })
    
    df = pd.DataFrame(df_data)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_kits = len(df)
        st.metric("Total Kits", total_kits)
    
    with col2:
        critical_kits = len(df[df['Status'] == 'CRITICAL'])
        st.metric("Critical Kits", critical_kits, delta=f"{critical_kits/total_kits*100:.1f}%" if total_kits > 0 else "0%")
    
    with col3:
        low_kits = len(df[df['Status'] == 'LOW'])
        st.metric("Low Stock Kits", low_kits)
    
    with col4:
        ok_kits = len(df[df['Status'] == 'OK'])
        st.metric("OK Status Kits", ok_kits)
    
    # Display table with color coding
    def color_status(val):
        if val == 'CRITICAL':
            return 'background-color: #ffcccb'
        elif val == 'LOW':
            return 'background-color: #fff2cc'
        else:
            return 'background-color: #d4edda'
    
    styled_df = df.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Chart: Kit availability
    if len(df) > 0:
        fig = px.bar(
            df, 
            x='Kit Name', 
            y='Max Kits Possible',
            color='Status',
            color_discrete_map={'OK': 'green', 'LOW': 'orange', 'CRITICAL': 'red'},
            title="Kit Availability by Status"
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

def display_what_if_analysis():
    """Display what-if analysis tools."""
    if not st.session_state.engine:
        st.warning("Please initialize the system first")
        return
    
    st.subheader("What-If Analysis")
    
    # Kit disassembly simulation
    st.write("### Kit Disassembly Simulator")
    
    kit_options = list(st.session_state.engine.kits.keys())
    if kit_options:
        selected_kit = st.selectbox("Select Kit to Disassemble:", kit_options)
        disassemble_qty = st.number_input("Quantity to Disassemble:", min_value=0, value=1)
        
        if st.button("Simulate Disassembly"):
            component_gains = st.session_state.engine.simulate_kit_disassembly(selected_kit, disassemble_qty)
            
            if component_gains:
                st.write("Components Gained:")
                for sku, quantity in component_gains.items():
                    st.write(f"• {sku}: +{quantity} units")
            else:
                st.warning("No components found for this kit")
    else:
        st.info("No kits configured")

def display_product_inventory():
    """Display all products and their inventory levels."""
    if not st.session_state.engine:
        st.warning("Please initialize the system first")
        return
    
    st.subheader("Product Inventory")
    
    if not st.session_state.engine.products:
        st.info("No products loaded from Shopify")
        return
    
    # Create DataFrame from products
    product_data = []
    for sku, product in st.session_state.engine.products.items():
        product_data.append({
            'SKU': sku,
            'Product Name': product.name,
            'Current Stock': product.current_stock,
            'Reserved Stock': product.reserved_stock,
            'Available Stock': product.available_stock,
            'Last Updated': product.last_updated.strftime('%Y-%m-%d %H:%M') if product.last_updated else 'Unknown'
        })
    
    df = pd.DataFrame(product_data)
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Products", len(df))
    
    with col2:
        total_stock = df['Current Stock'].sum()
        st.metric("Total Stock Units", f"{total_stock:,}")
    
    with col3:
        out_of_stock = len(df[df['Available Stock'] <= 0])
        st.metric("Out of Stock", out_of_stock)
    
    with col4:
        low_stock = len(df[(df['Available Stock'] > 0) & (df['Available Stock'] <= 5)])
        st.metric("Low Stock (≤5)", low_stock)
    
    # Search and filter options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search products by SKU or name:", placeholder="Enter SKU or product name...")
    
    with col2:
        stock_filter = st.selectbox("Filter by stock level:", 
                                   ["All", "In Stock", "Out of Stock", "Low Stock (≤5)"])
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        mask = (
            filtered_df['SKU'].str.contains(search_term, case=False, na=False) |
            filtered_df['Product Name'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if stock_filter == "In Stock":
        filtered_df = filtered_df[filtered_df['Available Stock'] > 0]
    elif stock_filter == "Out of Stock":
        filtered_df = filtered_df[filtered_df['Available Stock'] <= 0]
    elif stock_filter == "Low Stock (≤5)":
        filtered_df = filtered_df[(filtered_df['Available Stock'] > 0) & (filtered_df['Available Stock'] <= 5)]
    
    # Color coding function
    def color_stock_levels(val):
        if val <= 0:
            return 'background-color: #ffcccb'  # Red for out of stock
        elif val <= 5:
            return 'background-color: #fff2cc'  # Yellow for low stock
        else:
            return 'background-color: #d4edda'  # Green for good stock
    
    # Display filtered table
    if len(filtered_df) > 0:
        st.write(f"Showing {len(filtered_df)} of {len(df)} products")
        
        # Apply styling to Available Stock column
        styled_df = filtered_df.style.applymap(
            color_stock_levels, 
            subset=['Available Stock']
        )
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Download option
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="product_inventory.csv",
            mime="text/csv"
        )
    else:
        st.warning("No products match your search criteria")

def main():
    """Main dashboard application."""
    st.title("📦 Inventory Management Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        
        if st.button("Initialize System", type="primary"):
            with st.spinner("Connecting to APIs and loading data..."):
                initialize_engine()
        
        if st.button("Refresh Data"):
            if st.session_state.engine:
                with st.spinner("Refreshing data..."):
                    st.session_state.engine.load_data()
                    st.session_state.last_refresh = datetime.now()
                st.success("Data refreshed!")
            else:
                st.warning("Please initialize system first")
        
        if st.session_state.last_refresh:
            st.write(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
        
        st.divider()
        
        # Environment check
        st.subheader("Environment Check")
        required_vars = ['SHOPIFY_SHOP_DOMAIN', 'SHOPIFY_ACCESS_TOKEN', 'GOOGLE_SPREADSHEET_ID', 'GOOGLE_OAUTH_CREDENTIALS_PATH']
        for var in required_vars:
            if os.getenv(var):
                st.success(f"✅ {var}")
            else:
                st.error(f"❌ {var}")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["System Status", "Effective Inventory", "Product Inventory", "What-If Analysis"])
    
    with tab1:
        display_system_status()
    
    with tab2:
        display_effective_inventory()
    
    with tab3:
        display_product_inventory()
    
    with tab4:
        display_what_if_analysis()

if __name__ == "__main__":
    main()