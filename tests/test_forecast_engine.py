import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from fleet_analyst.forecasting.forecast_engine import evaluate_and_forecast, seasonal_naive_forecast


def test_seasonal_naive_forecast_length():
    series = pd.Series([100, 110, 105, 115, 108, 112, 106, 118])
    forecast = seasonal_naive_forecast(series, periods_ahead=4, season_length=4)
    assert len(forecast) == 4


def test_evaluate_and_forecast_insufficient_history():
    fuel_df = pd.DataFrame({"timestamp": ["2026-05-01"], "total_cost": [1000]})
    result = evaluate_and_forecast(fuel_df, periods_ahead=4, holdout=4)
    assert result["status"] == "insufficient_history"


def test_evaluate_and_forecast_with_enough_history():
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    fuel_df = pd.DataFrame({"timestamp": dates.astype(str), "total_cost": [1000 + i * 2 for i in range(100)]})
    result = evaluate_and_forecast(fuel_df, periods_ahead=4, holdout=4)
    assert result["status"] == "ok"
    assert "best_model" in result
    assert len(result["forecast_next_periods"]) == 4
