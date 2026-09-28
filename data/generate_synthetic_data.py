"""
Generates synthetic fleet fuel-card and GPS trip data for the AI Fleet Fuel
& Logistics Analyst, with injected messiness and injected fraud/anomaly
patterns so the analytics and QA layers have real things to catch.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

N_VEHICLES = 25
N_DRIVERS = 30
DAYS = 120
START_DATE = datetime(2026, 5, 1)

VEHICLE_TYPES = ["Rigid Truck 4T", "Rigid Truck 8T", "Panel Van", "Refrigerated Truck", "Bakkie"]
TANK_CAPACITY = {"Rigid Truck 4T": 120, "Rigid Truck 8T": 200, "Panel Van": 70, "Refrigerated Truck": 250, "Bakkie": 80}
BASE_CONSUMPTION_L_PER_100KM = {"Rigid Truck 4T": 18, "Rigid Truck 8T": 26, "Panel Van": 11, "Refrigerated Truck": 32, "Bakkie": 9}

vehicles = [f"VH-{1000+i}" for i in range(N_VEHICLES)]
vehicle_type_map = {v: random.choice(VEHICLE_TYPES) for v in vehicles}
drivers = [f"DR-{200+i}" for i in range(N_DRIVERS)]
driver_vehicle_map = {v: random.choice(drivers) for v in vehicles}
# a handful of vehicles get a "risky" driver profile (harsh driving / theft pattern)
risky_vehicles = random.sample(vehicles, 4)
depots = ["Pretoria DC", "Polokwane DC", "Nelspruit DC", "Johannesburg DC"]
vehicle_depot_map = {v: random.choice(depots) for v in vehicles}

fuel_rows = []
trip_rows = []

for day_offset in range(DAYS):
    date = START_DATE + timedelta(days=day_offset)
    if date.weekday() == 6:  # skip Sundays mostly
        if random.random() > 0.1:
            continue
    for v in vehicles:
        if random.random() > 0.85:  # not every vehicle drives every day
            continue
        vtype = vehicle_type_map[v]
        base_consumption = BASE_CONSUMPTION_L_PER_100KM[vtype]
        distance_km = max(20, np.random.normal(180, 60))

        driver_factor = 1.0
        if v in risky_vehicles:
            driver_factor = np.random.uniform(1.15, 1.35)  # harsher/wasteful driving

        litres_expected = (distance_km / 100) * base_consumption * driver_factor
        litres_expected *= np.random.normal(1.0, 0.05)

        odometer_start = 50000 + day_offset * 150 + random.randint(-20, 20)
        odometer_end = odometer_start + distance_km

        trip_rows.append({
            "trip_id": f"T-{v}-{day_offset}",
            "vehicle_id": v,
            "driver_id": driver_vehicle_map[v],
            "depot": vehicle_depot_map[v],
            "date": date.strftime("%Y-%m-%d"),
            "planned_distance_km": round(distance_km * np.random.uniform(0.9, 1.0), 1),
            "actual_distance_km": round(distance_km, 1),
            "odometer_start": round(odometer_start, 1),
            "odometer_end": round(odometer_end, 1),
            "harsh_braking_events": np.random.poisson(3 if v in risky_vehicles else 0.8),
            "harsh_accel_events": np.random.poisson(3 if v in risky_vehicles else 0.8),
            "idle_minutes": round(np.random.normal(45 if v in risky_vehicles else 20, 10), 1),
            "after_hours_km": round(distance_km * (0.25 if v in risky_vehicles else np.random.uniform(0, 0.03)), 1),
        })

        # fuel fill doesn't happen every day for every vehicle
        if random.random() < 0.55:
            fill_time = date + timedelta(hours=random.randint(6, 18))
            litres_filled = litres_expected * np.random.uniform(0.95, 1.05)

            # inject fraud pattern: some fills on risky vehicles are inflated relative to distance driven
            if v in risky_vehicles and random.random() < 0.3:
                litres_filled *= np.random.uniform(1.4, 1.9)

            # inject a few impossible fills exceeding tank capacity (data error / card fraud)
            if random.random() < 0.01:
                litres_filled = TANK_CAPACITY[vtype] * np.random.uniform(1.1, 1.4)

            price_per_litre = np.random.normal(23.50, 0.8)

            fuel_rows.append({
                "transaction_id": f"F-{v}-{day_offset}",
                "vehicle_id": v,
                "driver_id": driver_vehicle_map[v],
                "depot": vehicle_depot_map[v],
                "timestamp": fill_time.strftime("%Y-%m-%d %H:%M"),
                "litres": round(litres_filled, 2),
                "price_per_litre": round(price_per_litre, 2),
                "total_cost": round(litres_filled * price_per_litre, 2),
                "odometer_at_fill": round(odometer_end, 1),
                "fuel_type": "Diesel" if vtype != "Bakkie" or random.random() > 0.3 else "Petrol",
                "card_number": f"**** {random.randint(1000,9999)}",
                "merchant": random.choice(["Sasol Fleet", "Engen Fleet", "Shell Fleet", "BP Fleet"]),
            })

fuel_df = pd.DataFrame(fuel_rows)
trip_df = pd.DataFrame(trip_rows)

# --- inject messiness ---
# duplicate a few fuel transactions (common export error)
dupes = fuel_df.sample(15, random_state=1)
fuel_df = pd.concat([fuel_df, dupes], ignore_index=True)

# a few missing driver IDs
missing_idx = fuel_df.sample(10, random_state=2).index
fuel_df.loc[missing_idx, "driver_id"] = np.nan

# a few negative/zero litres (bad export rows)
bad_idx = fuel_df.sample(5, random_state=3).index
fuel_df.loc[bad_idx, "litres"] = 0

# a couple of odometer rollbacks in trip data (data entry errors)
roll_idx = trip_df.sample(4, random_state=4).index
trip_df.loc[roll_idx, "odometer_end"] = trip_df.loc[roll_idx, "odometer_start"] - 50

fuel_df = fuel_df.sample(frac=1, random_state=5).reset_index(drop=True)
trip_df = trip_df.sample(frac=1, random_state=6).reset_index(drop=True)

fuel_df.to_csv("/home/claude/ai_fleet_fuel_analyst/data/synthetic_fuel_transactions.csv", index=False)
trip_df.to_csv("/home/claude/ai_fleet_fuel_analyst/data/synthetic_trip_gps_log.csv", index=False)

print(f"Fuel transactions: {len(fuel_df)} rows")
print(f"Trip/GPS log: {len(trip_df)} rows")
print(f"Risky vehicles (for validation): {risky_vehicles}")
