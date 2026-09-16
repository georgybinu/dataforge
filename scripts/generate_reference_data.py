"""Generate synthetic reference data for DataForge retail orders.

The generated reference datasets cover the legitimate customer, product, and
store IDs used by scripts/generate_retail_data.py.
"""

from pathlib import Path
import random

import pandas as pd


RANDOM_SEED = 42
OUTPUT_DIR = Path("data/raw")

CUSTOMERS_OUTPUT_PATH = OUTPUT_DIR / "customers.csv"
PRODUCTS_OUTPUT_PATH = OUTPUT_DIR / "products.csv"
STORES_OUTPUT_PATH = OUTPUT_DIR / "stores.csv"

CITIES = [
    "Austin",
    "Boston",
    "Chicago",
    "Denver",
    "Miami",
    "New York",
    "Phoenix",
    "San Diego",
    "Seattle",
    "Atlanta",
]

PRODUCT_CATEGORIES = [
    "Apparel",
    "Electronics",
    "Grocery",
    "Home",
    "Office",
    "Outdoor",
    "Personal Care",
    "Toys",
]


def generate_customers(record_count: int = 750) -> pd.DataFrame:
    """Create customer reference records."""
    customers = []

    for customer_number in range(1, record_count + 1):
        customers.append(
            {
                "customer_id": f"CUST-{customer_number:05d}",
                "customer_name": f"Customer {customer_number:05d}",
                "city": random.choice(CITIES),
            }
        )

    return pd.DataFrame(customers)


def generate_products(record_count: int = 250) -> pd.DataFrame:
    """Create product reference records."""
    products = []

    for product_number in range(1, record_count + 1):
        category = random.choice(PRODUCT_CATEGORIES)
        products.append(
            {
                "product_id": f"PROD-{product_number:04d}",
                "product_name": f"{category} Product {product_number:04d}",
                "category": category,
            }
        )

    return pd.DataFrame(products)


def generate_stores(record_count: int = 25) -> pd.DataFrame:
    """Create store reference records."""
    stores = []

    for store_number in range(1, record_count + 1):
        stores.append(
            {
                "store_id": f"STORE-{store_number:03d}",
                "store_name": f"Store {store_number:03d}",
                "city": random.choice(CITIES),
            }
        )

    return pd.DataFrame(stores)


def main() -> None:
    """Write synthetic reference datasets to data/raw."""
    random.seed(RANDOM_SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    customers = generate_customers()
    products = generate_products()
    stores = generate_stores()

    customers.to_csv(CUSTOMERS_OUTPUT_PATH, index=False)
    products.to_csv(PRODUCTS_OUTPUT_PATH, index=False)
    stores.to_csv(STORES_OUTPUT_PATH, index=False)

    print("Reference data generated")
    print(f"customers: {len(customers)} records -> {CUSTOMERS_OUTPUT_PATH}")
    print(f"products: {len(products)} records -> {PRODUCTS_OUTPUT_PATH}")
    print(f"stores: {len(stores)} records -> {STORES_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
