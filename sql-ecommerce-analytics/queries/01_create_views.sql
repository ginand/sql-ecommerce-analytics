SELECT
  date_trunc('month', order_date) AS month,
  COUNT(*) FILTER (WHERE status='completed') AS completed_orders,
  COUNT(*) FILTER (WHERE status='cancelled') AS cancelled_orders,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status='cancelled') / NULLIF(COUNT(*),0), 2) AS cancel_rate_pct,
  ROUND(SUM(net_revenue) FILTER (WHERE status='completed'), 2) AS net_revenue,
  ROUND(
    SUM(net_revenue) FILTER (WHERE status='completed')
    / NULLIF(COUNT(*) FILTER (WHERE status='completed'), 0)
  , 2) AS aov_net
FROM v_order_net_revenue
GROUP BY 1
ORDER BY 1;