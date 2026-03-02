WITH first_purchase AS (
  SELECT customer_id, date_trunc('month', MIN(order_date)) AS cohort_month
  FROM orders
  WHERE status='completed'
  GROUP BY 1
),
activity AS (
  SELECT customer_id, date_trunc('month', order_date) AS active_month
  FROM orders
  WHERE status='completed'
),
cohort_activity AS (
  SELECT
    f.cohort_month,
    a.active_month,
    (EXTRACT(YEAR FROM a.active_month) - EXTRACT(YEAR FROM f.cohort_month)) * 12
      + (EXTRACT(MONTH FROM a.active_month) - EXTRACT(MONTH FROM f.cohort_month)) AS month_index,
    COUNT(DISTINCT a.customer_id) AS active_customers
  FROM first_purchase f
  JOIN activity a ON a.customer_id = f.customer_id
  GROUP BY 1,2,3
),
cohort_size AS (
  SELECT cohort_month, COUNT(*) AS cohort_customers
  FROM first_purchase
  GROUP BY 1
)
SELECT
  ca.cohort_month,
  ca.month_index,
  cs.cohort_customers,
  ca.active_customers,
  ROUND(100.0 * ca.active_customers / NULLIF(cs.cohort_customers,0), 2) AS retention_pct
FROM cohort_activity ca
JOIN cohort_size cs USING (cohort_month)
WHERE ca.month_index BETWEEN 0 AND 6
ORDER BY ca.cohort_month, ca.month_index;