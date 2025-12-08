"""Notification service for managing real-time notifications."""
import json
from typing import Dict, Any, List
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import utilities
from utils.config import KAFKA_BROKER, NOTIFICATION_SERVICE_PORT
from utils.data_persistence import load_dict_data, save_dict_data
from utils.logger_config import setup_logger

# Setup logger
logger = setup_logger(__name__, "notification_service.log")

# Kafka constants
TOPIC_QUEUE_UPDATED = "queue-updated"
TOPIC_FEEDBACK_SUBMITTED = "feedback-submitted"
TOPIC_CLIENT_LOGGED_IN = "client-logged-in"
TOPIC_NOTIFICATION_UPDATED = "notification-updated"

# Load data from persistence
def load_data():
    """Load notifications data from JSON file."""
    global notifications_by_client, admin_notifications
    
    data = load_dict_data("notifications")
    
    # Restore notifications_by_client structure
    notifications_by_client = {}
    admin_notifications = []
    
    for client_id, notifications in data.items():
        if client_id == "admin":
            admin_notifications = notifications if isinstance(notifications, list) else []
        else:
            notifications_by_client[client_id] = notifications if isinstance(notifications, list) else []
    
    total_notifications = sum(len(n) for n in notifications_by_client.values()) + len(admin_notifications)
    logger.info(f"Loaded {total_notifications} notifications")

def save_notifications():
    """Save notifications to JSON file."""
    data = {"admin": admin_notifications}
    data.update(notifications_by_client)
    
    if save_dict_data("notifications", data):
        logger.debug("Notifications saved successfully")
    else:
        logger.error("Failed to save notifications")

# Store notifications by client_id
notifications_by_client: Dict[str, List[Dict[str, Any]]] = {}
admin_notifications: List[Dict[str, Any]] = []

# Load on startup
load_data()

# Configure Kafka consumer with retry logic
def create_kafka_consumer():
    """Create Kafka consumer with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                TOPIC_QUEUE_UPDATED,
                TOPIC_FEEDBACK_SUBMITTED,
                TOPIC_CLIENT_LOGGED_IN,
                TOPIC_NOTIFICATION_UPDATED,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='notification-group',
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

consumer = create_kafka_consumer()

def add_notification(
    client_id: str,
    message: str,
    notification_type: str,
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Add a notification for a specific client.
    
    Args:
        client_id: Client ID
        message: Notification message
        notification_type: Type of notification
        data: Additional notification data
        
    Returns:
        Created notification
    """
    if client_id not in notifications_by_client:
        notifications_by_client[client_id] = []
    
    notification = {
        "notification_id": f"N{len(notifications_by_client[client_id]) + 1:06d}",
        "client_id": client_id,
        "message": message,
        "type": notification_type,
        "timestamp": datetime.now().isoformat(),
        "read": False,
        "data": data or {}
    }
    
    notifications_by_client[client_id].append(notification)
    
    # Also add to admin notifications
    admin_notification = notification.copy()
    admin_notification["admin_read"] = False
    admin_notifications.append(admin_notification)
    
    # Save to persistence
    save_notifications()
    
    logger.info(f"Added notification for client {client_id}: {message}")
    return notification

def handle_queue_update(data: Dict[str, Any]):
    """Handle queue status update notifications."""
    try:
        client_id = data.get("client_id")
        status = data.get("status")
        queue_id = data.get("queue_id")
        
        if status == "waiting":
            position = data.get("position", "unknown")
            wait_time = data.get("estimated_wait", "unknown")
            message = f"You are in queue (position {position}). Estimated wait: {wait_time} minutes."
            add_notification(client_id, message, "queue_update", data)
        elif status == "processing":
            message = "It's your turn now! Please proceed to your barber."
            add_notification(client_id, message, "queue_update", data)
        elif status == "completed":
            message = "Your haircut is completed. Thank you for visiting!"
            add_notification(client_id, message, "queue_update", data)
            add_notification(
                client_id,
                "Please share your feedback about your experience",
                "feedback_request",
                data
            )
    except Exception as e:
        logger.error(f"Error handling queue update: {e}", exc_info=True)

def handle_feedback_submitted(data: Dict[str, Any]):
    """Handle feedback submission notifications."""
    try:
        client_id = data.get("client_id")
        barber_id = data.get("barber_id", "unknown")
        rating = data.get("rating", "N/A")
        
        message = "Thank you for your feedback! We value your opinion."
        add_notification(client_id, message, "feedback_confirmation", data)
        
        # Notification for admin
        admin_message = f"New feedback received from client {client_id} for barber {barber_id}. Rating: {rating}/5"
        add_notification("admin", admin_message, "new_feedback", data)
    except Exception as e:
        logger.error(f"Error handling feedback submitted: {e}", exc_info=True)

def handle_client_login(data: Dict[str, Any]):
    """Handle client login event."""
    try:
        client_id = data.get("client_id")
        username = data.get("username", "a user")
        
        message = f"Welcome back, {username}!"
        add_notification(client_id, message, "login_welcome", data)
        
        # Notification for admin
        admin_message = f"Client {client_id} ({username}) has logged in"
        add_notification("admin", admin_message, "client_login", data)
    except Exception as e:
        logger.error(f"Error handling client login: {e}", exc_info=True)

def handle_appointment_booked(data: Dict[str, Any]):
    """Handle appointment booked notifications."""
    try:
        client_id = data.get("client_id")
        barber_name = data.get("barber_name", "Unknown Barber")
        service_name = data.get("service_name", "Unknown Service")
        datetime_info = data.get("datetime", "Unknown DateTime")
        
        message = f"You have successfully booked an appointment with {barber_name} for {service_name} on {datetime_info}."
        add_notification(client_id, message, "appointment_booked", data)
    except Exception as e:
        logger.error(f"Error handling appointment booked: {e}", exc_info=True)

def handle_appointment_cancelled(data: Dict[str, Any]):
    """Handle appointment cancelled notifications."""
    try:
        client_id = data.get("client_id")
        appointment_id = data.get("appointment_id", "Unknown ID")
        
        message = f"Your appointment (ID: {appointment_id}) has been cancelled."
        add_notification(client_id, message, "appointment_cancelled", data)
        
        logger.info(f"Appointment cancelled - Appointment ID: {appointment_id}, ClientID: {client_id}")
    except Exception as e:
        logger.error(f"Error handling appointment cancelled: {e}", exc_info=True)

def main():
    """Main Kafka consumer loop."""
    if not consumer:
        logger.warning("Kafka consumer not available")
        return
    
    logger.info("Notification service started. Listening for messages...")
    
    try:
        for message in consumer:
            try:
                data = message.value
                event_type = data.get("event_type")
                payload = data.get("data")
                
                if event_type == "queue_status_changed":
                    handle_queue_update(payload)
                elif event_type == "feedback_submitted":
                    handle_feedback_submitted(payload)
                elif event_type == "client_logged_in":
                    handle_client_login(payload)
                elif event_type == "appointment_booked":
                    handle_appointment_booked(payload)
                elif event_type == "appointment_cancelled":
                    handle_appointment_cancelled(payload)
                else:
                    logger.debug(f"Unknown event type: {event_type}")
            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}", exc_info=True)

# FastAPI app for HTTP endpoints
app = FastAPI(
    title="Notification Service",
    description="Service for managing notifications",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "notification",
        "timestamp": datetime.now().isoformat(),
        "notifications_count": sum(len(n) for n in notifications_by_client.values())
    }

@app.get("/notifications")
async def get_notifications(client_id: str = None):
    """
    Get notifications for a client or admin.
    
    Args:
        client_id: Client ID (optional, defaults to admin)
        
    Returns:
        List of notifications
    """
    try:
        if client_id:
            if client_id == "admin":
                notifications = admin_notifications
            else:
                notifications = notifications_by_client.get(client_id, [])
        else:
            notifications = admin_notifications
        
        # Sort by timestamp (newest first)
        notifications = sorted(
            notifications,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        logger.debug(f"Retrieved {len(notifications)} notifications for {client_id or 'admin'}")
        return {"notifications": notifications}
    except Exception as e:
        logger.error(f"Error getting notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve notifications"
        )

@app.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, client_id: str):
    """
    Mark a notification as read.
    
    Args:
        notification_id: Notification ID
        client_id: Client ID
        
    Returns:
        Success message
    """
    try:
        if client_id == "admin":
            for notif in admin_notifications:
                if notif.get("notification_id") == notification_id:
                    notif["admin_read"] = True
                    save_notifications()
                    return {"message": "Notification marked as read"}
        else:
            if client_id in notifications_by_client:
                for notif in notifications_by_client[client_id]:
                    if notif.get("notification_id") == notification_id:
                        notif["read"] = True
                        save_notifications()
                        return {"message": "Notification marked as read"}
        
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to mark notification as read"
        )

# Start Kafka consumer in a separate thread
if consumer:
    consumer_thread = threading.Thread(target=main, daemon=True)
    consumer_thread.start()

# Graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Handle graceful shutdown."""
    logger.info("Shutting down notification service")
    save_notifications()
    if consumer:
        consumer.close()

# Run the service
if __name__ == "__main__":
    logger.info(f"Starting notification service on port {NOTIFICATION_SERVICE_PORT}")
    
    # Start FastAPI server
    uvicorn.run(
        "notification_service:app",
        host="0.0.0.0",
        port=NOTIFICATION_SERVICE_PORT,
        reload=True
    )
