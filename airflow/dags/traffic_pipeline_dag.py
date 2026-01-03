from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'traffic_pipeline',
    default_args=default_args,
    description='Pipeline for Smart City Traffic Data',
    schedule_interval=timedelta(minutes=5),
    start_date=days_ago(1),
    catchup=False,
)

# This assumes Airflow has Spark client installed or connection configured. 
# For current setup (Bitnami Spark + Apache Airflow), direct SparkSubmitOperator 
# requires binaries. 
# SIMPLIFIED APPROACH for Demo: 
# We assume the user configures the 'spark_default' connection to point to Spark Master.
# However, without local binaries, SparkSubmitOperator fails in standard Airflow image.
# Alternative: Use SimpleHttpOperator to trigger livy? (Too complex setup)
# Alternative: Use DockerOperator (needs docker socket mount)
# Alternative: Run script in Airflow that communicates with Spark Master via REST (port 6066)

# We will try the SparkSubmitOperator. If it fails, we fall back.
# Note: In a real 'Devoir', we might assume Airflow runs on a node that has Spark.

process_traffic = SparkSubmitOperator(
    task_id='process_traffic_spark',
    application='/opt/spark-apps/traffic_processing.py', # We need to mount this!
    conn_id='spark_default',
    conf={'spark.master': 'spark://spark-master:7077'},
    dag=dag,
)

process_traffic
