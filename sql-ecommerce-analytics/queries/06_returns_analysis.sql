WITH completed_orders AS (
  SELECT o.order_id
  FROM orders o
  WHERE o.status='completed'
),
cat_orders AS (
  SELECT DISTINCT
    c.category_name,
    o.order_id
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  JOIN products p ON p.product_id = oi.product_id
  JOIN categories c ON c.category_id = p.category_id
  WHERE o.status='completed'
)
SELECT
  co.category_name,
  COUNT(DISTINCT r.order_id) AS returned_orders,
  COUNT(DISTINCT co.order_id) AS completed_orders,
  ROUND(100.0 * COUNT(DISTINCT r.order_id) / NULLIF(COUNT(DISTINCT co.order_id),0), 2) AS return_rate_pct
FROM cat_orders co
LEFT JOIN returns r ON r.order_id = co.order_id
GROUP BY 1
ORDER BY return_rate_pct DESC;