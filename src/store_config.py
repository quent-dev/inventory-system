"""
Store configuration module for multi-store Shopify support.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class StoreConfig:
    """Configuration for a single Shopify store."""
    store_id: str
    display_name: str
    shop_domain: str
    access_token: str
    sheet_suffix: str
    api_version: str
    location_name: Optional[str]  # Preferred location name for inventory


# Registry of supported stores
SUPPORTED_STORES = {
    "mexico": {
        "display_name": "Mexico",
        "env_suffix": "_MX",
        "sheet_suffix": " - Mexico",
        "api_version": "2024-01",
        "location_name": "Segmail",
    },
    "usa": {
        "display_name": "USA",
        "env_suffix": "_US",
        "sheet_suffix": " - USA",
        "api_version": "2026-01",
        "location_name": "Sage Distribution",
    },
}

DEFAULT_STORE = "mexico"


def get_store_config(store_id: str = None) -> StoreConfig:
    """
    Get store configuration with credentials from environment variables.

    Args:
        store_id: Store identifier (e.g., "mexico", "usa").
                  Defaults to DEFAULT_STORE if not specified.

    Returns:
        StoreConfig with credentials loaded from environment.

    Raises:
        ValueError: If store_id is not supported or credentials are missing.
    """
    if store_id is None:
        store_id = DEFAULT_STORE

    store_id = store_id.lower()

    if store_id not in SUPPORTED_STORES:
        raise ValueError(
            f"Unsupported store: '{store_id}'. "
            f"Supported stores: {', '.join(SUPPORTED_STORES.keys())}"
        )

    store_info = SUPPORTED_STORES[store_id]
    env_suffix = store_info["env_suffix"]

    # Try store-specific env vars first, fall back to legacy vars for Mexico
    shop_domain = os.getenv(f'SHOPIFY_SHOP_DOMAIN{env_suffix}')
    access_token = os.getenv(f'SHOPIFY_ACCESS_TOKEN{env_suffix}')

    # Backwards compatibility: Fall back to legacy env vars for Mexico store
    if store_id == "mexico":
        if not shop_domain:
            shop_domain = os.getenv('SHOPIFY_SHOP_DOMAIN')
        if not access_token:
            access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')

    if not shop_domain or not access_token:
        env_var_names = f"SHOPIFY_SHOP_DOMAIN{env_suffix} and SHOPIFY_ACCESS_TOKEN{env_suffix}"
        raise ValueError(
            f"Missing Shopify credentials for {store_info['display_name']} store. "
            f"Set {env_var_names} environment variables."
        )

    return StoreConfig(
        store_id=store_id,
        display_name=store_info["display_name"],
        shop_domain=shop_domain,
        access_token=access_token,
        sheet_suffix=store_info["sheet_suffix"],
        api_version=store_info["api_version"],
        location_name=store_info.get("location_name"),
    )


def get_available_stores() -> Dict[str, str]:
    """
    Get dictionary of stores that have credentials configured.

    Returns:
        Dict mapping store_id to display_name for stores with valid credentials.
    """
    available = {}

    for store_id, store_info in SUPPORTED_STORES.items():
        try:
            config = get_store_config(store_id)
            available[store_id] = config.display_name
        except ValueError:
            # Store credentials not configured, skip
            continue

    return available


def get_all_stores() -> Dict[str, str]:
    """
    Get dictionary of all supported stores (whether configured or not).

    Returns:
        Dict mapping store_id to display_name for all supported stores.
    """
    return {
        store_id: info["display_name"]
        for store_id, info in SUPPORTED_STORES.items()
    }
