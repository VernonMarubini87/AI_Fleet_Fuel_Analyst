import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from fleet_analyst.ingestion.schema import find_column, map_schema, rename_to_canonical, FUEL_ROLE_ALIASES
from fleet_analyst.ingestion.loader import load_fuel_transactions, load_trip_log
from fleet_analyst.ingestion.profiler import profile_dataframe

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def test_find_column_exact_match():
    assert find_column(["Vehicle ID", "Litres"], ["vehicle_id"]) == "Vehicle ID"


def test_find_column_alias_match():
    assert find_column(["reg_no", "qty"], FUEL_ROLE_ALIASES["vehicle_id"]) == "reg_no"


def test_find_column_none_when_missing():
    assert find_column(["foo", "bar"], ["vehicle_id"]) is None


def test_rename_to_canonical():
    df = pd.DataFrame({"reg_no": ["VH-1"], "qty": [10]})
    renamed, mapping = rename_to_canonical(df, FUEL_ROLE_ALIASES)
    assert "vehicle_id" in renamed.columns
    assert "litres" in renamed.columns


def test_load_fuel_transactions_ok():
    result = load_fuel_transactions(os.path.join(DATA_DIR, "synthetic_fuel_transactions.csv"))
    assert result.ok
    assert "vehicle_id" in result.df.columns
    assert len(result.df) > 0


def test_load_trip_log_ok():
    result = load_trip_log(os.path.join(DATA_DIR, "synthetic_trip_gps_log.csv"))
    assert result.ok
    assert "actual_distance_km" in result.df.columns


def test_profile_dataframe():
    df = pd.DataFrame({"vehicle_id": ["VH-1", "VH-1", "VH-2"], "litres": [10, 20, None]})
    profile = profile_dataframe(df)
    assert profile["n_rows"] == 3
    assert profile["n_unique_vehicles"] == 2
    assert profile["null_counts"]["litres"] == 1
