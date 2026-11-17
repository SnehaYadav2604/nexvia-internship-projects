import numpy as np
import pandas as pd
from faker import Faker

rng = np.random.default_rng(42)      # fixed seed = same data every run
fake = Faker("en_IN")
Faker.seed(42)

# ---------- products ----------
names = ["Milk", "Bread", "Rice", "Wheat Flour", "Sugar", "Tea", "Coffee",
         "Eggs", "Butter", "Cooking Oil", "Soap", "Shampoo", "Toothpaste",
         "Detergent", "Biscuits", "Noodles", "Juice", "Salt", "Lentils", "Yogurt"]
products = pd.DataFrame({
    "product_id": range(1, 21),
    "product_name": names,
    "unit_price": rng.integers(20, 400, 20),
    "base_daily_demand": rng.integers(8, 40, 20),   # units/day per store
    "supplier_id": rng.integers(1, 7, 20),
})
products["reorder_level"] = products["base_daily_demand"] * 3

# ---------- stores ----------
stores = pd.DataFrame({
    "store_id": range(1, 6),
    "city": ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Delhi"],
})

# ---------- suppliers ----------
suppliers = pd.DataFrame({
    "supplier_id": range(1, 7),
    "supplier_name": [fake.company() for _ in range(6)],
    "reliability": [0.95, 0.90, 0.85, 0.75, 0.60, 0.92],  # chance of on-time
    "avg_lead_days": [2, 3, 4, 5, 7, 3],
})

# ---------- daily sales (180 days) ----------
end = pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
dates = pd.date_range(end=end, periods=180)
weekend = np.where(dates.dayofweek >= 5, 1.3, 1.0)   # more sales on weekends
trend = np.linspace(1.0, 1.15, len(dates))           # slow growth
rows = []
for s in stores["store_id"]:
    for _, p in products.iterrows():
        mean = p["base_daily_demand"] * weekend * trend
        rows.append(pd.DataFrame({
            "sale_date": dates,
            "store_id": s,
            "product_id": int(p["product_id"]),
            "units_sold": rng.poisson(mean),
        }))
sales = pd.concat(rows, ignore_index=True)

# planted demand spike: Milk, Store 1, last 3 days
mask = ((sales["product_id"] == 1) & (sales["store_id"] == 1)
        & (sales["sale_date"] >= end - pd.Timedelta(days=2)))
sales.loc[mask, "units_sold"] *= 3

# ---------- hourly inventory (last 7 days) ----------
hours = pd.date_range(end=end + pd.Timedelta(hours=23), periods=168, freq="h")
inv_rows = []
for s in stores["store_id"]:
    for _, p in products.iterrows():
        base = int(p["base_daily_demand"])
        stock = base * 2 if (p["product_id"] == 3 and s == 2) else base * 6
        for i, h in enumerate(hours):
            stock -= rng.poisson(base / 24)
            if i % 72 == 71 and not (p["product_id"] == 3 and s == 2):
                stock += base * 7                      # restock arrives
            stock = max(stock, 0)
            inv_rows.append((h, s, int(p["product_id"]), stock))
inventory = pd.DataFrame(inv_rows, columns=["snapshot_time", "store_id", "product_id", "stock_on_hand"])

# ---------- deliveries (300 shipments) ----------
d = []
for k in range(300):
    sup = int(rng.integers(1, 7))
    order_date = end - pd.Timedelta(days=int(rng.integers(0, 180)))
    sup_row = suppliers[suppliers["supplier_id"] == sup].iloc[0]
    promised = order_date + pd.Timedelta(days=int(sup_row["avg_lead_days"]))
    delay = 0 if rng.random() < sup_row["reliability"] else int(rng.integers(1, 6))
    if sup == 5 and order_date >= end - pd.Timedelta(days=14):
        delay += 4                                      # planted supplier problem
    d.append((k + 1, sup, int(rng.integers(1, 6)), int(rng.integers(1, 21)),
              int(rng.integers(50, 500)), order_date, promised, promised + pd.Timedelta(days=delay)))
deliveries = pd.DataFrame(d, columns=["delivery_id", "supplier_id", "store_id", "product_id",
                                      "quantity", "order_date", "promised_date", "actual_date"])
deliveries["delay_days"] = (deliveries["actual_date"] - deliveries["promised_date"]).dt.days

# ---------- save ----------
for name, df in [("products", products), ("stores", stores), ("suppliers", suppliers),
                 ("sales_daily", sales), ("inventory_hourly", inventory), ("deliveries", deliveries)]:
    df.to_csv(f"data/{name}.csv", index=False)
    print(f"{name}.csv saved: {len(df)} rows")