import pandas as pd
from sklearn.metrics import roc_auc_score
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/finance_risk")

def q(sql):
    return pd.read_sql(sql, engine)

def test_tables_have_expected_rows():
    assert q("SELECT COUNT(*) AS n FROM accounts")["n"][0] == 12
    assert q("SELECT COUNT(*) AS n FROM gl_budget_actual")["n"][0] == 288
    assert q("SELECT COUNT(*) AS n FROM credit_scores")["n"][0] == 1000

def test_balance_sheet_balances_every_month():
    df = q("SELECT assets, liabilities_and_equity FROM v_balance_check").astype(float)
    assert ((df["assets"] - df["liabilities_and_equity"]).abs() < 1).all()

def test_cash_is_never_negative():
    assert q("SELECT MIN(amount) AS m FROM balance_sheet WHERE line_item='Cash'")["m"].astype(float)[0] > 0

def test_net_income_equals_revenue_minus_costs():
    df = q("SELECT revenue, cogs, opex, net_income FROM v_pnl_monthly").astype(float)
    assert ((df["revenue"] - df["cogs"] - df["opex"] - df["net_income"]).abs() < 1).all()

def test_planted_marketing_overspend_is_unfavorable():
    df = q("SELECT impact, variance_pct FROM v_variance_by_account WHERE account_name='Marketing'")
    assert df["impact"][0] == "Unfavorable" and float(df["variance_pct"][0]) > 20

def test_planted_services_shortfall_is_unfavorable():
    df = q("SELECT impact FROM v_variance_by_account WHERE account_name='Services'")
    assert df["impact"][0] == "Unfavorable"

def test_scorecard_discriminates_on_test_data():
    df = q("SELECT pd_bad, is_bad FROM credit_scores WHERE split='test'")
    assert roc_auc_score(df["is_bad"], df["pd_bad"].astype(float)) > 0.70

def test_five_risk_bands_with_rising_default_rate():
    df = q("SELECT risk_band, bad_rate_pct FROM credit_band_summary ORDER BY risk_band")
    assert list(df["risk_band"]) == ["A", "B", "C", "D", "E"]
    assert df["bad_rate_pct"].astype(float).is_monotonic_increasing

    