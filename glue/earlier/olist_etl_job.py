from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql.functions import col, year, month

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

bucket = "YOUR_BUCKET_NAME"  # my real bucket name removed; not used by the deployed job

# -------------------------
# ORDERS (FACT TABLE)
# -------------------------
orders = spark.read.option("header", "true").csv(f"s3://{bucket}/incoming/orders/")

orders = orders.withColumn(
    "order_purchase_timestamp",
    col("order_purchase_timestamp").cast("timestamp")
)

orders = orders.withColumn("year", year("order_purchase_timestamp")) \
               .withColumn("month", month("order_purchase_timestamp"))

orders.write.mode("overwrite") \
    .partitionBy("year", "month") \
    .parquet(f"s3://{bucket}/processed/orders/")

# -------------------------
# DIMENSION TABLES
# -------------------------
tables = [
    "customers",
    "order_items",
    "payments",
    "products",
    "reviews",
    "sellers"
]

for table in tables:
    df = spark.read.option("header", "true").csv(f"s3://{bucket}/incoming/{table}/")
    
    df.write.mode("overwrite") \
        .parquet(f"s3://{bucket}/processed/{table}/")

print("✅ FULL PIPELINE EXECUTED SUCCESSFULLY")