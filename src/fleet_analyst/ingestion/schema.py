"""
Flexible column role-mapping so the analyst can accept fuel-card exports and
GPS/telematics exports from different providers (Sasol Fleet, Cartrack,
MiX Telematics, Netstar, etc.) without hardcoding column names.
"""
import re

FUEL_ROLE_ALIASES = {
    "vehicle_id": ["vehicle_id", "vehicle", "reg_no", "registration", "fleet_no", "vehicle no"],
    "driver_id": ["driver_id", "driver", "driver_no", "driver name"],
    "timestamp": ["timestamp", "date", "transaction_date", "fill_date", "datetime"],
    "litres": ["litres", "liters", "volume", "qty", "quantity_l"],
    "total_cost": ["total_cost", "amount", "cost", "total", "value"],
    "price_per_litre": ["price_per_litre", "unit_price", "price_l", "ppl"],
    "odometer_at_fill": ["odometer_at_fill", "odometer", "odo", "mileage"],
    "card_number": ["card_number", "card", "card_no"],
    "merchant": ["merchant", "station", "vendor", "supplier"],
    "fuel_type": ["fuel_type", "product", "fuel"],
    "depot": ["depot", "branch", "site", "location"],
}

TRIP_ROLE_ALIASES = {
    "trip_id": ["trip_id", "trip", "journey_id"],
    "vehicle_id": ["vehicle_id", "vehicle", "reg_no", "registration"],
    "driver_id": ["driver_id", "driver", "driver_no"],
    "date": ["date", "trip_date"],
    "planned_distance_km": ["planned_distance_km", "planned_km", "planned distance"],
    "actual_distance_km": ["actual_distance_km", "distance_km", "km_travelled", "distance"],
    "odometer_start": ["odometer_start", "odo_start", "start_odo"],
    "odometer_end": ["odometer_end", "odo_end", "end_odo"],
    "harsh_braking_events": ["harsh_braking_events", "harsh_braking", "braking_events"],
    "harsh_accel_events": ["harsh_accel_events", "harsh_acceleration", "accel_events"],
    "idle_minutes": ["idle_minutes", "idle_time", "idling"],
    "after_hours_km": ["after_hours_km", "afterhours_km", "out_of_hours_km"],
    "depot": ["depot", "branch", "site"],
}


def _normalise(col: str) -> str:
    return re.sub(r"[^a-z0-9]", "", col.lower())


def find_column(columns, candidates):
    """Return the first matching original column name for a list of alias candidates."""
    norm_lookup = {_normalise(c): c for c in columns}
    for cand in candidates:
        norm_cand = _normalise(cand)
        if norm_cand in norm_lookup:
            return norm_lookup[norm_cand]
    # fallback: substring match
    for cand in candidates:
        norm_cand = _normalise(cand)
        for norm_col, orig_col in norm_lookup.items():
            if norm_cand in norm_col or norm_col in norm_cand:
                return orig_col
    return None


def map_schema(columns, role_aliases):
    """Map every known role to a source column, if present. Returns dict role -> column or None."""
    return {role: find_column(columns, aliases) for role, aliases in role_aliases.items()}


def rename_to_canonical(df, role_aliases):
    """Rename a dataframe's columns to canonical role names based on alias matching."""
    mapping = map_schema(df.columns, role_aliases)
    rename_dict = {v: k for k, v in mapping.items() if v is not None}
    return df.rename(columns=rename_dict), mapping
