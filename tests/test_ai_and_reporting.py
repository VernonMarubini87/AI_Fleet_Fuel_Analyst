import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from fleet_analyst.ai.intent_classifier import classify_intent, extract_vehicle_ids, extract_driver_ids
from fleet_analyst.ai.claude_client import ClaudeClient
from fleet_analyst.ai.orchestrator import FleetFuelAgent
from fleet_analyst.reporting.report_generator import generate_management_report
from fleet_analyst.qa.validators import validate_evidence, validate_kpis, gate_before_display


def test_classify_intent_fraud():
    assert "fraud_check" in classify_intent("Which vehicles look suspicious for fraud?")


def test_classify_intent_driver_risk():
    assert "driver_risk" in classify_intent("Which drivers are riskiest?")


def test_classify_intent_general_fallback():
    assert classify_intent("hello") == ["general"]


def test_extract_vehicle_ids():
    assert extract_vehicle_ids("What about VH-1023 and VH-1005?") == ["vh-1023", "vh-1005"]


def test_extract_driver_ids():
    assert extract_driver_ids("How is DR-201 doing?") == ["dr-201"]


def test_claude_client_disabled_without_key():
    client = ClaudeClient(api_key=None)
    assert not client.enabled
    result = client.interpret("system", {"foo": "bar"})
    assert "not configured" in result.lower()


def test_orchestrator_ask_without_api_key():
    vehicle_summary = pd.DataFrame({"vehicle_id": ["VH-1"], "cost_per_km": [5.0], "total_fuel_cost": [1000],
                                     "litres_per_100km": [15.0]})
    driver_scores = pd.DataFrame({"driver_id": ["DR-1"], "risk_score": [10.0], "risk_tier": ["LOW"]})
    anomaly_summary_dict = {"n_flagged_transactions": 0, "n_vehicles_with_fill_distance_mismatch": 0,
                             "top_mismatch_vehicles": []}
    forecast_result = {"status": "insufficient_history", "message": "not enough data"}
    agent = FleetFuelAgent(vehicle_summary, driver_scores, anomaly_summary_dict, pd.DataFrame(),
                            forecast_result, pd.DataFrame(), ClaudeClient(api_key=None))
    result = agent.ask("Which vehicles are most expensive?")
    assert "cost" in result["intents"]
    assert "not configured" in result["answer"].lower()


def test_generate_management_report_contains_key_sections():
    fleet_kpis = {"n_vehicles": 5, "total_distance_km": 1000, "total_fuel_cost": 5000,
                  "fleet_litres_per_100km": 18.0, "fleet_cost_per_km": 5.0}
    vehicle_summary = pd.DataFrame({"vehicle_id": ["VH-1"], "cost_per_km": [5.0], "litres_per_100km": [18.0]})
    driver_scores = pd.DataFrame({"driver_id": ["DR-1"], "risk_score": [10.0], "risk_tier": ["LOW"]})
    anomaly_summary_dict = {"n_flagged_transactions": 1, "n_vehicles_with_fill_distance_mismatch": 0,
                             "top_mismatch_vehicles": []}
    forecast_result = {"status": "insufficient_history", "message": "not enough data"}
    report = generate_management_report(fleet_kpis, vehicle_summary, driver_scores,
                                          anomaly_summary_dict, forecast_result)
    assert "FLEET OVERVIEW" in report
    assert "FRAUD / ANOMALY FLAGS" in report


def test_validate_evidence_catches_nan():
    evidence = {"a": float("nan")}
    problems = validate_evidence(evidence)
    assert len(problems) == 1


def test_validate_kpis_catches_negative_cost():
    problems = validate_kpis({"total_fuel_cost": -100, "total_distance_km": 100})
    assert any("negative" in p for p in problems)


def test_gate_before_display_passes_clean_evidence():
    gate = gate_before_display({"a": 1, "b": [1, 2, 3]})
    assert gate["passed"]
