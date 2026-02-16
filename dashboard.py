import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

from src.inventory_engine import InventoryEngine
from src.models import EffectiveInventory
from src.store_config import get_available_stores, get_all_stores, DEFAULT_STORE, SUPPORTED_STORES

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
if 'current_store' not in st.session_state:
    st.session_state.current_store = DEFAULT_STORE

def initialize_engine(store_id: str = None):
    """Initialize the inventory engine with error handling."""
    if store_id is None:
        store_id = st.session_state.current_store

    try:
        engine = InventoryEngine(store_id=store_id)
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
    
    styled_df = df.style.map(color_status, subset=['Status'])
    st.dataframe(styled_df, width='stretch')
    
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
        st.plotly_chart(fig, width='stretch')

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
        days_of_stock = product.days_of_stock
        # Use a large number for sorting (999999) when no sales, display as ∞
        days_of_stock_numeric = days_of_stock if days_of_stock is not None else 999999

        product_data.append({
            'SKU': sku,
            'Product Name': product.name,
            'Current Stock': product.current_stock,
            'Available Stock': product.available_stock,
            'Units Sold (30d)': product.units_sold_30_days,
            'Daily Sales Rate': product.daily_sales_velocity,
            'Days of Stock': days_of_stock_numeric,
            'Unit Cost': product.unit_cost,
            'Inventory Value': product.inventory_value,
            'Recommended Buffer': product.recommended_buffer,
            'Last Updated': product.last_updated.strftime('%Y-%m-%d %H:%M') if product.last_updated else 'Unknown'
        })

    df = pd.DataFrame(product_data)
    
    # Calculate total inventory value
    total_inventory_value = sum(product.inventory_value for product in st.session_state.engine.products.values())
    high_value_products = len(df[df['Inventory Value'] >= 1000])

    # Display summary metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Products", len(df))

    with col2:
        total_stock = df['Current Stock'].sum()
        st.metric("Total Stock Units", f"{total_stock:,}")

    with col3:
        st.metric("Total Inventory Value", f"${total_inventory_value:,.2f}")

    with col4:
        out_of_stock = len(df[df['Available Stock'] <= 0])
        st.metric("Out of Stock", out_of_stock)

    with col5:
        # Products with less than 30 days of stock (exclude 999999 which means no sales)
        low_days = len(df[(df['Days of Stock'] < 30) & (df['Days of Stock'] < 999999)])
        st.metric("< 30 Days Stock", low_days)

    with col6:
        st.metric("High Value Items (≥$1K)", high_value_products)
    
    # Search and filter options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search products by SKU or name:", placeholder="Enter SKU or product name...")
    
    with col2:
        stock_filter = st.selectbox("Filter by stock level:", 
                                   ["All", "In Stock", "Out of Stock", "Low Stock (≤5)", "< 30 Days Stock", "With Sales Activity", "High Value (≥$1K)", "No Cost Data"])
    
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
    elif stock_filter == "< 30 Days Stock":
        filtered_df = filtered_df[(filtered_df['Days of Stock'] < 30) & (filtered_df['Days of Stock'] < 999999)]
    elif stock_filter == "With Sales Activity":
        filtered_df = filtered_df[filtered_df['Units Sold (30d)'] > 0]
    elif stock_filter == "High Value (≥$1K)":
        filtered_df = filtered_df[filtered_df['Inventory Value'] >= 1000]
    elif stock_filter == "No Cost Data":
        filtered_df = filtered_df[filtered_df['Unit Cost'] == 0]
    
    # Color coding functions
    def color_stock_levels(val):
        if val <= 0:
            return 'background-color: #ffcccb'  # Red for out of stock
        elif val <= 5:
            return 'background-color: #fff2cc'  # Yellow for low stock
        else:
            return 'background-color: #d4edda'  # Green for good stock

    def color_inventory_value(val):
        if val >= 5000:
            return 'background-color: #e6f3ff'  # Light blue for very high value
        elif val >= 1000:
            return 'background-color: #f0f8ff'  # Lighter blue for high value
        else:
            return ''  # No color for lower values

    # Display filtered table
    if len(filtered_df) > 0:
        st.write(f"Showing {len(filtered_df)} of {len(df)} products")

        # Create display dataframe - keep numeric values for proper sorting
        display_df = filtered_df.copy()

        # Column configuration for proper formatting while keeping numeric sorting
        column_config = {
            'SKU': st.column_config.TextColumn('SKU'),
            'Product Name': st.column_config.TextColumn('Product Name'),
            'Current Stock': st.column_config.NumberColumn('Current Stock', format='%d'),
            'Available Stock': st.column_config.NumberColumn('Available Stock', format='%d'),
            'Units Sold (30d)': st.column_config.NumberColumn('Units Sold (30d)', format='%d'),
            'Daily Sales Rate': st.column_config.NumberColumn('Daily Sales Rate', format='%.2f'),
            'Days of Stock': st.column_config.NumberColumn('Days of Stock', format='%.1f'),
            'Unit Cost': st.column_config.NumberColumn('Unit Cost', format='$%.2f'),
            'Inventory Value': st.column_config.NumberColumn('Inventory Value', format='$%.2f'),
            'Recommended Buffer': st.column_config.NumberColumn('Recommended Buffer', format='%d'),
            'Last Updated': st.column_config.TextColumn('Last Updated'),
        }

        st.dataframe(display_df, column_config=column_config, width='stretch')
        
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
    # Get current store for title
    current_store_display = SUPPORTED_STORES.get(
        st.session_state.current_store, {}
    ).get('display_name', st.session_state.current_store.upper())

    st.title(f"📦 Inventory Management Dashboard - {current_store_display}")

    # Sidebar
    with st.sidebar:
        st.header("Controls")

        # Store selector
        st.subheader("Store Selection")
        all_stores = get_all_stores()
        available_stores = get_available_stores()

        # Create options list with availability status
        store_options = list(all_stores.keys())
        store_labels = {
            store_id: f"{name} {'✅' if store_id in available_stores else '❌'}"
            for store_id, name in all_stores.items()
        }

        # Find current index
        current_index = store_options.index(st.session_state.current_store) if st.session_state.current_store in store_options else 0

        selected_store = st.selectbox(
            "Select Store:",
            options=store_options,
            index=current_index,
            format_func=lambda x: store_labels.get(x, x),
            help="Select the Shopify store to manage. ✅ = configured, ❌ = not configured"
        )

        # Handle store change
        if selected_store != st.session_state.current_store:
            st.session_state.current_store = selected_store
            st.session_state.engine = None  # Clear engine on store change
            st.session_state.last_refresh = None
            st.rerun()

        st.divider()

        if st.button("Initialize System", type="primary"):
            if st.session_state.current_store not in available_stores:
                st.error(f"Store '{st.session_state.current_store}' is not configured. Please set the required environment variables.")
            else:
                with st.spinner(f"Connecting to {current_store_display} store..."):
                    initialize_engine(st.session_state.current_store)

        if st.button("Refresh Data"):
            if st.session_state.engine:
                with st.spinner("Refreshing data..."):
                    st.session_state.engine.load_data()
                    st.session_state.last_refresh = datetime.now()
                st.success("Data refreshed!")
            else:
                st.warning("Please initialize system first")

        if st.button("Recalculate Sales Data"):
            if st.session_state.engine:
                with st.spinner("Clearing cache and fetching fresh sales data..."):
                    st.session_state.engine.clear_sales_cache()
                    st.session_state.engine.load_data()
                    st.session_state.last_refresh = datetime.now()
                st.success("Sales data recalculated!")
            else:
                st.warning("Please initialize system first")

        if st.session_state.last_refresh:
            st.write(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

        st.divider()
        st.subheader("Quick Links")
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        if spreadsheet_id:
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            st.markdown(f"[📊 Open Google Sheet]({sheet_url})")

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
