# AI Fleet Fuel & Logistics Analyst

An end-to-end AI-assisted fleet analytics tool built for the South African
logistics/distribution market: upload fuel-card and GPS/trip exports and get
automatic fuel efficiency analysis, driver risk scoring, fuel-card fraud
detection, route variance analysis, and cost forecasting.

## Design principle

**Python/Pandas calculates every number. Claude only interprets validated,
pre-computed evidence — it is never trusted to calculate or invent a figure.**
A separate QA gate checks evidence for NaNs, implausible values, or empty
results before anything reaches the user or gets passed to Claude.

This makes the tool fully usable and defensible with **zero API cost** (the
deterministic report generator and every analytics tab work without an
Anthropic API key) and adds natural-language interpretation on top for those
who configure one.

## Architecture

```
src/fleet_analyst/
  ingestion/      # flexible column-mapping loader for fuel-card & GPS exports
  quality/        # severity-tiered validation + safe-only auto-cleaning
  analytics/
    fuel_engine.py        # litres/100km, cost/km, efficiency trend, benchmarking
    driver_behavior.py    # driver risk scorecard (harsh events, after-hours km)
    route_engine.py        # planned vs actual distance, detour flags, depot summary
    anomaly_engine.py      # fuel-card fraud & anomaly detection (core ROI driver)
  forecasting/    # seasonal-naive vs linear-trend fuel spend forecast, backtested
  ai/
    claude_client.py       # thin Anthropic API wrapper, evidence-only
    prompts.py              # evidence-only system prompts
    intent_classifier.py    # keyword-based routing (no LLM call, free & auditable)
    orchestrator.py         # FleetFuelAgent: question -> evidence -> Claude answer
  reporting/      # deterministic management report (no API key required)
  qa/             # QA gates run on evidence before display
app.py            # Streamlit dashboard (9 tabs)
data/             # synthetic fleet data generator + sample CSVs
tests/            # 41 pytest tests across every module
```

## Why fuel-card fraud detection is the core value driver

For a mid-size fleet (20+ vehicles), fuel-card fraud/wastage (siphoning,
inflated fills, duplicate same-day fills) typically costs far more per month
than the tool costs to run. The anomaly engine flags this with two
independent, auditable methods:

1. **Row-level rules** — impossible litre volumes, multiple same-day fills.
2. **Fill-vs-distance mismatch** — total litres purchased vs. what the
   distance actually driven should require, per vehicle.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tick "Use demo data" in the sidebar to explore immediately with a synthetic
25-vehicle fleet (120 days, ~1,260 fuel transactions, ~2,200 trips, with
injected messiness and injected fraud patterns for testing).

To use your own data, upload:
- A fuel-card export (CSV/XLSX) — needs at minimum vehicle ID, litres, cost
- A GPS/trip log export (CSV/XLSX) — needs at minimum vehicle ID, distance

Column names don't need to match exactly — the schema mapper recognises
common aliases (`reg_no`, `registration`, `fleet_no` all map to `vehicle_id`,
etc.) so exports from Cartrack, MiX Telematics, Netstar, Sasol/Engen/Shell/BP
fleet cards should map automatically.

Optionally add an Anthropic API key in the sidebar to enable the "Ask the
Analyst" tab and narrated summaries. Without a key, every other tab
(including the full management report) still works.

## Running tests

```bash
python -m pytest tests/ -v
```

41 tests passing across ingestion, data quality, all four analytics engines,
forecasting, the AI/orchestration layer, reporting, and QA gates.

## Extending to a new data source

Add new column aliases to `src/fleet_analyst/ingestion/schema.py` — no other
code changes needed for a new provider's export format, as long as it has
the same underlying fields (vehicle, driver, litres/cost, distance).
