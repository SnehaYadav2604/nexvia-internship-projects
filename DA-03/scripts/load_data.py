import pandas as pd
from sqlalchemy import create_engine, text

# connection: user = your Mac username, no password needed for local Postgres.app
engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/control_tower")

# order matters: tables that others point to must be filled first
ORDER = [
    ("suppliers", []),
    ("stores", []),
    ("products", []),
    ("sales_daily", ["sale_date"]),
    ("inventory_hourly", ["snapshot_time"]),
    ("deliveries", ["order_date", "promised_date", "actual_date"]),
]

with engine.begin() as conn:
    # empty all tables first, so re-running never creates duplicates
    conn.execute(text(
        "TRUNCATE deliveries, inventory_hourly, sales_daily, products, stores, suppliers"
    ))

for table, date_cols in ORDER:
    df = pd.read_csv(f"data/{table}.csv", parse_dates=date_cols)
    df.to_sql(table, engine, if_exists="append", index=False, chunksize=2000)
    print(f"{table}: {len(df)} rows loaded")