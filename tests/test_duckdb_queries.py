from pathlib import Path

import pandas as pd

from src.analytics.duckdb_queries import (
    query_customer_performance,
    query_daily_sales,
    query_filter_options,
    query_overall_sales_summary,
    query_pipeline_quality,
    query_product_performance,
    query_store_performance,
)


def _write_gold_fixtures(gold_path: Path) -> None:
    daily_sales = pd.DataFrame(
        {
            "order_date": pd.to_datetime(["2025-01-01", "2025-01-02"]),
            "total_orders": [2, 1],
            "total_quantity": [3, 4],
            "total_revenue": [30.0, 80.0],
            "average_order_value": [15.0, 80.0],
        }
    )
    product_metrics = pd.DataFrame(
        {
            "product_id": ["PROD-1", "PROD-2"],
            "total_orders": [2, 1],
            "total_quantity": [3, 4],
            "total_revenue": [30.0, 80.0],
            "average_unit_price": [10.0, 20.0],
        }
    )
    customer_metrics = pd.DataFrame(
        {
            "customer_id": ["CUST-1", "CUST-2"],
            "total_orders": [2, 1],
            "total_quantity": [3, 4],
            "total_revenue": [30.0, 80.0],
            "average_order_value": [15.0, 80.0],
        }
    )
    store_metrics = pd.DataFrame(
        {
            "store_id": ["STORE-1", "STORE-2"],
            "total_orders": [2, 1],
            "total_quantity": [3, 4],
            "total_revenue": [30.0, 80.0],
            "average_order_value": [15.0, 80.0],
        }
    )
    pipeline_metrics = pd.DataFrame(
        {
            "records_received": [100, 120],
            "records_valid": [95, 110],
            "records_rejected": [5, 10],
            "rejection_rate": [5.0, 8.333333],
            "status": ["success", "failed"],
            "pipeline_name": ["quality_pipeline", "quality_pipeline"],
            "start_time": ["2025-01-01T00:00:00+00:00", "2025-01-02T00:00:00+00:00"],
            "end_time": ["2025-01-01T00:01:00+00:00", "2025-01-02T00:01:00+00:00"],
        }
    )

    for name, dataframe in {
        "daily_sales": daily_sales,
        "product_metrics": product_metrics,
        "customer_metrics": customer_metrics,
        "store_metrics": store_metrics,
    }.items():
        output_path = gold_path / name
        output_path.mkdir(parents=True)
        dataframe.to_parquet(output_path / "part-00000.parquet", index=False)

    gold_path.mkdir(parents=True, exist_ok=True)
    pipeline_metrics.to_parquet(gold_path / "pipeline_metrics.parquet", index=False)


def test_query_overall_sales_summary_uses_weighted_order_value(tmp_path: Path) -> None:
    _write_gold_fixtures(tmp_path)

    result = query_overall_sales_summary(tmp_path).iloc[0]

    assert result["total_sales"] == 110.0
    assert result["total_orders"] == 3
    assert result["average_order_value"] == 110.0 / 3


def test_query_functions_support_filters_and_pipeline_latest(tmp_path: Path) -> None:
    _write_gold_fixtures(tmp_path)

    daily_sales = query_daily_sales("2025-01-02", "2025-01-02", tmp_path)
    products = query_product_performance("PROD-1", tmp_path)
    stores = query_store_performance("STORE-2", tmp_path)
    pipeline = query_pipeline_quality(tmp_path).iloc[0]

    assert daily_sales["order_count"].tolist() == [1]
    assert products["product_id"].tolist() == ["PROD-1"]
    assert stores["store_id"].tolist() == ["STORE-2"]
    assert pipeline["status"] == "failed"
    assert pipeline["records_rejected"] == 10


def test_query_customer_performance_and_filter_options(tmp_path: Path) -> None:
    _write_gold_fixtures(tmp_path)

    customers = query_customer_performance(tmp_path)
    options = query_filter_options(tmp_path)

    assert customers["customer_id"].tolist() == ["CUST-2", "CUST-1"]
    assert options == {
        "dates": ["2025-01-01", "2025-01-02"],
        "stores": ["STORE-1", "STORE-2"],
        "products": ["PROD-1", "PROD-2"],
    }
