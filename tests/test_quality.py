import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from fleet_analyst.quality.validation import validate_fuel_transactions, validate_trip_log, summarise_issues
from fleet_analyst.quality.cleaner import clean_fuel_transactions, clean_trip_log


def test_validate_fuel_zero_litres_flagged_critical():
    df = pd.DataFrame({"vehicle_id": ["VH-1"], "litres": [0], "total_cost": [0],
                        "price_per_litre": [23.0], "driver_id": ["DR-1"]})
    issues = validate_fuel_transactions(df)
    assert any(i["severity"] == "CRITICAL" and i["field"] == "litres" for i in issues)


def test_validate_fuel_excessive_litres_flagged_warning():
    df = pd.DataFrame({"vehicle_id": ["VH-1"], "litres": [500], "total_cost": [11750],
                        "price_per_litre": [23.5], "driver_id": ["DR-1"]})
    issues = validate_fuel_transactions(df)
    assert any(i["severity"] == "WARNING" and i["field"] == "litres" for i in issues)


def test_validate_trip_odometer_rollback_critical():
    df = pd.DataFrame({"vehicle_id": ["VH-1"], "odometer_start": [1000], "odometer_end": [900],
                        "actual_distance_km": [100]})
    issues = validate_trip_log(df)
    assert any(i["severity"] == "CRITICAL" and i["field"] == "odometer_end" for i in issues)


def test_summarise_issues():
    issues = [{"severity": "CRITICAL"}, {"severity": "WARNING"}, {"severity": "WARNING"}]
    summary = summarise_issues(issues)
    assert summary["CRITICAL"] == 1
    assert summary["WARNING"] == 2
    assert summary["total"] == 3


def test_clean_fuel_removes_duplicates():
    df = pd.DataFrame({"vehicle_id": ["VH-1", "VH-1"], "litres": [10, 10], "total_cost": [235, 235],
                        "price_per_litre": [23.5, 23.5], "driver_id": ["DR-1", "DR-1"]})
    cleaned, rejects, remaining_issues = clean_fuel_transactions(df)
    assert len(cleaned) == 1


def test_clean_fuel_drops_critical_rows():
    df = pd.DataFrame({"vehicle_id": ["VH-1", None], "litres": [10, 20], "total_cost": [235, 470],
                        "price_per_litre": [23.5, 23.5], "driver_id": ["DR-1", "DR-2"]})
    cleaned, rejects, remaining_issues = clean_fuel_transactions(df)
    assert len(cleaned) == 1
    assert any(r["reason"] == "critical_validation_failure" for r in rejects)


def test_clean_trip_drops_odometer_rollback():
    df = pd.DataFrame({"vehicle_id": ["VH-1", "VH-2"], "odometer_start": [1000, 2000],
                        "odometer_end": [1100, 1900], "actual_distance_km": [100, 100]})
    cleaned, rejects, remaining_issues = clean_trip_log(df)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["vehicle_id"] == "VH-1"
