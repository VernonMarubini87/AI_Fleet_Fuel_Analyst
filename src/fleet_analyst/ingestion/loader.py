"""
Loads fuel-card and GPS/trip export files (CSV or Excel) and normalises
columns to canonical role names via schema.py.
"""
import pandas as pd
from .schema import rename_to_canonical, FUEL_ROLE_ALIASES, TRIP_ROLE_ALIASES


class LoadResult:
    def __init__(self, df, mapping, unmapped_required):
        self.df = df
        self.mapping = mapping
        self.unmapped_required = unmapped_required

    @property
    def ok(self):
        return len(self.unmapped_required) == 0


def _read_any(path_or_buffer):
    if hasattr(path_or_buffer, "name"):
        name = path_or_buffer.name
    else:
        name = str(path_or_buffer)
    if name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path_or_buffer)
    return pd.read_csv(path_or_buffer)


def load_fuel_transactions(path_or_buffer, required=("vehicle_id", "litres", "total_cost")):
    df = _read_any(path_or_buffer)
    df, mapping = rename_to_canonical(df, FUEL_ROLE_ALIASES)
    unmapped_required = [r for r in required if mapping.get(r) is None]
    return LoadResult(df, mapping, unmapped_required)


def load_trip_log(path_or_buffer, required=("vehicle_id", "actual_distance_km")):
    df = _read_any(path_or_buffer)
    df, mapping = rename_to_canonical(df, TRIP_ROLE_ALIASES)
    unmapped_required = [r for r in required if mapping.get(r) is None]
    return LoadResult(df, mapping, unmapped_required)
