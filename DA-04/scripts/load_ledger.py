import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/finance_risk")
with engine.begin() as conn:
    conn.execute(text("TRUNCATE balance_sheet, gl_budget_actual, accounts"))

for table, date_cols in [("accounts", []), ("gl_budget_actual", ["month"]), ("balance_sheet", ["month"])]:
    df = pd.read_csv(f"data/{table}.csv", parse_dates=date_cols)
    df.to_sql(table, engine, if_exists="append", index=False)
    print(f"{table}: {len(df)} rows loaded")

    