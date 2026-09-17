"""Rule-based root-cause analysis for DataForge incidents."""

from typing import Any


def _percent_change(current_value: float, baseline_value: float) -> float:
    """Calculate percentage change while safely handling zero baselines."""
    if baseline_value == 0:
        return 0.0 if current_value == 0 else 100.0

    return (current_value - baseline_value) / baseline_value * 100


def analyze_root_cause(
    *,
    schema_status: str = "compatible",
    current_reference_count: int = 0,
    historical_reference_count: int = 0,
    current_ri_failures: int = 0,
    historical_ri_failures: int = 0,
    current_rejection_rate: float = 0.0,
    historical_rejection_rate: float = 0.0,
    reference_drop_threshold_percent: float = 30.0,
    ri_failure_increase_threshold_percent: float = 50.0,
    rejection_rate_increase_threshold_percent: float = 50.0,
) -> dict[str, Any]:
    """Identify a probable deterministic root cause from monitoring evidence."""
    reference_count_change = _percent_change(
        current_reference_count,
        historical_reference_count,
    )
    ri_failure_change = _percent_change(
        current_ri_failures,
        historical_ri_failures,
    )
    rejection_rate_change = _percent_change(
        current_rejection_rate,
        historical_rejection_rate,
    )

    evidence = [
        {"metric": "schema_status", "value": schema_status},
        {
            "metric": "historical_reference_count",
            "value": historical_reference_count,
        },
        {"metric": "current_reference_count", "value": current_reference_count},
        {
            "metric": "reference_count_change_percent",
            "value": reference_count_change,
        },
        {"metric": "historical_ri_failures", "value": historical_ri_failures},
        {"metric": "current_ri_failures", "value": current_ri_failures},
        {"metric": "ri_failure_change_percent", "value": ri_failure_change},
        {"metric": "historical_rejection_rate", "value": historical_rejection_rate},
        {"metric": "current_rejection_rate", "value": current_rejection_rate},
        {
            "metric": "rejection_rate_change_percent",
            "value": rejection_rate_change,
        },
    ]

    if schema_status == "breaking":
        return {
            "root_cause": "schema_breaking_change",
            "confidence": 0.9,
            "evidence": evidence,
            "explanation": (
                "The incoming schema has a breaking change, such as a removed "
                "required column or changed column type."
            ),
        }

    has_reference_drop = reference_count_change <= -reference_drop_threshold_percent
    has_ri_failure_spike = ri_failure_change >= ri_failure_increase_threshold_percent

    if has_reference_drop and has_ri_failure_spike:
        return {
            "root_cause": "upstream_volume_drop",
            "confidence": 0.85,
            "evidence": evidence,
            "explanation": (
                "Reference data volume dropped while referential-integrity "
                "failures increased, which points to missing upstream reference "
                "records."
            ),
        }

    if rejection_rate_change >= rejection_rate_increase_threshold_percent:
        return {
            "root_cause": "source_quality_degradation",
            "confidence": 0.75,
            "evidence": evidence,
            "explanation": (
                "The rejection rate increased significantly without enough "
                "evidence of a schema or reference-volume incident."
            ),
        }

    return {
        "root_cause": "unknown",
        "confidence": 0.0,
        "evidence": evidence,
        "explanation": "No configured rule had enough evidence to identify a root cause.",
    }
