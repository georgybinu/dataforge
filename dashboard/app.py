"""Local DataForge analytics dashboard."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.duckdb_queries import (
    query_customer_performance,
    query_daily_sales,
    query_filter_options,
    query_pipeline_quality,
    query_product_performance,
    query_store_performance,
)
from src.monitoring.anomaly_detection import detect_metric_anomaly, detect_volume_anomaly
from src.root_cause.analyzer import analyze_root_cause


st.set_page_config(
    page_title="DataForge Dashboard",
    page_icon="D",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_filter_options() -> dict[str, list[str]]:
    return query_filter_options()


@st.cache_data
def load_daily_sales(start_date: date, end_date: date):
    return query_daily_sales(start_date, end_date)


@st.cache_data
def load_products(product_id: str | None):
    return query_product_performance(product_id)


@st.cache_data
def load_stores(store_id: str | None):
    return query_store_performance(store_id)


@st.cache_data
def load_customers():
    return query_customer_performance()


@st.cache_data
def load_pipeline_quality():
    return query_pipeline_quality()


def _show_intelligence_demo() -> None:
    """Render the deterministic Step 13 intelligence demonstration."""
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
        historical_reference_count=round(sum(historical_customer_counts) / len(historical_customer_counts)),
        current_ri_failures=current_customer_ri_failures,
        historical_ri_failures=round(sum(historical_customer_ri_failures) / len(historical_customer_ri_failures)),
    )

    st.info(
        "Deterministic Step 13 intelligence demo. This scenario is fixed example "
        "data from the rule-based demo, not a live incident feed."
    )
    left_column, right_column = st.columns(2)
    with left_column:
        st.markdown("**Detected signals**")
        for result in (orders_volume_result, customer_volume_result, customer_ri_result):
            if result["is_anomaly"]:
                st.warning(result["message"])
    with right_column:
        st.markdown("**Probable root cause**")
        st.metric("Root cause", str(root_cause["root_cause"]).replace("_", " ").title())
        st.caption(
            f"Confidence: {root_cause['confidence']:.0%}. {root_cause['explanation']}"
        )


def main() -> None:
    st.title("DataForge")
    st.subheader("Intelligent Data Quality & Pipeline Reliability Platform")

    try:
        options = load_filter_options()
        if not options["dates"]:
            st.warning("No Gold sales data is available for the selected workspace.")
            return

        min_date = date.fromisoformat(options["dates"][0])
        max_date = date.fromisoformat(options["dates"][-1])
        with st.sidebar:
            st.header("Filters")
            selected_dates = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            selected_store = st.selectbox("Store", ["All stores", *options["stores"]])
            selected_product = st.selectbox(
                "Product", ["All products", *options["products"]]
            )

        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
        else:
            start_date = end_date = selected_dates
        store_id = None if selected_store == "All stores" else selected_store
        product_id = None if selected_product == "All products" else selected_product

        daily_sales = load_daily_sales(start_date, end_date)
        products = load_products(product_id)
        stores = load_stores(store_id)
        customers = load_customers()
        pipeline = load_pipeline_quality()

        total_sales = float(daily_sales["total_sales"].sum())
        total_orders = int(daily_sales["order_count"].sum())
        average_order_value = total_sales / total_orders if total_orders else 0.0
        pipeline_row = pipeline.iloc[0]

        st.markdown("### Key performance indicators")
        kpi_columns = st.columns(4)
        kpi_columns[0].metric("Total orders", f"{total_orders:,}")
        kpi_columns[1].metric("Valid records", f"{int(pipeline_row['records_valid']):,}")
        kpi_columns[2].metric("Rejected records", f"{int(pipeline_row['records_rejected']):,}")
        kpi_columns[3].metric("Rejection rate", f"{float(pipeline_row['rejection_rate']):.2f}%")

        st.caption(
            f"Sales: ${total_sales:,.2f} | Average order value: ${average_order_value:,.2f}"
        )

        st.markdown("### Sales analytics")
        sales_column, product_column = st.columns(2)
        with sales_column:
            st.markdown("**Daily sales**")
            daily_chart = px.line(
                daily_sales,
                x="order_date",
                y="total_sales",
                markers=True,
                labels={"order_date": "Date", "total_sales": "Sales"},
            )
            st.plotly_chart(daily_chart, use_container_width=True)
        with product_column:
            st.markdown("**Top products by sales**")
            product_chart = px.bar(
                products.head(10).sort_values("total_sales"),
                x="total_sales",
                y="product_id",
                orientation="h",
                labels={"product_id": "Product", "total_sales": "Sales"},
            )
            st.plotly_chart(product_chart, use_container_width=True)

        st.markdown("**Store performance**")
        store_chart = px.bar(
            stores.head(10).sort_values("total_sales"),
            x="store_id",
            y="total_sales",
            labels={"store_id": "Store", "total_sales": "Sales"},
        )
        st.plotly_chart(store_chart, use_container_width=True)

        st.markdown("### Customer analytics")
        customer_chart = px.bar(
            customers.head(10).sort_values("total_sales"),
            x="total_sales",
            y="customer_id",
            orientation="h",
            labels={"customer_id": "Customer", "total_sales": "Sales"},
        )
        st.plotly_chart(customer_chart, use_container_width=True)

        st.markdown("### Pipeline health")
        health_columns = st.columns(4)
        health_columns[0].metric("Status", str(pipeline_row["status"]).title())
        health_columns[1].metric("Records processed", f"{int(pipeline_row['records_received']):,}")
        health_columns[2].metric("Valid records", f"{int(pipeline_row['records_valid']):,}")
        health_columns[3].metric("Rejection rate", f"{float(pipeline_row['rejection_rate']):.2f}%")

        st.markdown("### Pipeline intelligence")
        _show_intelligence_demo()
    except (FileNotFoundError, ValueError) as error:
        st.error(f"Unable to load DataForge Gold data: {error}")


if __name__ == "__main__":
    main()
