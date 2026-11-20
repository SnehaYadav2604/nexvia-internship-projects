CREATE OR REPLACE VIEW whatif_supplier_delay AS
SELECT d.city,
       d.product_name,
       su.supplier_name,
       d.days_of_inventory,
       su.avg_lead_days,
       g.delay_days,
       su.avg_lead_days + g.delay_days AS delivery_arrives_in_days,
       GREATEST(0, ROUND((su.avg_lead_days + g.delay_days - d.days_of_inventory)::numeric, 1)) AS days_without_stock,
       CASE WHEN su.avg_lead_days + g.delay_days > d.days_of_inventory
            THEN 'STOCK-OUT' ELSE 'OK' END AS status
FROM kpi_days_of_inventory d
JOIN products p   ON p.product_name = d.product_name
JOIN suppliers su ON su.supplier_id = p.supplier_id
CROSS JOIN generate_series(0, 14) AS g(delay_days);
