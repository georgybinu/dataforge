SELECT
    customer_id,
    total_orders,
    total_revenue AS total_sales
FROM customer_metrics
ORDER BY total_sales DESC, customer_id
