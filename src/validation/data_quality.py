"""Basic data quality checks for DataForge."""

from typing import Iterable, Optional

import pandas as pd


def _validate_columns_exist(df: pd.DataFrame, columns: Iterable[str]) -> None:
    """Raise a clear error if any requested columns are missing."""
    missing_columns = [column for column in columns if column not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required column(s): {', '.join(missing_columns)}")


def validate_not_null(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    """Return True for rows where all specified columns contain non-null values."""
    _validate_columns_exist(df, columns)
    return df[columns].notna().all(axis=1)


def validate_unique(df: pd.DataFrame, column: str) -> pd.Series:
    """Return True for rows where the selected column value is unique and not null."""
    _validate_columns_exist(df, [column])
    return df[column].notna() & ~df[column].duplicated(keep=False)


def validate_positive(df: pd.DataFrame, column: str) -> pd.Series:
    """Return True for rows where the selected column value is greater than zero."""
    _validate_columns_exist(df, [column])
    return df[column] > 0


def validate_non_negative(df: pd.DataFrame, column: str) -> pd.Series:
    """Return True for rows where the selected column value is zero or greater."""
    _validate_columns_exist(df, [column])
    return df[column] >= 0


def validate_referential_integrity(
    df: pd.DataFrame,
    column: str,
    reference_df: pd.DataFrame,
    reference_column: str,
) -> pd.Series:
    """Return True when values exist in a reference dataset.

    Null values in the transaction dataframe are treated as invalid.
    """
    _validate_columns_exist(df, [column])
    _validate_columns_exist(reference_df, [reference_column])

    reference_values = set(reference_df[reference_column].dropna())
    return df[column].notna() & df[column].isin(reference_values)


def get_schema_differences(
    df: pd.DataFrame,
    expected_columns: list[str],
) -> dict[str, list[str]]:
    """Return missing and unexpected columns for a dataframe schema."""
    actual_columns = set(df.columns)
    expected_column_set = set(expected_columns)

    return {
        "missing_columns": sorted(expected_column_set - actual_columns),
        "unexpected_columns": sorted(actual_columns - expected_column_set),
    }


def validate_schema(df: pd.DataFrame, expected_columns: list[str]) -> bool:
    """Return True when dataframe columns exactly match the expected schema.

    Column order does not matter. Missing columns and unexpected extra columns
    both make the schema invalid.
    """
    differences = get_schema_differences(df, expected_columns)
    return not differences["missing_columns"] and not differences["unexpected_columns"]


def validate_column_type(
    df: pd.DataFrame,
    column: str,
    expected_type: str,
) -> pd.Series:
    """Return True for rows where values can be interpreted as the expected type."""
    _validate_columns_exist(df, [column])

    supported_types = {"string", "integer", "float", "numeric"}
    if expected_type not in supported_types:
        raise ValueError(f"Unsupported expected type: {expected_type}")

    values = df[column]

    if expected_type == "string":
        return values.notna()

    numeric_values = pd.to_numeric(values, errors="coerce")
    valid_numeric = values.notna() & numeric_values.notna()

    if expected_type == "integer":
        return valid_numeric & (numeric_values % 1 == 0)

    return valid_numeric


def validate_date(
    df: pd.DataFrame,
    column: str,
    date_format: Optional[str] = None,
) -> pd.Series:
    """Return True for rows where values can be parsed as valid dates.

    If date_format is provided, values must match that format. Null values are
    always invalid.
    """
    _validate_columns_exist(df, [column])

    parsed_dates = pd.to_datetime(
        df[column],
        format=date_format,
        errors="coerce",
    )
    return df[column].notna() & parsed_dates.notna()


def run_quality_checks(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    """Run configured quality checks and return row-level validation results.

    The rules dictionary maps rule names to rule definitions. Each rule definition
    must include a supported type: not_null, unique, positive, non_negative,
    referential_integrity, schema, type, or date.

    Schema rules validate the whole dataframe. If a schema rule fails, every row
    is marked invalid for that schema rule because the dataset shape is invalid.
    """
    rule_results = {}

    for rule_name, rule_config in rules.items():
        rule_type = rule_config.get("type")

        if rule_type == "not_null":
            rule_results[rule_name] = validate_not_null(df, rule_config["columns"])
        elif rule_type == "unique":
            rule_results[rule_name] = validate_unique(df, rule_config["column"])
        elif rule_type == "positive":
            rule_results[rule_name] = validate_positive(df, rule_config["column"])
        elif rule_type == "non_negative":
            rule_results[rule_name] = validate_non_negative(df, rule_config["column"])
        elif rule_type == "referential_integrity":
            rule_results[rule_name] = validate_referential_integrity(
                df,
                rule_config["column"],
                rule_config["reference_df"],
                rule_config["reference_column"],
            )
        elif rule_type == "schema":
            schema_is_valid = validate_schema(df, rule_config["expected_columns"])
            rule_results[rule_name] = pd.Series(schema_is_valid, index=df.index)
        elif rule_type == "type":
            rule_results[rule_name] = validate_column_type(
                df,
                rule_config["column"],
                rule_config["expected_type"],
            )
        elif rule_type == "date":
            rule_results[rule_name] = validate_date(
                df,
                rule_config["column"],
                rule_config.get("date_format"),
            )
        else:
            raise ValueError(f"Unsupported quality rule type: {rule_type}")

    failed_rules = []
    is_valid = []

    for row_index in df.index:
        row_failed_rules = [
            rule_name
            for rule_name, result in rule_results.items()
            if not bool(result.loc[row_index])
        ]
        failed_rules.append(row_failed_rules)
        is_valid.append(len(row_failed_rules) == 0)

    return pd.DataFrame(
        {
            "row_index": df.index,
            "is_valid": is_valid,
            "failed_rules": failed_rules,
        }
    )
