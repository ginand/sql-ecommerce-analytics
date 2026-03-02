SELECT
  channel,
  COUNT(*) FILTER (WHERE status='completed') AS completed_orders,
  ROUND(AVG(net_revenue) FILTER (WHERE status='completed'), 2) AS avg_order_value_net,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status='cancelled') / NULLIF(COUNT(*),0), 2) AS cancel_rate_pct
FROM v_order_net_revenue
GROUP BY 1
ORDER BY completed_orders DESC;