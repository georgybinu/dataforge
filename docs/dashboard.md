# DataForge Dashboard

The local dashboard in `dashboard/app.py` presents sales analytics and pipeline health from the existing Gold Parquet datasets. It uses Streamlit for the page, Plotly for charts, and DuckDB for SQL execution.

## How It Works

The helper module in `src/analytics/duckdb_queries.py` opens an in-memory DuckDB connection and registers views over:

- `data/gold/daily_sales/`
- `data/gold/product_metrics/`
- `data/gold/customer_metrics/`
- `data/gold/store_metrics/`
- `data/gold/pipeline_metrics.parquet`

The SQL files under `sql/` query those views directly with DuckDB `read_parquet`. No external database is created and the Gold datasets are not copied. The overall average order value is calculated from total sales divided by total orders.

The date filter applies to daily sales. Store and product filters apply to their corresponding aggregate views. Customer analytics remain at the available customer-metric grain.

The Pipeline Intelligence section reuses the existing Step 13 anomaly and root-cause functions with the deterministic scenario from `scripts/run_intelligence_demo.py`. It is labeled as a demo and does not claim to represent a live incident.

## Run Locally

From the repository root:

```bash
.venv/bin/streamlit run dashboard/app.py
```

The dashboard runs entirely locally and reads the checked-in or locally generated Gold Parquet data.

## Verify SQL Analytics

Run the focused helper tests or execute the full test suite:

```bash
.venv/bin/python -m pytest -q tests/test_duckdb_queries.py
.venv/bin/python -m pytest -q
```
