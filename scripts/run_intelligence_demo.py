"""Run a deterministic DataForge intelligence demo incident analysis."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring.anomaly_detection import detect_metric_anomaly, detect_volume_anomaly
from src.root_cause.analyzer import analyze_root_cause


def main() -> None:
    """Print a deterministic incident report for an upstream reference drop."""
    historical_orders_received = [2000, 2015, 1990, 2005]
    historical_customer_counts = [750, 750, 749, 751]
    historical_customer_ri_failures = [5, 6, 4, 5]

    current_orders_received = 1950
    current_customer_count = 420
    current_customer_ri_failures = 187

    orders_volume_result = detect_volume_anomaly(
        current_orders_received,
        historical_orders_received,
        metric="orders received",
    )
    customer_volume_result = detect_volume_anomaly(
        current_customer_count,
        historical_customer_counts,
        metric="customer reference volume",
    )
    customer_ri_result = detect_metric_anomaly(
        "customer referential-integrity failures",
        current_customer_ri_failures,
        historical_customer_ri_failures,
    )

    root_cause = analyze_root_cause(
        current_reference_count=current_customer_count,
        historical_reference_count=round(
            sum(historical_customer_counts) / len(historical_customer_counts)
        ),
        current_ri_failures=current_customer_ri_failures,
        historical_ri_failures=round(
            sum(historical_customer_ri_failures)
            / len(historical_customer_ri_failures)
        ),
    )

    print("# DATAFORGE INCIDENT ANALYSIS")
    print()
    print("Anomalies detected:")

    if orders_volume_result["is_anomaly"]:
        print(f"- {orders_volume_result['message']}")

    if customer_volume_result["is_anomaly"]:
        print(f"- {customer_volume_result['message']}")

    if customer_ri_result["is_anomaly"]:
        print(f"- {customer_ri_result['message']}")

    print()
    print("Probable root cause:")
    print(root_cause["root_cause"].upper())
    print()
    print("Evidence:")

    for item in root_cause["evidence"]:
        print(f"- {item['metric']}: {item['value']}")

    print()
    print("Explanation:")
    print(root_cause["explanation"])


if __name__ == "__main__":
    main()
