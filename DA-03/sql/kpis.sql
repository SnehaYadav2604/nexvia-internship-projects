-- KPI 1: stock-out rate per store and product
CREATE OR REPLACE VIEW kpi_stockout_rate AS
SELECT s.city,
       p.product_name,
       ROUND(100.0 * SUM(CASE WHEN i.stock_on_hand = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS stockout_rate_pct
FROM inventory_hourly i
JOIN products p ON p.product_id = i.product_id
JOIN stores s   ON s.store_id   = i.store_id
GROUP BY s.city, p.product_name;

-- KPI 2 and 3: on-time delivery % and lead time per supplier
CREATE OR REPLACE VIEW kpi_supplier_performance AS
SELECT su.supplier_id,
       su.supplier_name,
       COUNT(*) AS total_deliveries,
       ROUND(100.0 * SUM(CASE WHEN d.delay_days <= 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS on_time_pct,
       ROUND(AVG(d.actual_date - d.order_date), 1) AS avg_lead_days
FROM deliveries d
JOIN suppliers su ON su.supplier_id = d.supplier_id
GROUP BY su.supplier_id, su.supplier_name;


-- KPI 4: days of inventory (latest stock / average daily sales of last 14 days)
CREATE OR REPLACE VIEW kpi_days_of_inventory AS
WITH latest_stock AS (
    SELECT store_id, product_id, stock_on_hand
    FROM inventory_hourly
    WHERE snapshot_time = (SELECT MAX(snapshot_time) FROM inventory_hourly)
),
recent_sales AS (
    SELECT store_id, product_id, AVG(units_sold) AS avg_daily_sales
    FROM sales_daily
    WHERE sale_date > (SELECT MAX(sale_date) FROM sales_daily) - 14
    GROUP BY store_id, product_id
)
SELECT s.city,
       p.product_name,
       l.stock_on_hand,
       ROUND(r.avg_daily_sales, 1) AS avg_daily_sales,
       ROUND(l.stock_on_hand / NULLIF(r.avg_daily_sales, 0), 1) AS days_of_inventory
FROM latest_stock l
JOIN recent_sales r USING (store_id, product_id)
JOIN products p ON p.product_id = l.product_id
JOIN stores s   ON s.store_id   = l.store_id;

