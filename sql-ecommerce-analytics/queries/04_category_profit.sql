WITH base AS (
  SELECT
    c.category_name,
    (oi.quantity * oi.unit_price - oi.discount_amount) AS revenue_line,
    (oi.quantity * p.unit_cost) AS cogs_line
  FROM order_items oi
  JOIN orders o ON o.order_id = oi.order_id
  JOIN products p ON p.product_id = oi.product_id
  JOIN categories c ON c.category_id = p.category_id
  WHERE o.status='completed'
)
SELECT
  category_name,
  ROUND(SUM(revenue_line),2) AS revenue,
  ROUND(SUM(cogs_line),2) AS cogs,
  ROUND(SUM(revenue_line) - SUM(cogs_line),2) AS gross_profit,
  ROUND(100.0 * (SUM(revenue_line) - SUM(cogs_line)) / NULLIF(SUM(revenue_line),0), 2) AS gross_margin_pct
FROM base
GROUP BY 1
ORDER BY gross_profit DESC;