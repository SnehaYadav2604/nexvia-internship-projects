import os
import json
import urllib.request
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/control_tower")

# thresholds (change these to make alerts stricter or looser)
DEMAND_Z_ALERT = 5
SUPPLIER_Z_ALERT = 2

stock = pd.read_sql("""
    SELECT s.city, p.product_name, r.stock_on_hand, r.days_until_stockout, r.risk_level
    FROM stockout_risk r
    JOIN stores s ON s.store_id = r.store_id
    JOIN products p ON p.product_id = r.product_id
    WHERE r.risk_level IN ('CRITICAL', 'WARNING')
    ORDER BY r.days_until_stockout""", engine)

demand = pd.read_sql(f"""
    SELECT d.sale_date::date AS day, s.city, p.product_name, d.units_sold, d.z_score
    FROM demand_anomalies d
    JOIN stores s ON s.store_id = d.store_id
    JOIN products p ON p.product_id = d.product_id
    WHERE d.z_score > {DEMAND_Z_ALERT}
    ORDER BY d.z_score DESC""", engine)

supplier = pd.read_sql(f"""
    SELECT a.order_date::date AS day, su.supplier_name, a.delay_days, a.z_score
    FROM supplier_anomalies a
    JOIN suppliers su ON su.supplier_id = a.supplier_id
    WHERE a.z_score > {SUPPLIER_Z_ALERT}
    ORDER BY a.z_score DESC""", engine)

lines = ["CONTROL TOWER ALERTS"]

lines.append(f"\nSTOCK-OUT RISK ({len(stock)})")
for r in stock.itertuples():
    lines.append(f"  [{r.risk_level}] {r.product_name} in {r.city}: "
                 f"{r.stock_on_hand} units left, runs out in {r.days_until_stockout} day(s)")

lines.append(f"\nDEMAND SPIKES ({len(demand)})")
for r in demand.itertuples():
    lines.append(f"  {r.day} {r.product_name} in {r.city}: sold {r.units_sold} (z={r.z_score})")

lines.append(f"\nSUPPLIER DELAYS ({len(supplier)})")
for r in supplier.itertuples():
    lines.append(f"  Order {r.day} from {r.supplier_name}: {r.delay_days} days late (z={r.z_score})")

message = "\n".join(lines)
print(message)

# optional: send to Slack if a webhook link is set
webhook = os.environ.get("SLACK_WEBHOOK_URL")
if webhook:
    req = urllib.request.Request(webhook, data=json.dumps({"text": message}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    print("\nSent to Slack.")
else:
    print("\n(Slack not configured, printed only.)")

    