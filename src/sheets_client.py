import gspread
import os
from typing import List, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from .models import Kit, KitComponent, BusinessRule
from datetime import datetime


class GoogleSheetsClient:
    def __init__(self):
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
    
    def get_kit_master_data(self) -> List[Kit]:
        """Read kit master data from Google Sheets."""
        if not self.spreadsheet:
            return []
        
        try:
            worksheet = self.spreadsheet.worksheet('Kit Master')
            records = worksheet.get_all_records()
            
            kits = []
            for record in records:
                if record.get('Kit SKU'):
                    kit = Kit(
                        sku=record['Kit SKU'],
                        name=record.get('Kit Name', ''),
                        description=record.get('Kit Description', ''),
                        price=float(record.get('Kit Price', 0)),
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
            worksheet = self.spreadsheet.worksheet('Component Mapping')
            records = worksheet.get_all_records()
            
            components_by_kit = {}
            for record in records:
                kit_sku = record.get('Kit SKU')
                if kit_sku:
                    component = KitComponent(
                        kit_sku=kit_sku,
                        component_sku=record.get('Component SKU', ''),
                        component_name=record.get('Component Name', ''),
                        quantity_per_kit=float(record.get('Quantity per Kit', 1)),
                        component_cost=float(record.get('Component Cost', 0)),
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
            worksheet = self.spreadsheet.worksheet('Business Rules')
            records = worksheet.get_all_records()
            
            rules = {}
            for record in records:
                component_sku = record.get('Component SKU')
                if component_sku:
                    rule = BusinessRule(
                        component_sku=component_sku,
                        minimum_buffer_stock=int(record.get('Minimum Buffer Stock', 0)),
                        maximum_kit_assembly=int(record.get('Maximum Kit Assembly Quantity', 1000)),
                        lead_time_days=int(record.get('Lead Time for Component Restocking (days)', 7)),
                        assembly_time_minutes=int(record.get('Assembly/Disassembly Labor Time (minutes)', 15)),
                        priority_level=record.get('Priority Level', 'Medium')
                    )
                    rules[component_sku] = rule
            
            return rules
            
        except Exception as e:
            print(f"Error reading business rules: {e}")
            return {}
    
    def create_sample_sheets(self):
        """Create sample sheets with headers if they don't exist."""
        if not self.spreadsheet:
            return False
        
        try:
            # Kit Master sheet
            try:
                kit_master = self.spreadsheet.worksheet('Kit Master')
            except:
                kit_master = self.spreadsheet.add_worksheet('Kit Master', 100, 10)
                kit_master.append_row([
                    'Kit SKU', 'Kit Name', 'Kit Description', 'Kit Price',
                    'Active/Inactive Status', 'Created Date', 'Last Modified Date'
                ])
            
            # Component Mapping sheet
            try:
                component_mapping = self.spreadsheet.worksheet('Component Mapping')
            except:
                component_mapping = self.spreadsheet.add_worksheet('Component Mapping', 500, 10)
                component_mapping.append_row([
                    'Kit SKU', 'Component SKU', 'Component Name', 'Quantity per Kit',
                    'Component Cost', 'Is Critical Component (Y/N)'
                ])
            
            # Business Rules sheet
            try:
                business_rules = self.spreadsheet.worksheet('Business Rules')
            except:
                business_rules = self.spreadsheet.add_worksheet('Business Rules', 200, 10)
                business_rules.append_row([
                    'Component SKU', 'Minimum Buffer Stock', 'Maximum Kit Assembly Quantity',
                    'Lead Time for Component Restocking (days)', 'Assembly/Disassembly Labor Time (minutes)',
                    'Priority Level (High/Medium/Low)'
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