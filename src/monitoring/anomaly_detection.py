"""Lightweight statistical anomaly detection for DataForge monitoring."""

from statistics import mean, pstdev
from typing import Sequence


def _clean_numeric_history(values: Sequence[float]) -> list[float]:
    """Return non-null numeric history values as floats."""
    return [float(value) for value in values if value is not None]


def _empty_result(metric: str, current_value: float, message: str) -> dict[str, object]:
    """Build a standard non-anomaly result for insufficient history."""
    return {
        "metric": metric,
        "current_value": current_value,
        "baseline_value": None,
        "deviation": 0.0,
        "is_anomaly": False,
        "message": message,
    }


def detect_volume_anomaly(
    current_count: int,
    historical_counts: Sequence[int],
    threshold_percent: float = 30.0,
    metric: str = "record_count",
) -> dict[str, object]:
    """Detect unusual record volume using percentage change from history."""
    history = _clean_numeric_history(historical_counts)

    if not history:
        return _empty_result(metric, float(current_count), "No historical data available.")

    baseline = mean(history)
    if baseline == 0:
        is_anomaly = current_count != 0
        deviation = 0.0 if current_count == 0 else 100.0
    else:
        deviation = (current_count - baseline) / baseline * 100
        is_anomaly = abs(deviation) >= threshold_percent

    direction = "increased" if deviation > 0 else "dropped"
    message = (
        f"{metric} {direction} by {abs(deviation):.2f}% compared with baseline "
        f"{baseline:.2f}."
    )

    return {
        "metric": metric,
        "current_value": current_count,
        "baseline_value": baseline,
        "deviation": deviation,
        "is_anomaly": is_anomaly,
        "message": message,
    }


def detect_quality_anomaly(
    current_rejection_rate: float,
    historical_rejection_rates: Sequence[float],
    threshold_percent: float = 50.0,
    metric: str = "rejection_rate",
) -> dict[str, object]:
    """Detect unusual quality behavior using rejection-rate percentage change."""
    history = _clean_numeric_history(historical_rejection_rates)

    if not history:
        return _empty_result(
            metric,
            float(current_rejection_rate),
            "No historical rejection-rate data available.",
        )

    baseline = mean(history)
    if baseline == 0:
        is_anomaly = current_rejection_rate != 0
        deviation = 0.0 if current_rejection_rate == 0 else 100.0
    else:
        deviation = (current_rejection_rate - baseline) / baseline * 100
        is_anomaly = abs(deviation) >= threshold_percent

    direction = "increased" if deviation > 0 else "dropped"
    message = (
        f"{metric} {direction} by {abs(deviation):.2f}% compared with baseline "
        f"{baseline:.2f}."
    )

    return {
        "metric": metric,
        "current_value": current_rejection_rate,
        "baseline_value": baseline,
        "deviation": deviation,
        "is_anomaly": is_anomaly,
        "message": message,
    }


def detect_metric_anomaly(
    metric: str,
    current_value: float,
    historical_values: Sequence[float],
    z_score_threshold: float = 3.0,
) -> dict[str, object]:
    """Detect a generic numeric anomaly using population z-score."""
    history = _clean_numeric_history(historical_values)

    if not history:
        return _empty_result(metric, float(current_value), "No historical data available.")

    baseline = mean(history)

    if len(history) == 1:
        return {
            "metric": metric,
            "current_value": current_value,
            "baseline_value": baseline,
            "deviation": 0.0,
            "is_anomaly": False,
            "message": "At least two historical values are needed for z-score detection.",
        }

    standard_deviation = pstdev(history)
    if standard_deviation == 0:
        is_anomaly = current_value != baseline
        deviation = 0.0 if current_value == baseline else float("inf")
        message = (
            f"{metric} differs from a stable baseline of {baseline:.2f}."
            if is_anomaly
            else f"{metric} matches stable baseline {baseline:.2f}."
        )
    else:
        deviation = (current_value - baseline) / standard_deviation
        is_anomaly = abs(deviation) >= z_score_threshold
        message = (
            f"{metric} z-score is {deviation:.2f} compared with baseline "
            f"{baseline:.2f}."
        )

    return {
        "metric": metric,
        "current_value": current_value,
        "baseline_value": baseline,
        "deviation": deviation,
        "is_anomaly": is_anomaly,
        "message": message,
    }
