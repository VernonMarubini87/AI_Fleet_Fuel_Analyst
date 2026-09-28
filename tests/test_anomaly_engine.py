import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from fleet_analyst.analytics.anomaly_engine import (
    detect_fill_anomalies, detect_efficiency_outliers, detect_fill_vs_distance_mismatch, anomaly_summary
)


def test_detect_fill_anomalies_flags_excess_litres():
    df = pd.DataFrame({
        "transaction_id": ["F1", "F2"],
        "vehicle_id": ["VH-1", "VH-2"],
        "litres": [500, 50],
        "timestamp": ["2026-05-01 08:00", "2026-05-01 09:00"],
    })
    result = detect_fill_anomalies(df)
    assert result.loc[result["transaction_id"] == "F1", "is_flagged"].iloc[0]
    assert not result.loc[result["transaction_id"] == "F2", "is_flagged"].iloc[0]


def test_detect_fill_anomalies_flags_multiple_same_day():
    df = pd.DataFrame({
        "transaction_id": ["F1", "F2"],
        "vehicle_id": ["VH-1", "VH-1"],
        "litres": [50, 50],
        "timestamp": ["2026-05-01 08:00", "2026-05-01 18:00"],
    })
    result = detect_fill_anomalies(df)
    assert result["is_flagged"].all()


def test_detect_efficiency_outliers():
    summary = pd.DataFrame({"vehicle_id": ["VH-1", "VH-2", "VH-3", "VH-4", "VH-5", "VH-6"],
                             "litres_per_100km": [15, 16, 15.5, 14.8, 15.2, 60]})
    out = detect_efficiency_outliers(summary)
    assert out[out["vehicle_id"] == "VH-6"]["outlier_flag"].iloc[0]


def test_detect_fill_vs_distance_mismatch_flags_high_purchase():
    fuel_df = pd.DataFrame({"vehicle_id": ["VH-1"], "litres": [200]})
    trip_df = pd.DataFrame({"vehicle_id": ["VH-1"], "actual_distance_km": [100]})
    result = detect_fill_vs_distance_mismatch(fuel_df, trip_df, base_consumption_l_per_100km=20)
    assert result.iloc[0]["mismatch_flag"]


def test_anomaly_summary_structure():
    fill_df = pd.DataFrame({"transaction_id": ["F1"], "vehicle_id": ["VH-1"], "is_flagged": [True]})
    mismatch_df = pd.DataFrame({"vehicle_id": ["VH-1"], "mismatch_flag": [True], "litres_variance_pct": [80.0]})
    summary = anomaly_summary(fill_df, mismatch_df)
    assert summary["n_flagged_transactions"] == 1
    assert summary["n_vehicles_with_fill_distance_mismatch"] == 1
