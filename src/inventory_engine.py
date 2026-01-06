from typing import List, Dict, Tuple
from .models import Product, Kit, KitComponent, BusinessRule, EffectiveInventory
from .shopify_client import ShopifyClient
from .sheets_client import GoogleSheetsClient
import math


class InventoryEngine:
    def __init__(self):
        self.shopify_client = ShopifyClient()
        self.sheets_client = GoogleSheetsClient()
        self.products = {}  # SKU -> Product
        self.kits = {}  # Kit SKU -> Kit
        self.business_rules = {}  # Component SKU -> BusinessRule
        
    def load_data(self) -> bool:
        """Load all data from Shopify and Google Sheets."""
        try:
            # Load products from Shopify
            products_list = self.shopify_client.get_products()
            self.products = {p.sku: p for p in products_list}
            
            # Load kits from Google Sheets
            kits_list = self.sheets_client.get_kit_master_data()
            components_by_kit = self.sheets_client.get_kit_components()
            
            # Combine kits with their components
            for kit in kits_list:
                if kit.sku in components_by_kit:
                    kit.components = components_by_kit[kit.sku]
                self.kits[kit.sku] = kit
            
            # Load business rules
            self.business_rules = self.sheets_client.get_business_rules()
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def calculate_effective_inventory(self, kit_sku: str = None) -> List[EffectiveInventory]:
        """Calculate effective inventory for all kits or a specific kit."""
        if kit_sku:
            kits_to_process = {kit_sku: self.kits[kit_sku]} if kit_sku in self.kits else {}
        else:
            kits_to_process = {k: v for k, v in self.kits.items() if v.is_active}
        
        results = []
        
        for sku, kit in kits_to_process.items():
            effective_inv = self._calculate_kit_inventory(kit)
            results.append(effective_inv)
        
        return results
    
    def _calculate_kit_inventory(self, kit: Kit) -> EffectiveInventory:
        """Calculate effective inventory for a single kit."""
        if not kit.components:
            return EffectiveInventory(
                kit_sku=kit.sku,
                kit_name=kit.name,
                max_kits_possible=0,
                bottleneck_component="No components defined",
                status="CRITICAL"
            )
        
        min_possible = float('inf')
        bottleneck_component = None
        
        for component in kit.components:
            if component.component_sku not in self.products:
                return EffectiveInventory(
                    kit_sku=kit.sku,
                    kit_name=kit.name,
                    max_kits_possible=0,
                    bottleneck_component=f"Missing component: {component.component_sku}",
                    status="CRITICAL"
                )
            
            product = self.products[component.component_sku]
            available = product.available_stock
            
            # Apply buffer stock if business rule exists
            if component.component_sku in self.business_rules:
                buffer = self.business_rules[component.component_sku].minimum_buffer_stock
                available = max(0, available - buffer)
            
            # Calculate how many kits this component can support
            possible_kits = math.floor(available / component.quantity_per_kit)
            
            if possible_kits < min_possible:
                min_possible = possible_kits
                bottleneck_component = component.component_name or component.component_sku
        
        # Determine status
        status = "OK"
        if min_possible == 0:
            status = "CRITICAL"
        elif min_possible <= 5:  # Configurable threshold
            status = "LOW"
        
        return EffectiveInventory(
            kit_sku=kit.sku,
            kit_name=kit.name,
            max_kits_possible=int(min_possible) if min_possible != float('inf') else 0,
            bottleneck_component=bottleneck_component,
            status=status
        )
    
    def get_component_usage_forecast(self, days: int = 30) -> Dict[str, Dict]:
        """Forecast component usage based on kit sales."""
        # This would integrate with Shopify order data
        # For now, return placeholder structure
        forecast = {}
        
        for product_sku, product in self.products.items():
            forecast[product_sku] = {
                'current_stock': product.available_stock,
                'estimated_daily_usage': 0,  # Would calculate from historical data
                'days_remaining': None,
                'reorder_recommended': False
            }
        
        return forecast
    
    def simulate_kit_disassembly(self, kit_sku: str, quantity: int) -> Dict[str, int]:
        """Simulate what components would be gained by disassembling kits."""
        if kit_sku not in self.kits:
            return {}
        
        kit = self.kits[kit_sku]
        component_gains = {}
        
        for component in kit.components:
            gained = component.quantity_per_kit * quantity
            component_gains[component.component_sku] = gained
        
        return component_gains
    
    def validate_data_consistency(self) -> List[str]:
        """Validate data consistency between Shopify and Google Sheets."""
        issues = []
        
        # Check for components referenced in kits but not in Shopify
        for kit in self.kits.values():
            for component in kit.components:
                if component.component_sku not in self.products:
                    issues.append(f"Component {component.component_sku} in kit {kit.sku} not found in Shopify")
        
        # Check for business rules for non-existent components
        for sku in self.business_rules.keys():
            if sku not in self.products:
                issues.append(f"Business rule exists for non-existent component: {sku}")
        
        return issues
    
    def get_system_status(self) -> Dict:
        """Get overall system status and health."""
        return {
            'shopify_connected': self.shopify_client.test_connection(),
            'sheets_connected': self.sheets_client.test_connection(),
            'products_loaded': len(self.products),
            'kits_loaded': len(self.kits),
            'business_rules_loaded': len(self.business_rules),
            'data_issues': self.validate_data_consistency()
        }