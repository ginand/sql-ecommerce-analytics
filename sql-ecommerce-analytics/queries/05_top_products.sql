WITH base AS (
  SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    (oi.quantity * oi.unit_price - oi.discount_amount) AS revenue_line,
    (oi.quantity * p.unit_cost) AS cogs_line,
    oi.quantity
  FROM order_items oi
  JOIN orders o ON o.order_id = oi.order_id
  JOIN products p ON p.product_id = oi.product_id
  JOIN categories c ON c.category_id = p.category_id
  WHERE o.status='completed'
)
SELECT
  product_id,
  product_name,
  category_name,
  SUM(quantity) AS units_sold,
  ROUND(SUM(revenue_line),2) AS revenue,
  ROUND(SUM(revenue_line) - SUM(cogs_line),2) AS gross_profit
FROM base
GROUP BY 1,2,3
ORDER BY gross_profit DESC
LIMIT 20;