SELECT
    records_received,
    records_valid,
    records_rejected,
    rejection_rate,
    status,
    pipeline_name,
    start_time,
    end_time
FROM pipeline_metrics
ORDER BY TRY_CAST(end_time AS TIMESTAMP) DESC
LIMIT 1
