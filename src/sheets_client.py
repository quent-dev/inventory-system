import gspread
import os
from typing import List, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from .models import Kit, KitComponent, BusinessRule
from .store_config import get_store_config, DEFAULT_STORE
from datetime import datetime


class GoogleSheetsClient:
    def __init__(self, store_id: str = None):
        """
        Initialize Google Sheets client for a specific store.

        Args:
            store_id: Store identifier (e.g., "mexico", "usa").
                      Defaults to DEFAULT_STORE if not specified.
        """
        self.store_id = store_id or DEFAULT_STORE
        store_config = get_store_config(self.store_id)
        self.sheet_suffix = store_config.sheet_suffix
        self.store_display_name = store_config.display_name

        self.oauth_credentials_path = os.getenv('GOOGLE_OAUTH_CREDENTIALS_PATH', 'oauth_credentials.json')
        self.token_path = 'token.pickle'
        self.spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')

        if not self.spreadsheet_id:
            raise ValueError("Missing Google Sheets spreadsheet ID. Set GOOGLE_SPREADSHEET_ID environment variable.")
        
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = self._get_oauth_credentials(scopes)
            
            if credentials:
                self.client = gspread.authorize(credentials)
                self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            else:
                raise ValueError("Failed to obtain OAuth credentials.")
            
        except Exception as e:
            print(f"Google Sheets initialization error: {e}")
            self.client = None
            self.spreadsheet = None
    
    def _get_oauth_credentials(self, scopes):
        """Get OAuth 2.0 credentials with automatic refresh."""
        credentials = None
        
        # Load existing credentials from file
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                credentials = pickle.load(token)
        
        # If there are no valid credentials, request authorization
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    credentials = None
            
            if not credentials:
                if not os.path.exists(self.oauth_credentials_path):
                    raise ValueError(f"OAuth credentials file not found: {self.oauth_credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.oauth_credentials_path, scopes
                )
                credentials = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(credentials, token)
        
        return credentials

    def _get_worksheet_name(self, base_name: str) -> str:
        """
        Get the full worksheet name with store suffix.

        Args:
            base_name: Base worksheet name (e.g., "Kit Master")

        Returns:
            Full worksheet name with store suffix (e.g., "Kit Master - Mexico")
        """
        return f"{base_name}{self.sheet_suffix}"

    def get_kit_master_data(self) -> List[Kit]:
        """Read kit master data from Google Sheets."""
        if not self.spreadsheet:
            return []

        try:
            worksheet_name = self._get_worksheet_name('Kit Master')
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            records = worksheet.get_all_records()
            
            kits = []
            for record in records:
                if record.get('Kit SKU'):
                    # Handle empty price values
                    price_value = record.get('Kit Price', 0)
                    try:
                        price = float(price_value) if price_value else 0.0
                    except (ValueError, TypeError):
                        price = 0.0

                    kit = Kit(
                        sku=record['Kit SKU'],
                        name=record.get('Kit Name', ''),
                        description=record.get('Kit Description', ''),
                        price=price,
                        components=[],  # Will be populated by get_kit_components
                        is_active=record.get('Active/Inactive Status', 'Active') == 'Active',
                        created_date=self._parse_date(record.get('Created Date')),
                        last_modified=self._parse_date(record.get('Last Modified Date'))
                    )
                    kits.append(kit)
            
            return kits
            
        except Exception as e:
            print(f"Error reading kit master data: {e}")
            return []
    
    def get_kit_components(self) -> Dict[str, List[KitComponent]]:
        """Read component mapping from Google Sheets."""
        if not self.spreadsheet:
            return {}

        try:
            worksheet_name = self._get_worksheet_name('Component Mapping')
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            records = worksheet.get_all_records()
            
            components_by_kit = {}
            for record in records:
                kit_sku = record.get('Kit SKU')
                if kit_sku:
                    # Handle empty numeric values
                    qty_value = record.get('Quantity per Kit', 1)
                    try:
                        quantity = float(qty_value) if qty_value else 1.0
                    except (ValueError, TypeError):
                        quantity = 1.0

                    cost_value = record.get('Component Cost', 0)
                    try:
                        cost = float(cost_value) if cost_value else 0.0
                    except (ValueError, TypeError):
                        cost = 0.0

                    component = KitComponent(
                        kit_sku=kit_sku,
                        component_sku=record.get('Component SKU', ''),
                        component_name=record.get('Component Name', ''),
                        quantity_per_kit=quantity,
                        component_cost=cost,
                        is_critical=record.get('Is Critical Component', 'Y') == 'Y'
                    )

                    if kit_sku not in components_by_kit:
                        components_by_kit[kit_sku] = []
                    components_by_kit[kit_sku].append(component)
            
            return components_by_kit
            
        except Exception as e:
            print(f"Error reading component mapping: {e}")
            return {}
    
    def get_business_rules(self) -> Dict[str, BusinessRule]:
        """Read business rules from Google Sheets."""
        if not self.spreadsheet:
            return {}

        try:
            worksheet_name = self._get_worksheet_name('Business Rules')
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            records = worksheet.get_all_records()
            
            rules = {}
            for record in records:
                component_sku = record.get('Component SKU')
                if component_sku:
                    # Handle empty numeric values
                    def safe_int(value, default):
                        try:
                            return int(float(value)) if value else default
                        except (ValueError, TypeError):
                            return default

                    rule = BusinessRule(
                        component_sku=component_sku,
                        minimum_buffer_stock=safe_int(record.get('Minimum Buffer Stock'), 0),
                        maximum_kit_assembly=safe_int(record.get('Maximum Kit Assembly Quantity'), 1000),
                        lead_time_days=safe_int(record.get('Lead Time for Component Restocking (days)'), 7),
                        assembly_time_minutes=safe_int(record.get('Assembly/Disassembly Labor Time (minutes)'), 15),
                        priority_level=record.get('Priority Level', 'Medium')
                    )
                    rules[component_sku] = rule
            
            return rules
            
        except Exception as e:
            print(f"Error reading business rules: {e}")
            return {}
    
    def get_product_costs(self) -> Dict[str, float]:
        """Read product costs from Google Sheets with kit calculation support."""
        if not self.spreadsheet:
            return {}

        try:
            # Load manual costs first
            worksheet_name = self._get_worksheet_name('Product Costs')
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            records = worksheet.get_all_records()
            
            manual_costs = {}
            override_flags = {}
            
            for record in records:
                sku = record.get('SKU')
                if sku:
                    # Get manual cost
                    unit_cost = record.get('Unit Cost', 0)
                    try:
                        manual_costs[sku] = float(unit_cost)
                    except (ValueError, TypeError):
                        manual_costs[sku] = 0.0
                    
                    # Get override flag
                    override = record.get('Manual Override (Y/N)', '').upper()
                    override_flags[sku] = override == 'Y'
            
            # Now calculate final costs (manual + kit calculations)
            final_costs = self._calculate_final_costs(manual_costs, override_flags)
            return final_costs
            
        except Exception as e:
            print(f"Error reading product costs: {e}")
            return {}
    
    def _calculate_final_costs(self, manual_costs: Dict[str, float], override_flags: Dict[str, bool]) -> Dict[str, float]:
        """Calculate final costs combining manual costs and kit calculations."""
        try:
            # Get kit definitions and component mappings
            kits = self.get_kit_master_data()
            component_mappings = self.get_kit_components()
            
            final_costs = manual_costs.copy()
            
            # Calculate costs for kits that don't have manual override
            for kit in kits:
                kit_sku = kit.sku
                
                # Skip if manual override is enabled
                if override_flags.get(kit_sku, False):
                    print(f"   Using manual cost for kit {kit_sku}")
                    continue
                
                # Calculate cost from components
                if kit_sku in component_mappings:
                    calculated_cost = 0.0
                    components = component_mappings[kit_sku]
                    
                    for component in components:
                        component_sku = component.component_sku
                        quantity = component.quantity_per_kit
                        
                        # Get component cost (from manual costs or default to 0)
                        component_cost = manual_costs.get(component_sku, 0.0)
                        calculated_cost += component_cost * quantity
                    
                    if calculated_cost > 0:
                        final_costs[kit_sku] = calculated_cost
                        print(f"   Calculated cost for kit {kit_sku}: ${calculated_cost:.2f}")
                    else:
                        print(f"   Warning: Kit {kit_sku} has components with no costs")
            
            return final_costs
            
        except Exception as e:
            print(f"Error calculating kit costs: {e}")
            return manual_costs
    
    def create_sample_sheets(self):
        """Create sample sheets with headers if they don't exist."""
        if not self.spreadsheet:
            return False

        try:
            # Kit Master sheet
            kit_master_name = self._get_worksheet_name('Kit Master')
            try:
                kit_master = self.spreadsheet.worksheet(kit_master_name)
            except:
                kit_master = self.spreadsheet.add_worksheet(kit_master_name, 100, 10)
                kit_master.append_row([
                    'Kit SKU', 'Kit Name', 'Kit Description', 'Kit Price',
                    'Active/Inactive Status', 'Created Date', 'Last Modified Date'
                ])

            # Component Mapping sheet
            component_mapping_name = self._get_worksheet_name('Component Mapping')
            try:
                component_mapping = self.spreadsheet.worksheet(component_mapping_name)
            except:
                component_mapping = self.spreadsheet.add_worksheet(component_mapping_name, 500, 10)
                component_mapping.append_row([
                    'Kit SKU', 'Component SKU', 'Component Name', 'Quantity per Kit',
                    'Component Cost', 'Is Critical Component (Y/N)'
                ])

            # Business Rules sheet
            business_rules_name = self._get_worksheet_name('Business Rules')
            try:
                business_rules = self.spreadsheet.worksheet(business_rules_name)
            except:
                business_rules = self.spreadsheet.add_worksheet(business_rules_name, 200, 10)
                business_rules.append_row([
                    'Component SKU', 'Minimum Buffer Stock', 'Maximum Kit Assembly Quantity',
                    'Lead Time for Component Restocking (days)', 'Assembly/Disassembly Labor Time (minutes)',
                    'Priority Level (High/Medium/Low)'
                ])

            # Product Costs sheet
            product_costs_name = self._get_worksheet_name('Product Costs')
            try:
                product_costs = self.spreadsheet.worksheet(product_costs_name)
            except:
                product_costs = self.spreadsheet.add_worksheet(product_costs_name, 1000, 10)
                product_costs.append_row([
                    'SKU', 'Unit Cost', 'Cost Currency', 'Last Updated',
                    'Supplier', 'Notes', 'Manual Override (Y/N)'
                ])

            return True

        except Exception as e:
            print(f"Error creating sample sheets: {e}")
            return False
    
    def _parse_date(self, date_str) -> datetime:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            try:
                return datetime.strptime(date_str, '%m/%d/%Y')
            except:
                return None
    
    def test_connection(self) -> bool:
        """Test if Google Sheets connection is working."""
        return self.spreadsheet is not None