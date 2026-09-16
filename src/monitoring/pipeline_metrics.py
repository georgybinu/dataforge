"""Pipeline run metrics helpers for DataForge."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd


VALID_STATUSES = {"success", "failed"}
DEFAULT_METRICS_PATH = Path("data/gold/pipeline_metrics.parquet")


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def create_pipeline_metric(
    pipeline_name: str,
    start_time: datetime,
    end_time: datetime,
    records_received: int,
    records_valid: int,
    records_rejected: int,
    status: str,
) -> dict[str, Any]:
    """Create a single pipeline run metric record.

    The rejection rate is stored as a percentage. For example, 5 rejected records
    out of 100 received records is stored as 5.0.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Unsupported pipeline status: {status}")

    duration_seconds = (end_time - start_time).total_seconds()
    rejection_rate = (
        records_rejected / records_received * 100 if records_received else 0.0
    )

    return {
        "run_id": str(uuid4()),
        "pipeline_name": pipeline_name,
        "start_time": start_time.astimezone(timezone.utc).isoformat(),
        "end_time": end_time.astimezone(timezone.utc).isoformat(),
        "duration_seconds": duration_seconds,
        "records_received": records_received,
        "records_valid": records_valid,
        "records_rejected": records_rejected,
        "rejection_rate": rejection_rate,
        "status": status,
    }


def append_pipeline_metric(
    metric: dict[str, Any],
    metrics_path: Path = DEFAULT_METRICS_PATH,
) -> None:
    """Append one pipeline metric record to a Parquet metrics dataset."""
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    new_metric = pd.DataFrame([metric])

    if metrics_path.exists():
        existing_metrics = pd.read_parquet(metrics_path)
        metrics = pd.concat([existing_metrics, new_metric], ignore_index=True)
    else:
        metrics = new_metric

    metrics.to_parquet(metrics_path, index=False)
