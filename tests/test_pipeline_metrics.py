from datetime import datetime, timezone
from uuid import UUID

import pandas as pd

from src.monitoring.pipeline_metrics import (
    append_pipeline_metric,
    create_pipeline_metric,
)


def test_create_pipeline_metric_generates_run_id() -> None:
    metric = create_pipeline_metric(
        pipeline_name="test_pipeline",
        start_time=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
        records_received=10,
        records_valid=8,
        records_rejected=2,
        status="success",
    )

    assert UUID(metric["run_id"])


def test_create_pipeline_metric_calculates_successful_run_fields() -> None:
    metric = create_pipeline_metric(
        pipeline_name="quality_pipeline",
        start_time=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 1, 30, tzinfo=timezone.utc),
        records_received=100,
        records_valid=95,
        records_rejected=5,
        status="success",
    )

    assert metric["pipeline_name"] == "quality_pipeline"
    assert metric["duration_seconds"] == 90.0
    assert metric["records_received"] == 100
    assert metric["records_valid"] == 95
    assert metric["records_rejected"] == 5
    assert metric["status"] == "success"


def test_create_pipeline_metric_calculates_rejection_rate_percentage() -> None:
    metric = create_pipeline_metric(
        pipeline_name="quality_pipeline",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        records_received=200,
        records_valid=150,
        records_rejected=50,
        status="success",
    )

    assert metric["rejection_rate"] == 25.0


def test_create_pipeline_metric_handles_zero_records() -> None:
    metric = create_pipeline_metric(
        pipeline_name="quality_pipeline",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        records_received=0,
        records_valid=0,
        records_rejected=0,
        status="success",
    )

    assert metric["rejection_rate"] == 0.0


def test_append_pipeline_metric_persists_to_parquet(tmp_path) -> None:
    metrics_path = tmp_path / "pipeline_metrics.parquet"
    metric = create_pipeline_metric(
        pipeline_name="quality_pipeline",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        records_received=10,
        records_valid=9,
        records_rejected=1,
        status="success",
    )

    append_pipeline_metric(metric, metrics_path)
    saved_metrics = pd.read_parquet(metrics_path)

    assert metrics_path.exists()
    assert len(saved_metrics) == 1
    assert saved_metrics.loc[0, "run_id"] == metric["run_id"]


def test_append_pipeline_metric_adds_multiple_runs(tmp_path) -> None:
    metrics_path = tmp_path / "pipeline_metrics.parquet"
    first_metric = create_pipeline_metric(
        pipeline_name="quality_pipeline",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        records_received=10,
        records_valid=9,
        records_rejected=1,
        status="success",
    )
    second_metric = create_pipeline_metric(
        pipeline_name="quality_pipeline",
        start_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 2, 0, 0, 1, tzinfo=timezone.utc),
        records_received=20,
        records_valid=18,
        records_rejected=2,
        status="success",
    )

    append_pipeline_metric(first_metric, metrics_path)
    append_pipeline_metric(second_metric, metrics_path)
    saved_metrics = pd.read_parquet(metrics_path)

    assert len(saved_metrics) == 2
    assert saved_metrics["run_id"].tolist() == [
        first_metric["run_id"],
        second_metric["run_id"],
    ]
