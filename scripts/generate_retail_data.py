"""Generate synthetic retail order data for DataForge experiments.

This script creates two CSV files:
- data/raw/orders_clean.csv with realistic, valid retail sales records.
- data/raw/orders_dirty.csv with a small number of intentional data-quality issues.
"""

from datetime import date, timedelta
from pathlib import Path
import random

import pandas as pd


RANDOM_SEED = 42
RECORD_COUNT = 2000
OUTPUT_DIR = Path("data/raw")
CLEAN_OUTPUT_PATH = OUTPUT_DIR / "orders_clean.csv"
DIRTY_OUTPUT_PATH = OUTPUT_DIR / "orders_dirty.csv"


def generate_clean_orders(record_count: int) -> pd.DataFrame:
    """Create a clean synthetic retail orders dataset."""
    start_date = date(2025, 1, 1)
    end_date = start_date + timedelta(days=364)
    date_range_days = (end_date - start_date).days

    orders = []

    for row_number in range(1, record_count + 1):
        order_date = start_date + timedelta(days=random.randint(0, date_range_days))

        orders.append(
            {
                "order_id": f"ORD-{row_number:06d}",
                "customer_id": f"CUST-{random.randint(1, 750):05d}",
                "product_id": f"PROD-{random.randint(1, 250):04d}",
                "store_id": f"STORE-{random.randint(1, 25):03d}",
                "order_date": order_date.isoformat(),
                "quantity": random.randint(1, 8),
                "unit_price": round(random.uniform(4.99, 499.99), 2),
            }
        )

    return pd.DataFrame(orders)


def inject_dirty_data(clean_orders: pd.DataFrame) -> pd.DataFrame:
    """Create a copy of the clean dataset with intentional quality problems."""
    dirty_orders = clean_orders.copy()

    duplicate_indices = random.sample(range(RECORD_COUNT), 30)
    missing_customer_indices = random.sample(range(RECORD_COUNT), 25)
    negative_quantity_indices = random.sample(range(RECORD_COUNT), 20)
    negative_price_indices = random.sample(range(RECORD_COUNT), 15)
    invalid_date_indices = random.sample(range(RECORD_COUNT), 18)
    invalid_product_indices = random.sample(range(RECORD_COUNT), 22)

    for row_index in duplicate_indices:
        source_index = random.randint(0, row_index - 1) if row_index > 0 else 1
        dirty_orders.loc[row_index, "order_id"] = dirty_orders.loc[source_index, "order_id"]

    dirty_orders.loc[missing_customer_indices, "customer_id"] = None
    dirty_orders.loc[negative_quantity_indices, "quantity"] = -random.randint(1, 5)
    dirty_orders.loc[negative_price_indices, "unit_price"] = -round(random.uniform(1.0, 200.0), 2)
    dirty_orders.loc[invalid_date_indices, "order_date"] = "not-a-date"
    dirty_orders.loc[invalid_product_indices, "product_id"] = "INVALID"

    return dirty_orders


def print_dirty_data_summary(dirty_orders: pd.DataFrame) -> None:
    """Print a concise summary of injected data-quality issues."""
    parsed_dates = pd.to_datetime(dirty_orders["order_date"], errors="coerce")

    print("Synthetic retail data generated")
    print(f"total records: {len(dirty_orders)}")
    print(f"duplicate order IDs: {dirty_orders['order_id'].duplicated(keep=False).sum()}")
    print(f"missing customer IDs: {dirty_orders['customer_id'].isna().sum()}")
    print(f"negative quantities: {(dirty_orders['quantity'] < 0).sum()}")
    print(f"negative unit prices: {(dirty_orders['unit_price'] < 0).sum()}")
    print(f"invalid dates: {parsed_dates.isna().sum()}")
    print(f"invalid product IDs: {(dirty_orders['product_id'] == 'INVALID').sum()}")


def main() -> None:
    """Generate clean and dirty retail order CSV files."""
    random.seed(RANDOM_SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    clean_orders = generate_clean_orders(RECORD_COUNT)
    dirty_orders = inject_dirty_data(clean_orders)

    clean_orders.to_csv(CLEAN_OUTPUT_PATH, index=False)
    dirty_orders.to_csv(DIRTY_OUTPUT_PATH, index=False)

    print_dirty_data_summary(dirty_orders)


if __name__ == "__main__":
    main()
