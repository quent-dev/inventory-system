# Inventory MVP Phase 1 Implementation Plan

## **Architecture Overview**

**Recommended Approach**: Python + Streamlit + Google Sheets hybrid

```
Shopify API → Python Backend → Streamlit Dashboard
                ↓
           Google Sheets (Data Storage & Manual Override)
```

## **Tool Comparison Analysis**

### **Python + Streamlit (Recommended)**
- ✅ Full control over logic and data processing
- ✅ Easy integration with Shopify API
- ✅ Can build custom dashboards with Streamlit/Plotly
- ✅ Better for complex calculations and data transformations
- ✅ You're already familiar with it
- ❌ Requires more initial setup time

### **ReTool Alternative**
- ✅ Quick visual dashboard creation
- ✅ Built-in integrations with APIs
- ✅ Good for non-technical team members
- ❌ Monthly subscription cost (~$10-50/user)
- ❌ Learning curve required
- ❌ Less flexibility for complex logic

### **Google Sheets Role**
- ✅ Familiar to all team members
- ✅ Easy collaboration and sharing
- ✅ Perfect for manual data entry and overrides
- ❌ Limited for real-time API processing
- ❌ Performance issues with large datasets

## **Implementation Components**

### **1. Python Backend** (`inventory_engine.py`)
- Shopify API integration and authentication
- Bundle composition logic and calculations
- Effective inventory algorithms
- Data validation and error handling
- Real-time data synchronization

### **2. Streamlit Dashboard** (`dashboard.py`)
- Real-time inventory visualization
- Effective inventory calculator
- Alert system for low stock scenarios
- Manual override capabilities
- What-if analysis tools

### **3. Google Sheets Integration**
- Kit composition master data
- Historical tracking and audit log
- Manual adjustments and overrides
- Team collaboration workspace

## **Required Kit Information Structure**

### **Kit Master Data (Google Sheets)**
```
- Kit SKU (e.g., "KIT-STARTER-001")
- Kit Name (e.g., "Starter Makeup Kit")
- Kit Description
- Kit Price
- Active/Inactive Status
- Created Date
- Last Modified Date
```

### **Component Mapping**
```
- Kit SKU
- Component SKU (e.g., "LIPSTICK-RED-001")
- Component Name
- Quantity per Kit (e.g., 1, 2, 0.5 for partial units)
- Component Cost
- Is Critical Component (Y/N) - if out of stock, can't make kit
```

### **Business Rules**
```
- Minimum Buffer Stock per Component
- Maximum Kit Assembly Quantity
- Lead Time for Component Restocking (days)
- Assembly/Disassembly Labor Time (minutes)
- Priority Level (High/Medium/Low)
```

### **Current Inventory Data (from Shopify)**
```
- SKU
- Current Stock Level
- Reserved Stock (for pending orders)
- Available Stock
- Last Updated Timestamp
```

## **Week-by-Week Implementation**

### **Week 1: Foundation**
1. **Day 1-2**: Set up Shopify API connection and authentication
2. **Day 3**: Create Google Sheets template for kit composition data
3. **Day 4-5**: Build basic Python data ingestion script
4. **Day 6**: Implement effective inventory calculation logic
5. **Day 7**: Create simple Streamlit prototype

### **Week 2: Enhancement & Testing**
1. **Day 8-9**: Add data validation and error handling
2. **Day 10-11**: Build comprehensive dashboard with charts/tables
3. **Day 12**: Implement alert system for low stock scenarios
4. **Day 13**: Add manual override functionality
5. **Day 14**: Test with sample kit data and validate accuracy

## **Key Dashboard Features**

### **1. Real-time Effective Inventory Display**
- Show how many complete kits can be made
- Highlight bottleneck components
- Display days of stock remaining
- Color-coded status indicators

### **2. Alert System**
- Low stock warnings with thresholds
- Impossible kit combination alerts
- Stale data notifications
- Manual intervention required flags

### **3. What-if Analysis Tools**
- "If we disassemble X kits, how many individual items do we get?"
- "What happens to kit availability if we sell Y units of component Z?"
- Impact simulation for rebalancing decisions

### **4. Data Validation Features**
- Cross-check Shopify data with manual counts
- Flag discrepancies for investigation
- Audit trail for all changes
- Data freshness indicators

## **Technical Requirements**

### **Virtual Environment Management**

#### **Poetry Setup (Recommended)**
```bash
# Install Poetry (one-time setup)
curl -sSL https://install.python-poetry.org | python3 -

# Initialize inventory project
poetry init
poetry add streamlit requests pandas plotly gspread python-dotenv
poetry add --group dev pytest black flake8

# Activate environment
poetry shell

# Install dependencies
poetry install
```

#### **Project Isolation**
- Use Poetry for this inventory project (clean dependency management)
- Keep existing `/home/quent/sarelly-venv/` for current automation scripts
- Separate environments prevent dependency conflicts

### **Python Libraries Needed**
```python
- streamlit (dashboard framework)
- requests (Shopify API calls)
- pandas (data manipulation)
- plotly (interactive charts)
- gspread (Google Sheets integration)
- python-dotenv (environment variables)
```

### **API Credentials Required**
- Shopify Admin API access token
- Google Sheets API service account
- Environment variables for secure credential storage

## **Success Criteria**

1. **Accuracy**: 99%+ match between calculated and actual effective inventory
2. **Performance**: Dashboard loads in <3 seconds
3. **Usability**: Non-technical team members can use without training
4. **Reliability**: System handles API failures gracefully
5. **Scalability**: Can process 100+ SKUs and 50+ kit combinations

## **Risk Mitigation**

- **API Rate Limits**: Implement exponential backoff and caching
- **Data Inconsistency**: Add validation checks and manual override capabilities
- **System Downtime**: Build offline mode with cached data
- **User Errors**: Implement confirmation dialogs for critical actions

---

**Next Steps**: Begin Week 1 implementation with Shopify API setup and Google Sheets template creation.
