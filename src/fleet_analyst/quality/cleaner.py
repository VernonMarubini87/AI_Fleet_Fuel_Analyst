"""
Applies only SAFE auto-fixes (deduplication, dropping unusable CRITICAL rows)
and logs every rejected row with a reason, so nothing is silently discarded.
"""
import pandas as pd
from .validation import validate_fuel_transactions, validate_trip_log


def clean_fuel_transactions(df: pd.DataFrame):
    rejected_log = []
    working = df.copy()

    before = len(working)
    working = working.drop_duplicates()
    n_dupes_removed = before - len(working)
    if n_dupes_removed:
        rejected_log.append({"reason": "exact_duplicate_removed", "count": n_dupes_removed})

    issues = validate_fuel_transactions(working)
    critical_rows = sorted({i["row"] for i in issues if i["severity"] == "CRITICAL" and i["row"] in working.index})
    if critical_rows:
        rejected_rows = working.loc[critical_rows].copy()
        rejected_rows["rejection_reason"] = [
            "; ".join(i["message"] for i in issues if i["row"] == r and i["severity"] == "CRITICAL")
            for r in critical_rows
        ]
        rejected_log.append({"reason": "critical_validation_failure", "count": len(critical_rows),
                              "rows": rejected_rows.to_dict("records")})
        working = working.drop(index=critical_rows)

    remaining_issues = validate_fuel_transactions(working)
    return working.reset_index(drop=True), rejected_log, remaining_issues


def clean_trip_log(df: pd.DataFrame):
    rejected_log = []
    working = df.copy()

    before = len(working)
    working = working.drop_duplicates()
    n_dupes_removed = before - len(working)
    if n_dupes_removed:
        rejected_log.append({"reason": "exact_duplicate_removed", "count": n_dupes_removed})

    issues = validate_trip_log(working)
    critical_rows = sorted({i["row"] for i in issues if i["severity"] == "CRITICAL" and i["row"] in working.index})
    if critical_rows:
        rejected_rows = working.loc[critical_rows].copy()
        rejected_rows["rejection_reason"] = [
            "; ".join(i["message"] for i in issues if i["row"] == r and i["severity"] == "CRITICAL")
            for r in critical_rows
        ]
        rejected_log.append({"reason": "critical_validation_failure", "count": len(critical_rows),
                              "rows": rejected_rows.to_dict("records")})
        working = working.drop(index=critical_rows)

    remaining_issues = validate_trip_log(working)
    return working.reset_index(drop=True), rejected_log, remaining_issues
