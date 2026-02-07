# Inventory Management System - Fixes & Improvements

This document tracks known issues, bugs, and planned improvements for the inventory management system.

## Current Issues

### 🔴 Critical Issues
- [ ] **Issue #006**: Add all products lead times in our GoogleSheet to use with Sales Velocity to calculate next reorder date based on minimum buffer and lead times

- [ ] **Issue #007**: Modify Shopify data structure for "regalos en compra" (gifts with purchase)
  - **Description**: Currently "regalos en compra" appear as duplicate SKUs in sales data, skewing velocity calculations
  - **Impact**: Inaccurate sales velocity and days of stock calculations due to duplicate counting
  - **Solution**: External Shopify restructuring needed:
    - Create separate kit SKUs for "regalos en compra" bundles
    - Map kit components to original individual SKUs
    - Ensure each sale is counted only once per actual SKU
  - **Status**: External task - modify Shopify product structure outside this project

- [ ] **Issue #008**: Add wholesale order forecasting sheet and integration
  - **Description**: Wholesale orders (not tracked in Shopify) need to be factored into days of stock calculations
  - **Impact**: Days of stock calculations are incomplete without wholesale demand forecasting
  - **Files**: `src/sheets_client.py`, `src/models.py`, `dashboard.py`
  - **Solution**: 
    - Add "Wholesale Forecast" sheet to Google Sheets template
    - Include columns: SKU, Forecasted Quantity (30d), Order Date, Customer, Notes
    - Modify daily sales velocity calculation to include wholesale forecasted demand
    - Update days of stock formula: Available Stock ÷ (Shopify Daily Sales + Wholesale Daily Demand)
    - Add wholesale forecast display in dashboard


### 🟡 Medium Priority Issues
- [ ] **Issue #011**: Improve error handling for Google Sheets authentication
  - **Description**: OAuth flow could provide better error messages for common failures
  - **Impact**: User experience during setup
  - **Files**: `src/sheets_client.py`
  - **Solution**: Add specific error handling for common OAuth issues

- [ ] **Issue #013**: Add Google Sheets link to dashboard System Status
  - **Description**: Dashboard doesn't show a direct link to the Google Sheets document
  - **Impact**: User experience - users need to manually find their spreadsheet
  - **Files**: `dashboard.py`
  - **Solution**: Add clickable link to Google Sheets in System Status tab using the GOOGLE_SPREADSHEET_ID

- [ ] **Issue #014**: Add data completeness recap in dashboard
  - **Description**: No visibility into what data is missing or incomplete in Google Sheets
  - **Impact**: Users don't know what to update in their sheets (missing components, empty costs, etc.)
  - **Files**: `dashboard.py`, `src/inventory_engine.py`
  - **Solution**: Add a "Data Completeness" section showing:
    - Kits without component mappings
    - Components referenced but not in Shopify
    - Products missing cost data
    - Components missing business rules
    - Empty/invalid numeric fields

### 🟢 Low Priority Issues
- [ ] **Issue #012**: Add pagination for large product catalogs
  - **Description**: Shopify API only returns 250 products per request
  - **Impact**: Won't load all products for stores with >250 SKUs
  - **Files**: `src/shopify_client.py`
  - **Solution**: Implement pagination to fetch all products

- [ ] **Issue #005**: Add product image support
  - **Description**: Dashboard doesn't show product images
  - **Impact**: User experience - harder to identify products
  - **Files**: `dashboard.py`, `src/models.py`
  - **Solution**: Add image URLs to Product model and display in dashboard

## Planned Features

### 📈 Dashboard Improvements
- [ ] **Feature #001**: Add inventory value calculations
  - **Description**: Show total inventory value and value by product
  - **Priority**: Medium
  - **Estimated Effort**: 2-3 hours

- [ ] **Feature #002**: Add historical inventory tracking
  - **Description**: Track inventory changes over time with charts
  - **Priority**: Low
  - **Estimated Effort**: 1 day

- [ ] **Feature #003**: Add bulk operations for kits
  - **Description**: Bulk create/edit/delete kits in dashboard
  - **Priority**: Medium
  - **Estimated Effort**: 4-6 hours

### 🔧 Technical Improvements
- [ ] **Feature #004**: Add automated testing
  - **Description**: Unit tests for core business logic
  - **Priority**: High
  - **Estimated Effort**: 1-2 days

- [ ] **Feature #005**: Add configuration validation
  - **Description**: Validate Google Sheets structure and data
  - **Priority**: Medium
  - **Estimated Effort**: 3-4 hours

- [ ] **Feature #006**: Add data caching
  - **Description**: Cache API responses to reduce API calls
  - **Priority**: Low
  - **Estimated Effort**: 4-6 hours

### 🚀 Performance Optimizations
- [ ] **Feature #007**: Optimize Shopify API calls
  - **Description**: Batch requests and use more efficient endpoints
  - **Priority**: Medium
  - **Estimated Effort**: 6-8 hours

- [ ] **Feature #008**: Add background data refresh
  - **Description**: Refresh data automatically without blocking UI
  - **Priority**: Low
  - **Estimated Effort**: 1 day

## Completed Fixes

### ✅ Resolved Issues
- [x] **Issue #001**: Fixed double domain issue in Shopify URL construction
  - **Resolved**: 2024-01-05
  - **Solution**: Added domain cleaning to remove duplicate .myshopify.com

- [x] **Issue #002**: Fixed null SKU handling causing crashes
  - **Resolved**: 2024-01-05
  - **Solution**: Added null safety checks for variant SKU processing

- [x] **Issue #003**: Added active products only filter
  - **Resolved**: 2024-01-05
  - **Solution**: Filter Shopify products to exclude archived/draft products

- [x] **Issue #004**: Implemented OAuth 2.0 for Google Sheets
  - **Resolved**: 2024-01-05
  - **Solution**: Replaced service account auth with OAuth to bypass organization policies

- [x] **Issue #001**: Add sales velocity (units sold last 30 days) for each product to calculate Days of Stock left and minimum buffer
  - **Resolved**: 2024-01-05
  - **Solution**: Implemented comprehensive sales velocity tracking with the following features:
    - **Smart order fetching**: Uses Shopify Analytics API with fallback to orders API
    - **Full 30-day coverage**: Fetches all orders from last 30 days (not limited to arbitrary page counts)
    - **Intelligent caching**: 6-hour cache system to avoid repeated expensive API calls
    - **Timezone-aware processing**: Proper UTC datetime handling for accurate date ranges
    - **Performance optimized**: Processes up to 50,000 orders with safety limits
    - **Dashboard integration**: Added sales velocity columns (Units Sold 30d, Daily Sales Rate, Days of Stock, Recommended Buffer)
    - **Advanced filtering**: Filter products by days of stock remaining and sales activity
    - **Null-safe processing**: Handles missing SKUs gracefully during order processing

- [x] **Issue #009**: Add product costs and inventory value calculations
  - **Resolved**: 2024-01-05
  - **Solution**: Implemented comprehensive cost tracking and inventory valuation with the following features:
    - **Product model enhancement**: Added unit_cost field and inventory value calculations
    - **Google Sheets integration**: New "Product Costs" sheet template with columns for SKU, Unit Cost, Currency, Last Updated, Supplier, Notes
    - **Automatic cost loading**: System loads product costs from Google Sheets and applies to inventory calculations
    - **Dashboard financial metrics**: Added Total Inventory Value, High Value Items count, inventory value per product
    - **Advanced filtering**: Filter by "High Value (≥$1K)" and "No Cost Data" to identify costing gaps
    - **Visual indicators**: Color-coded inventory values (light blue for ≥$1K, darker blue for ≥$5K)
    - **Financial insights**: Individual product inventory values displayed alongside operational metrics

- [x] **Issue #010**: Remove debug logging from production Shopify client
  - **Resolved**: 2026-01-11
  - **Solution**: Added DEBUG environment variable to control verbose logging:
    - **Debug flag**: Added `self.debug` flag that reads from `DEBUG` environment variable
    - **Conditional logging**: All verbose print statements now wrapped in `if self.debug:` checks
    - **Production ready**: Clean output in production, detailed logging available when DEBUG=true
    - **Coverage**: Applied to all methods including product fetching, sales velocity, order processing, and caching
    - **Usage**: Set `DEBUG=true` or `DEBUG=1` environment variable to enable verbose logging

## How to Report Issues

1. **Create a new issue entry** in the appropriate section above
2. **Include the following information**:
   - Clear description of the problem
   - Steps to reproduce (if applicable)
   - Expected vs actual behavior
   - Impact on system functionality
   - Suggested solution (if known)

## Priority Levels

- 🔴 **Critical**: System-breaking issues that prevent core functionality
- 🟡 **Medium**: Issues that impact user experience or performance
- 🟢 **Low**: Minor improvements or nice-to-have features

## Contributing

When working on fixes:

1. Move the issue to "In Progress" 
2. Create a branch for the fix (if using git)
3. Test the fix thoroughly
4. Update this document when the issue is resolved
5. Move completed items to the "Completed Fixes" section

---

*Last updated: 2026-01-12*
