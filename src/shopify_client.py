import requests
import os
from typing import List, Dict, Optional
from datetime import datetime
import time
from .models import Product


class ShopifyClient:
    def __init__(self):
        self.shop_domain = os.getenv('SHOPIFY_SHOP_DOMAIN')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.api_version = '2024-01'
        
        if not self.shop_domain or not self.access_token:
            raise ValueError("Missing Shopify credentials. Set SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN environment variables.")
        
        self.base_url = f"https://{self.shop_domain}.myshopify.com/admin/api/{self.api_version}"
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with rate limiting and error handling."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                time.sleep(retry_after)
                return self._make_request(endpoint, params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Shopify API error: {e}")
            return {}
    
    def get_products(self, limit: int = 250) -> List[Product]:
        """Fetch all products with inventory information."""
        products = []
        params = {
            'limit': limit, 
            'fields': 'id,title,variants,status',
            'status': 'active'  # Only get active products
        }
        
        response = self._make_request('products.json', params)
        
        if 'products' not in response:
            print("No products found in Shopify response")
            return products
        
        total_variants_found = 0
        variants_with_sku = 0
        variants_without_sku = 0
        products_processed = 0
        products_skipped = 0
        
        for product in response['products']:
            product_status = product.get('status', 'unknown')
            product_title = product.get('title', 'No Title')
            
            # Skip non-active products (extra safety check)
            if product_status != 'active':
                products_skipped += 1
                print(f"Skipping {product_status} product: {product_title}")
                continue
            
            products_processed += 1
            print(f"Processing active product: {product_title}")
            
            variants = product.get('variants', [])
            total_variants_found += len(variants)
            
            for variant in variants:
                # Handle None/null SKU safely
                variant_sku_raw = variant.get('sku')
                variant_sku = variant_sku_raw.strip() if variant_sku_raw else ''
                
                variant_title = variant.get('title', 'Default')
                variant_id = variant.get('id')
                inventory_qty = variant.get('inventory_quantity', 0)
                
                print(f"  Variant: {variant_title}, SKU: '{variant_sku}', ID: {variant_id}, Inventory: {inventory_qty}")
                
                if variant_sku:
                    variants_with_sku += 1
                    products.append(Product(
                        sku=variant_sku,
                        name=f"{product_title} - {variant_title}",
                        current_stock=inventory_qty,
                        reserved_stock=0,  # Will be calculated separately if needed
                        last_updated=datetime.now()
                    ))
                else:
                    variants_without_sku += 1
                    print(f"    ⚠️ Variant {variant_id} has no SKU")
        
        print(f"\n📊 Product Summary:")
        print(f"  Active products processed: {products_processed}")
        print(f"  Non-active products skipped: {products_skipped}")
        print(f"  Total variants found: {total_variants_found}")
        print(f"  Variants with SKUs: {variants_with_sku}")
        print(f"  Variants without SKUs: {variants_without_sku}")
        
        return products
    
    def get_inventory_levels(self, location_id: Optional[str] = None) -> Dict[str, int]:
        """Get inventory levels for all SKUs at a specific location."""
        if not location_id:
            # Get primary location if none specified
            locations = self._make_request('locations.json')
            if locations.get('locations'):
                location_id = locations['locations'][0]['id']
        
        inventory_levels = {}
        params = {'location_ids': location_id}
        
        response = self._make_request('inventory_levels.json', params)
        
        for level in response.get('inventory_levels', []):
            # Get inventory item details to map to SKU
            item_response = self._make_request(f"inventory_items/{level['inventory_item_id']}.json")
            if item_response.get('inventory_item'):
                sku = item_response['inventory_item'].get('sku')
                if sku:
                    inventory_levels[sku] = level.get('available', 0)
        
        return inventory_levels
    
    def test_connection(self) -> bool:
        """Test if the Shopify connection is working."""
        try:
            response = self._make_request('shop.json')
            return 'shop' in response
        except:
            return False