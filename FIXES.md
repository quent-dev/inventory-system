# Inventory Management System - Fixes & Improvements

This document tracks known issues, bugs, and planned improvements for the inventory management system.

## Current Issues

### 🔴 Critical Issues
- [ ] **Issue #001**: Add sales velocity (units sold last 30 days) for each product to be able to calculate Days of Stock left and minimum buffer for all products.

- [ ] **Issue #006**: Add all products lead times in our GoogleSheet to use with Sales Velocity to calculate next reorder date based on minimum buffer and lead times

### 🟡 Medium Priority Issues
- [ ] **Issue #002**: Remove debug logging from production Shopify client
  - **Description**: Shopify API calls currently print detailed product/variant information to console
  - **Impact**: Performance and clean output in production
  - **Files**: `src/shopify_client.py`
  - **Solution**: Add DEBUG environment variable to control verbose logging

- [ ] **Issue #003**: Improve error handling for Google Sheets authentication
  - **Description**: OAuth flow could provide better error messages for common failures
  - **Impact**: User experience during setup
  - **Files**: `src/sheets_client.py`
  - **Solution**: Add specific error handling for common OAuth issues

### 🟢 Low Priority Issues
- [ ] **Issue #004**: Add pagination for large product catalogs
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

*Last updated: 2024-01-05*
