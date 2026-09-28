"""
Lightweight keyword-based intent classifier. Deliberately simple and
auditable rather than an LLM call, so routing is deterministic and free.
"""
import re

INTENT_KEYWORDS = {
    "fraud_check": ["fraud", "theft", "steal", "siphon", "suspicious", "flagged", "anomaly", "anomalies"],
    "driver_risk": ["driver", "risk", "harsh braking", "harsh accel", "behaviour", "behavior", "risky"],
    "efficiency": ["efficien", "litres per", "l/100km", "consumption", "fuel usage", "burn rate"],
    "cost": ["cost", "spend", "expensive", "budget", "price"],
    "forecast": ["forecast", "predict", "next month", "next week", "trend", "projection"],
    "route": ["route", "detour", "distance", "trip", "planned vs actual"],
    "depot": ["depot", "branch", "site", "location"],
    "vehicle_lookup": ["vehicle", "vh-", "truck", "van", "bakkie"],
}


def classify_intent(question: str) -> list:
    q = question.lower()
    matched = []
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                matched.append(intent)
                break
    return matched or ["general"]


def extract_vehicle_ids(question: str) -> list:
    return re.findall(r"vh-\d+", question.lower())


def extract_driver_ids(question: str) -> list:
    return re.findall(r"dr-\d+", question.lower())
