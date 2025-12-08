"""Queue service for processing queue entries."""
import json
from typing import Dict, Any, List, Optional
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import threading
import time
from datetime import datetime

# Import utilities
from utils.config import KAFKA_BROKER
from utils.data_persistence import load_dict_data, save_dict_data
from utils.logger_config import setup_logger

# Setup logger
logger = setup_logger(__name__, "queue_service.log")

# Queue management data
active_queue: Dict[str, Any] = {}
processed_queue: Dict[str, Any] = {}

# Load data from persistence
def load_data():
    """Load queue data from JSON files."""
    global active_queue, processed_queue
    
    # Load active queue
    queue_data = load_dict_data("queue")
    active_queue = {k: v for k, v in queue_data.items() if v.get("status") in ["waiting", "processing"]}
    
    # Load processed queue (from bookings or separate file)
    processed_queue = {}
    
    logger.info(f"Loaded {len(active_queue)} active queue entries")

def save_queue():
    """Save queue data to JSON file."""
    # Save active queue
    if save_dict_data("queue", active_queue):
        logger.debug("Queue saved successfully")
    else:
        logger.error("Failed to save queue")

# Load on startup
load_data()

# Configure Kafka consumer with retry logic
def create_kafka_consumer():
    """Create Kafka consumer with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                'booking-created',
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='queue-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info("Kafka consumer connected successfully")
            return consumer
        except Exception as e:
            logger.warning(f"Kafka connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("Failed to connect to Kafka after retries")
                return None

# Configure Kafka producer with retry logic
def create_kafka_producer():
    """Create Kafka producer with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=3,
                acks='all'
            )
            logger.info("Kafka producer connected successfully")
            return producer
        except Exception as e:
            logger.warning(f"Kafka producer connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("Failed to connect to Kafka producer after retries")
                raise

consumer = create_kafka_consumer()
producer = create_kafka_producer()

def handle_queue_update(queue_entry: Dict[str, Any]):
    """
    Handle a queue update by updating the queue status and notifying clients.
    
    Args:
        queue_entry: Queue entry data
    """
    try:
        queue_id = queue_entry.get("queue_id")
        if not queue_id:
            return
        
        active_queue[queue_id] = queue_entry
        
        # Save to persistence
        save_queue()
        
        # Send notification about updated queue status
        try:
            producer.send('queue-updated', {
                "event_type": "queue_status_changed",
                "data": {
                    "queue_id": queue_id,
                    "client_id": queue_entry.get("client_id"),
                    "status": queue_entry.get("status", "waiting"),
                    "position": get_queue_position(queue_id),
                    "estimated_wait": get_estimated_wait(queue_id),
                    "timestamp": datetime.now().isoformat()
                }
            })
            producer.flush()
        except KafkaError as e:
            logger.error(f"Failed to send Kafka message: {e}")
        
        logger.info(f"Queue updated: {queue_id}")
    except Exception as e:
        logger.error(f"Error handling queue update: {e}", exc_info=True)

def handle_booking_created(booking: Dict[str, Any]):
    """
    Handle a new booking by adding it to the queue system.
    
    Args:
        booking: Booking data
    """
    try:
        # For bookings that are for future dates, we don't add them to active queue
        if "booking_date" in booking and "booking_time" in booking:
            # This is a scheduled booking, not a queue entry
            logger.debug(f"Received scheduled booking: {booking.get('booking_id')}")
            return
        
        # Otherwise process as a queue entry
        handle_queue_update(booking)
    except Exception as e:
        logger.error(f"Error handling booking created: {e}", exc_info=True)

def get_queue_position(queue_id: str) -> Optional[int]:
    """
    Get position in queue (starting from 1).
    
    Args:
        queue_id: Queue entry ID
        
    Returns:
        Position in queue or None if not found
    """
    try:
        sorted_queue = sorted(
            active_queue.values(),
            key=lambda x: x.get("timestamp", "")
        )
        
        for i, entry in enumerate(sorted_queue):
            if entry.get("queue_id") == queue_id:
                return i + 1
        
        return None
    except Exception as e:
        logger.error(f"Error getting queue position: {e}", exc_info=True)
        return None

def get_estimated_wait(queue_id: str) -> Optional[int]:
    """
    Estimate wait time based on position (5 mins per person).
    
    Args:
        queue_id: Queue entry ID
        
    Returns:
        Estimated wait time in minutes or None
    """
    try:
        position = get_queue_position(queue_id)
        if position is None:
            return None
        
        # Each client takes about 5 minutes
        return position * 5
    except Exception as e:
        logger.error(f"Error getting estimated wait: {e}", exc_info=True)
        return None

def process_queue_periodically():
    """Simulate queue processing - every 30 seconds, move the first client forward."""
    logger.info("Queue processing thread started")
    
    while True:
        try:
            time.sleep(30)  # Process every 30 seconds
            
            # Sort queue by timestamp
            sorted_queue = sorted(
                active_queue.values(),
                key=lambda x: x.get("timestamp", "")
            )
            
            if not sorted_queue:
                continue
            
            # Get the first waiting client
            waiting_clients = [
                q for q in sorted_queue
                if q.get("status") == "waiting"
            ]
            if not waiting_clients:
                continue
            
            next_client = waiting_clients[0]
            queue_id = next_client.get("queue_id")
            
            if not queue_id:
                continue
            
            # Update status
            active_queue[queue_id]["status"] = "processing"
            save_queue()
            
            # Notify about the update
            try:
                producer.send('queue-updated', {
                    "event_type": "queue_status_changed",
                    "data": {
                        "queue_id": queue_id,
                        "client_id": next_client.get("client_id"),
                        "status": "processing",
                        "timestamp": datetime.now().isoformat()
                    }
                })
                producer.flush()
            except KafkaError as e:
                logger.error(f"Failed to send Kafka message: {e}")
            
            logger.info(f"Processing client: {queue_id}")
            
            # Simulate service time (in real system, barber would mark as completed)
            time.sleep(10)  # For demo, use shorter time
            
            # Mark as completed
            active_queue[queue_id]["status"] = "completed"
            active_queue[queue_id]["completed_at"] = datetime.now().isoformat()
            
            # Move to processed queue
            processed_queue[queue_id] = active_queue[queue_id]
            del active_queue[queue_id]
            save_queue()
            
            # Notify about completion
            try:
                producer.send('queue-updated', {
                    "event_type": "queue_status_changed",
                    "data": {
                        "queue_id": queue_id,
                        "client_id": next_client.get("client_id"),
                        "status": "completed",
                        "timestamp": datetime.now().isoformat()
                    }
                })
                producer.flush()
            except KafkaError as e:
                logger.error(f"Failed to send Kafka message: {e}")
            
            logger.info(f"Completed client: {queue_id}")
            
            # Recalculate and notify all waiting clients about their new positions
            for entry in active_queue.values():
                if entry.get("status") == "waiting":
                    try:
                        producer.send('queue-updated', {
                            "event_type": "queue_status_changed",
                            "data": {
                                "queue_id": entry.get("queue_id"),
                                "client_id": entry.get("client_id"),
                                "status": entry.get("status"),
                                "position": get_queue_position(entry.get("queue_id")),
                                "estimated_wait": get_estimated_wait(entry.get("queue_id")),
                                "timestamp": datetime.now().isoformat()
                            }
                        })
                    except KafkaError as e:
                        logger.error(f"Failed to send Kafka message: {e}")
            
            producer.flush()
        except Exception as e:
            logger.error(f"Error in queue processing: {e}", exc_info=True)
            time.sleep(5)  # Wait before retrying

def main():
    """Main function to start queue service."""
    # Start queue processing in a separate thread
    processing_thread = threading.Thread(target=process_queue_periodically, daemon=True)
    processing_thread.start()
    
    if not consumer:
        logger.warning("Kafka consumer not available, queue service will not process messages")
        # Keep the service running for queue processing
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Queue service shutting down")
        return
    
    logger.info("Queue service started. Listening for messages...")
    
    # Main loop to process messages
    try:
        for message in consumer:
            try:
                data = message.value
                event_type = data.get("event_type")
                payload = data.get("data")
                
                if event_type == "queue_created":
                    handle_queue_update(payload)
                elif event_type == "booking_created":
                    handle_booking_created(payload)
                else:
                    logger.debug(f"Unknown event type: {event_type}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Queue service shutting down")
    except Exception as e:
        logger.error(f"Queue service error: {e}", exc_info=True)
    finally:
        save_queue()
        if producer:
            producer.close()
        if consumer:
            consumer.close()

if __name__ == "__main__":
    main()
