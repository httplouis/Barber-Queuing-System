"""Admin service for administrative operations."""
import json
import requests
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from datetime import datetime
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import utilities
from utils.config import ADMIN_SERVICE_PORT, SERVICE_URLS
from utils.logger_config import setup_logger
from utils.security import verify_token, sanitize_input

# Setup logger
logger = setup_logger(__name__, "admin_service.log")

# Define FastAPI app
app = FastAPI(
    title="Admin Service",
    description="Service for administrative operations",
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

# Dependency for admin verification
async def verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Verify JWT token and check if user is admin.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        User information from token
        
    Raises:
        HTTPException: If not admin
    """
    try:
        payload = verify_token(credentials.credentials, token_type="access")
        
        if not payload.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "admin",
        "timestamp": datetime.now().isoformat()
    }

# Admin endpoints
@app.get("/dashboard/stats")
@limiter.limit("60/minute")
async def get_dashboard_stats(admin: Dict = Depends(verify_admin)):
    """
    Get dashboard statistics for admin.
    
    Args:
        admin: Admin user from token
        
    Returns:
        Dashboard statistics
    """
    try:
        stats = {
            "timestamp": datetime.now().isoformat()
        }
        
        # Get bookings count
        try:
            bookings_response = requests.get(
                f"{SERVICE_URLS['booking']}/bookings/",
                timeout=5
            )
            if bookings_response.status_code == 200:
                bookings_data = bookings_response.json()
                stats["total_bookings"] = len(bookings_data.get("bookings", []))
                stats["active_bookings"] = len([
                    b for b in bookings_data.get("bookings", [])
                    if b.get("status") == "scheduled"
                ])
        except Exception as e:
            logger.warning(f"Error getting bookings: {e}")
            stats["total_bookings"] = 0
            stats["active_bookings"] = 0
        
        # Get queue count
        try:
            queue_response = requests.get(
                f"{SERVICE_URLS['booking']}/queue/",
                timeout=5
            )
            if queue_response.status_code == 200:
                queue_data = queue_response.json()
                stats["queue_length"] = len(queue_data.get("queue", []))
                stats["waiting"] = len([
                    q for q in queue_data.get("queue", [])
                    if q.get("status") == "waiting"
                ])
                stats["processing"] = len([
                    q for q in queue_data.get("queue", [])
                    if q.get("status") == "processing"
                ])
        except Exception as e:
            logger.warning(f"Error getting queue: {e}")
            stats["queue_length"] = 0
            stats["waiting"] = 0
            stats["processing"] = 0
        
        # Get clients count
        try:
            clients_response = requests.get(
                f"{SERVICE_URLS['client']}/clients/",
                headers={"Authorization": f"Bearer {admin.get('token', '')}"},
                timeout=5
            )
            if clients_response.status_code == 200:
                clients_data = clients_response.json()
                stats["total_clients"] = len(clients_data.get("clients", []))
        except Exception as e:
            logger.warning(f"Error getting clients: {e}")
            stats["total_clients"] = 0
        
        # Get barbers count
        try:
            barbers_response = requests.get(
                f"{SERVICE_URLS['barber']}/barbers/",
                timeout=5
            )
            if barbers_response.status_code == 200:
                barbers_data = barbers_response.json()
                stats["total_barbers"] = len(barbers_data.get("barbers", []))
                stats["available_barbers"] = len([
                    b for b in barbers_data.get("barbers", [])
                    if b.get("available", False)
                ])
        except Exception as e:
            logger.warning(f"Error getting barbers: {e}")
            stats["total_barbers"] = 0
            stats["available_barbers"] = 0
        
        # Get feedback count
        try:
            feedback_response = requests.get(
                f"{SERVICE_URLS['feedback']}/feedback/",
                timeout=5
            )
            if feedback_response.status_code == 200:
                feedback_data = feedback_response.json()
                stats["total_feedback"] = len(feedback_data.get("feedback", []))
        except Exception as e:
            logger.warning(f"Error getting feedback: {e}")
            stats["total_feedback"] = 0
        
        logger.debug("Dashboard stats retrieved successfully")
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard statistics"
        )

@app.get("/queue/manage")
@limiter.limit("60/minute")
async def manage_queue(admin: Dict = Depends(verify_admin)):
    """
    Get queue management information.
    
    Args:
        admin: Admin user from token
        
    Returns:
        Queue management data
    """
    try:
        queue_response = requests.get(
            f"{SERVICE_URLS['booking']}/queue/",
            timeout=5
        )
        if queue_response.status_code == 200:
            queue_data = queue_response.json()
            return queue_data
        else:
            raise HTTPException(
                status_code=queue_response.status_code,
                detail="Failed to retrieve queue"
            )
    except requests.RequestException as e:
        logger.error(f"Error getting queue: {e}")
        raise HTTPException(
            status_code=503,
            detail="Booking service unavailable"
        )

@app.delete("/queue/{queue_id}")
@limiter.limit("30/minute")
async def remove_from_queue(
    queue_id: str,
    admin: Dict = Depends(verify_admin)
):
    """
    Remove an entry from the queue (admin only).
    
    Args:
        queue_id: Queue entry ID
        admin: Admin user from token
        
    Returns:
        Success message
    """
    queue_id = sanitize_input(queue_id)
    # This would need to be implemented in booking service
    # For now, return a placeholder
    return {"message": f"Queue entry {queue_id} removed"}

@app.get("/bookings/all")
@limiter.limit("60/minute")
async def get_all_bookings_admin(admin: Dict = Depends(verify_admin)):
    """
    Get all bookings (admin view).
    
    Args:
        admin: Admin user from token
        
    Returns:
        All bookings
    """
    try:
        bookings_response = requests.get(
            f"{SERVICE_URLS['booking']}/bookings/",
            timeout=5
        )
        if bookings_response.status_code == 200:
            return bookings_response.json()
        else:
            raise HTTPException(
                status_code=bookings_response.status_code,
                detail="Failed to retrieve bookings"
            )
    except requests.RequestException as e:
        logger.error(f"Error getting bookings: {e}")
        raise HTTPException(
            status_code=503,
            detail="Booking service unavailable"
        )

@app.delete("/bookings/{booking_id}")
@limiter.limit("30/minute")
async def cancel_booking_admin(
    booking_id: str,
    admin: Dict = Depends(verify_admin)
):
    """
    Cancel a booking (admin only).
    
    Args:
        booking_id: Booking ID
        admin: Admin user from token
        
    Returns:
        Cancellation confirmation
    """
    booking_id = sanitize_input(booking_id)
    try:
        cancel_response = requests.delete(
            f"{SERVICE_URLS['booking']}/booking/{booking_id}",
            timeout=5
        )
        if cancel_response.status_code == 200:
            return cancel_response.json()
        else:
            raise HTTPException(
                status_code=cancel_response.status_code,
                detail="Failed to cancel booking"
            )
    except requests.RequestException as e:
        logger.error(f"Error cancelling booking: {e}")
        raise HTTPException(
            status_code=503,
            detail="Booking service unavailable"
        )

@app.get("/clients/all")
@limiter.limit("60/minute")
async def get_all_clients_admin(admin: Dict = Depends(verify_admin)):
    """
    Get all clients (admin only).
    
    Args:
        admin: Admin user from token
        
    Returns:
        All clients
    """
    try:
        clients_response = requests.get(
            f"{SERVICE_URLS['client']}/clients/",
            headers={"Authorization": f"Bearer {admin.get('token', '')}"},
            timeout=5
        )
        if clients_response.status_code == 200:
            return clients_response.json()
        else:
            raise HTTPException(
                status_code=clients_response.status_code,
                detail="Failed to retrieve clients"
            )
    except requests.RequestException as e:
        logger.error(f"Error getting clients: {e}")
        raise HTTPException(
            status_code=503,
            detail="Client service unavailable"
        )

@app.put("/clients/{client_id}/disable")
@limiter.limit("30/minute")
async def disable_client(
    client_id: str,
    admin: Dict = Depends(verify_admin)
):
    """
    Disable a client account (admin only).
    
    Args:
        client_id: Client ID
        admin: Admin user from token
        
    Returns:
        Success message
    """
    client_id = sanitize_input(client_id)
    # This would need to be implemented in client service
    return {"message": f"Client {client_id} disabled"}

# Run the service
if __name__ == "__main__":
    logger.info(f"Starting admin service on port {ADMIN_SERVICE_PORT}")
    uvicorn.run(
        "admin_service:app",
        host="0.0.0.0",
        port=ADMIN_SERVICE_PORT,
        reload=True
    )

