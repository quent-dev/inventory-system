# Inventory Management System

A Python-based inventory management system for kit-based products that integrates with Shopify and Google Sheets to calculate effective inventory levels.

## Features

- **Real-time Shopify Integration**: Fetch product inventory data via Shopify Admin API
- **Google Sheets Configuration**: Manage kit compositions and business rules in spreadsheets
- **Effective Inventory Calculation**: Determine how many complete kits can be assembled
- **Interactive Dashboard**: Streamlit-based web interface with charts and analytics
- **What-If Analysis**: Simulate kit disassembly and rebalancing scenarios
- **Alert System**: Identify bottlenecks and low stock situations

## Quick Start

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   export PATH="/home/quent/.local/bin:$PATH"
   ```

2. **Install Dependencies**:
   ```bash
   poetry install
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

4. **Test the System**:
   ```bash
   poetry shell
   python main.py
   ```

5. **Launch Dashboard**:
   ```bash
   streamlit run dashboard.py
   ```

## Configuration

### Required Environment Variables

- `SHOPIFY_SHOP_DOMAIN`: Your Shopify store domain (without .myshopify.com)
- `SHOPIFY_ACCESS_TOKEN`: Shopify Admin API access token
- `GOOGLE_SPREADSHEET_ID`: ID of your Google Sheets document
- `GOOGLE_OAUTH_CREDENTIALS_PATH`: Path to OAuth 2.0 credentials JSON file

### OAuth 2.0 Authentication

The system uses OAuth 2.0 for Google Sheets access:
- First run will open browser for authentication
- Subsequent runs use stored refresh token
- Token stored automatically in `token.pickle`

### Google Sheets Structure

The system expects three worksheets:

1. **Kit Master**: Kit definitions and metadata
2. **Component Mapping**: Kit-to-component relationships
3. **Business Rules**: Inventory rules and thresholds

## Project Structure

```
inventoryagent/
├── src/
│   ├── models.py           # Data models
│   ├── shopify_client.py   # Shopify API integration
│   ├── sheets_client.py    # Google Sheets integration
│   └── inventory_engine.py # Core business logic
├── dashboard.py            # Streamlit dashboard
├── main.py                 # CLI entry point
├── .env.example            # Environment template
└── pyproject.toml          # Poetry configuration
```

## Usage

### CLI Mode
```bash
python main.py
```

### Dashboard Mode
```bash
streamlit run dashboard.py
```

### Development
```bash
poetry shell
# Make changes to code
python main.py  # Test CLI
streamlit run dashboard.py  # Test dashboard
```

## Architecture

- **Data Sources**: Shopify API + Google Sheets
- **Backend**: Python with requests, pandas, gspread
- **Frontend**: Streamlit with Plotly charts
- **Environment**: Poetry for dependency management