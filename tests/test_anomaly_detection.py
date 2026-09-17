from src.monitoring.anomaly_detection import (
    detect_metric_anomaly,
    detect_quality_anomaly,
    detect_volume_anomaly,
)


def test_detect_volume_anomaly_returns_normal_for_expected_volume() -> None:
    result = detect_volume_anomaly(1980, [2000, 2010, 1990])

    assert not result["is_anomaly"]


def test_detect_volume_anomaly_flags_abnormal_volume() -> None:
    result = detect_volume_anomaly(1100, [2000, 2010, 1990])

    assert result["is_anomaly"]
    assert result["deviation"] < -30


def test_detect_quality_anomaly_returns_normal_rejection_rate() -> None:
    result = detect_quality_anomaly(5.5, [5.0, 5.3, 5.2])

    assert not result["is_anomaly"]


def test_detect_quality_anomaly_flags_abnormal_rejection_rate() -> None:
    result = detect_quality_anomaly(12.0, [5.0, 5.3, 5.2])

    assert result["is_anomaly"]
    assert result["deviation"] > 50


def test_detect_metric_anomaly_flags_z_score_anomaly() -> None:
    result = detect_metric_anomaly("failed_rules", 40, [10, 11, 9, 10, 10])

    assert result["is_anomaly"]
    assert result["deviation"] >= 3.0


def test_detect_metric_anomaly_handles_no_history() -> None:
    result = detect_metric_anomaly("failed_rules", 10, [])

    assert not result["is_anomaly"]
    assert result["baseline_value"] is None


def test_detect_metric_anomaly_handles_zero_standard_deviation() -> None:
    result = detect_metric_anomaly("failed_rules", 12, [10, 10, 10])

    assert result["is_anomaly"]
    assert result["deviation"] == float("inf")


def test_detect_volume_anomaly_handles_empty_inputs() -> None:
    result = detect_volume_anomaly(0, [])

    assert not result["is_anomaly"]
    assert result["baseline_value"] is None
