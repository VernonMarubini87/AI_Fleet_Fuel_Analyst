"""
FleetFuelAgent: routes a natural-language question to the right deterministic
analytics module(s), assembles evidence JSON, then (optionally) asks Claude
to interpret it. Works with or without an API key.
"""
from .intent_classifier import classify_intent, extract_vehicle_ids, extract_driver_ids
from .prompts import QUESTION_ANSWER_PROMPT
from .claude_client import ClaudeClient


class FleetFuelAgent:
    def __init__(self, vehicle_summary, driver_scores, anomaly_summary_dict,
                 mismatch_df, forecast_result, route_variance_df, claude_client: ClaudeClient = None):
        self.vehicle_summary = vehicle_summary
        self.driver_scores = driver_scores
        self.anomaly_summary_dict = anomaly_summary_dict
        self.mismatch_df = mismatch_df
        self.forecast_result = forecast_result
        self.route_variance_df = route_variance_df
        self.claude = claude_client or ClaudeClient()

    def _gather_evidence(self, intents, vehicle_ids, driver_ids) -> dict:
        evidence = {}
        if "fraud_check" in intents:
            evidence["anomaly_summary"] = self.anomaly_summary_dict
        if "efficiency" in intents or "vehicle_lookup" in intents:
            df = self.vehicle_summary
            if vehicle_ids:
                df = df[df["vehicle_id"].str.lower().isin(vehicle_ids)]
            evidence["vehicle_efficiency"] = df.head(15).to_dict("records")
        if "driver_risk" in intents:
            df = self.driver_scores
            if driver_ids:
                df = df[df["driver_id"].str.lower().isin(driver_ids)]
            evidence["driver_scorecard"] = df.head(15).to_dict("records")
        if "cost" in intents:
            evidence["cost_summary"] = self.vehicle_summary[
                ["vehicle_id", "total_fuel_cost", "cost_per_km"]
            ].sort_values("total_fuel_cost", ascending=False).head(10).to_dict("records")
        if "forecast" in intents:
            evidence["forecast"] = self.forecast_result
        if "route" in intents and self.route_variance_df is not None and len(self.route_variance_df):
            evidence["route_variance_sample"] = self.route_variance_df[
                self.route_variance_df.get("detour_flag", False) == True
            ].head(10).to_dict("records")
        if not evidence:
            evidence["fleet_summary"] = self.vehicle_summary.head(10).to_dict("records")
        return evidence

    def ask(self, question: str) -> dict:
        intents = classify_intent(question)
        vehicle_ids = extract_vehicle_ids(question)
        driver_ids = extract_driver_ids(question)
        evidence = self._gather_evidence(intents, vehicle_ids, driver_ids)
        answer = self.claude.interpret(QUESTION_ANSWER_PROMPT, evidence, question=question)
        return {"intents": intents, "evidence": evidence, "answer": answer}
