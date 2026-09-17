"""Schema evolution detection utilities for DataForge."""

from typing import Any

import pandas as pd


def _normalize_schema(schema: dict[str, Any]) -> dict[str, str]:
    """Convert schema type values into comparable string names."""
    return {column: str(column_type) for column, column_type in schema.items()}


def get_dataframe_schema(df: pd.DataFrame) -> dict[str, str]:
    """Return a simple column-to-type mapping for a pandas dataframe."""
    return {column: str(dtype) for column, dtype in df.dtypes.items()}


def compare_schemas(
    expected_schema: dict[str, Any],
    incoming_schema: dict[str, Any],
) -> dict[str, Any]:
    """Compare expected and incoming schemas and classify compatibility.

    Added columns are treated as non-breaking. Removed columns and changed types
    are treated as breaking changes.
    """
    expected = _normalize_schema(expected_schema)
    incoming = _normalize_schema(incoming_schema)

    expected_columns = set(expected)
    incoming_columns = set(incoming)

    added_columns = sorted(incoming_columns - expected_columns)
    removed_columns = sorted(expected_columns - incoming_columns)
    changed_types = [
        {
            "column": column,
            "expected_type": expected[column],
            "incoming_type": incoming[column],
        }
        for column in sorted(expected_columns & incoming_columns)
        if expected[column] != incoming[column]
    ]

    has_breaking_change = bool(removed_columns or changed_types)

    return {
        "status": "breaking" if has_breaking_change else "compatible",
        "added_columns": added_columns,
        "removed_columns": removed_columns,
        "changed_types": changed_types,
    }


def compare_dataframe_schema(
    expected_schema: dict[str, Any],
    incoming_df: pd.DataFrame,
) -> dict[str, Any]:
    """Compare an expected schema with the schema of an incoming dataframe."""
    return compare_schemas(expected_schema, get_dataframe_schema(incoming_df))
