"""Local DataForge data quality and pipeline reliability dashboard."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.duckdb_queries import (
    query_customer_performance,
    query_daily_sales,
    query_filter_options,
    query_overall_sales_summary,
    query_pipeline_quality,
    query_product_performance,
    query_store_performance,
)
from src.monitoring.anomaly_detection import detect_metric_anomaly, detect_volume_anomaly
from src.root_cause.analyzer import analyze_root_cause


st.set_page_config(
    page_title="DataForge | Reliability Platform",
    page_icon="D",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "ink": "#132238",
    "muted": "#617083",
    "blue": "#1976D2",
    "green": "#18845B",
    "amber": "#B87503",
    "red": "#C44747",
    "line": "#DCE4EC",
    "canvas": "#F5F7FA",
    "white": "#FFFFFF",
}


@st.cache_data
def load_filter_options() -> dict[str, list[str]]:
    return query_filter_options()


@st.cache_data
def load_summary():
    return query_overall_sales_summary()


@st.cache_data
def load_daily_sales(start_date: date | None, end_date: date | None):
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


def _inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        :root {{ --df-ink:{COLORS['ink']}; --df-muted:{COLORS['muted']}; --df-line:{COLORS['line']}; --df-canvas:{COLORS['canvas']}; }}
        .stApp {{ background:var(--df-canvas); color:var(--df-ink); }}
        [data-testid="stHeader"] {{ background:transparent; }}
        [data-testid="stSidebar"] {{ background:#102033; }}
        [data-testid="stSidebar"] * {{ color:#EAF1F8; }}
        .df-brand {{ border-bottom:1px solid var(--df-line); padding:.5rem 0 1.25rem; margin-bottom:1.5rem; }}
        .df-brand h1 {{ margin:0; color:var(--df-ink); font-size:2.1rem; letter-spacing:0; }}
        .df-brand p {{ color:var(--df-muted); margin:.35rem 0 0; font-size:1rem; }}
        .df-kicker {{ color:{COLORS['blue']}; font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.35rem; }}
        .df-context {{ background:{COLORS['white']}; border:1px solid var(--df-line); border-left:4px solid {COLORS['blue']}; padding:.75rem 1rem; margin-bottom:1.25rem; color:var(--df-muted); font-size:.9rem; }}
        .df-section {{ margin:1.4rem 0 .7rem; }}
        .df-section h2 {{ color:var(--df-ink); font-size:1.35rem; margin:0; }}
        .df-section p {{ color:var(--df-muted); margin:.25rem 0 0; }}
        .df-panel {{ background:{COLORS['white']}; border:1px solid var(--df-line); padding:1rem 1.1rem; min-height:100%; }}
        .df-status {{ display:inline-flex; align-items:center; gap:.45rem; font-weight:700; font-size:.82rem; text-transform:uppercase; }}
        .df-dot {{ width:.6rem; height:.6rem; border-radius:50%; display:inline-block; }}
        .df-demo {{ background:#FFF5DF; border:1px solid #EBC979; border-left:5px solid {COLORS['amber']}; padding:.9rem 1rem; color:#6D4A08; margin:.8rem 0 1rem; }}
        .df-note {{ background:#EDF2F7; border:1px solid var(--df-line); padding:.8rem 1rem; color:var(--df-muted); font-size:.9rem; }}
        .df-footer {{ color:var(--df-muted); font-size:.78rem; border-top:1px solid var(--df-line); padding-top:1rem; margin-top:2rem; }}
        div[data-testid="stMetric"] {{ background:{COLORS['white']}; border:1px solid var(--df-line); padding:.85rem 1rem; }}
        div[data-testid="stMetricLabel"] {{ color:var(--df-muted); }}
        div[data-testid="stMetricValue"] {{ color:var(--df-ink); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section(title: str, description: str = "") -> None:
    st.markdown(f'<div class="df-section"><h2>{title}</h2><p>{description}</p></div>', unsafe_allow_html=True)


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _format_timestamp(value: Any) -> str:
    return "Unavailable" if value is None else str(value).replace("T", " ").replace("+00:00", " UTC")


def _status_details(status: str) -> tuple[str, str, str]:
    normalized = status.lower()
    if normalized == "success":
        return "Healthy", COLORS["green"], "#E8F5EF"
    if normalized in {"warning", "partial"}:
        return "Warning", COLORS["amber"], "#FFF5DF"
    return status.title(), COLORS["red"], "#FDECEC"


def _status_badge(status: str) -> None:
    label, color, background = _status_details(status)
    st.markdown(
        f'<span class="df-status" style="color:{color};background:{background};padding:.4rem .65rem;">'
        f'<span class="df-dot" style="background:{color};"></span>{label}</span>',
        unsafe_allow_html=True,
    )


def _plot_layout(title: str) -> dict[str, Any]:
    return {
        "title": {"text": title, "font": {"size": 16, "color": COLORS["ink"]}},
        "paper_bgcolor": COLORS["white"],
        "plot_bgcolor": COLORS["white"],
        "font": {"color": COLORS["muted"]},
        "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
        "hoverlabel": {"bgcolor": COLORS["ink"], "font": {"color": "white"}},
        "legend": {"orientation": "h", "y": 1.08},
    }


def _show_empty(message: str) -> None:
    st.markdown(f'<div class="df-note">{message}</div>', unsafe_allow_html=True)


def _render_header(pipeline_row: Any) -> None:
    st.markdown(
        '<div class="df-brand"><div class="df-kicker">Data quality operations</div>'
        '<h1>DataForge</h1><p>Data Quality &amp; Pipeline Reliability Platform</p></div>',
        unsafe_allow_html=True,
    )
    status = str(pipeline_row["status"]) if pipeline_row is not None else "unavailable"
    end_time = pipeline_row["end_time"] if pipeline_row is not None else None
    st.markdown(
        f'<div class="df-context"><strong>Local data workspace</strong> · Latest recorded pipeline run · '
        f'Last run: {_format_timestamp(end_time)} · Status: {status.title()}</div>',
        unsafe_allow_html=True,
    )


def _render_sidebar(options: dict[str, list[str]]) -> tuple[str, date | None, date | None, str | None, str | None]:
    with st.sidebar:
        st.markdown("# DataForge")
        st.caption("Reliability workspace")
        view = st.radio("Workspace", ["Overview", "Data Quality", "Pipeline Health", "Intelligence", "Data Explorer"], label_visibility="collapsed")
        st.divider()
        st.markdown("**Global filters**")
        if options["dates"]:
            minimum_date = date.fromisoformat(options["dates"][0])
            maximum_date = date.fromisoformat(options["dates"][-1])
            selected_dates = st.date_input("Sales date range", value=(minimum_date, maximum_date), min_value=minimum_date, max_value=maximum_date)
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                start_date, end_date = selected_dates
            else:
                start_date = end_date = selected_dates
        else:
            start_date = end_date = None
        selected_store = st.selectbox("Store", ["All stores", *options["stores"]])
        selected_product = st.selectbox("Product", ["All products", *options["products"]])
        st.divider()
        st.caption("Filters affect only views supported by the underlying Gold query.")
    return view, start_date, end_date, None if selected_store == "All stores" else selected_store, None if selected_product == "All products" else selected_product


def _render_kpis(summary_row: Any, pipeline_row: Any) -> None:
    kpis = [
        ("Total Revenue", _format_currency(float(summary_row["total_sales"])), "Sales across the Gold daily aggregate"),
        ("Total Orders", f"{int(summary_row['total_orders']):,}", "Aggregated Gold orders"),
        ("Average Order Value", _format_currency(float(summary_row["average_order_value"])), "Weighted from total sales"),
        ("Records Processed", f"{int(pipeline_row['records_received']):,}", "Latest recorded run"),
        ("Valid Records", f"{int(pipeline_row['records_valid']):,}", "Passed quality checks"),
        ("Rejected Records", f"{int(pipeline_row['records_rejected']):,}", "Sent to quarantine"),
        ("Rejection Rate", f"{float(pipeline_row['rejection_rate']):.2f}%", "Latest recorded run"),
    ]
    columns = st.columns(4)
    for index, (label, value, help_text) in enumerate(kpis):
        columns[index % 4].metric(label, value, help=help_text)


def _render_sales_charts(daily_sales: Any, products: Any, stores: Any) -> None:
    _section("Sales performance", "Revenue trend and operational performance by product and store.")
    if daily_sales.empty:
        _show_empty("No daily sales rows match the selected date range.")
    else:
        sales_chart = px.line(daily_sales, x="order_date", y="total_sales", markers=True, labels={"order_date": "Date", "total_sales": "Revenue"}, hover_data={"total_sales": ":$,.2f", "order_count": ":,"})
        sales_chart.update_layout(**_plot_layout("Revenue trend"), yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(sales_chart, width="stretch")

    product_column, store_column = st.columns(2)
    with product_column:
        if products.empty:
            _show_empty("No product metrics available for the selected product filter.")
        else:
            product_chart = px.bar(products.head(10).sort_values("total_sales"), x="total_sales", y="product_id", orientation="h", labels={"product_id": "Product", "total_sales": "Revenue"}, hover_data={"total_sales": ":$,.2f", "total_orders": ":,", "total_quantity": ":,"}, color_discrete_sequence=[COLORS["blue"]])
            product_chart.update_layout(**_plot_layout("Top products by revenue"), xaxis_tickprefix="$", xaxis_tickformat=",.0f")
            st.plotly_chart(product_chart, width="stretch")
    with store_column:
        if stores.empty:
            _show_empty("No store metrics available for the selected store filter.")
        else:
            store_chart = px.bar(stores.head(10).sort_values("total_sales"), x="total_sales", y="store_id", orientation="h", labels={"store_id": "Store", "total_sales": "Revenue"}, hover_data={"total_sales": ":$,.2f", "total_orders": ":,"}, color_discrete_sequence=[COLORS["green"]])
            store_chart.update_layout(**_plot_layout("Top stores by revenue"), xaxis_tickprefix="$", xaxis_tickformat=",.0f")
            st.plotly_chart(store_chart, width="stretch")


def _render_overview(summary: Any, pipeline: Any, daily_sales: Any, products: Any, stores: Any) -> None:
    _section("Overview", "A decision-ready view of sales performance and the latest local pipeline run.")
    _render_kpis(summary.iloc[0], pipeline.iloc[0])
    _render_sales_charts(daily_sales, products, stores)


def _render_data_quality(pipeline: Any) -> None:
    row = pipeline.iloc[0]
    _section("Data Quality", "Aggregate quality outcomes from the latest recorded pipeline run.")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Total records", f"{int(row['records_received']):,}")
    metric_columns[1].metric("Valid records", f"{int(row['records_valid']):,}")
    metric_columns[2].metric("Rejected records", f"{int(row['records_rejected']):,}")
    metric_columns[3].metric("Rejection rate", f"{float(row['rejection_rate']):.2f}%")
    quality_column, note_column = st.columns([1, 1])
    with quality_column:
        chart = go.Figure(go.Pie(labels=["Valid", "Rejected"], values=[int(row["records_valid"]), int(row["records_rejected"])], hole=0.64, marker_colors=[COLORS["green"], COLORS["red"]], textinfo="label+percent", hovertemplate="%{label}: %{value:,} records<extra></extra>"))
        chart.update_layout(**_plot_layout("Valid versus rejected records"), showlegend=False)
        st.plotly_chart(chart, width="stretch")
    with note_column:
        st.markdown('<div class="df-panel">', unsafe_allow_html=True)
        st.markdown("**Quality outcome**")
        st.markdown(f"The latest local run accepted **{int(row['records_valid']):,}** records and routed **{int(row['records_rejected']):,}** records to the Quarantine output.")
        st.markdown('<div class="df-note"><strong>Rule-level detail unavailable</strong><br>The current Gold and DuckDB query contract exposes aggregate pipeline metrics, not per-rule failure counts or row-level quarantine records. No rule-level metrics are inferred or fabricated in this dashboard.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def _render_pipeline_health(pipeline: Any) -> None:
    row = pipeline.iloc[0]
    _section("Pipeline Health", "Operational context for the latest locally recorded run.")
    status_column, detail_column = st.columns([1, 2])
    with status_column:
        st.markdown('<div class="df-panel">', unsafe_allow_html=True)
        st.markdown('<div class="df-kicker">Latest local run</div>', unsafe_allow_html=True)
        _status_badge(str(row["status"]))
        st.metric("Pipeline", str(row["pipeline_name"]))
        st.markdown('</div>', unsafe_allow_html=True)
    with detail_column:
        st.markdown('<div class="df-panel">', unsafe_allow_html=True)
        metrics = st.columns(4)
        metrics[0].metric("Records received", f"{int(row['records_received']):,}")
        metrics[1].metric("Valid", f"{int(row['records_valid']):,}")
        metrics[2].metric("Rejected", f"{int(row['records_rejected']):,}")
        metrics[3].metric("Rejection rate", f"{float(row['rejection_rate']):.2f}%")
        st.markdown(f"**Duration:** {float(row.get('duration_seconds', 0.0)):.2f} seconds  ·  **Started:** {_format_timestamp(row['start_time'])}  ·  **Finished:** {_format_timestamp(row['end_time'])}")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="df-note" style="margin-top:1rem"><strong>Local latest-run view:</strong> These values come from the most recent Parquet pipeline metric. This is not live production monitoring and does not imply an active alerting service.</div>', unsafe_allow_html=True)


def _intelligence_results() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    historical_orders_received = [2000, 2015, 1990, 2005]
    historical_customer_counts = [750, 750, 749, 751]
    historical_customer_ri_failures = [5, 6, 4, 5]
    current_orders_received = 1950
    current_customer_count = 420
    current_customer_ri_failures = 187
    results = [
        detect_volume_anomaly(current_orders_received, historical_orders_received, metric="orders received"),
        detect_volume_anomaly(current_customer_count, historical_customer_counts, metric="customer reference volume"),
        detect_metric_anomaly("customer referential-integrity failures", current_customer_ri_failures, historical_customer_ri_failures),
    ]
    root_cause = analyze_root_cause(current_reference_count=current_customer_count, historical_reference_count=round(sum(historical_customer_counts) / len(historical_customer_counts)), current_ri_failures=current_customer_ri_failures, historical_ri_failures=round(sum(historical_customer_ri_failures) / len(historical_customer_ri_failures)))
    return results, root_cause


def _render_intelligence() -> None:
    _section("Intelligence", "Rule-based anomaly signals and root-cause reasoning from the Step 13 demonstration.")
    st.markdown('<div class="df-demo"><strong>DETERMINISTIC DEMO — NOT LIVE INCIDENT DETECTION</strong><br>This panel replays the fixed Step 13 scenario. It is example evidence for the rule-based intelligence layer, not a live production incident.</div>', unsafe_allow_html=True)
    results, root_cause = _intelligence_results()
    st.markdown("**Anomaly evidence**")
    anomaly_columns = st.columns(len(results))
    for column, result in zip(anomaly_columns, results):
        with column:
            state = "Anomaly" if result["is_anomaly"] else "Normal"
            color = COLORS["red"] if result["is_anomaly"] else COLORS["green"]
            background = "#FDECEC" if result["is_anomaly"] else "#E8F5EF"
            st.markdown(f'<div class="df-panel" style="border-top:4px solid {color};background:{background}"><div class="df-kicker">{state}</div><strong>{result["metric"].title()}</strong><p>{result["message"]}</p></div>', unsafe_allow_html=True)
    root_column, evidence_column = st.columns([1, 1.5])
    with root_column:
        st.markdown('<div class="df-panel">', unsafe_allow_html=True)
        st.markdown('<div class="df-kicker">Probable root cause</div>', unsafe_allow_html=True)
        st.subheader(str(root_cause["root_cause"]).replace("_", " ").title())
        st.metric("Confidence", f"{float(root_cause['confidence']):.0%}")
        st.markdown(f"**Explanation:** {root_cause['explanation']}")
        st.markdown('</div>', unsafe_allow_html=True)
    with evidence_column:
        st.markdown('<div class="df-panel">', unsafe_allow_html=True)
        st.markdown('<div class="df-kicker">Evidence supplied to the rule engine</div>', unsafe_allow_html=True)
        evidence_rows = [
            {"metric": item["metric"], "value": str(item["value"])}
            for item in root_cause.get("evidence", [])
        ]
        st.dataframe(pd.DataFrame(evidence_rows), width="stretch", hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)


def _render_explorer(daily_sales: Any, products: Any, customers: Any, stores: Any) -> None:
    _section("Data Explorer", "Inspect the Gold aggregates that power the dashboard.")
    dataset = st.selectbox("Gold dataset", ["Daily Sales", "Product Metrics", "Customer Metrics", "Store Metrics"])
    row_limit = st.slider("Rows to display", min_value=10, max_value=100, value=25, step=5)
    frames = {"Daily Sales": daily_sales, "Product Metrics": products, "Customer Metrics": customers, "Store Metrics": stores}
    dataframe = frames[dataset].head(row_limit).copy()
    if dataframe.empty:
        _show_empty("No rows are available for this dataset and the current filters.")
        return
    for column in dataframe.columns:
        if column in {"total_sales", "average_order_value", "average_unit_price"}:
            dataframe[column] = dataframe[column].map(_format_currency)
    st.caption(f"Showing {len(dataframe):,} of {len(frames[dataset]):,} available rows")
    st.dataframe(dataframe, width="stretch", hide_index=True)


def main() -> None:
    _inject_styles()
    try:
        options = load_filter_options()
        pipeline = load_pipeline_quality()
        if pipeline.empty:
            st.error("No pipeline metrics are available in the Gold data.")
            return
        _render_header(pipeline.iloc[0])
        view, start_date, end_date, store_id, product_id = _render_sidebar(options)
        summary = load_summary()
        daily_sales = load_daily_sales(start_date, end_date)
        products = load_products(product_id)
        stores = load_stores(store_id)
        customers = load_customers()
        if view == "Overview":
            _render_overview(summary, pipeline, daily_sales, products, stores)
        elif view == "Data Quality":
            _render_data_quality(pipeline)
        elif view == "Pipeline Health":
            _render_pipeline_health(pipeline)
        elif view == "Intelligence":
            _render_intelligence()
        else:
            _render_explorer(daily_sales, products, customers, stores)
        st.markdown('<div class="df-footer">DataForge runs locally over Gold Parquet data through DuckDB. Latest-run metrics are historical records, not live production telemetry.</div>', unsafe_allow_html=True)
    except (FileNotFoundError, ValueError) as error:
        st.error(f"Unable to load DataForge Gold data: {error}")


if __name__ == "__main__":
    main()
