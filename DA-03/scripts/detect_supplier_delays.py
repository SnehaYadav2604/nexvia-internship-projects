import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/control_tower")

d = pd.read_sql("SELECT * FROM deliveries", engine)
d["order_date"] = pd.to_datetime(d["order_date"])

# "normal" = orders placed before the last 14 days
cutoff = d["order_date"].max() - pd.Timedelta(days=13)
normal = (d[d["order_date"] < cutoff].groupby("supplier_id")["delay_days"]
          .agg(avg_delay="mean", spread="std").reset_index())

# score recent deliveries against each supplier's normal
recent = d[d["order_date"] >= cutoff].merge(normal, on="supplier_id")
recent["z_score"] = ((recent["delay_days"] - recent["avg_delay"]) / recent["spread"]).round(2)

flagged = recent[recent["z_score"] > 2]
flagged[["delivery_id", "supplier_id", "order_date", "delay_days", "z_score"]].to_sql(
    "supplier_anomalies", engine, if_exists="replace", index=False)

result = pd.read_sql("""
    SELECT a.order_date::date AS order_date, su.supplier_name, a.delay_days, a.z_score
    FROM supplier_anomalies a
    JOIN suppliers su ON su.supplier_id = a.supplier_id
    ORDER BY a.z_score DESC""", engine)
print(result.to_string(index=False))

