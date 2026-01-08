from airflow import DAG
from airflow.operators.bash import BashOperator
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
    description='Pipeline for Smart City Traffic Data (Sidecar Pattern)',
    schedule_interval=timedelta(minutes=5),
    start_date=days_ago(1),
    catchup=False,
)

# Step 1: Cleanup old data using docker exec on namenode
cleanup_hdfs = BashOperator(
    task_id='cleanup_old_hdfs_data',
    bash_command='''
    # Delete data older than 3 days in HDFS
    # Note: Using docker exec to run directly on the namenode
    docker exec namenode hdfs dfs -rm -r -f /data/raw/traffic/date=$(date -d "3 days ago" +%Y-%m-%d) || true
    ''',
    dag=dag,
)

# Step 2: Process traffic using docker exec on spark-master
process_traffic = BashOperator(
    task_id='process_traffic_spark',
    bash_command='''
    docker exec spark-master /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --jars /opt/spark/jars/postgresql-42.2.18.jar \
        /opt/spark-apps/traffic_processing.py
    ''',
    dag=dag,
)

cleanup_hdfs >> process_traffic
