"""Basic profiling of an ingested dataframe: shape, nulls, dtypes, date range."""
import pandas as pd


def profile_dataframe(df: pd.DataFrame, date_col: str = None) -> dict:
    profile = {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
    }
    if date_col and date_col in df.columns:
        parsed = pd.to_datetime(df[date_col], errors="coerce")
        profile["date_range"] = {
            "min": str(parsed.min()),
            "max": str(parsed.max()),
            "unparseable_dates": int(parsed.isna().sum()),
        }
    if "vehicle_id" in df.columns:
        profile["n_unique_vehicles"] = df["vehicle_id"].nunique(dropna=True)
    if "driver_id" in df.columns:
        profile["n_unique_drivers"] = df["driver_id"].nunique(dropna=True)
    return profile
