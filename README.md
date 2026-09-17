# DataForge

DataForge is a local, production-style data engineering portfolio project for reliable retail analytics. It ingests deliberately imperfect order data, validates it against business and reference-data rules, preserves rejected records for investigation, produces Spark-based Gold datasets, and exposes pipeline health and analytics through SQL and a dashboard.

The current implementation runs entirely on a local machine with synthetic sample data. It is not deployed to Azure, Databricks, or any other cloud service.

## Problem Statement

Retail analytics are only as trustworthy as the data pipeline behind them. Duplicate orders, invalid dates, negative quantities, missing customers, and broken reference relationships can silently distort reporting. DataForge demonstrates how to detect those problems, separate valid and invalid data, measure pipeline health, and make the resulting datasets usable for analysis.

## Architecture and Data Flow

```text
data/raw CSVs
	-> Python ingestion -> Bronze Parquet
	-> quality validation -> Silver valid orders + Quarantine rejected orders
	-> PySpark Silver-to-Gold -> Gold analytics Parquet
	-> DuckDB SQL + monitoring/intelligence -> Streamlit + Plotly dashboard
```

See [docs/architecture.md](docs/architecture.md) for the Mermaid diagram and future Azure/Databricks mapping.

## Technology Stack

- Python and pandas for ingestion, validation, metrics, and orchestration
- PyArrow and Parquet for local data storage
- PySpark for Silver-to-Gold transformations
- DuckDB for SQL directly over Gold Parquet files
- Streamlit and Plotly for the local analytics dashboard
- PyYAML for project configuration
- pytest and GitHub Actions for automated verification

## Engineering Features

### Data quality and quarantine

The quality pipeline validates the retail order schema, required fields, unique order IDs, numeric types, valid dates, positive quantities, non-negative prices, and referential integrity against customer, product, and store reference data. Valid records are written to `data/silver/orders_valid.parquet`; rejected records, including failed-rule details, are written to `data/quarantine/orders_invalid.parquet`.

### Bronze, Silver, and Gold

`src/ingestion/csv_ingestor.py` adds ingestion metadata and writes each raw CSV to Bronze. `src/pipeline/quality_pipeline.py` creates the validated Silver and Quarantine outputs while recording run metrics. `spark/orders_silver_to_gold.py` uses PySpark to produce daily sales, product, customer, and store Gold datasets.

### Monitoring and schema evolution

Pipeline metrics record received, valid, and rejected records, rejection rate, duration, status, and run timestamps. Schema utilities classify added columns as compatible while detecting removed columns and changed types as breaking changes.

### Anomaly detection and root-cause analysis

Step 13 provides lightweight volume, quality-rate, and z-score anomaly detection plus deterministic rule-based root-cause analysis. The dashboard displays the existing fixed intelligence demonstration as demo data; it does not claim to detect live incidents.

### DuckDB analytics and dashboard

Reusable SQL files under `sql/` query Gold Parquet through in-memory DuckDB views. The Streamlit dashboard presents KPIs, daily sales, product and store performance, customer rankings, pipeline health, filters, and the labeled Step 13 intelligence demo. No external database is required.

## Reproducible Local Run

Prerequisites: Python 3.11 or a compatible Python version, Java available for the local PySpark job, and a virtual environment.

```bash
git clone <repository-url>
cd dataforge
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python scripts/run_pipeline.py
```

The runner consumes the tracked files in `data/raw/` and executes ingestion, quality validation, Quarantine/Silver writes, metrics, and the existing Spark Gold job in order. It does not regenerate or modify the raw source CSVs.

Run the dashboard after the pipeline completes:

```bash
./.venv/bin/streamlit run dashboard/app.py
```

Run the test suite:

```bash
./.venv/bin/python -m pytest -q
```

## Representative Results

With the included sample data, a verified local run produced approximately:

```text
received=2000, valid=1849, rejected=151
daily sales: 364 rows
product metrics: 250 rows
customer metrics: 688 rows
store metrics: 25 rows
```

Exact timestamps and generated Parquet contents can vary between runs because pipeline run IDs and timestamps are generated at runtime.

## CI/CD

GitHub Actions runs the full pytest suite on every push and pull request. CI installs the declared Python dependencies and does not require cloud credentials, paid services, Databricks, Azure, or a dashboard server. The workflow intentionally tests the code without rebuilding local Spark Gold artifacts.

## Limitations

- The source data is synthetic and local rather than a production feed.
- The dashboard is a local Streamlit application with no authentication or multi-user deployment layer.
- Pipeline metrics are stored in a local Parquet file rather than a durable monitoring system.
- The intelligence demo is deterministic example input, not live incident detection.
- The current pipeline is designed for a small portfolio-scale dataset and does not include production orchestration, retries, lineage, secrets management, or SLA alerting.

## Future Cloud Architecture

A future deployment could use ADLS Gen2 or Blob Storage for the data layers, Azure Data Factory or event ingestion for source delivery, Databricks jobs and Delta Lake for validation and transformation, Azure Monitor for operational metrics, and a secured application host for the dashboard. That is a proposed target architecture only; this repository currently demonstrates the equivalent workflow locally.

## Repository Layout

```text
src/                 ingestion, validation, pipeline, monitoring, intelligence, analytics
spark/               Silver-to-Gold PySpark job
sql/                 reusable DuckDB analytics queries
dashboard/           Streamlit + Plotly application
scripts/             deterministic data generators, demos, and pipeline runner
tests/               pytest suite
docs/                dashboard and architecture documentation
data/raw/            tracked sample CSV and reference data
```
