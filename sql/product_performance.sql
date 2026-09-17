SELECT
    product_id,
    total_quantity,
    total_revenue AS total_sales,
    average_unit_price,
    total_orders,
    CASE
        WHEN total_orders = 0 THEN 0.0
        ELSE total_revenue / total_orders
    END AS average_order_value
FROM product_metrics
WHERE (? IS NULL OR product_id = ?)
ORDER BY total_sales DESC, product_id
