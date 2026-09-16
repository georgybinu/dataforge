"""Transform validated Silver retail orders into Gold analytics datasets."""

from pathlib import Path
from typing import Dict

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import avg, col, count, sum, to_date
from pyspark.sql.types import DecimalType, LongType


APP_NAME = "DataForge-Silver-to-Gold"
SILVER_INPUT_PATH = Path("data/silver/orders_valid.parquet")
GOLD_OUTPUT_PATHS = {
    "daily_sales": Path("data/gold/daily_sales"),
    "product_metrics": Path("data/gold/product_metrics"),
    "customer_metrics": Path("data/gold/customer_metrics"),
    "store_metrics": Path("data/gold/store_metrics"),
}


def create_spark_session() -> SparkSession:
    """Create a SparkSession for the Silver-to-Gold transformation job."""
    return (
        SparkSession.builder.appName(APP_NAME)
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def load_silver_orders(spark: SparkSession, input_path: Path) -> DataFrame:
    """Load validated Silver orders from Parquet."""
    if not input_path.exists():
        raise FileNotFoundError(f"Silver input file not found: {input_path}")

    return spark.read.parquet(str(input_path))


def transform_orders(orders: DataFrame) -> DataFrame:
    """Prepare Silver orders with typed fields and derived revenue."""
    quantity_column = col("quantity").cast(LongType())
    unit_price_column = col("unit_price").cast(DecimalType(12, 2))

    return (
        orders.withColumn("quantity", quantity_column)
        .withColumn("unit_price", unit_price_column)
        .withColumn("order_date", to_date(col("order_date"), "yyyy-MM-dd"))
        .withColumn(
            "total_amount",
            (col("quantity").cast(DecimalType(12, 2)) * col("unit_price")).cast(
                DecimalType(14, 2)
            ),
        )
        .select(
            "order_id",
            "customer_id",
            "product_id",
            "store_id",
            "order_date",
            "quantity",
            "unit_price",
            "total_amount",
        )
    )


def build_daily_sales(orders: DataFrame) -> DataFrame:
    """Aggregate daily sales metrics."""
    return (
        orders.groupBy("order_date")
        .agg(
            count("order_id").alias("total_orders"),
            sum("quantity").alias("total_quantity"),
            sum("total_amount").alias("total_revenue"),
            avg("total_amount").alias("average_order_value"),
        )
        .orderBy("order_date")
    )


def build_product_metrics(orders: DataFrame) -> DataFrame:
    """Aggregate product-level sales metrics."""
    return (
        orders.groupBy("product_id")
        .agg(
            count("order_id").alias("total_orders"),
            sum("quantity").alias("total_quantity"),
            sum("total_amount").alias("total_revenue"),
            avg("unit_price").alias("average_unit_price"),
        )
        .orderBy("product_id")
    )


def build_customer_metrics(orders: DataFrame) -> DataFrame:
    """Aggregate customer-level sales metrics."""
    return (
        orders.groupBy("customer_id")
        .agg(
            count("order_id").alias("total_orders"),
            sum("quantity").alias("total_quantity"),
            sum("total_amount").alias("total_revenue"),
            avg("total_amount").alias("average_order_value"),
        )
        .orderBy("customer_id")
    )


def build_store_metrics(orders: DataFrame) -> DataFrame:
    """Aggregate store-level sales metrics."""
    return (
        orders.groupBy("store_id")
        .agg(
            count("order_id").alias("total_orders"),
            sum("quantity").alias("total_quantity"),
            sum("total_amount").alias("total_revenue"),
            avg("total_amount").alias("average_order_value"),
        )
        .orderBy("store_id")
    )


def write_gold_dataset(dataframe: DataFrame, output_path: Path) -> None:
    """Write a Gold dataset as Parquet in overwrite mode."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.write.mode("overwrite").parquet(str(output_path))


def build_gold_datasets(orders: DataFrame) -> Dict[str, DataFrame]:
    """Build all Gold analytics datasets from transformed orders."""
    return {
        "daily_sales": build_daily_sales(orders),
        "product_metrics": build_product_metrics(orders),
        "customer_metrics": build_customer_metrics(orders),
        "store_metrics": build_store_metrics(orders),
    }


def main() -> None:
    """Run the Silver-to-Gold Spark transformation job."""
    spark = None

    try:
        print("DataForge Spark transformation started")

        if not SILVER_INPUT_PATH.exists():
            raise FileNotFoundError(f"Silver input file not found: {SILVER_INPUT_PATH}")

        spark = create_spark_session()
        silver_orders = load_silver_orders(spark, SILVER_INPUT_PATH)

        input_record_count = silver_orders.count()
        print(f"Input records: {input_record_count}")
        print("Input schema:")
        silver_orders.printSchema()

        transformed_orders = transform_orders(silver_orders)
        gold_datasets = build_gold_datasets(transformed_orders)

        for dataset_name, dataframe in gold_datasets.items():
            record_count = dataframe.count()
            readable_name = dataset_name.replace("_", " ")
            print(f"{readable_name.title()} records: {record_count}")
            write_gold_dataset(dataframe, GOLD_OUTPUT_PATHS[dataset_name])

        print("Gold datasets written successfully")
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    main()
