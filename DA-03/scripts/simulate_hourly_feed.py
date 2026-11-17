import numpy as np
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/control_tower")
rng = np.random.default_rng()          # no fixed seed: new data differs each run

base_demand = pd.read_sql(
    "SELECT product_id, base_daily_demand FROM products", engine
).set_index("product_id")["base_daily_demand"]

last_time = pd.Timestamp(pd.read_sql(
    "SELECT MAX(snapshot_time) AS t FROM inventory_hourly", engine)["t"].iloc[0])
now = pd.Timestamp.now().floor("h")

if last_time >= now:
    print(f"Already up to date (latest reading: {last_time})")
    raise SystemExit

hours = pd.date_range(last_time + pd.Timedelta(hours=1), now, freq="h")

latest = pd.read_sql("""
    SELECT store_id, product_id, stock_on_hand FROM inventory_hourly
    WHERE snapshot_time = (SELECT MAX(snapshot_time) FROM inventory_hourly)""", engine)

rows = []
for r in latest.itertuples():
    base = int(base_demand[r.product_id])
    current = int(r.stock_on_hand)
    stuck = (r.product_id == 3 and r.store_id == 2)    # planted: Rice in Bengaluru
    for h in hours:
        current -= rng.poisson(base / 24)
        if not stuck and current < base * 2 and rng.random() < 0.10:
            current += base * 7                         # restock arrives
        current = max(current, 0)
        rows.append((h, r.store_id, r.product_id, current))

pd.DataFrame(rows, columns=["snapshot_time", "store_id", "product_id", "stock_on_hand"]).to_sql(
    "inventory_hourly", engine, if_exists="append", index=False)
print(f"Added {len(rows)} rows for {len(hours)} new hour(s), up to {hours[-1]}")

