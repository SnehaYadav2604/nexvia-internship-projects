import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://snehayadav@localhost:5432/control_tower")

def q(sql):
    return pd.read_sql(sql, engine)

def test_all_tables_have_data():
    for t in ["products", "stores", "suppliers", "sales_daily", "inventory_hourly", "deliveries"]:
        assert q(f"SELECT COUNT(*) AS n FROM {t}")["n"][0] > 0, t

def test_no_negative_stock():
    assert q("SELECT COUNT(*) AS n FROM inventory_hourly WHERE stock_on_hand < 0")["n"][0] == 0

def test_no_negative_sales():
    assert q("SELECT COUNT(*) AS n FROM sales_daily WHERE units_sold < 0")["n"][0] == 0

def test_on_time_pct_is_a_valid_percentage():
    assert q("SELECT on_time_pct FROM kpi_supplier_performance")["on_time_pct"].between(0, 100).all()

def test_stockout_rate_is_a_valid_percentage():
    assert q("SELECT stockout_rate_pct FROM kpi_stockout_rate")["stockout_rate_pct"].between(0, 100).all()

def test_planted_rice_stockout_is_found():
    df = q("SELECT stockout_rate_pct FROM kpi_stockout_rate WHERE city='Bengaluru' AND product_name='Rice'")
    assert df["stockout_rate_pct"][0] > 50

def test_planted_milk_spike_is_detected():
    assert len(q("SELECT * FROM demand_anomalies WHERE store_id=1 AND product_id=1 AND z_score > 5")) >= 1

def test_planted_supplier_delay_is_detected():
    assert len(q("SELECT * FROM supplier_anomalies WHERE supplier_id=5 AND z_score > 2")) >= 1

def test_forecast_covers_every_series_and_is_non_negative():
    df = q("SELECT predicted_units FROM demand_forecast")
    assert len(df) == 100 * 14
    assert df["predicted_units"].min() >= 0

def test_rice_bengaluru_flagged_critical():
    df = q("SELECT risk_level FROM stockout_risk WHERE store_id=2 AND product_id=3")
    assert df["risk_level"][0] == "CRITICAL"

    