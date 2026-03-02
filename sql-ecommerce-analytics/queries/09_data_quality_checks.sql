-- 1) Orphans
SELECT COUNT(*) AS orphan_orders
FROM orders o LEFT JOIN customers c ON c.customer_id=o.customer_id
WHERE c.customer_id IS NULL;

SELECT COUNT(*) AS orphan_items
FROM order_items oi
LEFT JOIN orders o ON o.order_id=oi.order_id
LEFT JOIN products p ON p.product_id=oi.product_id
WHERE o.order_id IS NULL OR p.product_id IS NULL;

-- 2) Returns must be completed
SELECT COUNT(*) AS bad_returns
FROM returns r JOIN orders o ON o.order_id=r.order_id
WHERE o.status <> 'completed';

-- 3) Refund should not exceed paid
SELECT COUNT(*) AS refund_overpaid
FROM returns r JOIN payments p ON p.order_id=r.order_id
WHERE r.refund_amount > p.paid_amount + 0.01;