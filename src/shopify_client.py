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
    
    def get_sales_velocity_analytics(self, days: int = 30) -> Dict[str, int]:
        """Get sales velocity using Shopify Analytics API (efficient)."""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"📊 Fetching sales analytics for last {days} days...")
        
        # Try the Analytics API first
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        # Try different analytics endpoints
        analytics_endpoints = [
            'analytics/reports/products.json',
            'analytics/reports/variants.json',
            'reports/sales_by_product_variant.json'
        ]
        
        sales_by_sku = {}
        
        for endpoint in analytics_endpoints:
            try:
                response = self._make_request(endpoint, params)
                
                if response and 'reports' in response:
                    reports = response['reports']
                    print(f"   Found {len(reports)} analytics reports")
                    
                    for report in reports:
                        # Different report structures possible
                        if 'variant_sku' in report and 'quantity' in report:
                            sku = report['variant_sku']
                            quantity = int(report.get('quantity', 0))
                            if sku:
                                sales_by_sku[sku] = sales_by_sku.get(sku, 0) + quantity
                        
                        elif 'sku' in report and 'units_sold' in report:
                            sku = report['sku'] 
                            quantity = int(report.get('units_sold', 0))
                            if sku:
                                sales_by_sku[sku] = sales_by_sku.get(sku, 0) + quantity
                    
                    if sales_by_sku:
                        print(f"   Successfully got sales data from {endpoint}")
                        break
                        
            except Exception as e:
                print(f"   Analytics endpoint {endpoint} failed: {e}")
                continue
        
        # If analytics API doesn't work, fall back to recent orders (limited)
        if not sales_by_sku:
            print("   Analytics API unavailable, using fallback method...")
            sales_by_sku = self._get_recent_sales_fallback(days)
        
        print(f"   Found sales data for {len(sales_by_sku)} SKUs")
        return sales_by_sku
    
    def _get_recent_sales_fallback(self, days: int = 30) -> Dict[str, int]:
        """Fallback method to get recent sales from orders with smart pagination."""
        from datetime import datetime, timedelta
        import os
        import json
        
        # Check for cached data first
        cache_file = 'sales_velocity_cache.json'
        cache_hours = 6  # Refresh every 6 hours
        
        if os.path.exists(cache_file):
            try:
                cache_time = os.path.getmtime(cache_file)
                hours_old = (datetime.now().timestamp() - cache_time) / 3600
                
                if hours_old < cache_hours:
                    print(f"   Using cached sales data ({hours_old:.1f} hours old)")
                    with open(cache_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
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
        
        print(f"   Processed {total_orders_processed} orders total")
        print(f"   Found sales data for {len(sales_by_sku)} SKUs")
        
        # Cache the results
        try:
            with open(cache_file, 'w') as f:
                json.dump(sales_by_sku, f)
            print(f"   Cached sales data for next {cache_hours} hours")
        except Exception as e:
            print(f"   Cache write error: {e}")
        
        return sales_by_sku
    
    def test_connection(self) -> bool:
        """Test if the Shopify connection is working."""
        try:
            response = self._make_request('shop.json')
            return 'shop' in response
        except:
            return False