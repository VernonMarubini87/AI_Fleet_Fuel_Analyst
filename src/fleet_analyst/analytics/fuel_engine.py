"""
Deterministic fuel efficiency and cost analytics. All numbers here are
calculated in Python/Pandas — Claude never computes these, only interprets
the resulting evidence JSON.
"""
import pandas as pd
import numpy as np


def per_vehicle_fuel_summary(fuel_df: pd.DataFrame, trip_df: pd.DataFrame) -> pd.DataFrame:
    fuel_agg = fuel_df.groupby("vehicle_id").agg(
        total_litres=("litres", "sum"),
        total_fuel_cost=("total_cost", "sum"),
        n_fills=("litres", "count"),
        avg_price_per_litre=("price_per_litre", "mean"),
    ).reset_index()

    trip_agg = trip_df.groupby("vehicle_id").agg(
        total_distance_km=("actual_distance_km", "sum"),
        n_trips=("actual_distance_km", "count"),
        total_idle_minutes=("idle_minutes", "sum") if "idle_minutes" in trip_df.columns else ("actual_distance_km", "count"),
    ).reset_index()

    merged = pd.merge(fuel_agg, trip_agg, on="vehicle_id", how="outer").fillna(0)
    merged["litres_per_100km"] = np.where(
        merged["total_distance_km"] > 0,
        (merged["total_litres"] / merged["total_distance_km"]) * 100,
        np.nan,
    )
    merged["cost_per_km"] = np.where(
        merged["total_distance_km"] > 0,
        merged["total_fuel_cost"] / merged["total_distance_km"],
        np.nan,
    )
    return merged.sort_values("cost_per_km", ascending=False).reset_index(drop=True)


def fleet_wide_kpis(fuel_df: pd.DataFrame, trip_df: pd.DataFrame) -> dict:
    total_litres = float(fuel_df["litres"].sum())
    total_cost = float(fuel_df["total_cost"].sum())
    total_distance = float(trip_df["actual_distance_km"].sum())
    return {
        "total_litres": round(total_litres, 1),
        "total_fuel_cost": round(total_cost, 2),
        "total_distance_km": round(total_distance, 1),
        "fleet_litres_per_100km": round((total_litres / total_distance) * 100, 2) if total_distance else None,
        "fleet_cost_per_km": round(total_cost / total_distance, 2) if total_distance else None,
        "n_vehicles": int(fuel_df["vehicle_id"].nunique()),
        "n_fill_transactions": int(len(fuel_df)),
        "n_trips": int(len(trip_df)),
    }


def efficiency_trend(fuel_df: pd.DataFrame, trip_df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """Fleet-wide litres/100km trend over time, resampled at given frequency (default weekly)."""
    fuel = fuel_df.copy()
    fuel["timestamp"] = pd.to_datetime(fuel["timestamp"], errors="coerce")
    trip = trip_df.copy()
    trip["date"] = pd.to_datetime(trip["date"], errors="coerce")

    fuel_by_period = fuel.set_index("timestamp").resample(freq)["litres"].sum()
    dist_by_period = trip.set_index("date").resample(freq)["actual_distance_km"].sum()

    combined = pd.DataFrame({"litres": fuel_by_period, "distance_km": dist_by_period}).fillna(0)
    combined["litres_per_100km"] = np.where(
        combined["distance_km"] > 0, (combined["litres"] / combined["distance_km"]) * 100, np.nan
    )
    return combined.reset_index().rename(columns={"index": "period"})


def benchmark_against_fleet(vehicle_summary: pd.DataFrame) -> pd.DataFrame:
    """Flags vehicles whose litres_per_100km is materially worse than fleet median."""
    median_l100 = vehicle_summary["litres_per_100km"].median()
    out = vehicle_summary.copy()
    out["pct_above_fleet_median"] = ((out["litres_per_100km"] - median_l100) / median_l100) * 100
    out["efficiency_flag"] = np.where(
        out["pct_above_fleet_median"] > 15, "INEFFICIENT",
        np.where(out["pct_above_fleet_median"] < -15, "HIGH_EFFICIENCY", "NORMAL"),
    )
    return out
