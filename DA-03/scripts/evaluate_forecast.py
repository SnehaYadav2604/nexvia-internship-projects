import logging
import numpy as np
import pandas as pd
from prophet import Prophet
from sqlalchemy import create_engine

logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
logging.getLogger("prophet").setLevel(logging.ERROR)

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/control_tower")
sales = pd.read_sql("SELECT * FROM sales_daily", engine)
sales["sale_date"] = pd.to_datetime(sales["sale_date"])
cutoff = sales["sale_date"].max() - pd.Timedelta(days=13)

abs_err, abs_err_naive, actual_total = 0.0, 0.0, 0.0
for (s, p), g in sales.groupby(["store_id", "product_id"]):
    train = g[g["sale_date"] < cutoff].rename(columns={"sale_date": "ds", "units_sold": "y"})[["ds", "y"]]
    test = g[g["sale_date"] >= cutoff].sort_values("sale_date")
    m = Prophet(weekly_seasonality=True, yearly_seasonality=False, daily_seasonality=False)
    m.fit(train)
    pred = m.predict(pd.DataFrame({"ds": test["sale_date"]}))["yhat"].clip(lower=0).values
    naive = train["y"].tail(14).mean()
    abs_err += np.abs(test["units_sold"].values - pred).sum()
    abs_err_naive += np.abs(test["units_sold"].values - naive).sum()
    actual_total += test["units_sold"].sum()

mae_p = abs_err / (100 * 14)
result = (f"Forecast accuracy on the last 14 days (100 store-product series)\n"
          f"Prophet  MAE: {mae_p:.2f} units/day | WAPE: {100 * abs_err / actual_total:.1f}%\n"
          f"Baseline MAE: {abs_err_naive / (100 * 14):.2f} units/day | WAPE: {100 * abs_err_naive / actual_total:.1f}%\n")
print(result)
open("docs/forecast_accuracy.txt", "w").write(result)

