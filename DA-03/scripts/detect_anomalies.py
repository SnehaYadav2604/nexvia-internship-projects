import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/control_tower")

sales = pd.read_sql("SELECT * FROM sales_daily", engine)
sales["sale_date"] = pd.to_datetime(sales["sale_date"])

# "normal" = everything before the last 7 days
cutoff = sales["sale_date"].max() - pd.Timedelta(days=6)
history = sales[sales["sale_date"] < cutoff]
normal = (history.groupby(["store_id", "product_id"])["units_sold"]
          .agg(avg="mean", spread="std").reset_index())

# score the last 7 days against normal
recent = sales[sales["sale_date"] >= cutoff].merge(normal, on=["store_id", "product_id"])
recent["z_score"] = ((recent["units_sold"] - recent["avg"]) / recent["spread"]).round(2)

# keep only the big ones and save them to the database
spikes = recent[recent["z_score"] > 3]
spikes[["sale_date", "store_id", "product_id", "units_sold", "z_score"]].to_sql(
    "demand_anomalies", engine, if_exists="replace", index=False)

result = pd.read_sql("""
    SELECT d.sale_date, s.city, p.product_name, d.units_sold, d.z_score
    FROM demand_anomalies d
    JOIN stores s   ON s.store_id   = d.store_id
    JOIN products p ON p.product_id = d.product_id
    ORDER BY d.z_score DESC""", engine)
print(result.to_string(index=False))

