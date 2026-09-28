"""
QA gates that run on evidence JSON before it is shown to the user or passed
to Claude, catching pipeline bugs (NaNs leaking through, negative costs,
empty evidence) before they become a false or misleading conclusion.
"""
import math


def _has_bad_numeric(value) -> bool:
    if isinstance(value, float):
        return math.isnan(value) or math.isinf(value)
    return False


def validate_evidence(evidence: dict) -> list:
    """Returns a list of QA problems found in an evidence dict (empty = passed)."""
    problems = []

    def _walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _walk(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]")
        else:
            if _has_bad_numeric(obj):
                problems.append(f"NaN/Inf value found at {path}")

    if not evidence:
        problems.append("Evidence dict is empty — nothing to interpret")
        return problems

    _walk(evidence)
    return problems


def validate_kpis(kpis: dict) -> list:
    problems = []
    if kpis.get("total_fuel_cost", 0) < 0:
        problems.append("total_fuel_cost is negative — upstream data error")
    if kpis.get("total_distance_km", 0) < 0:
        problems.append("total_distance_km is negative — upstream data error")
    if kpis.get("fleet_litres_per_100km") is not None and kpis["fleet_litres_per_100km"] > 200:
        problems.append("fleet_litres_per_100km implausibly high (>200) — check unit mismatches")
    return problems


def gate_before_display(evidence: dict, kpis: dict = None) -> dict:
    """Runs all QA checks; returns {'passed': bool, 'problems': [...]}."""
    problems = validate_evidence(evidence)
    if kpis:
        problems += validate_kpis(kpis)
    return {"passed": len(problems) == 0, "problems": problems}
