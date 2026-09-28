"""Route/trip-level analytics: planned vs actual distance, detour detection, cost per trip."""
import pandas as pd
import numpy as np


def route_variance(trip_df: pd.DataFrame) -> pd.DataFrame:
    if "planned_distance_km" not in trip_df.columns:
        return pd.DataFrame()
    out = trip_df.copy()
    out["distance_variance_km"] = out["actual_distance_km"] - out["planned_distance_km"]
    out["distance_variance_pct"] = np.where(
        out["planned_distance_km"] > 0,
        (out["distance_variance_km"] / out["planned_distance_km"]) * 100,
        np.nan,
    )
    out["detour_flag"] = out["distance_variance_pct"] > 20
    return out


def depot_summary(trip_df: pd.DataFrame, fuel_df: pd.DataFrame) -> pd.DataFrame:
    if "depot" not in trip_df.columns:
        return pd.DataFrame()
    trip_agg = trip_df.groupby("depot").agg(
        total_distance_km=("actual_distance_km", "sum"), n_trips=("actual_distance_km", "count")
    ).reset_index()
    if "depot" in fuel_df.columns:
        fuel_agg = fuel_df.groupby("depot").agg(
            total_fuel_cost=("total_cost", "sum"), total_litres=("litres", "sum")
        ).reset_index()
        merged = pd.merge(trip_agg, fuel_agg, on="depot", how="outer").fillna(0)
    else:
        merged = trip_agg
    return merged.sort_values("total_distance_km", ascending=False).reset_index(drop=True)


def cost_per_trip(trip_df: pd.DataFrame, fuel_df: pd.DataFrame, vehicle_summary: pd.DataFrame) -> pd.DataFrame:
    """Approximates an average fuel cost per trip per vehicle using vehicle-level cost/km."""
    trips_per_vehicle = trip_df.groupby("vehicle_id").agg(
        n_trips=("actual_distance_km", "count"), avg_distance_km=("actual_distance_km", "mean")
    ).reset_index()
    merged = pd.merge(trips_per_vehicle, vehicle_summary[["vehicle_id", "cost_per_km"]], on="vehicle_id", how="left")
    merged["avg_cost_per_trip"] = merged["avg_distance_km"] * merged["cost_per_km"]
    return merged
