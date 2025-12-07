"""Feedback service for managing customer feedback."""
import json
import uvicorn
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import utilities
from utils.config import KAFKA_BROKER, FEEDBACK_SERVICE_PORT
from utils.data_persistence import load_dict_data, save_dict_data
from utils.logger_config import setup_logger
from utils.security import sanitize_input, verify_token
from utils.models import FeedbackRequest

# Setup logger
logger = setup_logger(__name__, "feedback_service.log")

# Define FastAPI app
app = FastAPI(
    title="Feedback Service",
    description="Service for managing customer feedback",
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
    """Load feedback data from JSON file."""
    global feedback_db
    feedback_db = load_dict_data("feedback")
    logger.info(f"Loaded {len(feedback_db)} feedback entries")

def save_feedback():
    """Save feedback to JSON file."""
    if save_dict_data("feedback", feedback_db):
        logger.debug("Feedback saved successfully")
    else:
        logger.error("Failed to save feedback")

# Initialize data
feedback_db: Dict[str, Any] = {}

# Load on startup
load_data()

# Dependency for token verification (optional)
async def verify_token_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify JWT token from request."""
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except HTTPException:
        return None

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "feedback",
        "timestamp": datetime.now().isoformat(),
        "feedback_count": len(feedback_db)
    }

# Feedback endpoints
@app.post("/feedback/")
@limiter.limit("20/minute")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit customer feedback.
    
    Args:
        request: Feedback information
        
    Returns:
        Feedback confirmation
    """
    try:
        # Sanitize inputs
        client_id = sanitize_input(request.client_id)
        barber_id = sanitize_input(request.barber_id)
        service_id = sanitize_input(request.service_id)
        comment = sanitize_input(request.comment) if request.comment else None
        
        logger.info(f"Feedback submission from client {client_id} for barber {barber_id}")
        
        # Validate rating
        if request.rating < 1 or request.rating > 5:
            raise HTTPException(
                status_code=400,
                detail="Rating must be between 1 and 5"
            )
        
        # Generate feedback ID
        feedback_id = f"F{len(feedback_db) + 1:03d}"
        
        # Create feedback entry
        timestamp = datetime.now().isoformat()
        feedback = {
            "feedback_id": feedback_id,
            "client_id": client_id,
            "barber_id": barber_id,
            "service_id": service_id,
            "rating": request.rating,
            "comment": comment,
            "timestamp": timestamp
        }
        
        # Save to local DB
        feedback_db[feedback_id] = feedback
        save_feedback()
        
        # Send message to feedback-submitted topic
        try:
            producer.send('feedback-submitted', {
                "event_type": "feedback_submitted",
                "data": feedback
            })
            producer.flush()
        except KafkaError as e:
            logger.error(f"Failed to send Kafka message: {e}")
        
        logger.info(f"Feedback {feedback_id} submitted successfully")
        return {
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully"
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@app.get("/feedback/")
async def get_all_feedback():
    """
    Get all feedback entries.
    
    Returns:
        List of all feedback
    """
    try:
        feedback_list = list(feedback_db.values())
        logger.debug(f"Retrieved {len(feedback_list)} feedback entries")
        return {"feedback": feedback_list}
    except Exception as e:
        logger.error(f"Error getting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve feedback"
        )

@app.get("/feedback/client/{client_id}")
async def get_client_feedback(client_id: str):
    """
    Get all feedback from a specific client.
    
    Args:
        client_id: Client ID
        
    Returns:
        List of client's feedback
    """
    client_id = sanitize_input(client_id)
    try:
        client_feedback = [
            f for f in feedback_db.values()
            if f.get("client_id") == client_id
        ]
        logger.debug(f"Retrieved {len(client_feedback)} feedback entries for client {client_id}")
        return {"feedback": client_feedback}
    except Exception as e:
        logger.error(f"Error getting client feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve client feedback"
        )

@app.get("/feedback/barber/{barber_id}")
async def get_barber_feedback(barber_id: str):
    """
    Get all feedback for a specific barber.
    
    Args:
        barber_id: Barber ID
        
    Returns:
        Barber feedback summary and list
    """
    barber_id = sanitize_input(barber_id)
    try:
        barber_feedback = [
            f for f in feedback_db.values()
            if f.get("barber_id") == barber_id
        ]
        
        # Calculate average rating
        if barber_feedback:
            avg_rating = sum(f.get("rating", 0) for f in barber_feedback) / len(barber_feedback)
        else:
            avg_rating = 0.0
        
        logger.debug(f"Retrieved {len(barber_feedback)} feedback entries for barber {barber_id}")
        
        return {
            "barber_id": barber_id,
            "feedback_count": len(barber_feedback),
            "average_rating": round(avg_rating, 2),
            "feedback": barber_feedback
        }
    except Exception as e:
        logger.error(f"Error getting barber feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve barber feedback"
        )

# Graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Handle graceful shutdown."""
    logger.info("Shutting down feedback service")
    save_feedback()
    producer.close()

# Run the service
if __name__ == "__main__":
    logger.info(f"Starting feedback service on port {FEEDBACK_SERVICE_PORT}")
    uvicorn.run(
        "feedback_service:app",
        host="0.0.0.0",
        port=FEEDBACK_SERVICE_PORT,
        reload=True
    )
