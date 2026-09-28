"""Driver-level risk and efficiency scoring from telematics/trip data."""
import pandas as pd
import numpy as np


def driver_scorecard(trip_df: pd.DataFrame) -> pd.DataFrame:
    agg_cols = {
        "total_distance_km": ("actual_distance_km", "sum"),
        "n_trips": ("actual_distance_km", "count"),
    }
    if "harsh_braking_events" in trip_df.columns:
        agg_cols["harsh_braking_events"] = ("harsh_braking_events", "sum")
    if "harsh_accel_events" in trip_df.columns:
        agg_cols["harsh_accel_events"] = ("harsh_accel_events", "sum")
    if "idle_minutes" in trip_df.columns:
        agg_cols["total_idle_minutes"] = ("idle_minutes", "sum")
    if "after_hours_km" in trip_df.columns:
        agg_cols["total_after_hours_km"] = ("after_hours_km", "sum")

    scorecard = trip_df.groupby("driver_id").agg(**agg_cols).reset_index()

    if "harsh_braking_events" in scorecard.columns and "harsh_accel_events" in scorecard.columns:
        scorecard["harsh_events_per_100km"] = np.where(
            scorecard["total_distance_km"] > 0,
            ((scorecard["harsh_braking_events"] + scorecard["harsh_accel_events"]) / scorecard["total_distance_km"]) * 100,
            0,
        )
    if "total_after_hours_km" in scorecard.columns:
        scorecard["pct_after_hours"] = np.where(
            scorecard["total_distance_km"] > 0,
            (scorecard["total_after_hours_km"] / scorecard["total_distance_km"]) * 100,
            0,
        )

    # simple composite risk score (0-100, higher = riskier), weights are transparent and tunable
    score = pd.Series(0.0, index=scorecard.index)
    if "harsh_events_per_100km" in scorecard.columns:
        score += (scorecard["harsh_events_per_100km"].clip(0, 20) / 20) * 50
    if "pct_after_hours" in scorecard.columns:
        score += (scorecard["pct_after_hours"].clip(0, 50) / 50) * 50
    scorecard["risk_score"] = score.round(1)
    scorecard["risk_tier"] = pd.cut(
        scorecard["risk_score"], bins=[-1, 20, 50, 101], labels=["LOW", "MEDIUM", "HIGH"]
    )
    return scorecard.sort_values("risk_score", ascending=False).reset_index(drop=True)


def driver_fuel_link(fuel_df: pd.DataFrame, driver_scores: pd.DataFrame) -> pd.DataFrame:
    """Joins fuel spend per driver onto the behaviour scorecard, where driver_id is present in fuel data."""
    if "driver_id" not in fuel_df.columns:
        return driver_scores
    fuel_by_driver = fuel_df.dropna(subset=["driver_id"]).groupby("driver_id").agg(
        total_litres=("litres", "sum"), total_fuel_cost=("total_cost", "sum"), n_fills=("litres", "count")
    ).reset_index()
    return pd.merge(driver_scores, fuel_by_driver, on="driver_id", how="left")
