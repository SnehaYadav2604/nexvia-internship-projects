import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/finance_risk")
pnl = pd.read_sql("SELECT * FROM v_pnl_monthly ORDER BY month", engine)
var = pd.read_sql("SELECT * FROM v_variance_by_account", engine)
bands = pd.read_sql("SELECT * FROM credit_band_summary ORDER BY risk_band", engine)
bs = pd.read_sql("SELECT * FROM v_balance_latest", engine)
for c in ["revenue", "cogs", "opex", "gross_profit", "net_income", "budget_net_income"]:
    pnl[c] = pnl[c].astype(float)
for c in ["budget", "actual", "variance", "variance_pct"]:
    var[c] = var[c].astype(float)
bs["amount"] = bs["amount"].astype(float)

latest = pnl.iloc[-1]
label = pd.Timestamp(latest["month"]).strftime("%Y-%m")
cash = bs.loc[bs["line_item"] == "Cash", "amount"].iloc[0]
metrics = open("docs/scorecard_metrics.txt").read().splitlines()
def money(x): return f"INR {x / 1e6:,.2f}M"

path = f"reports/board_pack_{label}.pdf"
with PdfPages(path) as pdf:
    # page 1: summary
    fig, ax = plt.subplots(figsize=(11.7, 8.3)); ax.axis("off")
    gap = 100 * (latest["net_income"] - latest["budget_net_income"]) / latest["budget_net_income"]
    lines = [f"MONTHLY BOARD PACK - {label}", "",
             f"Revenue:        {money(latest['revenue'])}",
             f"Gross profit:   {money(latest['gross_profit'])}",
             f"Net income:     {money(latest['net_income'])} (budget {money(latest['budget_net_income'])}, {gap:+.1f}%)",
             f"Cash balance:   {money(cash)}", "",
             "Credit risk scorecard:", metrics[2]]
    ax.text(0.03, 0.95, "\n".join(lines), va="top", family="monospace", fontsize=15)
    pdf.savefig(fig); plt.close(fig)

    # page 2: net income, actual vs budget
    fig, ax = plt.subplots(figsize=(11.7, 8.3))
    ax.plot(pnl["month"], pnl["net_income"] / 1e6, marker="o", label="Actual")
    ax.plot(pnl["month"], pnl["budget_net_income"] / 1e6, marker="o", linestyle="--", label="Budget")
    ax.set_title("Net income: actual vs budget (INR million)"); ax.legend(); ax.grid(alpha=0.3)
    fig.autofmt_xdate(); pdf.savefig(fig); plt.close(fig)

    # page 3: biggest variances, last 3 months
    top = var.reindex(var["variance"].abs().sort_values(ascending=False).index).head(8)
    cells = [[r.account_name, f"{r.budget / 1e6:.2f}", f"{r.actual / 1e6:.2f}", f"{r.variance_pct:+.1f}%", r.impact]
             for r in top.itertuples()]
    fig, ax = plt.subplots(figsize=(11.7, 8.3)); ax.axis("off")
    ax.set_title("Largest budget variances, last 3 months (INR million)")
    tbl = ax.table(cellText=cells, colLabels=["Account", "Budget", "Actual", "Variance", "Impact"], loc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(11); tbl.scale(1, 2)
    pdf.savefig(fig); plt.close(fig)

    # page 4: credit risk bands
    fig, ax = plt.subplots(figsize=(11.7, 8.3))
    ax.bar(bands["risk_band"], bands["bad_rate_pct"])
    ax.set_title("Credit risk bands: actual default rate (%)")
    ax.set_xlabel("Risk band (A = lowest risk, E = highest risk)")
    fig.text(0.05, 0.02, metrics[2], fontsize=10)
    pdf.savefig(fig); plt.close(fig)
print("Saved", path)

