from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, avg, count
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import sys

# Schema matching the new JSON required by assignment
schema = StructType([
    StructField("sensor_id", StringType(), True),
    StructField("road_id", StringType(), True),
    StructField("road_type", StringType(), True),
    StructField("zone", StringType(), True),
    StructField("vehicle_count", DoubleType(), True),
    StructField("average_speed", DoubleType(), True),
    StructField("occupancy_rate", DoubleType(), True),
    StructField("event_time", TimestampType(), True)
])

def main():
    spark = SparkSession.builder \
        .appName("TrafficProcessing") \
        .getOrCreate()

    # Read from HDFS partitioned by date and zone
    input_path = "hdfs://namenode:9000/data/raw/traffic/*/*/*"
    
    df = spark.read.json(input_path) 
    
    if df.count() == 0:
        print("DEBUG: No data to process. Exiting.")
        return

    # Cast event_time if read as string
    if dict(df.dtypes)['event_time'] == 'string':
         df = df.withColumn("event_time", col("event_time").cast("timestamp"))
            
    # Compute Aggregates
    # 1. Traffic moyen par zone
    zone_stats = df.groupBy("zone", window("event_time", "5 minutes")) \
        .agg(
            avg("vehicle_count").alias("avg_traffic"),
            avg("average_speed").alias("avg_speed"),
            avg("occupancy_rate").alias("avg_occupancy")
        ) \
        .withColumn("window_start", col("window.start")) \
        .drop("window")

    # 2. Vitesse moyenne par route
    road_stats = df.groupBy("road_id", "road_type", "zone") \
        .agg(avg("average_speed").alias("road_avg_speed"))

    # Add congestion flag based on occupancy or speed
    from pyspark.sql.functions import when
    zone_stats = zone_stats.withColumn("status", 
                                      when(col("avg_occupancy") > 70, "CONGESTION")
                                      .otherwise("FLUID"))

    # Write Results to HDFS (Analytics Zone) - Format Parquet
    output_path = "hdfs://namenode:9000/data/analytics/traffic"
    zone_stats.write.mode("append").parquet(output_path)
    
    # Write to Postgres for Grafana
    jdbc_url = "jdbc:postgresql://postgres:5432/airflow" 
    props = {
        "user": "airflow",
        "password": "airflow",
        "driver": "org.postgresql.Driver"
    }
    
    zone_stats.write.mode("append").jdbc(jdbc_url, "traffic_stats_zone", properties=props)
    road_stats.write.mode("append").jdbc(jdbc_url, "traffic_stats_road", properties=props)

    print("Job completed successfully.")
    spark.stop()

if __name__ == "__main__":
    main()
