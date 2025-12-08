"""Barber service for managing barbers and services."""
import json
import uvicorn
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import threading
import uuid
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import utilities
from utils.config import KAFKA_BROKER, BARBER_SERVICE_PORT
from utils.data_persistence import (
    load_dict_data, save_dict_data,
    load_list_data, save_list_data
)
from utils.logger_config import setup_logger
from utils.security import sanitize_input
from utils.models import BarberCreate

# Setup logger
logger = setup_logger(__name__, "barber_service.log")

# Define FastAPI app
app = FastAPI(
    title="Barber Service",
    description="Service for managing barbers and services",
    version="2.0.0"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configure Kafka consumer
def create_kafka_consumer():
    """Create Kafka consumer with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                "feedback-submitted",
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='barber-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info("Kafka consumer connected successfully")
            return consumer
        except Exception as e:
            logger.warning(f"Kafka consumer connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("Failed to connect to Kafka consumer after retries")
                return None

# Configure Kafka producer
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
                logger.error("Failed to connect to Kafka producer after retries. Continuing without Kafka.")
                return None

consumer = create_kafka_consumer()
producer = create_kafka_producer()

# Load data from persistence
def load_data():
    """Load barbers, services, and feedback data from JSON files."""
    global barbers_db, barber_feedback_db, service_types
    
    barbers_db = load_dict_data("barbers")
    barber_feedback_db = load_dict_data("feedback")  # Reuse feedback data
    service_types = load_list_data("services")
    
    # Initialize default barbers if empty
    if not barbers_db:
        default_barbers = {
            "B001": {
                "barber_id": "B001",
                "name": "John Smith",
                "specialties": ["Classic Cut", "Beard Trim"],
                "available": True
            },
            "B002": {
                "barber_id": "B002",
                "name": "Mike Johnson",
                "specialties": ["Fade", "Hair Coloring"],
                "available": True
            },
            "B003": {
                "barber_id": "B003",
                "name": "Sarah Williams",
                "specialties": ["Styling", "Hair Treatment"],
                "available": True
            }
        }
        barbers_db = default_barbers
        save_barbers()
    
    # Initialize default services if empty
    if not service_types:
        default_services = [
            {"id": "S001", "name": "Classic Haircut", "duration": 30, "price": 25.00},
            {"id": "S002", "name": "Beard Trim", "duration": 15, "price": 15.00},
            {"id": "S003", "name": "Fade", "duration": 45, "price": 35.00},
            {"id": "S004", "name": "Hair Coloring", "duration": 60, "price": 50.00},
            {"id": "S005", "name": "Hair Treatment", "duration": 45, "price": 40.00},
            {"id": "S006", "name": "Full Service (Cut + Beard)", "duration": 60, "price": 45.00}
        ]
        service_types = default_services
        save_services()
    
    logger.info(f"Loaded {len(barbers_db)} barbers and {len(service_types)} services")

def save_barbers():
    """Save barbers to JSON file."""
    if save_dict_data("barbers", barbers_db):
        logger.debug("Barbers saved successfully")
    else:
        logger.error("Failed to save barbers")

def save_services():
    """Save services to JSON file."""
    if save_list_data("services", service_types):
        logger.debug("Services saved successfully")
    else:
        logger.error("Failed to save services")

# Initialize data
barbers_db: Dict[str, Any] = {}
barber_feedback_db: Dict[str, Any] = {}
service_types: List[Dict[str, Any]] = []

# Load on startup
load_data()

# Models
class BarberAvailabilityUpdate(BaseModel):
    """Model for updating barber availability."""
    barber_id: str = Field(..., min_length=1)
    available: bool

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "barber",
        "timestamp": datetime.now().isoformat(),
        "barbers_count": len(barbers_db),
        "services_count": len(service_types)
    }

# Barber endpoints
@app.get("/barbers/")
async def get_all_barbers():
    """
    Get all barbers.
    
    Returns:
        List of all barbers
    """
    try:
        barbers = list(barbers_db.values())
        logger.debug(f"Retrieved {len(barbers)} barbers")
        return {"barbers": barbers}
    except Exception as e:
        logger.error(f"Error getting barbers: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve barbers"
        )

@app.get("/barbers/{barber_id}")
async def get_barber(barber_id: str):
    """
    Get a specific barber.
    
    Args:
        barber_id: Barber ID
        
    Returns:
        Barber information
    """
    barber_id = sanitize_input(barber_id)
    if barber_id not in barbers_db:
        raise HTTPException(
            status_code=404,
            detail="Barber not found"
        )
    return barbers_db[barber_id]

@app.post("/barbers/")
@limiter.limit("10/minute")
async def create_barber(barber: BarberCreate):
    """
    Create a new barber.
    
    Args:
        barber: Barber information
        
    Returns:
        Created barber information
    """
    try:
        name = sanitize_input(barber.name)
        barber_id = f"B{str(uuid.uuid4())[:8].upper()}"
        
        new_barber = {
            "barber_id": barber_id,
            "name": name,
            "specialties": barber.specialties if hasattr(barber, 'specialties') else [barber.specialty] if hasattr(barber, 'specialty') else [],
            "available": barber.available if hasattr(barber, 'available') else True
        }
        
        barbers_db[barber_id] = new_barber
        save_barbers()
        
        logger.info(f"Barber {barber_id} created successfully")
        return {
            "message": "Barber created successfully",
            "barber": new_barber
        }
    except Exception as e:
        logger.error(f"Error creating barber: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create barber: {str(e)}"
        )

@app.put("/barbers/{barber_id}/availability")
@limiter.limit("20/minute")
async def update_barber_availability(
    barber_id: str,
    update: BarberAvailabilityUpdate
):
    """
    Update barber availability.
    
    Args:
        barber_id: Barber ID
        update: Availability update
        
    Returns:
        Updated barber information
    """
    barber_id = sanitize_input(barber_id)
    if barber_id not in barbers_db:
        raise HTTPException(
            status_code=404,
            detail="Barber not found"
        )
    
    barbers_db[barber_id]["available"] = update.available
    save_barbers()
    
    logger.info(f"Barber {barber_id} availability updated to {update.available}")
    return barbers_db[barber_id]

@app.get("/services/")
async def get_all_services():
    """
    Get all services.
    
    Returns:
        List of all services
    """
    try:
        logger.debug(f"Retrieved {len(service_types)} services")
        return {"services": service_types}
    except Exception as e:
        logger.error(f"Error getting services: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve services"
        )

def process_feedback(feedback_data: Dict[str, Any]):
    """
    Process received feedback and update barber statistics.
    
    Args:
        feedback_data: Feedback data from Kafka
    """
    try:
        barber_id = feedback_data.get("barber_id")
        if not barber_id:
            return
        
        if barber_id not in barber_feedback_db:
            barber_feedback_db[barber_id] = []
        
        # Add feedback to barber's record
        barber_feedback_db[barber_id].append(feedback_data)
        
        # Calculate new average rating
        ratings = [f.get("rating", 0) for f in barber_feedback_db[barber_id]]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
        else:
            avg_rating = 0
        
        # Send feedback notification to barber
        try:
            producer.send('barber-feedback', {
                "event_type": "barber_feedback_received",
                "data": {
                    "barber_id": barber_id,
                    "feedback": feedback_data,
                    "average_rating": avg_rating,
                    "total_ratings": len(ratings)
                }
            })
            producer.flush()
        except KafkaError as e:
            logger.error(f"Failed to send Kafka message: {e}")
        
        logger.info(f"Processed feedback for barber {barber_id}: rating {feedback_data.get('rating', 'N/A')}/5")
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)

def kafka_consumer_thread():
    """Listen for feedback submissions."""
    if not consumer:
        logger.warning("Kafka consumer not available, skipping feedback processing")
        return
    
    logger.info("Barber service started. Listening for feedback...")
    
    try:
        for message in consumer:
            try:
                data = message.value
                event_type = data.get("event_type")
                payload = data.get("data")
                
                if event_type == "feedback_submitted":
                    process_feedback(payload)
                else:
                    logger.debug(f"Unknown event type: {event_type}")
            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}", exc_info=True)

# Start Kafka consumer in a separate thread
if consumer:
    consumer_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
    consumer_thread.start()

# Graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Handle graceful shutdown."""
    logger.info("Shutting down barber service")
    save_barbers()
    save_services()
    if producer:
        producer.close()
    if consumer:
        consumer.close()

# Run the service
if __name__ == "__main__":
    logger.info(f"Starting barber service on port {BARBER_SERVICE_PORT}")
    uvicorn.run(
        "barber_service:app",
        host="0.0.0.0",
        port=BARBER_SERVICE_PORT,
        reload=True
    )
