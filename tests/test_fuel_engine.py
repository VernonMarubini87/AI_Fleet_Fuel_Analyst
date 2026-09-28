import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from fleet_analyst.analytics.fuel_engine import (
    per_vehicle_fuel_summary, fleet_wide_kpis, efficiency_trend, benchmark_against_fleet
)

fuel_df = pd.DataFrame({
    "vehicle_id": ["VH-1", "VH-1", "VH-2"],
    "litres": [50, 50, 20],
    "total_cost": [1175, 1175, 470],
    "price_per_litre": [23.5, 23.5, 23.5],
    "timestamp": ["2026-05-01 08:00", "2026-05-08 08:00", "2026-05-01 09:00"],
})
trip_df = pd.DataFrame({
    "vehicle_id": ["VH-1", "VH-1", "VH-2"],
    "actual_distance_km": [400, 400, 100],
    "idle_minutes": [10, 10, 5],
    "date": ["2026-05-01", "2026-05-08", "2026-05-01"],
})


def test_per_vehicle_fuel_summary_calculates_litres_per_100km():
    summary = per_vehicle_fuel_summary(fuel_df, trip_df)
    vh1 = summary[summary["vehicle_id"] == "VH-1"].iloc[0]
    assert round(vh1["litres_per_100km"], 1) == 12.5  # 100 litres / 800km * 100


def test_fleet_wide_kpis():
    kpis = fleet_wide_kpis(fuel_df, trip_df)
    assert kpis["total_litres"] == 120
    assert kpis["n_vehicles"] == 2


def test_efficiency_trend_returns_periods():
    trend = efficiency_trend(fuel_df, trip_df, freq="W")
    assert "litres_per_100km" in trend.columns
    assert len(trend) > 0


def test_benchmark_against_fleet_flags_outlier():
    summary = per_vehicle_fuel_summary(fuel_df, trip_df)
    benchmarked = benchmark_against_fleet(summary)
    assert "efficiency_flag" in benchmarked.columns
