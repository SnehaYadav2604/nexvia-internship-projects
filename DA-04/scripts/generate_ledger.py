import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
months = pd.date_range(end="2026-10-01", periods=24, freq="MS")

accounts = pd.DataFrame([
    (4010, "Product Sales",  "Revenue", 9_000_000),
    (4020, "Services",       "Revenue", 4_000_000),
    (4030, "Subscriptions",  "Revenue", 3_000_000),
    (4040, "Other Revenue",  "Revenue",   500_000),
    (5010, "Materials",      "COGS",    5_000_000),
    (5020, "Direct Labour",  "COGS",    3_000_000),
    (6010, "Salaries",       "Opex",    4_500_000),
    (6020, "Marketing",      "Opex",    1_200_000),
    (6030, "Rent",           "Opex",      500_000),
    (6040, "Utilities",      "Opex",      200_000),
    (6050, "Software",       "Opex",      400_000),
    (6060, "Travel",         "Opex",      300_000),
], columns=["account_id", "account_name", "account_type", "base_budget"])

rows = []
for t, m in enumerate(months):
    growth = 1.01 ** t
    for a in accounts.itertuples():
        budget = round(a.base_budget * growth, -3)
        factor = 1.0
        if a.account_id == 6020 and t >= 21: factor = 1.35   # marketing overspend, last 3 months
        if a.account_id == 6060 and t >= 21: factor = 1.30   # travel overspend, last 3 months
        if a.account_id == 4020 and t >= 20: factor = 0.80   # services revenue shortfall, last 4 months
        actual = round(budget * factor * (1 + rng.normal(0, 0.03)), -3)
        rows.append((m, a.account_id, budget, actual))

gl = pd.DataFrame(rows, columns=["month", "account_id", "budget", "actual"])
typed = gl.merge(accounts[["account_id", "account_type"]], on="account_id")
pl = typed.pivot_table(index="month", columns="account_type", values="actual", aggfunc="sum")

equity = 40_000_000
bs_rows = []
for m, r in pl.iterrows():
    equity += r["Revenue"] - r["COGS"] - r["Opex"]
    receivables = 1.5 * r["Revenue"]
    inventory = r["COGS"]
    fixed_assets = 20_000_000
    payables = 0.6 * (r["COGS"] + r["Opex"])
    loan = 15_000_000
    cash = payables + loan + equity - fixed_assets - receivables - inventory
    for line, section, amt in [("Cash", "Assets", cash), ("Receivables", "Assets", receivables),
                               ("Inventory", "Assets", inventory), ("Fixed Assets", "Assets", fixed_assets),
                               ("Payables", "Liabilities", payables), ("Bank Loan", "Liabilities", loan),
                               ("Equity", "Equity", equity)]:
        bs_rows.append((m, line, section, round(amt, 2)))

bs = pd.DataFrame(bs_rows, columns=["month", "line_item", "section", "amount"])
accounts.to_csv("data/accounts.csv", index=False)
gl.to_csv("data/gl_budget_actual.csv", index=False)
bs.to_csv("data/balance_sheet.csv", index=False)
print(f"accounts: {len(accounts)} | gl rows: {len(gl)} | balance sheet rows: {len(bs)}")

