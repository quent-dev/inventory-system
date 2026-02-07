#!/usr/bin/env python3
"""
Setup script to initialize Google Sheets structure for Inventory Management System
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.sheets_client import GoogleSheetsClient


def main():
    """Set up Google Sheets structure."""
    print("🔧 Google Sheets Setup Utility")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    if not spreadsheet_id:
        print("❌ Error: GOOGLE_SPREADSHEET_ID not found in .env file")
        print("\nPlease:")
        print("1. Create a new Google Sheets document")
        print("2. Copy the Spreadsheet ID from the URL")
        print("3. Add it to your .env file as GOOGLE_SPREADSHEET_ID=your-id-here")
        return

    print(f"📊 Spreadsheet ID: {spreadsheet_id}")
    print(f"\nConnecting to Google Sheets...")

    try:
        # Initialize the Google Sheets client
        sheets_client = GoogleSheetsClient()

        if not sheets_client.test_connection():
            print("❌ Failed to connect to Google Sheets")
            print("\nPlease check:")
            print("1. Your OAuth credentials file exists")
            print("2. You have access to the spreadsheet")
            print("3. The spreadsheet ID is correct")
            return

        print("✅ Connected successfully!")

        # Check existing worksheets
        print(f"\n📋 Checking existing worksheets...")
        existing_worksheets = [ws.title for ws in sheets_client.spreadsheet.worksheets()]
        print(f"Found worksheets: {', '.join(existing_worksheets)}")

        required_sheets = ['Kit Master', 'Component Mapping', 'Business Rules', 'Product Costs']
        missing_sheets = [sheet for sheet in required_sheets if sheet not in existing_worksheets]

        if not missing_sheets:
            print("\n✅ All required worksheets already exist!")

            # Check if they have data
            print("\n📊 Checking data in worksheets...")
            kit_master = sheets_client.spreadsheet.worksheet('Kit Master')
            kit_data = kit_master.get_all_records()

            component_mapping = sheets_client.spreadsheet.worksheet('Component Mapping')
            component_data = component_mapping.get_all_records()

            print(f"   Kit Master: {len(kit_data)} rows of data")
            print(f"   Component Mapping: {len(component_data)} rows of data")

            if len(kit_data) == 0:
                print("\n⚠️  Kit Master worksheet is empty!")
                print("\nTo add kits, you can either:")
                print("1. Manually add data to the 'Kit Master' worksheet in Google Sheets")
                print("2. See SHEETS_STRUCTURE.md for the required column structure")
                print("\nExample data:")
                print("Kit SKU          | Kit Name           | Kit Price | Active/Inactive Status")
                print("KIT-STARTER-001  | Starter Kit        | 49.99     | Active")

            if len(component_data) == 0:
                print("\n⚠️  Component Mapping worksheet is empty!")
                print("\nAfter adding kits, you need to map their components:")
                print("Kit SKU         | Component SKU | Quantity per Kit | Is Critical Component (Y/N)")
                print("KIT-STARTER-001 | SCL-0033     | 1               | Y")
        else:
            print(f"\n⚠️  Missing worksheets: {', '.join(missing_sheets)}")
            print("\nCreating missing worksheets...")

            success = sheets_client.create_sample_sheets()

            if success:
                print("✅ Worksheets created successfully!")
                print("\n📝 Next steps:")
                print("1. Open your Google Sheets document")
                print("2. Add kit definitions to 'Kit Master' worksheet")
                print("3. Map kit components in 'Component Mapping' worksheet")
                print("4. Optionally add business rules and product costs")
                print("\nSee SHEETS_STRUCTURE.md for detailed instructions and examples")
            else:
                print("❌ Failed to create worksheets")
                print("Please check your permissions and try again")

        # Show the spreadsheet URL
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        print(f"\n🔗 Open your spreadsheet: {spreadsheet_url}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
