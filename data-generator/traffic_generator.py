import json
import time
import random
import uuid
import datetime
from kafka import KafkaProducer
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os

# Constants
TOPIC_NAME = "traffic-events"
BOOTSTRAP_SERVERS = os.getenv('BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
SENSOR_LOCATIONS = [
    {"sensor_id": "S-001", "lat": 48.8566, "lon": 2.3522}, # Paris
    {"sensor_id": "S-002", "lat": 48.8606, "lon": 2.3376},
    {"sensor_id": "S-003", "lat": 48.8530, "lon": 2.3499},
    {"sensor_id": "S-004", "lat": 48.8588, "lon": 2.3200},
    {"sensor_id": "S-005", "lat": 48.8647, "lon": 2.3780},
    {"sensor_id": "S-006", "lat": 34.0208, "lon": -6.8416}, # Rabat
    {"sensor_id": "S-007", "lat": 33.5731, "lon": -7.5898}, # Casablanca
]

def get_traffic_density():
    """Returns a multiplier (0.1 to 1.0) based on time of day to simulate peak hours."""
    hour = datetime.datetime.now().hour
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        return 1.0 # Peak
    elif 10 <= hour <= 16:
        return 0.7 # Normal day
    else:
        return 0.2 # Night

def generate_event(sensor):
    traffic_factor = get_traffic_density()
    
    # Speed is inversely proportional to traffic density (simplified)
    # Peak hour = slower speeds.
    base_speed = 50 # km/h
    if traffic_factor > 0.8:
        speed = random.normalvariate(15, 5) # Congestion
    else:
        speed = random.normalvariate(base_speed, 10)
    
    speed = max(0, speed)
    
    return {
        "event_id": str(uuid.uuid4()),
        "sensor_id": sensor["sensor_id"],
        "location": {"lat": sensor["lat"], "lon": sensor["lon"]},
        "timestamp": datetime.datetime.now().isoformat(),
        "vehicle_type": random.choice(["car", "car", "car", "truck", "bus", "motorcycle"]),
        "speed": round(speed, 2),
        "traffic_density_factor": traffic_factor
    }

def main():
    parser = argparse.ArgumentParser(description="Traffic Data Generator")
    parser.add_argument("--rate", type=float, default=1.0, help="Events per second per sensor")
    args = parser.parse_args()

    producer = None
    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Connected to Kafka")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return

    logger.info(f"Starting data generation. Press Ctrl+C to stop.")
    try:
        while True:
            for sensor in SENSOR_LOCATIONS:
                event = generate_event(sensor)
                producer.send(TOPIC_NAME, event)
                # logger.info(f"Sent: {event}") # Uncomment to see logs
            
            time.sleep(1 / args.rate)
            
    except KeyboardInterrupt:
        logger.info("Stopping generator...")
    finally:
        if producer:
            producer.close()

if __name__ == "__main__":
    main()
