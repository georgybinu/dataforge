SELECT
    order_date,
    total_revenue AS total_sales,
    total_orders AS order_count
FROM daily_sales
WHERE (? IS NULL OR order_date >= ?)
  AND (? IS NULL OR order_date <= ?)
ORDER BY order_date
