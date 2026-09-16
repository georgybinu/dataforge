"""End-to-end quality pipeline for retail order data.

The pipeline reads dirty retail order CSV data, runs DataForge quality checks,
and writes valid records to Silver and rejected records to Quarantine.
"""

from pathlib import Path
from typing import Any, Union

import pandas as pd

from src.validation.data_quality import run_quality_checks


DEFAULT_INPUT_PATH = Path("data/raw/orders_dirty.csv")
DEFAULT_CUSTOMERS_PATH = Path("data/raw/customers.csv")
DEFAULT_PRODUCTS_PATH = Path("data/raw/products.csv")
DEFAULT_STORES_PATH = Path("data/raw/stores.csv")
DEFAULT_SILVER_OUTPUT_PATH = Path("data/silver/orders_valid.parquet")
DEFAULT_QUARANTINE_OUTPUT_PATH = Path("data/quarantine/orders_invalid.parquet")


def _read_csv_file(path: Path, description: str) -> pd.DataFrame:
    """Read a CSV file or raise a clear error when it is missing."""
    if not path.exists():
        raise FileNotFoundError(f"{description} CSV file not found: {path}")

    return pd.read_csv(path)


def build_retail_order_rules(
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
    stores_df: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    """Build retail order quality rules using loaded reference data."""
    return {
        "order_id_unique": {"type": "unique", "column": "order_id"},
        "customer_required": {"type": "not_null", "columns": ["customer_id"]},
        "quantity_positive": {"type": "positive", "column": "quantity"},
        "price_non_negative": {"type": "non_negative", "column": "unit_price"},
        "customer_referential_integrity": {
            "type": "referential_integrity",
            "column": "customer_id",
            "reference_df": customers_df,
            "reference_column": "customer_id",
        },
        "product_referential_integrity": {
            "type": "referential_integrity",
            "column": "product_id",
            "reference_df": products_df,
            "reference_column": "product_id",
        },
        "store_referential_integrity": {
            "type": "referential_integrity",
            "column": "store_id",
            "reference_df": stores_df,
            "reference_column": "store_id",
        },
    }


def run_quality_pipeline(
    input_path: Union[str, Path] = DEFAULT_INPUT_PATH,
    customers_path: Union[str, Path] = DEFAULT_CUSTOMERS_PATH,
    products_path: Union[str, Path] = DEFAULT_PRODUCTS_PATH,
    stores_path: Union[str, Path] = DEFAULT_STORES_PATH,
    silver_output_path: Union[str, Path] = DEFAULT_SILVER_OUTPUT_PATH,
    quarantine_output_path: Union[str, Path] = DEFAULT_QUARANTINE_OUTPUT_PATH,
) -> dict[str, Any]:
    """Run quality checks and write valid and invalid retail order records.

    Args:
        input_path: CSV file containing retail order records.
        customers_path: CSV file containing valid customers.
        products_path: CSV file containing valid products.
        stores_path: CSV file containing valid stores.
        silver_output_path: Parquet path for valid records.
        quarantine_output_path: Parquet path for invalid records.

    Returns:
        A summary dictionary with record counts, rejection rate, and status.

    Raises:
        FileNotFoundError: If the input CSV file does not exist.
        ValueError: If required validation columns are missing.
    """
    input_file = Path(input_path)
    customers_file = Path(customers_path)
    products_file = Path(products_path)
    stores_file = Path(stores_path)
    silver_file = Path(silver_output_path)
    quarantine_file = Path(quarantine_output_path)

    orders = _read_csv_file(input_file, "Input")
    customers = _read_csv_file(customers_file, "Customers reference")
    products = _read_csv_file(products_file, "Products reference")
    stores = _read_csv_file(stores_file, "Stores reference")

    rules = build_retail_order_rules(customers, products, stores)
    validation_results = run_quality_checks(orders, rules)

    orders_with_results = orders.copy()
    orders_with_results["is_valid"] = validation_results["is_valid"]
    orders_with_results["failed_rules"] = validation_results["failed_rules"]

    valid_records = orders_with_results[orders_with_results["is_valid"]].copy()
    invalid_records = orders_with_results[~orders_with_results["is_valid"]].copy()

    valid_records = valid_records.drop(columns=["is_valid", "failed_rules"])
    invalid_records["failed_rules"] = invalid_records["failed_rules"].apply(", ".join)
    invalid_records = invalid_records.drop(columns=["is_valid"])

    silver_file.parent.mkdir(parents=True, exist_ok=True)
    quarantine_file.parent.mkdir(parents=True, exist_ok=True)

    valid_records.to_parquet(silver_file, index=False)
    invalid_records.to_parquet(quarantine_file, index=False)

    total_records = len(orders)
    rejected_records = len(invalid_records)
    rejection_rate = rejected_records / total_records if total_records else 0.0

    return {
        "total_records": total_records,
        "valid_records": len(valid_records),
        "rejected_records": rejected_records,
        "rejection_rate": rejection_rate,
        "status": "success",
    }


def main() -> None:
    """Run the default retail order quality pipeline and print a summary."""
    summary = run_quality_pipeline()

    print("DataForge quality pipeline summary")
    print(f"total records: {summary['total_records']}")
    print(f"valid records: {summary['valid_records']}")
    print(f"rejected records: {summary['rejected_records']}")
    print(f"rejection rate: {summary['rejection_rate']:.2%}")
    print(f"status: {summary['status']}")


if __name__ == "__main__":
    main()
