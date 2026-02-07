# Inventory Management System

A Python-based inventory management system for kit-based products that integrates with Shopify and Google Sheets to calculate effective inventory levels.

## Features

- **Real-time Shopify Integration**: Fetch product inventory data via Shopify Admin API
- **Google Sheets Configuration**: Manage kit compositions and business rules in spreadsheets
- **Effective Inventory Calculation**: Determine how many complete kits can be assembled
- **Interactive Dashboard**: Streamlit-based web interface with charts and analytics
- **What-If Analysis**: Simulate kit disassembly and rebalancing scenarios
- **Alert System**: Identify bottlenecks and low stock situations
- **Multi-Store Support**: Manage multiple Shopify stores (e.g., Mexico, USA) from one system

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

Each Shopify store requires its own credentials with a store suffix:

| Variable | Description |
|----------|-------------|
| `SHOPIFY_SHOP_DOMAIN_MX` | Mexico store domain (without .myshopify.com) |
| `SHOPIFY_ACCESS_TOKEN_MX` | Mexico store Admin API access token |
| `SHOPIFY_SHOP_DOMAIN_US` | USA store domain (without .myshopify.com) |
| `SHOPIFY_ACCESS_TOKEN_US` | USA store Admin API access token |
| `GOOGLE_SPREADSHEET_ID` | ID of your Google Sheets document |
| `GOOGLE_OAUTH_CREDENTIALS_PATH` | Path to OAuth 2.0 credentials JSON file |

For backwards compatibility, the Mexico store falls back to `SHOPIFY_SHOP_DOMAIN` and `SHOPIFY_ACCESS_TOKEN` if the `_MX` variants are not set.

### Optional Environment Variables

- `DEBUG`: Enable verbose logging for troubleshooting (set to `true`, `1`, or `yes`)

### OAuth 2.0 Authentication

The system uses OAuth 2.0 for Google Sheets access:
- First run will open browser for authentication
- Subsequent runs use stored refresh token
- Token stored automatically in `token.pickle`

### Google Sheets Structure

The system uses a single spreadsheet with store-specific tabs. Each store has its own set of worksheets:

| Base Name | Mexico Tab | USA Tab |
|-----------|-----------|---------|
| Kit Master | Kit Master - Mexico | Kit Master - USA |
| Component Mapping | Component Mapping - Mexico | Component Mapping - USA |
| Business Rules | Business Rules - Mexico | Business Rules - USA |
| Product Costs | Product Costs - Mexico | Product Costs - USA |

## Project Structure

```
inventoryagent/
├── src/
│   ├── models.py           # Data models
│   ├── store_config.py     # Multi-store configuration
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
python main.py                  # Default store (Mexico)
python main.py --store mexico   # Explicit Mexico store
python main.py --store usa      # USA store
python main.py --list-stores    # Show available stores and config status
python main.py --help           # Show all options
```

### Dashboard Mode

```bash
streamlit run dashboard.py
```

The dashboard includes a store selector dropdown in the sidebar. Switching stores clears the current session and loads data for the selected store.

### Development

```bash
poetry shell
# Make changes to code
python main.py --store usa  # Test CLI against a specific store
streamlit run dashboard.py  # Test dashboard (store selected in UI)
```

## Architecture

- **Data Sources**: Shopify API + Google Sheets
- **Backend**: Python with requests, pandas, gspread
- **Frontend**: Streamlit with Plotly charts
- **Environment**: Poetry for dependency management