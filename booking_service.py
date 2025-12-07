"""Booking service for managing appointments and queue entries."""
import json
import requests
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import uvicorn
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import utilities
from utils.config import (
    KAFKA_BROKER, BOOKING_SERVICE_PORT, SERVICE_URLS,
    DATA_FILES
)
from utils.data_persistence import load_dict_data, save_dict_data
from utils.logger_config import setup_logger
from utils.security import sanitize_input, verify_token
from utils.models import QueueRequest, BookingRequest
from pydantic import BaseModel

# Setup logger
logger = setup_logger(__name__, "booking_service.log")

# Define FastAPI app
app = FastAPI(
    title="Booking Service",
    description="Service for managing bookings and queue entries",
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
            logger.warning(f"Kafka connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("Failed to connect to Kafka after retries")
                raise

producer = create_kafka_producer()

# Load data from persistence
def load_data():
    """Load bookings and queue data from JSON files."""
    global bookings_db, queue_db, next_queue_id
    
    bookings_db = load_dict_data("bookings")
    queue_db = load_dict_data("queue")
    
    # Calculate next_queue_id from existing data
    if queue_db:
        max_id = 0
        for qid in queue_db.keys():
            if qid.startswith("Q") and len(qid) > 1:
                try:
                    num = int(qid[1:])
                    max_id = max(max_id, num)
                except ValueError:
                    pass
        next_queue_id = max_id + 1
    else:
        next_queue_id = 1
    
    logger.info(f"Loaded {len(bookings_db)} bookings and {len(queue_db)} queue entries")

def save_bookings():
    """Save bookings to JSON file."""
    if save_dict_data("bookings", bookings_db):
        logger.debug("Bookings saved successfully")
    else:
        logger.error("Failed to save bookings")

def save_queue():
    """Save queue to JSON file."""
    if save_dict_data("queue", queue_db):
        logger.debug("Queue saved successfully")
    else:
        logger.error("Failed to save queue")

# Initialize data
bookings_db: Dict[str, Any] = {}
queue_db: Dict[str, Any] = {}
next_queue_id: int = 1

# Load on startup
load_data()

# Dependency for token verification (optional for now, can be enabled later)
async def verify_token_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from request."""
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except HTTPException:
        # For now, allow requests without token (can be made required later)
        return None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "booking",
        "timestamp": datetime.now().isoformat(),
        "bookings_count": len(bookings_db),
        "queue_count": len(queue_db)
    }

# Queue endpoints
@app.post("/queue/")
@limiter.limit("30/minute")
async def add_to_queue(request: QueueRequest):
    """
    Add a client to the queue.
    
    Args:
        request: Queue request with client_id
        
    Returns:
        Queue entry information
    """
    try:
        # Sanitize input
        client_id = sanitize_input(request.client_id)
        
        logger.info(f"Adding client {client_id} to queue")
        
        # Check if client exists
        try:
            client_response = requests.get(
                f"{SERVICE_URLS['client']}/client/{client_id}",
                timeout=5
            )
            if client_response.status_code != 200:
                logger.warning(f"Client {client_id} not found")
                raise HTTPException(
                    status_code=404,
                    detail="Client not found"
                )
        except requests.RequestException as e:
            logger.error(f"Error checking client: {e}")
            raise HTTPException(
                status_code=503,
                detail="Client service unavailable"
            )
        
        # Check if already in queue
        for entry in queue_db.values():
            if entry.get("client_id") == client_id and entry.get("status") in ["waiting", "processing"]:
                logger.warning(f"Client {client_id} already in queue")
                raise HTTPException(
                    status_code=400,
                    detail="Client already in queue"
                )
        
        # Generate queue entry
        queue_id = f"Q{next_queue_id:03d}"
        next_queue_id += 1
        
        timestamp = datetime.now().isoformat()
        
        queue_entry = {
            "queue_id": queue_id,
            "client_id": client_id,
            "service_type": sanitize_input(request.service_type) if request.service_type else None,
            "barber_id": sanitize_input(request.barber_id) if request.barber_id else None,
            "timestamp": timestamp,
            "status": "waiting"
        }
        
        # Save to local DB
        queue_db[queue_id] = queue_entry
        save_queue()
        
        # Send message to queue-created topic
        try:
            producer.send('booking-created', {
                "event_type": "queue_created",
                "data": queue_entry
            })
            producer.flush()
        except KafkaError as e:
            logger.error(f"Failed to send Kafka message: {e}")
        
        logger.info(f"Client {client_id} added to queue with ID {queue_id}")
        return {
            "queue_id": queue_id,
            "position": len([q for q in queue_db.values() if q.get("status") == "waiting"]),
            "estimated_wait": len([q for q in queue_db.values() if q.get("status") == "waiting"]) * 5,
            "message": "Successfully added to queue"
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error adding to queue: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add to queue: {str(e)}"
        )

@app.get("/queue/")
async def get_queue_status():
    """
    Get current queue status.
    
    Returns:
        List of all queue entries sorted by timestamp
    """
    try:
        sorted_queue = sorted(
            queue_db.values(),
            key=lambda x: x.get("timestamp", "")
        )
        logger.debug(f"Retrieved queue status: {len(sorted_queue)} entries")
        return {"queue": sorted_queue}
    except Exception as e:
        logger.error(f"Error getting queue status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve queue status"
        )

@app.get("/queue/{queue_id}")
async def get_queue_entry(queue_id: str):
    """
    Get a specific queue entry.
    
    Args:
        queue_id: Queue entry ID
        
    Returns:
        Queue entry information
    """
    queue_id = sanitize_input(queue_id)
    if queue_id not in queue_db:
        raise HTTPException(
            status_code=404,
            detail="Queue entry not found"
        )
    return queue_db[queue_id]

# Booking endpoints
@app.post("/booking/")
@limiter.limit("30/minute")
async def create_booking(request: BookingRequest):
    """
    Create a new booking.
    
    Args:
        request: Booking request with details
        
    Returns:
        Booking confirmation
    """
    try:
        # Sanitize inputs
        client_id = sanitize_input(request.client_id)
        barber_id = sanitize_input(request.barber_id)
        service_type = sanitize_input(request.service_type)
        
        logger.info(f"Creating booking for client {client_id}")
        
        # Check if client exists
        try:
            client_response = requests.get(
                f"{SERVICE_URLS['client']}/client/{client_id}",
                timeout=5
            )
            if client_response.status_code != 200:
                logger.warning(f"Client {client_id} not found")
                raise HTTPException(
                    status_code=404,
                    detail="Client not found"
                )
        except requests.RequestException as e:
            logger.error(f"Error checking client: {e}")
            raise HTTPException(
                status_code=503,
                detail="Client service unavailable"
            )
        
        # Validate date is not in the past
        try:
            booking_datetime = datetime.strptime(
                f"{request.booking_date} {request.booking_time}",
                "%Y-%m-%d %H:%M"
            )
            if booking_datetime < datetime.now():
                raise HTTPException(
                    status_code=400,
                    detail="Cannot book appointments in the past"
                )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date or time format"
            )
        
        # Generate booking ID
        booking_id = f"B{len(bookings_db) + 1:03d}"
        
        # Create booking entry
        booking = {
            "booking_id": booking_id,
            "client_id": client_id,
            "barber_id": barber_id,
            "service_type": service_type,
            "booking_date": request.booking_date,
            "booking_time": request.booking_time,
            "created_at": datetime.now().isoformat(),
            "status": "scheduled"
        }
        
        # Save to local DB
        bookings_db[booking_id] = booking
        save_bookings()
        
        # Send message to booking-created topic
        try:
            producer.send('booking-created', {
                "event_type": "booking_created",
                "data": booking
            })
            producer.flush()
        except KafkaError as e:
            logger.error(f"Failed to send Kafka message: {e}")
        
        logger.info(f"Booking {booking_id} created successfully")
        return {
            "booking_id": booking_id,
            "message": "Booking created successfully"
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating booking: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create booking: {str(e)}"
        )

@app.get("/bookings/")
async def get_all_bookings():
    """
    Get all bookings.
    
    Returns:
        List of all bookings
    """
    try:
        bookings = list(bookings_db.values())
        logger.debug(f"Retrieved {len(bookings)} bookings")
        return {"bookings": bookings}
    except Exception as e:
        logger.error(f"Error getting bookings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve bookings"
        )

@app.get("/booking/client/{client_id}")
async def get_client_bookings(client_id: str):
    """
    Get all bookings for a specific client.
    
    Args:
        client_id: Client ID
        
    Returns:
        List of client's bookings
    """
    client_id = sanitize_input(client_id)
    try:
        client_bookings = [
            b for b in bookings_db.values()
            if b.get("client_id") == client_id
        ]
        logger.debug(f"Retrieved {len(client_bookings)} bookings for client {client_id}")
        return {"bookings": client_bookings}
    except Exception as e:
        logger.error(f"Error getting client bookings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve client bookings"
        )

@app.delete("/booking/{booking_id}")
async def cancel_booking(booking_id: str):
    """
    Cancel a booking.
    
    Args:
        booking_id: Booking ID to cancel
        
    Returns:
        Cancellation confirmation
    """
    booking_id = sanitize_input(booking_id)
    if booking_id not in bookings_db:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )
    
    booking = bookings_db[booking_id]
    booking["status"] = "cancelled"
    booking["cancelled_at"] = datetime.now().isoformat()
    
    save_bookings()
    
    logger.info(f"Booking {booking_id} cancelled")
    return {"message": "Booking cancelled successfully"}

# Graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Handle graceful shutdown."""
    logger.info("Shutting down booking service")
    save_bookings()
    save_queue()
    producer.close()

# Run the service
if __name__ == "__main__":
    logger.info(f"Starting booking service on port {BOOKING_SERVICE_PORT}")
    uvicorn.run(
        "booking_service:app",
        host="0.0.0.0",
        port=BOOKING_SERVICE_PORT,
        reload=True
    )
