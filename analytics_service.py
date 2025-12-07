"""Analytics service for generating reports and statistics."""
import json
import requests
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import utilities
from utils.config import ANALYTICS_SERVICE_PORT, SERVICE_URLS
from utils.logger_config import setup_logger
from utils.security import verify_token

# Setup logger
logger = setup_logger(__name__, "analytics_service.log")

# Define FastAPI app
app = FastAPI(
    title="Analytics Service",
    description="Service for analytics and reporting",
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

def fetch_bookings() -> List[Dict[str, Any]]:
    """Fetch all bookings from booking service."""
    try:
        response = requests.get(
            f"{SERVICE_URLS['booking']}/bookings/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("bookings", [])
        return []
    except Exception as e:
        logger.warning(f"Error fetching bookings: {e}")
        return []

def fetch_feedback() -> List[Dict[str, Any]]:
    """Fetch all feedback from feedback service."""
    try:
        response = requests.get(
            f"{SERVICE_URLS['feedback']}/feedback/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("feedback", [])
        return []
    except Exception as e:
        logger.warning(f"Error fetching feedback: {e}")
        return []

def fetch_barbers() -> List[Dict[str, Any]]:
    """Fetch all barbers from barber service."""
    try:
        response = requests.get(
            f"{SERVICE_URLS['barber']}/barbers/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("barbers", [])
        return []
    except Exception as e:
        logger.warning(f"Error fetching barbers: {e}")
        return []

def fetch_services() -> List[Dict[str, Any]]:
    """Fetch all services from barber service."""
    try:
        response = requests.get(
            f"{SERVICE_URLS['barber']}/services/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("services", [])
        return []
    except Exception as e:
        logger.warning(f"Error fetching services: {e}")
        return []

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.now().isoformat()
    }

# Analytics endpoints
@app.get("/analytics/popular-services")
@limiter.limit("60/minute")
async def get_popular_services(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: Dict = Depends(verify_admin)
):
    """
    Get popular services statistics.
    
    Args:
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        admin: Admin user from token
        
    Returns:
        Popular services statistics
    """
    try:
        bookings = fetch_bookings()
        services = fetch_services()
        
        # Create service lookup
        service_lookup = {s.get("id"): s for s in services}
        
        # Filter by date if provided
        if start_date or end_date:
            filtered_bookings = []
            for booking in bookings:
                booking_date = booking.get("booking_date", "")
                if start_date and booking_date < start_date:
                    continue
                if end_date and booking_date > end_date:
                    continue
                filtered_bookings.append(booking)
            bookings = filtered_bookings
        
        # Count service usage
        service_counts = Counter(b.get("service_type") for b in bookings)
        
        # Build result
        popular_services = []
        for service_id, count in service_counts.most_common():
            service_info = service_lookup.get(service_id, {"name": service_id, "price": 0})
            popular_services.append({
                "service_id": service_id,
                "service_name": service_info.get("name", service_id),
                "booking_count": count,
                "revenue": count * service_info.get("price", 0)
            })
        
        logger.debug(f"Retrieved popular services: {len(popular_services)}")
        return {
            "popular_services": popular_services,
            "total_bookings": len(bookings),
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        logger.error(f"Error getting popular services: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve popular services"
        )

@app.get("/analytics/barber-performance")
@limiter.limit("60/minute")
async def get_barber_performance(admin: Dict = Depends(verify_admin)):
    """
    Get barber performance statistics.
    
    Args:
        admin: Admin user from token
        
    Returns:
        Barber performance data
    """
    try:
        barbers = fetch_barbers()
        feedback = fetch_feedback()
        bookings = fetch_bookings()
        
        # Calculate performance for each barber
        barber_performance = []
        
        for barber in barbers:
            barber_id = barber.get("barber_id")
            
            # Get feedback for this barber
            barber_feedback = [
                f for f in feedback
                if f.get("barber_id") == barber_id
            ]
            
            # Calculate average rating
            if barber_feedback:
                avg_rating = sum(f.get("rating", 0) for f in barber_feedback) / len(barber_feedback)
                total_ratings = len(barber_feedback)
            else:
                avg_rating = 0.0
                total_ratings = 0
            
            # Count bookings
            barber_bookings = [
                b for b in bookings
                if b.get("barber_id") == barber_id
            ]
            
            barber_performance.append({
                "barber_id": barber_id,
                "barber_name": barber.get("name"),
                "average_rating": round(avg_rating, 2),
                "total_ratings": total_ratings,
                "total_bookings": len(barber_bookings),
                "available": barber.get("available", False)
            })
        
        # Sort by average rating (descending)
        barber_performance.sort(key=lambda x: x["average_rating"], reverse=True)
        
        logger.debug(f"Retrieved performance for {len(barber_performance)} barbers")
        return {"barber_performance": barber_performance}
    except Exception as e:
        logger.error(f"Error getting barber performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve barber performance"
        )

@app.get("/analytics/revenue")
@limiter.limit("60/minute")
async def get_revenue_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: Dict = Depends(verify_admin)
):
    """
    Get revenue statistics.
    
    Args:
        start_date: Start date filter (YYYY-MM-DD)
        end_date: End date filter (YYYY-MM-DD)
        admin: Admin user from token
        
    Returns:
        Revenue statistics
    """
    try:
        bookings = fetch_bookings()
        services = fetch_services()
        
        # Create service lookup
        service_lookup = {s.get("id"): s for s in services}
        
        # Filter by date if provided
        if start_date or end_date:
            filtered_bookings = []
            for booking in bookings:
                booking_date = booking.get("booking_date", "")
                if start_date and booking_date < start_date:
                    continue
                if end_date and booking_date > end_date:
                    continue
                filtered_bookings.append(booking)
            bookings = filtered_bookings
        
        # Calculate revenue
        total_revenue = 0
        revenue_by_service = defaultdict(float)
        revenue_by_date = defaultdict(float)
        
        for booking in bookings:
            if booking.get("status") != "cancelled":
                service_id = booking.get("service_type")
                service_info = service_lookup.get(service_id, {"price": 0})
                price = service_info.get("price", 0)
                
                total_revenue += price
                revenue_by_service[service_id] += price
                
                booking_date = booking.get("booking_date", "")
                if booking_date:
                    revenue_by_date[booking_date] += price
        
        # Format revenue by service
        revenue_by_service_list = [
            {
                "service_id": service_id,
                "service_name": service_lookup.get(service_id, {}).get("name", service_id),
                "revenue": revenue
            }
            for service_id, revenue in revenue_by_service.items()
        ]
        revenue_by_service_list.sort(key=lambda x: x["revenue"], reverse=True)
        
        # Format revenue by date
        revenue_by_date_list = [
            {
                "date": date,
                "revenue": revenue
            }
            for date, revenue in sorted(revenue_by_date.items())
        ]
        
        logger.debug(f"Calculated revenue: ${total_revenue}")
        return {
            "total_revenue": round(total_revenue, 2),
            "total_bookings": len(bookings),
            "revenue_by_service": revenue_by_service_list,
            "revenue_by_date": revenue_by_date_list,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        logger.error(f"Error getting revenue stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve revenue statistics"
        )

@app.get("/analytics/queue-stats")
@limiter.limit("60/minute")
async def get_queue_stats(admin: Dict = Depends(verify_admin)):
    """
    Get queue statistics.
    
    Args:
        admin: Admin user from token
        
    Returns:
        Queue statistics
    """
    try:
        queue_response = requests.get(
            f"{SERVICE_URLS['booking']}/queue/",
            timeout=5
        )
        
        if queue_response.status_code != 200:
            raise HTTPException(
                status_code=queue_response.status_code,
                detail="Failed to retrieve queue"
            )
        
        queue_data = queue_response.json().get("queue", [])
        
        # Calculate statistics
        waiting_count = len([q for q in queue_data if q.get("status") == "waiting"])
        processing_count = len([q for q in queue_data if q.get("status") == "processing"])
        
        # Calculate average wait times
        wait_times = [
            q.get("estimated_wait", 0) for q in queue_data
            if q.get("status") == "waiting" and q.get("estimated_wait")
        ]
        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        
        return {
            "total_in_queue": len(queue_data),
            "waiting": waiting_count,
            "processing": processing_count,
            "average_wait_time_minutes": round(avg_wait_time, 2),
            "queue": queue_data
        }
    except requests.RequestException as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(
            status_code=503,
            detail="Booking service unavailable"
        )

@app.get("/analytics/daily-bookings")
@limiter.limit("60/minute")
async def get_daily_bookings(
    days: int = Query(30, ge=1, le=365),
    admin: Dict = Depends(verify_admin)
):
    """
    Get daily bookings count for the last N days.
    
    Args:
        days: Number of days to analyze
        admin: Admin user from token
        
    Returns:
        Daily bookings statistics
    """
    try:
        bookings = fetch_bookings()
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Filter bookings by date range
        daily_counts = defaultdict(int)
        
        for booking in bookings:
            booking_date_str = booking.get("booking_date", "")
            if booking_date_str:
                try:
                    booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
                    if start_date <= booking_date <= end_date:
                        daily_counts[booking_date_str] += 1
                except ValueError:
                    continue
        
        # Format result
        daily_stats = [
            {
                "date": date,
                "bookings_count": count
            }
            for date, count in sorted(daily_counts.items())
        ]
        
        logger.debug(f"Retrieved daily bookings for {len(daily_stats)} days")
        return {
            "daily_bookings": daily_stats,
            "total_bookings": sum(count for count in daily_counts.values()),
            "average_per_day": round(sum(count for count in daily_counts.values()) / len(daily_counts), 2) if daily_counts else 0,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }
        }
    except Exception as e:
        logger.error(f"Error getting daily bookings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve daily bookings"
        )

# Run the service
if __name__ == "__main__":
    logger.info(f"Starting analytics service on port {ANALYTICS_SERVICE_PORT}")
    uvicorn.run(
        "analytics_service:app",
        host="0.0.0.0",
        port=ANALYTICS_SERVICE_PORT,
        reload=True
    )

