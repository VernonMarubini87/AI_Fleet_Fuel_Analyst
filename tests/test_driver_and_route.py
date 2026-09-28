import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from fleet_analyst.analytics.driver_behavior import driver_scorecard, driver_fuel_link
from fleet_analyst.analytics.route_engine import route_variance, depot_summary, cost_per_trip

trip_df = pd.DataFrame({
    "vehicle_id": ["VH-1", "VH-2"],
    "driver_id": ["DR-1", "DR-2"],
    "actual_distance_km": [400, 100],
    "planned_distance_km": [380, 100],
    "harsh_braking_events": [10, 1],
    "harsh_accel_events": [8, 0],
    "idle_minutes": [60, 10],
    "after_hours_km": [100, 2],
    "depot": ["Pretoria DC", "Polokwane DC"],
})
fuel_df = pd.DataFrame({
    "vehicle_id": ["VH-1", "VH-2"],
    "driver_id": ["DR-1", "DR-2"],
    "litres": [50, 20],
    "total_cost": [1175, 470],
    "depot": ["Pretoria DC", "Polokwane DC"],
})


def test_driver_scorecard_flags_risky_driver_higher():
    scores = driver_scorecard(trip_df)
    dr1 = scores[scores["driver_id"] == "DR-1"].iloc[0]
    dr2 = scores[scores["driver_id"] == "DR-2"].iloc[0]
    assert dr1["risk_score"] > dr2["risk_score"]


def test_driver_fuel_link_merges_cost():
    scores = driver_scorecard(trip_df)
    linked = driver_fuel_link(fuel_df, scores)
    assert "total_fuel_cost" in linked.columns


def test_route_variance_flags_detour():
    rv = route_variance(trip_df)
    assert "distance_variance_pct" in rv.columns


def test_depot_summary_aggregates():
    ds = depot_summary(trip_df, fuel_df)
    assert len(ds) == 2
    assert "total_distance_km" in ds.columns
