import logging
import pandas as pd
from prophet import Prophet
from sqlalchemy import create_engine

logging.getLogger("cmdstanpy").setLevel(logging.ERROR)   # hide Prophet's noisy logs
logging.getLogger("prophet").setLevel(logging.ERROR)

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/control_tower")
HORIZON = 14

sales = pd.read_sql("SELECT * FROM sales_daily", engine)
sales["sale_date"] = pd.to_datetime(sales["sale_date"])

# latest stock for every store + product
stock = pd.read_sql("""
    SELECT store_id, product_id, stock_on_hand FROM inventory_hourly
    WHERE snapshot_time = (SELECT MAX(snapshot_time) FROM inventory_hourly)""", engine)
stock_map = {(r.store_id, r.product_id): r.stock_on_hand for r in stock.itertuples()}

forecasts, summary = [], []
groups = list(sales.groupby(["store_id", "product_id"]))
for n, ((store_id, product_id), g) in enumerate(groups, start=1):
    df = g.rename(columns={"sale_date": "ds", "units_sold": "y"})[["ds", "y"]]
    m = Prophet(weekly_seasonality=True, yearly_seasonality=False, daily_seasonality=False)
    m.fit(df)
    fc = m.predict(m.make_future_dataframe(periods=HORIZON)).tail(HORIZON)[["ds", "yhat"]].copy()
    fc["yhat"] = fc["yhat"].clip(lower=0).round(1)
    fc["store_id"], fc["product_id"] = store_id, product_id
    forecasts.append(fc)

    # when does cumulative forecast demand pass the stock we hold?
    on_hand = stock_map[(store_id, product_id)]
    cum = fc["yhat"].cumsum().tolist()
    days = 0 if on_hand <= 0 else next((i + 1 for i, c in enumerate(cum) if c >= on_hand), None)
    risk = "OK" if days is None or days > 7 else ("CRITICAL" if days <= 3 else "WARNING")
    summary.append((store_id, product_id, on_hand, round(sum(fc["yhat"]), 1), days, risk))

    if n % 20 == 0:
        print(f"{n}/{len(groups)} series done")

pd.concat(forecasts).rename(columns={"ds": "forecast_date", "yhat": "predicted_units"}).to_sql(
    "demand_forecast", engine, if_exists="replace", index=False)
pd.DataFrame(summary, columns=["store_id", "product_id", "stock_on_hand",
    "forecast_14d_units", "days_until_stockout", "risk_level"]).to_sql(
    "stockout_risk", engine, if_exists="replace", index=False)

print(pd.read_sql("""
    SELECT s.city, p.product_name, r.stock_on_hand, r.forecast_14d_units,
           r.days_until_stockout, r.risk_level
    FROM stockout_risk r
    JOIN stores s ON s.store_id = r.store_id
    JOIN products p ON p.product_id = r.product_id
    WHERE r.risk_level <> 'OK'
    ORDER BY r.days_until_stockout""", engine).to_string(index=False))

