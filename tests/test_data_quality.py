import pandas as pd
import pytest

from src.validation.data_quality import (
    get_schema_differences,
    run_quality_checks,
    validate_column_type,
    validate_date,
    validate_referential_integrity,
    validate_schema,
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


def test_validate_schema_returns_true_for_valid_schema() -> None:
    dataframe = pd.DataFrame(columns=["order_id", "customer_id", "quantity"])

    assert validate_schema(dataframe, ["order_id", "customer_id", "quantity"])


def test_validate_schema_returns_false_for_missing_column() -> None:
    dataframe = pd.DataFrame(columns=["order_id", "quantity"])

    assert not validate_schema(dataframe, ["order_id", "customer_id", "quantity"])
    assert get_schema_differences(
        dataframe,
        ["order_id", "customer_id", "quantity"],
    ) == {
        "missing_columns": ["customer_id"],
        "unexpected_columns": [],
    }


def test_validate_schema_returns_false_for_unexpected_column() -> None:
    dataframe = pd.DataFrame(columns=["order_id", "customer_id", "quantity", "extra"])

    assert not validate_schema(dataframe, ["order_id", "customer_id", "quantity"])
    assert get_schema_differences(
        dataframe,
        ["order_id", "customer_id", "quantity"],
    ) == {
        "missing_columns": [],
        "unexpected_columns": ["extra"],
    }


def test_validate_schema_ignores_column_order() -> None:
    dataframe = pd.DataFrame(columns=["quantity", "order_id", "customer_id"])

    assert validate_schema(dataframe, ["order_id", "customer_id", "quantity"])


def test_validate_column_type_accepts_valid_integer_values() -> None:
    dataframe = pd.DataFrame({"quantity": [1, "2", "3.0"]})

    result = validate_column_type(dataframe, "quantity", "integer")

    assert result.tolist() == [True, True, True]


def test_validate_column_type_rejects_invalid_integer_values() -> None:
    dataframe = pd.DataFrame({"quantity": [1, "2.5", "many", None]})

    result = validate_column_type(dataframe, "quantity", "integer")

    assert result.tolist() == [True, False, False, False]


def test_validate_column_type_accepts_valid_numeric_values() -> None:
    dataframe = pd.DataFrame({"unit_price": [10, "19.99", "-4.50"]})

    result = validate_column_type(dataframe, "unit_price", "numeric")

    assert result.tolist() == [True, True, True]


def test_validate_column_type_rejects_invalid_numeric_values() -> None:
    dataframe = pd.DataFrame({"unit_price": [10, "free", None]})

    result = validate_column_type(dataframe, "unit_price", "numeric")

    assert result.tolist() == [True, False, False]


def test_validate_date_accepts_valid_dates() -> None:
    dataframe = pd.DataFrame({"order_date": ["2025-01-01", "2025-12-31"]})

    result = validate_date(dataframe, "order_date", "%Y-%m-%d")

    assert result.tolist() == [True, True]


def test_validate_date_rejects_invalid_dates() -> None:
    dataframe = pd.DataFrame({"order_date": ["2025-01-01", "not-a-date"]})

    result = validate_date(dataframe, "order_date", "%Y-%m-%d")

    assert result.tolist() == [True, False]


def test_validate_date_rejects_null_dates() -> None:
    dataframe = pd.DataFrame({"order_date": ["2025-01-01", None]})

    result = validate_date(dataframe, "order_date", "%Y-%m-%d")

    assert result.tolist() == [True, False]


def test_validate_column_type_raises_for_missing_column() -> None:
    dataframe = pd.DataFrame({"quantity": [1]})

    with pytest.raises(ValueError, match="Missing required column"):
        validate_column_type(dataframe, "unit_price", "numeric")


def test_validate_date_raises_for_missing_column() -> None:
    dataframe = pd.DataFrame({"quantity": [1]})

    with pytest.raises(ValueError, match="Missing required column"):
        validate_date(dataframe, "order_date")


def test_validate_column_type_raises_for_unsupported_type() -> None:
    dataframe = pd.DataFrame({"quantity": [1]})

    with pytest.raises(ValueError, match="Unsupported expected type"):
        validate_column_type(dataframe, "quantity", "boolean")


def test_run_quality_checks_supports_type_and_date_rules() -> None:
    dataframe = pd.DataFrame(
        {
            "quantity": ["2", "bad"],
            "order_date": ["2025-01-01", "not-a-date"],
        }
    )
    rules = {
        "quantity_type": {
            "type": "type",
            "column": "quantity",
            "expected_type": "integer",
        },
        "order_date_valid": {
            "type": "date",
            "column": "order_date",
            "date_format": "%Y-%m-%d",
        },
    }

    result = run_quality_checks(dataframe, rules)

    assert result["is_valid"].tolist() == [True, False]
    assert result["failed_rules"].tolist() == [
        [],
        ["quantity_type", "order_date_valid"],
    ]


def test_run_quality_checks_marks_all_rows_invalid_for_failed_schema() -> None:
    dataframe = pd.DataFrame({"order_id": ["ORD-000001"], "extra": ["value"]})
    rules = {
        "retail_schema": {
            "type": "schema",
            "expected_columns": ["order_id", "customer_id"],
        }
    }

    result = run_quality_checks(dataframe, rules)

    assert result["is_valid"].tolist() == [False]
    assert result["failed_rules"].tolist() == [["retail_schema"]]
