# Google Sheets Structure for Inventory Management System

This document details the required structure for all Google Sheets tabs that work with the inventory management system.

## Required Sheets Overview

The system supports multiple Shopify stores from a single spreadsheet. Each store has its own set of tabs with a store suffix appended to the base name.

### Tab Naming Convention

| Base Name | Mexico Tab | USA Tab |
|-----------|-----------|---------|
| Kit Master | Kit Master - Mexico | Kit Master - USA |
| Component Mapping | Component Mapping - Mexico | Component Mapping - USA |
| Business Rules | Business Rules - Mexico | Business Rules - USA |
| Product Costs | Product Costs - Mexico | Product Costs - USA |

All four tabs are required per store. The column structure is identical across stores — only the tab name and data differ.

---

## 1. Kit Master (per store)

**Tab names**: `Kit Master - Mexico`, `Kit Master - USA`

**Purpose**: Define kit products and their basic information.

### Column Structure
| Column | Data Type | Required | Description | Example |
|--------|-----------|----------|-------------|---------|
| Kit SKU | Text | Yes | Unique identifier for the kit | KIT-STARTER-001 |
| Kit Name | Text | Yes | Display name for the kit | Starter Makeup Kit |
| Kit Description | Text | No | Detailed description | Basic makeup essentials for beginners |
| Kit Price | Number | Yes | Selling price of the kit | 49.99 |
| Active/Inactive Status | Text | Yes | Whether kit is currently active | Active |
| Created Date | Date | No | When the kit was created | 2024-01-01 |
| Last Modified Date | Date | No | When the kit was last updated | 2024-01-05 |

### Sample Data
```
Kit SKU              | Kit Name            | Kit Description              | Kit Price | Active/Inactive Status | Created Date | Last Modified Date
KIT-STARTER-001      | Starter Makeup Kit  | Basic makeup essentials     | 49.99     | Active                | 2024-01-01   | 2024-01-01
KIT-PREMIUM-001      | Premium Beauty Kit  | Complete beauty collection  | 89.99     | Active                | 2024-01-01   | 2024-01-01
KIT-TRAVEL-001       | Travel Kit          | Compact travel-sized items  | 29.99     | Inactive              | 2024-01-01   | 2024-01-05
```

---

## 2. Component Mapping (per store)

**Tab names**: `Component Mapping - Mexico`, `Component Mapping - USA`

**Purpose**: Define which individual products (components) make up each kit and in what quantities.

### Column Structure
| Column | Data Type | Required | Description | Example |
|--------|-----------|----------|-------------|---------|
| Kit SKU | Text | Yes | Must match a Kit SKU from Kit Master | KIT-STARTER-001 |
| Component SKU | Text | Yes | Must match a SKU from Shopify | SCL-0033 |
| Component Name | Text | No | Display name for the component | Red Lipstick |
| Quantity per Kit | Number | Yes | How many units needed per kit | 1 |
| Component Cost | Number | No | Cost of this component | 8.50 |
| Is Critical Component (Y/N) | Text | Yes | Y if required, N if optional | Y |

### Sample Data
```
Kit SKU         | Component SKU | Component Name      | Quantity per Kit | Component Cost | Is Critical Component (Y/N)
KIT-STARTER-001 | SCL-0033     | Red Lipstick        | 1               | 8.50          | Y
KIT-STARTER-001 | SCL-0117     | Light Foundation    | 1               | 12.00         | Y
KIT-STARTER-001 | SCL-0045     | Black Mascara       | 1               | 6.75          | Y
KIT-PREMIUM-001 | SCL-0033     | Red Lipstick        | 2               | 8.50          | Y
KIT-PREMIUM-001 | SCL-0117     | Light Foundation    | 1               | 12.00         | Y
KIT-PREMIUM-001 | SCL-0089     | Eyeshadow Palette   | 1               | 15.00         | Y
```

### Important Notes
- **Component SKUs must exist in Shopify** - The system will flag missing SKUs as data issues
- **Quantity per Kit** can be fractional (e.g., 0.5 for half units)
- **Critical Components** marked "Y" will prevent kit assembly if out of stock

---

## 3. Business Rules (per store)

**Tab names**: `Business Rules - Mexico`, `Business Rules - USA`

**Purpose**: Define inventory management rules and thresholds for individual components.

### Column Structure
| Column | Data Type | Required | Description | Example |
|--------|-----------|----------|-------------|---------|
| Component SKU | Text | Yes | Must match a SKU from Shopify | SCL-0033 |
| Minimum Buffer Stock | Number | Yes | Safety stock level | 5 |
| Maximum Kit Assembly Quantity | Number | Yes | Max kits to assemble at once | 100 |
| Lead Time for Component Restocking (days) | Number | Yes | Days to restock this component | 7 |
| Assembly/Disassembly Labor Time (minutes) | Number | Yes | Time to process this component | 5 |
| Priority Level (High/Medium/Low) | Text | Yes | Restocking priority | High |

### Sample Data
```
Component SKU | Minimum Buffer Stock | Maximum Kit Assembly Quantity | Lead Time for Component Restocking (days) | Assembly/Disassembly Labor Time (minutes) | Priority Level (High/Medium/Low)
SCL-0033     | 5                   | 100                          | 7                                         | 5                                         | High
SCL-0117     | 3                   | 50                           | 14                                        | 10                                        | High
SCL-0045     | 10                  | 200                          | 7                                         | 3                                         | Medium
SCL-0089     | 2                   | 25                           | 21                                        | 15                                        | Medium
```

### Business Logic
- **Minimum Buffer Stock**: Subtracted from available stock in effective inventory calculations
- **Lead Time**: Used for reorder point calculations and forecasting
- **Priority Level**: Affects reorder recommendations (High priority items reordered first)

---

## 4. Product Costs (per store)

**Tab names**: `Product Costs - Mexico`, `Product Costs - USA`

**Purpose**: Track product costs for inventory valuation and financial analysis.

### Column Structure
| Column | Data Type | Required | Description | Example |
|--------|-----------|----------|-------------|---------|
| SKU | Text | Yes | Must match a SKU from Shopify | SCL-0033 |
| Unit Cost | Number | Yes | Cost per unit (manual or auto-calculated) | 4.25 |
| Cost Currency | Text | No | Currency for the cost | USD |
| Last Updated | Date | No | When cost was last updated | 2024-01-05 |
| Supplier | Text | No | Who supplies this product | Beauty Supply Co |
| Notes | Text | No | Additional cost information | Volume discount applied |
| Manual Override (Y/N) | Text | No | Y = use manual cost, N/blank = auto-calculate if kit | N |

### Sample Data
```
SKU         | Unit Cost | Cost Currency | Last Updated | Supplier           | Notes                    | Manual Override (Y/N)
SCL-0033    | 4.25     | USD          | 2024-01-05   | Beauty Supply Co   | Volume discount applied  | N
SCL-0117    | 6.00     | USD          | 2024-01-04   | Cosmetics Inc      |                         | N  
SCL-0045    | 3.75     | USD          | 2024-01-05   | Beauty Supply Co   | Bulk order pricing      | N
SCL-0089    | 8.50     | USD          | 2024-01-03   | Premium Makeup Ltd | Limited edition cost    | N
KIT-001     | 25.00    | USD          | 2024-01-05   | Internal           | Auto-calculated from components | N
KIT-002     | 40.00    | USD          | 2024-01-05   | Internal           | Manual cost for labor   | Y
```

### Kit Cost Calculation Logic

The system automatically calculates costs for kit SKUs based on their components:

**Automatic Kit Detection:**
- If a SKU exists in both "Kit Master" and "Product Costs" sheets
- AND "Manual Override" is NOT set to "Y"
- THEN cost is auto-calculated from components

**Calculation Formula:**
```
Kit Cost = Σ (Component Cost × Quantity per Kit)
```

**Example:**
```
KIT-STARTER-001 components:
- SCL-0033 (Red Lipstick): $4.25 × 1 = $4.25
- SCL-0117 (Foundation): $6.00 × 1 = $6.00  
- SCL-0045 (Mascara): $3.75 × 1 = $3.75
Total Kit Cost = $14.00 (auto-calculated)
```

**Manual Override:**
- Set "Manual Override (Y/N)" = "Y" to use manual cost entry
- Useful for: labor costs, packaging, special pricing
- System will use "Unit Cost" value instead of calculating from components

### Financial Calculations
- **Inventory Value** = Available Stock × Unit Cost
- **Total Inventory Value** = Sum of all product inventory values
- **High Value Items** = Products with inventory value ≥ $1,000

---

## Setup Instructions

### 1. Create Google Sheets Document
1. Create a new Google Sheets document
2. Name it "Inventory Kit Management" (or your preferred name)
3. Copy the Spreadsheet ID from the URL

### 2. Add Required Worksheets
The system will automatically create worksheets with proper headers when you run it for the first time. Alternatively, you can create them manually.

Create the following tabs for **each store** you want to use:

**Mexico store:**
- `Kit Master - Mexico`
- `Component Mapping - Mexico`
- `Business Rules - Mexico`
- `Product Costs - Mexico`

**USA store:**
- `Kit Master - USA`
- `Component Mapping - USA`
- `Business Rules - USA`
- `Product Costs - USA`

Add headers (first row) exactly as specified in the column structures above. The column structure is the same for all stores.

### 3. Share with Service Account (OAuth)
1. Share the spreadsheet with your OAuth-authenticated Google account
2. Ensure the account has "Editor" permissions

### 4. Populate Sample Data
1. Add your actual kit definitions to **Kit Master**
2. Map kit components in **Component Mapping** (use real Shopify SKUs)
3. Set inventory rules in **Business Rules** for key components
4. Add product costs in **Product Costs** for financial tracking

---

## Data Validation Rules

### Required Field Validation
- All fields marked "Required" must have values
- Empty required fields will be ignored by the system

### Data Type Validation
- **Numbers**: Must be valid numeric values (decimals allowed)
- **Dates**: Accepted formats: YYYY-MM-DD or MM/DD/YYYY
- **Text**: Any text value accepted

### Cross-Reference Validation
- **Component SKUs** in Component Mapping and Business Rules must exist in Shopify
- **Kit SKUs** in Component Mapping must exist in Kit Master
- System will report validation issues in the dashboard "System Status" tab

---

## Common Issues & Troubleshooting

### "Component not found in Shopify" Error
- **Cause**: Component SKU in sheets doesn't match any Shopify product SKU
- **Solution**: Verify SKU spelling and ensure product is active in Shopify

### "Kit has no components" Warning
- **Cause**: Kit SKU in Kit Master has no corresponding entries in Component Mapping
- **Solution**: Add component mappings for the kit

### "No cost data" in Dashboard
- **Cause**: Products missing from Product Costs sheet
- **Solution**: Add cost information for missing SKUs

### Sheet Not Found Error
- **Cause**: Worksheet name doesn't match exactly (case-sensitive, including the store suffix)
- **Solution**: Ensure worksheet names match exactly, including the store suffix. For example: `Kit Master - Mexico`, `Kit Master - USA`, `Component Mapping - Mexico`, etc.

---

## Best Practices

### Data Entry
1. **Use consistent SKU format** across all sheets
2. **Keep component names descriptive** for easy identification
3. **Update costs regularly** to maintain accurate inventory valuations
4. **Use business rules** for all critical components

### Maintenance
1. **Review kit compositions monthly** to ensure accuracy
2. **Update lead times seasonally** based on supplier performance  
3. **Audit cost data quarterly** for pricing changes
4. **Archive inactive kits** rather than deleting them

### Performance
1. **Limit to 1000 rows per sheet** for optimal performance
2. **Use data validation** in Google Sheets to prevent input errors
3. **Regularly clean up** outdated or duplicate entries