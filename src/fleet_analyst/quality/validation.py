"""
Severity-tiered validation checks for fuel-transaction and trip-log data.
Severities: CRITICAL (row unusable), WARNING (row suspect, keep but flag),
INFO (informational, no action needed).
"""
import pandas as pd

TANK_CAPACITY_CEILING = 400  # litres — generous ceiling across all vehicle classes


def validate_fuel_transactions(df: pd.DataFrame) -> list:
    issues = []

    if "litres" in df.columns:
        zero_or_neg = df[df["litres"] <= 0]
        for idx in zero_or_neg.index:
            issues.append({"row": idx, "severity": "CRITICAL", "field": "litres",
                            "message": "Litres is zero or negative", "value": df.loc[idx, "litres"]})

        too_large = df[df["litres"] > TANK_CAPACITY_CEILING]
        for idx in too_large.index:
            issues.append({"row": idx, "severity": "WARNING", "field": "litres",
                            "message": f"Litres exceeds plausible tank capacity ({TANK_CAPACITY_CEILING}L)",
                            "value": df.loc[idx, "litres"]})

    if "driver_id" in df.columns:
        missing_driver = df[df["driver_id"].isna()]
        for idx in missing_driver.index:
            issues.append({"row": idx, "severity": "WARNING", "field": "driver_id",
                            "message": "Missing driver ID", "value": None})

    if "vehicle_id" in df.columns:
        missing_vehicle = df[df["vehicle_id"].isna()]
        for idx in missing_vehicle.index:
            issues.append({"row": idx, "severity": "CRITICAL", "field": "vehicle_id",
                            "message": "Missing vehicle ID", "value": None})

    if {"litres", "total_cost", "price_per_litre"}.issubset(df.columns):
        expected_cost = df["litres"] * df["price_per_litre"]
        mismatch = df[(df["total_cost"] - expected_cost).abs() > 5]
        for idx in mismatch.index:
            issues.append({"row": idx, "severity": "INFO", "field": "total_cost",
                            "message": "total_cost does not match litres x price_per_litre within tolerance",
                            "value": df.loc[idx, "total_cost"]})

    dup_mask = df.duplicated(keep=False)
    for idx in df[dup_mask].index:
        issues.append({"row": idx, "severity": "WARNING", "field": "*",
                        "message": "Exact duplicate row", "value": None})

    return issues


def validate_trip_log(df: pd.DataFrame) -> list:
    issues = []

    if {"odometer_start", "odometer_end"}.issubset(df.columns):
        rollback = df[df["odometer_end"] < df["odometer_start"]]
        for idx in rollback.index:
            issues.append({"row": idx, "severity": "CRITICAL", "field": "odometer_end",
                            "message": "Odometer end is before odometer start (rollback/data error)",
                            "value": df.loc[idx, "odometer_end"]})

    if "actual_distance_km" in df.columns:
        implausible = df[(df["actual_distance_km"] <= 0) | (df["actual_distance_km"] > 1500)]
        for idx in implausible.index:
            issues.append({"row": idx, "severity": "WARNING", "field": "actual_distance_km",
                            "message": "Implausible single-day distance", "value": df.loc[idx, "actual_distance_km"]})

    if "vehicle_id" in df.columns:
        missing_vehicle = df[df["vehicle_id"].isna()]
        for idx in missing_vehicle.index:
            issues.append({"row": idx, "severity": "CRITICAL", "field": "vehicle_id",
                            "message": "Missing vehicle ID", "value": None})

    return issues


def summarise_issues(issues: list) -> dict:
    summary = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for i in issues:
        summary[i["severity"]] = summary.get(i["severity"], 0) + 1
    summary["total"] = len(issues)
    return summary
