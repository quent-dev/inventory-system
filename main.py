#!/usr/bin/env python3
"""
Inventory Management System - Main Entry Point
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.inventory_engine import InventoryEngine


def main():
    """Main function for CLI testing and debugging."""
    print("🚀 Inventory Management System")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize the inventory engine
        print("Initializing inventory engine...")
        engine = InventoryEngine()
        
        # Test connections
        print("\n📡 Testing connections...")
        status = engine.get_system_status()
        
        print(f"Shopify: {'✅ Connected' if status['shopify_connected'] else '❌ Failed'}")
        print(f"Google Sheets: {'✅ Connected' if status['sheets_connected'] else '❌ Failed'}")
        
        if not status['shopify_connected'] or not status['sheets_connected']:
            print("\n⚠️  Please check your .env file and API credentials")
            return
        
        # Load data
        print("\n📊 Loading data...")
        success = engine.load_data()
        
        if success:
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