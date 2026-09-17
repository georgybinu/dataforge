SELECT
    SUM(total_revenue) AS total_sales,
    SUM(total_orders) AS total_orders,
    CASE
        WHEN SUM(total_orders) = 0 THEN 0.0
        ELSE SUM(total_revenue) / SUM(total_orders)
    END AS average_order_value
FROM daily_sales
