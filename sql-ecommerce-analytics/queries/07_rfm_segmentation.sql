WITH base AS (
  SELECT
    o.customer_id,
    MAX(o.order_date) AS last_order_date,
    COUNT(DISTINCT o.order_id) AS frequency,
    SUM(p.paid_amount - COALESCE(r.refund_amount,0)) AS monetary
  FROM orders o
  JOIN payments p ON p.order_id = o.order_id AND p.status IN ('captured','authorized')
  LEFT JOIN returns r ON r.order_id = o.order_id
  WHERE o.status='completed'
  GROUP BY 1
),
scored AS (
  SELECT
    b.*,
    (CURRENT_DATE - b.last_order_date::date) AS recency_days,
    NTILE(5) OVER (ORDER BY (CURRENT_DATE - b.last_order_date::date) ASC) AS r_score,
    NTILE(5) OVER (ORDER BY b.frequency DESC) AS f_score,
    NTILE(5) OVER (ORDER BY b.monetary DESC) AS m_score
  FROM base b
),
seg AS (
  SELECT
    *,
    CASE
      WHEN r_score>=4 AND f_score>=4 AND m_score>=4 THEN 'VIP'
      WHEN r_score>=4 AND (f_score>=3 OR m_score>=3) THEN 'Loyal'
      WHEN r_score<=2 AND (f_score>=4 OR m_score>=4) THEN 'At Risk'
      WHEN r_score<=2 AND f_score<=2 AND m_score<=2 THEN 'Lost'
      ELSE 'Potential'
    END AS segment
  FROM scored
)
SELECT
  segment,
  COUNT(*) AS customers,
  ROUND(AVG(recency_days),1) AS avg_recency_days,
  ROUND(AVG(frequency),2) AS avg_frequency,
  ROUND(AVG(monetary),2) AS avg_monetary
FROM seg
GROUP BY 1
ORDER BY customers DESC;