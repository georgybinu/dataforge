"""Run the local DataForge pipeline from raw CSV files through Gold."""

from __future__ import annotations

import sys
import os
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.csv_ingestor import ingest_csv
from src.pipeline.quality_pipeline import run_quality_pipeline


RAW_PATHS = {
    "orders": PROJECT_ROOT / "data" / "raw" / "orders_dirty.csv",
    "customers": PROJECT_ROOT / "data" / "raw" / "customers.csv",
    "products": PROJECT_ROOT / "data" / "raw" / "products.csv",
    "stores": PROJECT_ROOT / "data" / "raw" / "stores.csv",
}
BRONZE_PATHS = {
    name: PROJECT_ROOT / "data" / "bronze" / f"{name}.parquet"
    for name in RAW_PATHS
}


def _require_raw_inputs() -> None:
    missing_paths = [path for path in RAW_PATHS.values() if not path.exists()]
    if missing_paths:
        missing = ", ".join(str(path.relative_to(PROJECT_ROOT)) for path in missing_paths)
        raise FileNotFoundError(f"Required raw input file(s) missing: {missing}")


def _run_ingestion() -> None:
    print("[1/3] Ingesting raw CSV files into Bronze")
    for name, input_path in RAW_PATHS.items():
        result = ingest_csv(str(input_path), str(BRONZE_PATHS[name]))
        print(f"  {name}: {result['records_ingested']} records -> {result['output_path']}")


def _run_quality_pipeline() -> None:
    print("[2/3] Validating orders and writing Silver, Quarantine, and metrics")
    summary = run_quality_pipeline(
        input_path=RAW_PATHS["orders"],
        customers_path=RAW_PATHS["customers"],
        products_path=RAW_PATHS["products"],
        stores_path=RAW_PATHS["stores"],
        silver_output_path=PROJECT_ROOT / "data" / "silver" / "orders_valid.parquet",
        quarantine_output_path=PROJECT_ROOT / "data" / "quarantine" / "orders_invalid.parquet",
        metrics_output_path=PROJECT_ROOT / "data" / "gold" / "pipeline_metrics.parquet",
    )
    print(
        "  received={total_records}, valid={valid_records}, rejected={rejected_records}, "
        "rejection_rate={rejection_rate:.2%}, status={status}".format(**summary)
    )


def _run_gold_pipeline() -> None:
    print("[3/3] Building Gold datasets with the existing Spark job")
    java_path = shutil.which("java")
    if java_path is None:
        raise RuntimeError(
            "A Java runtime is required for the PySpark Gold stage. "
            "Install Java and retry the pipeline."
        )
    java_check = subprocess.run(
        [java_path, "-version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if java_check.returncode != 0:
        raise RuntimeError(
            "A working Java runtime is required for the PySpark Gold stage. "
            "Install Java and retry the pipeline."
        )
    from spark.orders_silver_to_gold import main as build_gold_datasets

    build_gold_datasets()
    print("  Gold datasets written under data/gold/")


def main() -> None:
    """Run ingestion, quality validation, and Spark Gold generation."""
    os.chdir(PROJECT_ROOT)
    _require_raw_inputs()
    _run_ingestion()
    _run_quality_pipeline()
    _run_gold_pipeline()
    print("DataForge pipeline completed successfully")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError) as error:
        print(f"DataForge pipeline failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
