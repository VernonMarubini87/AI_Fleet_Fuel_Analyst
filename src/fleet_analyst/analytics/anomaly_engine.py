"""
Statistical anomaly and fraud detection for fuel-card usage. Every flag here
is a deterministic rule or statistical threshold — never an LLM guess — so
findings are auditable and defensible if a driver disputes a flag.
"""
import pandas as pd
import numpy as np

TANK_CAPACITY_CEILING = 400


def detect_fill_anomalies(fuel_df: pd.DataFrame) -> pd.DataFrame:
    """Row-level fraud/error flags on individual fuel transactions."""
    df = fuel_df.copy()
    flags = []

    for idx, row in df.iterrows():
        row_flags = []
        if row.get("litres", 0) > TANK_CAPACITY_CEILING:
            row_flags.append("EXCEEDS_TANK_CAPACITY")
        flags.append(row_flags)
    df["fraud_flags"] = flags

    # duplicate fills for same vehicle within a short time window (same day, multiple fills)
    if "timestamp" in df.columns:
        df["timestamp_parsed"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["fill_date"] = df["timestamp_parsed"].dt.date
        same_day_counts = df.groupby(["vehicle_id", "fill_date"]).size()
        multi_fill_keys = set(same_day_counts[same_day_counts > 1].index)
        for idx, row in df.iterrows():
            if (row["vehicle_id"], row["fill_date"]) in multi_fill_keys:
                df.at[idx, "fraud_flags"] = df.at[idx, "fraud_flags"] + ["MULTIPLE_FILLS_SAME_DAY"]

    df["is_flagged"] = df["fraud_flags"].apply(lambda x: len(x) > 0)
    return df


def detect_efficiency_outliers(vehicle_summary: pd.DataFrame, z_threshold: float = 2.0) -> pd.DataFrame:
    """Flags vehicles whose litres_per_100km is a statistical outlier vs the fleet (z-score based)."""
    df = vehicle_summary.copy()
    valid = df["litres_per_100km"].dropna()
    if len(valid) < 3:
        df["z_score"] = np.nan
        df["outlier_flag"] = False
        return df
    mean, std = valid.mean(), valid.std()
    df["z_score"] = (df["litres_per_100km"] - mean) / std if std > 0 else 0
    df["outlier_flag"] = df["z_score"].abs() > z_threshold
    return df


def detect_fill_vs_distance_mismatch(fuel_df: pd.DataFrame, trip_df: pd.DataFrame,
                                       base_consumption_l_per_100km: float = 20.0,
                                       tolerance_pct: float = 40.0) -> pd.DataFrame:
    """
    Flags vehicles where total litres purchased is materially higher than what
    the distance actually driven should require — a classic card-fraud/siphoning
    signal, independent of per-driver efficiency variation.
    """
    fuel_totals = fuel_df.groupby("vehicle_id")["litres"].sum().reset_index(name="total_litres_bought")
    trip_totals = trip_df.groupby("vehicle_id")["actual_distance_km"].sum().reset_index(name="total_distance_km")
    merged = pd.merge(fuel_totals, trip_totals, on="vehicle_id", how="outer").fillna(0)

    merged["expected_litres"] = (merged["total_distance_km"] / 100) * base_consumption_l_per_100km
    merged["litres_variance_pct"] = np.where(
        merged["expected_litres"] > 0,
        ((merged["total_litres_bought"] - merged["expected_litres"]) / merged["expected_litres"]) * 100,
        np.nan,
    )
    merged["mismatch_flag"] = merged["litres_variance_pct"] > tolerance_pct
    return merged.sort_values("litres_variance_pct", ascending=False).reset_index(drop=True)


def anomaly_summary(fill_anomalies: pd.DataFrame, mismatch_df: pd.DataFrame) -> dict:
    return {
        "n_flagged_transactions": int(fill_anomalies["is_flagged"].sum()),
        "n_vehicles_with_fill_distance_mismatch": int(mismatch_df["mismatch_flag"].sum()),
        "top_mismatch_vehicles": mismatch_df[mismatch_df["mismatch_flag"]].head(10).to_dict("records"),
        "flagged_transaction_ids": fill_anomalies[fill_anomalies["is_flagged"]]["transaction_id"].tolist()
        if "transaction_id" in fill_anomalies.columns else [],
    }
