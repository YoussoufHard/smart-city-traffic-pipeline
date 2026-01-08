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

# Enriched sensor list to meet assignment requirements
SENSOR_LOCATIONS = [
    {"sensor_id": "S-001", "road_id": "R-001", "road_type": "autoroute", "zone": "Secteur-Nord", "lat": 48.8566, "lon": 2.3522},
    {"sensor_id": "S-002", "road_id": "R-002", "road_type": "avenue", "zone": "Secteur-Centre", "lat": 48.8606, "lon": 2.3376},
    {"sensor_id": "S-003", "road_id": "R-003", "road_type": "rue", "zone": "Secteur-Sud", "lat": 48.8530, "lon": 2.3499},
    {"sensor_id": "S-004", "road_id": "R-004", "road_type": "autoroute", "zone": "Secteur-Nord", "lat": 48.8588, "lon": 2.3200},
    {"sensor_id": "S-005", "road_id": "R-005", "road_type": "avenue", "zone": "Secteur-Est", "lat": 48.8647, "lon": 2.3780},
]

def get_traffic_density():
    """Returns a multiplier (0.1 to 1.0) based on time of day to simulate peak hours."""
    hour = datetime.datetime.now().hour
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        return 0.9 # Peak
    elif 10 <= hour <= 16:
        return 0.6 # Normal day
    else:
        return 0.2 # Night

def generate_event(sensor):
    traffic_factor = get_traffic_density()
    
    # Values generation
    # Peak hour = slower speeds + more vehicles.
    if traffic_factor > 0.8:
        speed = random.normalvariate(20, 10) # Congestion
        vehicle_count = random.randint(50, 150)
    else:
        speed = random.normalvariate(60, 15)
        vehicle_count = random.randint(5, 40)
    
    speed = max(5, speed)
    occupancy = min(100, (vehicle_count / 200) * 100 + random.uniform(0, 10))
    
    return {
        "sensor_id": sensor["sensor_id"],
        "road_id": sensor["road_id"],
        "road_type": sensor["road_type"],
        "zone": sensor["zone"],
        "vehicle_count": vehicle_count,
        "average_speed": round(speed, 2),
        "occupancy_rate": round(occupancy, 2),
        "event_time": datetime.datetime.now().isoformat(),
        "location": {"lat": sensor["lat"], "lon": sensor["lon"]} # Added for Viz
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
