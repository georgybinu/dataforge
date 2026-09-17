from src.root_cause.analyzer import analyze_root_cause


def test_analyze_root_cause_detects_upstream_volume_drop_with_ri_failures() -> None:
    result = analyze_root_cause(
        current_reference_count=420,
        historical_reference_count=750,
        current_ri_failures=187,
        historical_ri_failures=5,
    )

    assert result["root_cause"] == "upstream_volume_drop"
    assert result["confidence"] == 0.85


def test_analyze_root_cause_detects_schema_breaking_change() -> None:
    result = analyze_root_cause(schema_status="breaking")

    assert result["root_cause"] == "schema_breaking_change"
    assert result["confidence"] == 0.9


def test_analyze_root_cause_detects_source_quality_degradation() -> None:
    result = analyze_root_cause(
        current_rejection_rate=15.0,
        historical_rejection_rate=5.0,
    )

    assert result["root_cause"] == "source_quality_degradation"
    assert result["confidence"] == 0.75


def test_analyze_root_cause_returns_unknown_when_evidence_is_weak() -> None:
    result = analyze_root_cause(
        current_reference_count=740,
        historical_reference_count=750,
        current_ri_failures=6,
        historical_ri_failures=5,
        current_rejection_rate=5.1,
        historical_rejection_rate=5.0,
    )

    assert result["root_cause"] == "unknown"
    assert result["confidence"] == 0.0


def test_analyze_root_cause_includes_evidence() -> None:
    result = analyze_root_cause(
        current_reference_count=420,
        historical_reference_count=750,
        current_ri_failures=187,
        historical_ri_failures=5,
    )

    evidence_metrics = {item["metric"] for item in result["evidence"]}

    assert "historical_reference_count" in evidence_metrics
    assert "current_reference_count" in evidence_metrics
    assert "historical_ri_failures" in evidence_metrics
    assert "current_ri_failures" in evidence_metrics
    assert "reference_count_change_percent" in evidence_metrics
    assert "ri_failure_change_percent" in evidence_metrics


def test_analyze_root_cause_is_deterministic() -> None:
    first_result = analyze_root_cause(
        current_reference_count=420,
        historical_reference_count=750,
        current_ri_failures=187,
        historical_ri_failures=5,
    )
    second_result = analyze_root_cause(
        current_reference_count=420,
        historical_reference_count=750,
        current_ri_failures=187,
        historical_ri_failures=5,
    )

    assert first_result == second_result
