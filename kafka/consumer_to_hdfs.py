from kafka import KafkaConsumer
from hdfs import InsecureClient
import json
import time
import os
import datetime
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
KAFKA_TOPIC = "traffic-events"
BOOTSTRAP_SERVERS = os.getenv('BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
HDFS_URL = os.getenv('HDFS_URL', "http://localhost:9870") # WebHDFS
HDFS_USER = "root"
BUFFER_SIZE = 100
FLUSH_INTERVAL = 60 # seconds

def get_hdfs_client():
    try:
        return InsecureClient(HDFS_URL, user=HDFS_USER)
    except Exception as e:
        logger.error(f"Could not connect to HDFS: {e}")
        return None

def flush_to_hdfs(client, buffer, zone="unknown"):
    if not buffer:
        return
    
    # Partition by Date and Zone
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    hdfs_path = f"/data/raw/traffic/date={today}/zone={zone}"
    
    # Create filename with timestamp
    filename = f"traffic_data_{int(time.time())}_{random.randint(0,1000)}.json"
    full_path = f"{hdfs_path}/{filename}"
    
    data_str = "\n".join([json.dumps(r) for r in buffer])
    
    try:
        # Client writes create the necessary directories
        with client.write(full_path, encoding='utf-8') as writer:
            writer.write(data_str)
        logger.info(f"Flushed {len(buffer)} records to {full_path}")
    except Exception as e:
        logger.error(f"Failed to write to HDFS: {e}")

def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='hdfs-archiver',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    client = get_hdfs_client()
    while not client:
        logger.warning("Waiting for HDFS...")
        time.sleep(5)
        client = get_hdfs_client()

    # Buffering by zone
    buffers = {} # {zone: [records]}
    last_flush = time.time()

    logger.info("Starting Kafka to HDFS consumer with Zone Partitioning...")
    
    for message in consumer:
        event = message.value
        zone = event.get("zone", "unknown")
        
        if zone not in buffers:
            buffers[zone] = []
        
        buffers[zone].append(event)
        
        current_time = time.time()
        # Flush if any buffer is big or interval passed
        total_records = sum(len(b) for b in buffers.values())
        if total_records >= BUFFER_SIZE or (current_time - last_flush) >= FLUSH_INTERVAL:
            for z, b in buffers.items():
                if b:
                    flush_to_hdfs(client, b, z)
            buffers = {}
            last_flush = current_time

if __name__ == "__main__":
    main()
