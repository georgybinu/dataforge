"""DuckDB query helpers for DataForge Gold Parquet datasets."""

from __future__ import annotations

from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLD_PATH = PROJECT_ROOT / "data" / "gold"
SQL_PATH = PROJECT_ROOT / "sql"

_DATASET_PATHS = {
    "daily_sales": "daily_sales",
    "product_metrics": "product_metrics",
    "customer_metrics": "customer_metrics",
    "store_metrics": "store_metrics",
    "pipeline_metrics": "pipeline_metrics.parquet",
}


def _parquet_source(path: Path) -> str:
    """Return a Parquet file or directory glob for DuckDB to read."""
    if path.is_dir():
        return str(path / "*.parquet")
    return str(path)


def _sql_string(value: str) -> str:
    """Escape a local path for use as a DuckDB SQL string literal."""
    return value.replace("'", "''")


def _sql(query_name: str) -> str:
    query_path = SQL_PATH / f"{query_name}.sql"
    if not query_path.exists():
        raise FileNotFoundError(f"SQL query file not found: {query_path}")
    return query_path.read_text(encoding="utf-8")


def create_connection(gold_path: str | Path = DEFAULT_GOLD_PATH) -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB connection with Gold views registered."""
    gold_root = Path(gold_path)
    connection = duckdb.connect(database=":memory:")

    try:
        for view_name, relative_path in _DATASET_PATHS.items():
            dataset_path = gold_root / relative_path
            if not dataset_path.exists():
                raise FileNotFoundError(f"Gold dataset not found: {dataset_path}")
            parquet_source = _sql_string(_parquet_source(dataset_path))
            connection.execute(
                f"CREATE VIEW {view_name} AS SELECT * FROM read_parquet('{parquet_source}')"
            )
    except Exception:
        connection.close()
        raise

    return connection


def _date_value(value: date | str | None) -> str | None:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, date) else value


def _run_dataframe_query(
    query_name: str,
    params: Iterable[Any] = (),
    gold_path: str | Path = DEFAULT_GOLD_PATH,
) -> pd.DataFrame:
    with closing(create_connection(gold_path)) as connection:
        return connection.execute(_sql(query_name), list(params)).fetchdf()


def query_overall_sales_summary(
    gold_path: str | Path = DEFAULT_GOLD_PATH,
) -> pd.DataFrame:
    """Return total sales, order count, and weighted average order value."""
    return _run_dataframe_query("overall_sales_summary", gold_path=gold_path)


def query_daily_sales(
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    gold_path: str | Path = DEFAULT_GOLD_PATH,
) -> pd.DataFrame:
    """Return daily sales optionally constrained to an inclusive date range."""
    start_value = _date_value(start_date)
    end_value = _date_value(end_date)
    return _run_dataframe_query(
        "daily_sales",
        [start_value, start_value, end_value, end_value],
        gold_path,
    )


def query_product_performance(
    product_id: str | None = None,
    gold_path: str | Path = DEFAULT_GOLD_PATH,
) -> pd.DataFrame:
    """Return product performance, optionally for one product."""
    return _run_dataframe_query(
        "product_performance",
        [product_id, product_id],
        gold_path,
    )


def query_customer_performance(
    gold_path: str | Path = DEFAULT_GOLD_PATH,
) -> pd.DataFrame:
    """Return customer performance ordered by total sales."""
    return _run_dataframe_query("customer_performance", gold_path=gold_path)


def query_store_performance(
    store_id: str | None = None,
    gold_path: str | Path = DEFAULT_GOLD_PATH,
) -> pd.DataFrame:
    """Return store performance, optionally for one store."""
    return _run_dataframe_query(
        "store_performance",
        [store_id, store_id],
        gold_path,
    )


def query_pipeline_quality(
    gold_path: str | Path = DEFAULT_GOLD_PATH,
) -> pd.DataFrame:
    """Return the latest recorded pipeline quality metric."""
    return _run_dataframe_query("pipeline_quality", gold_path=gold_path)


def query_filter_options(
    gold_path: str | Path = DEFAULT_GOLD_PATH,
) -> dict[str, list[str]]:
    """Return available date, store, and product filter values."""
    with closing(create_connection(gold_path)) as connection:
        dates = connection.execute(
            "SELECT DISTINCT CAST(CAST(order_date AS DATE) AS VARCHAR) "
            "FROM daily_sales ORDER BY 1"
        ).fetchall()
        stores = connection.execute(
            "SELECT DISTINCT store_id FROM store_metrics ORDER BY 1"
        ).fetchall()
        products = connection.execute(
            "SELECT DISTINCT product_id FROM product_metrics ORDER BY 1"
        ).fetchall()

    return {
        "dates": [row[0] for row in dates],
        "stores": [row[0] for row in stores],
        "products": [row[0] for row in products],
    }
