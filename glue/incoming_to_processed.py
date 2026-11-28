import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType, IntegerType

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# Changed from the version I ran: the bucket name now comes from a job argument
# instead of being written into the script.
args = getResolvedOptions(sys.argv, ["JOB_NAME", "BUCKET"])
job.init(args["JOB_NAME"], args)
BUCKET = args["BUCKET"]

SCHEMAS = {
    "orders": StructType([
        StructField("order_id", StringType()),
        StructField("customer_id", StringType()),
        StructField("order_status", StringType()),
        StructField("order_purchase_timestamp", StringType()),
        StructField("order_approved_at", StringType()),
        StructField("order_delivered_carrier_date", StringType()),
        StructField("order_delivered_customer_date", StringType()),
        StructField("order_estimated_delivery_date", StringType()),
        StructField("date", StringType()),
    ]),
    "customers": StructType([
        StructField("customer_id", StringType()),
        StructField("customer_unique_id", StringType()),
        StructField("customer_zip_code_prefix", StringType()),
        StructField("customer_city", StringType()),
        StructField("customer_state", StringType()),
        StructField("date", StringType()),
    ]),
    "order_items": StructType([
        StructField("order_id", StringType()),
        StructField("order_item_id", StringType()),
        StructField("product_id", StringType()),
        StructField("seller_id", StringType()),
        StructField("shipping_limit_date", StringType()),
        StructField("price", DoubleType()),
        StructField("freight_value", DoubleType()),
        StructField("date", StringType()),
    ]),
    "payments": StructType([
        StructField("order_id", StringType()),
        StructField("payment_sequential", IntegerType()),
        StructField("payment_type", StringType()),
        StructField("payment_installments", IntegerType()),
        StructField("payment_value", DoubleType()),
        StructField("date", StringType()),
    ]),
    "products": StructType([
        StructField("product_id", StringType()),
        StructField("product_category_name", StringType()),
        StructField("product_name_length", IntegerType()),
        StructField("product_description_length", IntegerType()),
        StructField("product_photos_qty", IntegerType()),
        StructField("product_weight_g", DoubleType()),
        StructField("product_length_cm", DoubleType()),
        StructField("product_height_cm", DoubleType()),
        StructField("product_width_cm", DoubleType()),
        StructField("date", StringType()),
    ]),
    "reviews": StructType([
        StructField("review_id", StringType()),
        StructField("order_id", StringType()),
        StructField("review_score", IntegerType()),
        StructField("review_comment_title", StringType()),
        StructField("review_comment_message", StringType()),
        StructField("review_creation_date", StringType()),
        StructField("review_answer_timestamp", StringType()),
        StructField("date", StringType()),
    ]),
    "sellers": StructType([
        StructField("seller_id", StringType()),
        StructField("seller_zip_code_prefix", StringType()),
        StructField("seller_city", StringType()),
        StructField("seller_state", StringType()),
        StructField("date", StringType()),
    ]),
}

TABLES = ["customers", "orders", "order_items", "payments", "products", "reviews", "sellers"]

for table in TABLES:
    input_path = f"s3://{BUCKET}/incoming/{table}/"
    output_path = f"s3://{BUCKET}/processed/{table}/"
    print(f"Processing {table}")
    try:
        schema = SCHEMAS[table]
        df = spark.read.option(
            "recursiveFileLookup", "true"
        ).schema(schema).csv(input_path)
        if len(df.columns) > 0:
            df = df.dropDuplicates()
            df.write.mode("overwrite").parquet(output_path)
            print(f"{table} written successfully")
    except Exception as e:
        print(f"Skipping {table}: {str(e)}")

job.commit()