import pandas as pd

from src.monitoring.schema_evolution import (
    compare_dataframe_schema,
    compare_schemas,
    get_dataframe_schema,
)


def test_compare_schemas_detects_no_schema_change() -> None:
    expected = {"order_id": "object", "quantity": "int64"}
    incoming = {"order_id": "object", "quantity": "int64"}

    result = compare_schemas(expected, incoming)

    assert result == {
        "status": "compatible",
        "added_columns": [],
        "removed_columns": [],
        "changed_types": [],
    }


def test_compare_schemas_detects_added_column_as_compatible() -> None:
    result = compare_schemas(
        {"order_id": "object"},
        {"order_id": "object", "source_file": "object"},
    )

    assert result["status"] == "compatible"
    assert result["added_columns"] == ["source_file"]


def test_compare_schemas_detects_removed_required_column_as_breaking() -> None:
    result = compare_schemas(
        {"order_id": "object", "customer_id": "object"},
        {"order_id": "object"},
    )

    assert result["status"] == "breaking"
    assert result["removed_columns"] == ["customer_id"]


def test_compare_schemas_detects_changed_column_type_as_breaking() -> None:
    result = compare_schemas(
        {"quantity": "int64"},
        {"quantity": "object"},
    )

    assert result["status"] == "breaking"
    assert result["changed_types"] == [
        {
            "column": "quantity",
            "expected_type": "int64",
            "incoming_type": "object",
        }
    ]


def test_compare_schemas_detects_multiple_changes() -> None:
    result = compare_schemas(
        {"order_id": "object", "customer_id": "object", "quantity": "int64"},
        {"order_id": "object", "quantity": "float64", "source_file": "object"},
    )

    assert result["status"] == "breaking"
    assert result["added_columns"] == ["source_file"]
    assert result["removed_columns"] == ["customer_id"]
    assert result["changed_types"] == [
        {
            "column": "quantity",
            "expected_type": "int64",
            "incoming_type": "float64",
        }
    ]


def test_compare_dataframe_schema_uses_dataframe_dtypes() -> None:
    dataframe = pd.DataFrame({"order_id": ["ORD-1"], "quantity": [1]})
    expected = get_dataframe_schema(dataframe)

    result = compare_dataframe_schema(expected, dataframe)

    assert result["status"] == "compatible"
