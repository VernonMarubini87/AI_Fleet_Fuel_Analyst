"""
AI Fleet Fuel & Logistics Analyst — Streamlit dashboard.
Run with: streamlit run app.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
import plotly.express as px

from fleet_analyst.ingestion.loader import load_fuel_transactions, load_trip_log
from fleet_analyst.ingestion.profiler import profile_dataframe
from fleet_analyst.quality.cleaner import clean_fuel_transactions, clean_trip_log
from fleet_analyst.analytics.fuel_engine import (
    per_vehicle_fuel_summary, fleet_wide_kpis, efficiency_trend, benchmark_against_fleet
)
from fleet_analyst.analytics.driver_behavior import driver_scorecard, driver_fuel_link
from fleet_analyst.analytics.route_engine import route_variance, depot_summary
from fleet_analyst.analytics.anomaly_engine import (
    detect_fill_anomalies, detect_efficiency_outliers, detect_fill_vs_distance_mismatch, anomaly_summary
)
from fleet_analyst.forecasting.forecast_engine import evaluate_and_forecast
from fleet_analyst.ai.claude_client import ClaudeClient
from fleet_analyst.ai.orchestrator import FleetFuelAgent
from fleet_analyst.reporting.report_generator import generate_management_report
from fleet_analyst.qa.validators import gate_before_display

st.set_page_config(page_title="AI Fleet Fuel & Logistics Analyst", layout="wide")
st.title("🚚 AI Fleet Fuel & Logistics Analyst")
st.caption("Upload fuel-card and GPS/trip exports for automatic efficiency, fraud, and cost analysis.")

DEFAULT_FUEL_PATH = os.path.join(os.path.dirname(__file__), "data", "synthetic_fuel_transactions.csv")
DEFAULT_TRIP_PATH = os.path.join(os.path.dirname(__file__), "data", "synthetic_trip_gps_log.csv")

with st.sidebar:
    st.header("Data")
    fuel_file = st.file_uploader("Fuel-card export (CSV/XLSX)", type=["csv", "xlsx"])
    trip_file = st.file_uploader("GPS/trip log export (CSV/XLSX)", type=["csv", "xlsx"])
    use_demo = st.checkbox("Use demo data", value=(fuel_file is None and trip_file is None))
    api_key = st.text_input("Anthropic API key (optional)", type="password")
    st.caption("Without a key, the deterministic report tab still works fully.")

if use_demo:
    fuel_result = load_fuel_transactions(DEFAULT_FUEL_PATH)
    trip_result = load_trip_log(DEFAULT_TRIP_PATH)
elif fuel_file and trip_file:
    fuel_result = load_fuel_transactions(fuel_file)
    trip_result = load_trip_log(trip_file)
else:
    st.info("Upload both files, or tick 'Use demo data' to explore with a synthetic fleet.")
    st.stop()

if not fuel_result.ok:
    st.error(f"Fuel file missing required columns: {fuel_result.unmapped_required}")
    st.stop()
if not trip_result.ok:
    st.error(f"Trip file missing required columns: {trip_result.unmapped_required}")
    st.stop()

fuel_df, fuel_rejects, fuel_issues = clean_fuel_transactions(fuel_result.df)
trip_df, trip_rejects, trip_issues = clean_trip_log(trip_result.df)

vehicle_summary = per_vehicle_fuel_summary(fuel_df, trip_df)
vehicle_summary = benchmark_against_fleet(vehicle_summary)
vehicle_summary = detect_efficiency_outliers(vehicle_summary)
fleet_kpis = fleet_wide_kpis(fuel_df, trip_df)
driver_scores = driver_scorecard(trip_df)
driver_scores = driver_fuel_link(fuel_df, driver_scores)
route_var_df = route_variance(trip_df)
depot_df = depot_summary(trip_df, fuel_df)
fill_anomalies_df = detect_fill_anomalies(fuel_df)
mismatch_df = detect_fill_vs_distance_mismatch(fuel_df, trip_df)
anomaly_summary_dict = anomaly_summary(fill_anomalies_df, mismatch_df)
forecast_result = evaluate_and_forecast(fuel_df)

claude_client = ClaudeClient(api_key=api_key) if api_key else ClaudeClient()
agent = FleetFuelAgent(vehicle_summary, driver_scores, anomaly_summary_dict,
                        mismatch_df, forecast_result, route_var_df, claude_client)

tabs = st.tabs(["Overview", "Vehicle Efficiency", "Driver Risk", "Fraud & Anomalies",
                 "Routes & Depots", "Forecast", "Ask the Analyst", "Management Report", "Data Quality"])

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vehicles", fleet_kpis["n_vehicles"])
    c2.metric("Total distance (km)", f"{fleet_kpis['total_distance_km']:,.0f}")
    c3.metric("Total fuel spend", f"R{fleet_kpis['total_fuel_cost']:,.0f}")
    c4.metric("Fleet L/100km", fleet_kpis["fleet_litres_per_100km"])

    trend_df = efficiency_trend(fuel_df, trip_df)
    fig = px.line(trend_df, x="period", y="litres_per_100km", title="Fleet-wide fuel efficiency trend (weekly)")
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("Per-vehicle fuel summary")
    st.dataframe(vehicle_summary, use_container_width=True)
    fig2 = px.bar(vehicle_summary.head(15), x="vehicle_id", y="cost_per_km",
                  color="efficiency_flag", title="Cost per km by vehicle (top 15)")
    st.plotly_chart(fig2, use_container_width=True)

with tabs[2]:
    st.subheader("Driver risk scorecard")
    st.dataframe(driver_scores, use_container_width=True)
    if "risk_score" in driver_scores.columns:
        fig3 = px.bar(driver_scores.head(15), x="driver_id", y="risk_score",
                      color="risk_tier", title="Driver risk score (top 15)")
        st.plotly_chart(fig3, use_container_width=True)

with tabs[3]:
    st.subheader("Fuel card fraud & anomaly flags")
    st.metric("Flagged transactions", anomaly_summary_dict["n_flagged_transactions"])
    st.metric("Vehicles with fill-vs-distance mismatch", anomaly_summary_dict["n_vehicles_with_fill_distance_mismatch"])
    st.write("**Flagged transactions:**")
    st.dataframe(fill_anomalies_df[fill_anomalies_df["is_flagged"]], use_container_width=True)
    st.write("**Fill-vs-distance mismatch by vehicle:**")
    st.dataframe(mismatch_df, use_container_width=True)

with tabs[4]:
    st.subheader("Route variance (planned vs actual)")
    if len(route_var_df):
        st.dataframe(route_var_df[route_var_df.get("detour_flag", False) == True], use_container_width=True)
    st.subheader("Depot summary")
    st.dataframe(depot_df, use_container_width=True)

with tabs[5]:
    st.subheader("Fuel spend forecast")
    if forecast_result.get("status") == "ok":
        st.write(f"Best-performing model on backtest: **{forecast_result['best_model']}**")
        st.json(forecast_result["backtest_mae"])
        forecast_chart_df = pd.DataFrame({
            "week": list(range(len(forecast_result["historical_weekly_spend"]))) +
                    list(range(len(forecast_result["historical_weekly_spend"]),
                                len(forecast_result["historical_weekly_spend"]) + len(forecast_result["forecast_next_periods"]))),
            "spend": forecast_result["historical_weekly_spend"] + forecast_result["forecast_next_periods"],
            "type": ["actual"] * len(forecast_result["historical_weekly_spend"]) +
                    ["forecast"] * len(forecast_result["forecast_next_periods"]),
        })
        fig4 = px.line(forecast_chart_df, x="week", y="spend", color="type", title="Weekly fuel spend: actual + forecast")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning(forecast_result.get("message"))

with tabs[6]:
    st.subheader("Ask the Analyst")
    question = st.text_input("Ask a question about your fleet (e.g. 'Which drivers are riskiest?')")
    if question:
        result = agent.ask(question)
        qa_gate = gate_before_display(result["evidence"])
        if not qa_gate["passed"]:
            st.error(f"QA gate failed: {qa_gate['problems']}")
        else:
            st.write(result["answer"])
            with st.expander("Evidence used"):
                st.json(result["evidence"])

with tabs[7]:
    st.subheader("Deterministic management report (no API key required)")
    report_text = generate_management_report(
        fleet_kpis, vehicle_summary.head(5), driver_scores.head(5), anomaly_summary_dict, forecast_result
    )
    st.text(report_text)
    st.download_button("Download report (.txt)", report_text, file_name="fleet_management_report.txt")

with tabs[8]:
    st.subheader("Data quality")
    st.write("**Fuel data profile:**")
    st.json(profile_dataframe(fuel_df, date_col="timestamp"))
    st.write(f"**Fuel rejected rows log:** {len(fuel_rejects)} issue batches")
    st.json(fuel_rejects)
    st.write("**Trip data profile:**")
    st.json(profile_dataframe(trip_df, date_col="date"))
    st.write(f"**Trip rejected rows log:** {len(trip_rejects)} issue batches")
    st.json(trip_rejects)
