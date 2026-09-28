"""
Deterministic, template-based management report — no API key required.
Guarantees the tool is useful even with zero Claude spend, and gives a
consistent baseline the Claude-narrated version can be compared against.
"""


def generate_management_report(fleet_kpis: dict, vehicle_summary_top5, driver_risk_top5,
                                 anomaly_summary_dict: dict, forecast_result: dict) -> str:
    lines = []
    lines.append("FLEET FUEL & LOGISTICS — MANAGEMENT REPORT")
    lines.append("=" * 50)
    lines.append("")
    lines.append("FLEET OVERVIEW")
    lines.append(f"  Vehicles: {fleet_kpis.get('n_vehicles')}")
    lines.append(f"  Total distance: {fleet_kpis.get('total_distance_km'):,.0f} km")
    lines.append(f"  Total fuel spend: R{fleet_kpis.get('total_fuel_cost'):,.2f}")
    lines.append(f"  Fleet-wide consumption: {fleet_kpis.get('fleet_litres_per_100km')} L/100km")
    lines.append(f"  Fleet-wide cost per km: R{fleet_kpis.get('fleet_cost_per_km')}")
    lines.append("")

    lines.append("LEAST EFFICIENT VEHICLES (highest cost per km)")
    for _, row in vehicle_summary_top5.iterrows():
        lines.append(f"  {row['vehicle_id']}: R{row['cost_per_km']:.2f}/km, "
                      f"{row['litres_per_100km']:.1f} L/100km")
    lines.append("")

    lines.append("HIGHEST-RISK DRIVERS")
    for _, row in driver_risk_top5.iterrows():
        lines.append(f"  {row['driver_id']}: risk score {row['risk_score']} ({row['risk_tier']})")
    lines.append("")

    lines.append("FRAUD / ANOMALY FLAGS")
    lines.append(f"  Flagged transactions: {anomaly_summary_dict.get('n_flagged_transactions', 0)}")
    lines.append(f"  Vehicles with fill-vs-distance mismatch: "
                  f"{anomaly_summary_dict.get('n_vehicles_with_fill_distance_mismatch', 0)}")
    for v in anomaly_summary_dict.get("top_mismatch_vehicles", [])[:5]:
        lines.append(f"    {v.get('vehicle_id')}: {v.get('litres_variance_pct', 0):.0f}% more fuel bought "
                      f"than distance driven would suggest")
    lines.append("")

    lines.append("FUEL SPEND FORECAST")
    if forecast_result.get("status") == "ok":
        lines.append(f"  Best-performing model: {forecast_result['best_model']}")
        lines.append(f"  Next {len(forecast_result['forecast_next_periods'])} weeks (R): "
                      f"{forecast_result['forecast_next_periods']}")
    else:
        lines.append(f"  {forecast_result.get('message', 'Forecast unavailable')}")

    lines.append("")
    lines.append("=" * 50)
    return "\n".join(lines)
