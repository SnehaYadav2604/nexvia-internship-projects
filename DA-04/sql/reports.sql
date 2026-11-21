CREATE OR REPLACE VIEW v_pnl_monthly AS
SELECT g.month,
       SUM(g.actual) FILTER (WHERE a.account_type = 'Revenue') AS revenue,
       SUM(g.actual) FILTER (WHERE a.account_type = 'COGS')    AS cogs,
       SUM(g.actual) FILTER (WHERE a.account_type = 'Opex')    AS opex,
       SUM(g.actual) FILTER (WHERE a.account_type = 'Revenue')
         - SUM(g.actual) FILTER (WHERE a.account_type = 'COGS') AS gross_profit,
       SUM(CASE WHEN a.account_type = 'Revenue' THEN g.actual ELSE -g.actual END) AS net_income,
       SUM(CASE WHEN a.account_type = 'Revenue' THEN g.budget ELSE -g.budget END) AS budget_net_income
FROM gl_budget_actual g
JOIN accounts a USING (account_id)
GROUP BY g.month;

CREATE OR REPLACE VIEW v_variance_by_account AS
SELECT a.account_name,
       a.account_type,
       SUM(g.budget) AS budget,
       SUM(g.actual) AS actual,
       SUM(g.actual) - SUM(g.budget) AS variance,
       ROUND(100.0 * (SUM(g.actual) - SUM(g.budget)) / SUM(g.budget), 1) AS variance_pct,
       CASE WHEN (a.account_type = 'Revenue' AND SUM(g.actual) >= SUM(g.budget))
              OR (a.account_type <> 'Revenue' AND SUM(g.actual) <= SUM(g.budget))
            THEN 'Favorable' ELSE 'Unfavorable' END AS impact
FROM gl_budget_actual g
JOIN accounts a USING (account_id)
WHERE g.month >= (SELECT MAX(month) FROM gl_budget_actual) - INTERVAL '2 months'
GROUP BY a.account_name, a.account_type;

CREATE OR REPLACE VIEW v_balance_latest AS
SELECT month, section, line_item, ROUND(amount, 0) AS amount
FROM balance_sheet
WHERE month = (SELECT MAX(month) FROM balance_sheet);

CREATE OR REPLACE VIEW v_balance_check AS
SELECT month,
       SUM(amount) FILTER (WHERE section = 'Assets') AS assets,
       SUM(amount) FILTER (WHERE section IN ('Liabilities', 'Equity')) AS liabilities_and_equity
FROM balance_sheet
GROUP BY month;

