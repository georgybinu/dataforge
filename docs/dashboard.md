# DataForge Dashboard

The local dashboard in `dashboard/app.py` presents five focused views over the existing Gold Parquet datasets. It uses Streamlit for the interface, Plotly for charts, and DuckDB for SQL execution.

## Views

- **Overview**: branded workspace context, revenue/orders/AOV KPIs, pipeline quality KPIs, sales trend, and product/store performance.
- **Data Quality**: valid-versus-rejected records, rejection rate, quarantine explanation, and an explicit limitation notice for rule-level details.
- **Pipeline Health**: latest local run status, counts, rejection rate, duration, and timestamps. This is historical local-run information, not live production monitoring.
- **Intelligence**: the existing Step 13 anomaly and root-cause functions with evidence, confidence, and explanation. The scenario is prominently labeled `DETERMINISTIC DEMO — NOT LIVE INCIDENT DETECTION`.
- **Data Explorer**: controlled-size tables for Daily Sales, Product Metrics, Customer Metrics, and Store Metrics.

## How It Works

The helper module in `src/analytics/duckdb_queries.py` opens an in-memory DuckDB connection and registers views over:

- `data/gold/daily_sales/`
- `data/gold/product_metrics/`
- `data/gold/customer_metrics/`
- `data/gold/store_metrics/`
- `data/gold/pipeline_metrics.parquet`

The SQL files under `sql/` query those views directly with DuckDB `read_parquet`. No external database is created and the Gold datasets are not copied. The overall average order value is calculated from total sales divided by total orders.

The date filter applies to daily sales. Store and product filters apply to their corresponding aggregate views. Customer analytics remain at the available customer-metric grain. The overall summary and pipeline health are not artificially filtered because their existing query contracts do not expose those filters.

The current Gold and DuckDB query contract exposes aggregate pipeline metrics, not per-rule failure counts or row-level quarantine records. The Data Quality view states that limitation rather than fabricating rule-level metrics.

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
