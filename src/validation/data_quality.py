"""Basic data quality checks for DataForge."""

from typing import Iterable

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


def run_quality_checks(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    """Run configured quality checks and return row-level validation results.

    The rules dictionary maps rule names to rule definitions. Each rule definition
    must include a supported type: not_null, unique, positive, non_negative, or
    referential_integrity.
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
