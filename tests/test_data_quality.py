import pandas as pd
import pytest

from src.validation.data_quality import (
    run_quality_checks,
    validate_referential_integrity,
)


def test_validate_referential_integrity_flags_missing_and_null_values() -> None:
    transactions = pd.DataFrame({"product_id": ["PROD-0001", "INVALID", None]})
    products = pd.DataFrame({"product_id": ["PROD-0001", "PROD-0002"]})

    result = validate_referential_integrity(
        transactions,
        "product_id",
        products,
        "product_id",
    )

    assert result.tolist() == [True, False, False]


def test_validate_referential_integrity_raises_for_missing_transaction_column() -> None:
    transactions = pd.DataFrame({"missing_product_id": ["PROD-0001"]})
    products = pd.DataFrame({"product_id": ["PROD-0001"]})

    with pytest.raises(ValueError, match="Missing required column"):
        validate_referential_integrity(
            transactions,
            "product_id",
            products,
            "product_id",
        )


def test_validate_referential_integrity_raises_for_missing_reference_column() -> None:
    transactions = pd.DataFrame({"product_id": ["PROD-0001"]})
    products = pd.DataFrame({"missing_product_id": ["PROD-0001"]})

    with pytest.raises(ValueError, match="Missing required column"):
        validate_referential_integrity(
            transactions,
            "product_id",
            products,
            "product_id",
        )


def test_run_quality_checks_supports_referential_integrity_rules() -> None:
    transactions = pd.DataFrame({"product_id": ["PROD-0001", "INVALID"]})
    products = pd.DataFrame({"product_id": ["PROD-0001"]})
    rules = {
        "product_referential_integrity": {
            "type": "referential_integrity",
            "column": "product_id",
            "reference_df": products,
            "reference_column": "product_id",
        }
    }

    result = run_quality_checks(transactions, rules)

    assert result["is_valid"].tolist() == [True, False]
    assert result["failed_rules"].tolist() == [
        [],
        ["product_referential_integrity"],
    ]
