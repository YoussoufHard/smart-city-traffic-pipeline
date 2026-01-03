from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, avg, count
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import sys

# Schema matching the JSON from generator
schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("sensor_id", StringType(), True),
    StructField("location", StringType(), True), # Struct simplified to string or complex
    StructField("timestamp", TimestampType(), True),
    StructField("vehicle_type", StringType(), True),
    StructField("speed", DoubleType(), True),
    StructField("traffic_density_factor", DoubleType(), True)
])

def main():
    spark = SparkSession.builder \
        .appName("TrafficProcessing") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.2.18") \
        .getOrCreate()

    # Read from HDFS (Assuming we process a specific date or * all)
    # in production we pass date as arg
    input_path = "hdfs://namenode:9000/data/raw/traffic/*/*"
    
    df = spark.read.json(input_path) # Schema inference or apply schema
    # Better to apply schema if possible, but json inference works for simple demo
    
    # Cast timestamp if read as string
    if dict(df.dtypes)['timestamp'] == 'string':
         df = df.withColumn("timestamp", col("timestamp").cast("timestamp"))
            
    # Compute Aggregates
    # Group by sensor and 1-minute window
    stats = df.groupBy("sensor_id", window("timestamp", "1 minute")) \
        .agg(
            avg("speed").alias("avg_speed"),
            count("event_id").alias("vehicle_count")
        ) \
        .withColumn("window_start", col("window.start")) \
        .drop("window")

    # Add congestion flag
    stats = stats.withColumn("status", \
                             from_json(col("avg_speed") < 30, StringType())) # Logic: < 30km/h = CONGESTION?
    # Simple case statement
    # from pyspark.sql.functions import when
    # stats = stats.withColumn("status", when(col("avg_speed") < 30, "CONGESTION").otherwise("FLUID"))

    # Write to Parquet (HDFS)
    output_path = "hdfs://namenode:9000/data/analytics/traffic"
    stats.write.mode("append").parquet(output_path)
    
    # Write to Postgres (for Grafana)
    jdbc_url = "jdbc:postgresql://postgres:5432/airflow" # Reusing DB for demo simplicity
    props = {
        "user": "airflow",
        "password": "airflow",
        "driver": "org.postgresql.Driver"
    }
    
    stats.write.mode("append").jdbc(jdbc_url, "traffic_stats", properties=props)

    print("Job completed successfully.")
    spark.stop()

if __name__ == "__main__":
    main()
