import requests
import os
from typing import List, Dict, Optional
from datetime import datetime
import time
from .models import Product
from .store_config import get_store_config, DEFAULT_STORE


class ShopifyClient:
    def __init__(self, store_id: str = None):
        """
        Initialize Shopify client for a specific store.

        Args:
            store_id: Store identifier (e.g., "mexico", "usa").
                      Defaults to DEFAULT_STORE if not specified.
        """
        self.store_id = store_id or DEFAULT_STORE
        store_config = get_store_config(self.store_id)

        self.shop_domain = store_config.shop_domain
        self.access_token = store_config.access_token
        self.store_display_name = store_config.display_name
        self.api_version = store_config.api_version
        self.location_name = store_config.location_name
        self.debug = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

        self.base_url = f"https://{self.shop_domain}.myshopify.com/admin/api/{self.api_version}"
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }

        # Cache the location ID once resolved
        self._location_id = None
        
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
            if self.debug:
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
                if self.debug:
                    print(f"Skipping {product_status} product: {product_title}")
                continue

            products_processed += 1
            if self.debug:
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

                if self.debug:
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
                    if self.debug:
                        print(f"    ⚠️ Variant {variant_id} has no SKU")

        if self.debug:
            print(f"\n📊 Product Summary:")
            print(f"  Active products processed: {products_processed}")
            print(f"  Non-active products skipped: {products_skipped}")
            print(f"  Total variants found: {total_variants_found}")
            print(f"  Variants with SKUs: {variants_with_sku}")
            print(f"  Variants without SKUs: {variants_without_sku}")
        
        return products
    
    def get_location_id(self) -> Optional[str]:
        """Get the location ID for this store's configured location."""
        if self._location_id:
            return self._location_id

        locations = self._make_request('locations.json')
        if not locations.get('locations'):
            return None

        # If a specific location name is configured, find it
        if self.location_name:
            for loc in locations['locations']:
                if loc.get('name') == self.location_name:
                    self._location_id = loc['id']
                    if self.debug:
                        print(f"   Using location: {self.location_name} (ID: {self._location_id})")
                    return self._location_id

            # Location name not found, warn and fall back to first
            if self.debug:
                available = [loc.get('name') for loc in locations['locations']]
                print(f"   ⚠️ Location '{self.location_name}' not found. Available: {available}")

        # Fall back to first location
        self._location_id = locations['locations'][0]['id']
        if self.debug:
            print(f"   Using default location: {locations['locations'][0].get('name')} (ID: {self._location_id})")
        return self._location_id

    def get_inventory_levels(self, location_id: Optional[str] = None) -> Dict[str, int]:
        """Get inventory levels for all SKUs at a specific location."""
        if not location_id:
            location_id = self.get_location_id()
        
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
    
    def get_sales_velocity_analytics(self, days: int = 30) -> Dict[str, int]:
        """Get sales velocity by fetching recent orders."""
        if self.debug:
            print(f"📊 Fetching sales data for last {days} days...")

        sales_by_sku = self._get_recent_sales_fallback(days)

        if self.debug:
            print(f"   Found sales data for {len(sales_by_sku)} SKUs")
        return sales_by_sku
    
    def _get_recent_sales_fallback(self, days: int = 30) -> Dict[str, int]:
        """Fallback method to get recent sales from orders with smart pagination."""
        from datetime import datetime, timedelta
        import os
        import json
        
        # Check for cached data first (store-specific cache file)
        cache_file = f'sales_velocity_cache_{self.store_id}.json'
        cache_hours = 6  # Refresh every 6 hours
        
        if os.path.exists(cache_file):
            try:
                cache_time = os.path.getmtime(cache_file)
                hours_old = (datetime.now().timestamp() - cache_time) / 3600

                if hours_old < cache_hours:
                    if self.debug:
                        print(f"   Using cached sales data ({hours_old:.1f} hours old)")
                    with open(cache_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                if self.debug:
                    print(f"   Cache read error: {e}")
        
        from datetime import timezone
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        sales_by_sku = {}
        total_orders_processed = 0
        
        # Use smarter pagination strategy
        params = {
            'status': 'any',
            'created_at_min': start_date.isoformat(),
            'limit': 250,  # Max per request
            'fields': 'line_items,created_at,id'
        }

        if self.debug:
            print(f"   Fetching orders from last {days} days (may take a moment)...")
        
        # Get all orders from the 30-day period with safety limits
        page = 0
        max_orders = 50000  # Safety limit to prevent infinite loops
        
        while total_orders_processed < max_orders:  # Safety limit + date checking
            response = self._make_request('orders.json', params)
            
            if not response or 'orders' not in response:
                break
            
            orders = response['orders']
            if not orders:
                break

            total_orders_processed += len(orders)
            if self.debug:
                print(f"   Page {page + 1}: Processing {len(orders)} orders...")
            
            # Check if we've gone beyond our date range
            oldest_order_in_batch = None
            
            for order in orders:
                order_date_str = order.get('created_at', '')
                if order_date_str:
                    # Parse Shopify datetime (always in UTC with 'Z' suffix)
                    order_date = datetime.fromisoformat(order_date_str.replace('Z', '+00:00'))
                    
                    # Stop if this order is older than our start date
                    if order_date < start_date:
                        if self.debug:
                            print(f"   Reached orders older than {days} days, stopping...")
                        oldest_order_in_batch = order_date
                        break
                    
                    oldest_order_in_batch = order_date
                
                line_items = order.get('line_items', [])
                
                for item in line_items:
                    # Handle None/null SKU safely
                    sku_raw = item.get('sku')
                    sku = sku_raw.strip() if sku_raw else ''
                    quantity = int(item.get('quantity', 0))
                    
                    if sku and quantity > 0:
                        sales_by_sku[sku] = sales_by_sku.get(sku, 0) + quantity
            
            # Stop if we found an order older than our date range
            if oldest_order_in_batch and oldest_order_in_batch < start_date:
                break
            
            # Setup for next page - use the last order's created_at as the new max
            if len(orders) == 250:  # Full page, likely more data
                last_order = orders[-1]
                params['created_at_max'] = last_order.get('created_at')
                page += 1
            else:
                # Partial page, we're done
                break

        if self.debug:
            print(f"   Processed {total_orders_processed} orders total")
            print(f"   Found sales data for {len(sales_by_sku)} SKUs")

        # Cache the results
        try:
            with open(cache_file, 'w') as f:
                json.dump(sales_by_sku, f)
            if self.debug:
                print(f"   Cached sales data for next {cache_hours} hours")
        except Exception as e:
            if self.debug:
                print(f"   Cache write error: {e}")
        
        return sales_by_sku
    
    def clear_sales_cache(self) -> bool:
        """Delete the sales velocity cache file to force fresh data on next load."""
        cache_file = f'sales_velocity_cache_{self.store_id}.json'
        if os.path.exists(cache_file):
            os.remove(cache_file)
            return True
        return False

    def test_connection(self) -> bool:
        """Test if the Shopify connection is working."""
        try:
            response = self._make_request('shop.json')
            return 'shop' in response
        except:
            return False