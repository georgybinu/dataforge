SELECT
    store_id,
    total_orders,
    total_revenue AS total_sales
FROM store_metrics
WHERE (? IS NULL OR store_id = ?)
ORDER BY total_sales DESC, store_id
