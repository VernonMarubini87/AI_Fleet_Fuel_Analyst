"""
Fuel spend forecasting. Compares a seasonal-naive baseline against a simple
linear regression on time trend, and reports which performed better on a
held-out tail of history, rather than assuming one model is correct.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


def _weekly_spend_series(fuel_df: pd.DataFrame) -> pd.Series:
    df = fuel_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.set_index("timestamp").resample("W")["total_cost"].sum()


def seasonal_naive_forecast(series: pd.Series, periods_ahead: int, season_length: int = 4) -> pd.Series:
    if len(series) < season_length:
        last_val = series.iloc[-1] if len(series) else 0
        return pd.Series([last_val] * periods_ahead)
    last_season = series.iloc[-season_length:].values
    reps = int(np.ceil(periods_ahead / season_length))
    forecast_vals = np.tile(last_season, reps)[:periods_ahead]
    return pd.Series(forecast_vals)


def linear_trend_forecast(series: pd.Series, periods_ahead: int):
    x = np.arange(len(series)).reshape(-1, 1)
    y = series.values
    model = LinearRegression().fit(x, y)
    future_x = np.arange(len(series), len(series) + periods_ahead).reshape(-1, 1)
    return pd.Series(model.predict(future_x)), model


def evaluate_and_forecast(fuel_df: pd.DataFrame, periods_ahead: int = 4, holdout: int = 4) -> dict:
    series = _weekly_spend_series(fuel_df)
    series = series[series.index.notna()]

    if len(series) <= holdout + 2:
        return {
            "status": "insufficient_history",
            "message": f"Need more than {holdout + 2} weeks of history to backtest; have {len(series)}.",
        }

    train, test = series.iloc[:-holdout], series.iloc[-holdout:]

    naive_pred = seasonal_naive_forecast(train, holdout)
    naive_mae = mean_absolute_error(test.values, naive_pred.values)

    linear_pred, _ = linear_trend_forecast(train, holdout)
    linear_mae = mean_absolute_error(test.values, linear_pred.values)

    best_model = "seasonal_naive" if naive_mae <= linear_mae else "linear_trend"

    if best_model == "seasonal_naive":
        future_forecast = seasonal_naive_forecast(series, periods_ahead)
    else:
        future_forecast, _ = linear_trend_forecast(series, periods_ahead)

    return {
        "status": "ok",
        "backtest_mae": {"seasonal_naive": round(float(naive_mae), 2), "linear_trend": round(float(linear_mae), 2)},
        "best_model": best_model,
        "history_weeks": len(series),
        "forecast_next_periods": [round(float(v), 2) for v in future_forecast],
        "historical_weekly_spend": [round(float(v), 2) for v in series.values],
    }
