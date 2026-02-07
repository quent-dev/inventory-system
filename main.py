#!/usr/bin/env python3
"""
Inventory Management System - Main Entry Point
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.inventory_engine import InventoryEngine
from src.store_config import get_available_stores, get_all_stores, SUPPORTED_STORES, DEFAULT_STORE


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Inventory Management System - Multi-Store Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  # Run with default store (Mexico)
  python main.py --store mexico   # Explicit Mexico store
  python main.py --store usa      # USA store
  python main.py --list-stores    # Show available stores
        """
    )

    parser.add_argument(
        '--store',
        type=str,
        choices=list(SUPPORTED_STORES.keys()),
        default=DEFAULT_STORE,
        help=f"Store to connect to (default: {DEFAULT_STORE})"
    )

    parser.add_argument(
        '--list-stores',
        action='store_true',
        help="List all available stores and their configuration status"
    )

    return parser.parse_args()


def list_stores():
    """Display available stores and their configuration status."""
    print("🏪 Supported Stores:")
    print("-" * 40)

    all_stores = get_all_stores()
    available_stores = get_available_stores()

    for store_id, display_name in all_stores.items():
        if store_id in available_stores:
            status = "✅ Configured"
        else:
            status = "❌ Not configured"
        default_marker = " (default)" if store_id == DEFAULT_STORE else ""
        print(f"  {store_id}: {display_name} - {status}{default_marker}")

    print()
    print("To configure a store, set the following environment variables:")
    for store_id, info in SUPPORTED_STORES.items():
        suffix = info["env_suffix"]
        print(f"  {store_id}: SHOPIFY_SHOP_DOMAIN{suffix}, SHOPIFY_ACCESS_TOKEN{suffix}")


def main():
    """Main function for CLI testing and debugging."""
    args = parse_args()

    # Handle --list-stores
    if args.list_stores:
        load_dotenv()
        list_stores()
        return

    store_id = args.store

    print("🚀 Inventory Management System")
    print("=" * 40)

    # Load environment variables
    load_dotenv()

    try:
        # Initialize the inventory engine for the selected store
        print(f"Initializing inventory engine for {store_id.upper()} store...")
        engine = InventoryEngine(store_id=store_id)
        
        # Test connections
        print("\n📡 Testing connections...")
        status = engine.get_system_status()
        
        print(f"Store: {status['store_display_name']} ({status['store_id']})")
        print(f"Shopify: {'✅ Connected' if status['shopify_connected'] else '❌ Failed'}")
        print(f"Google Sheets: {'✅ Connected' if status['sheets_connected'] else '❌ Failed'}")
        
        if not status['shopify_connected'] or not status['sheets_connected']:
            print("\n⚠️  Please check your .env file and API credentials")
            return
        
        # Load data
        print("\n📊 Loading data...")
        success = engine.load_data()

        if success:
            # Get updated status after loading
            status = engine.get_system_status()
            print(f"✅ Loaded {status['products_loaded']} products and {status['kits_loaded']} kits")
            
            # Debug: Show summary and check for specific SKUs
            if engine.products:
                print(f"\n🔍 SKU Check:")
                target_skus = ['SCL-0033', 'SCL-0117']
                for sku in target_skus:
                    if sku in engine.products:
                        print(f"   ✅ Found {sku}: {engine.products[sku].name}")
                    else:
                        print(f"   ❌ Missing {sku}")
                        # Check for case variations
                        found_variations = [s for s in engine.products.keys() if s.upper() == sku.upper()]
                        if found_variations:
                            print(f"      🔍 Found case variation: {found_variations[0]}")
            else:
                print("❌ No products loaded from Shopify")
            
            # Calculate effective inventory
            print("\n📦 Calculating effective inventory...")
            effective_inventory = engine.calculate_effective_inventory()
            
            if effective_inventory:
                print("\nEffective Inventory Results:")
                print("-" * 60)
                for inv in effective_inventory:
                    status_emoji = {"OK": "✅", "LOW": "⚠️", "CRITICAL": "❌"}.get(inv.status, "❓")
                    print(f"{status_emoji} {inv.kit_name}: {inv.max_kits_possible} kits possible")
                    if inv.bottleneck_component:
                        print(f"   Bottleneck: {inv.bottleneck_component}")
            else:
                print("No kit data available")
            
            # Check for data issues
            issues = status['data_issues']
            if issues:
                print(f"\n⚠️  Found {len(issues)} data issues:")
                for issue in issues:
                    print(f"   • {issue}")
        else:
            print("❌ Failed to load data")
        
        print(f"\n🎯 To start the dashboard, run: streamlit run dashboard.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()