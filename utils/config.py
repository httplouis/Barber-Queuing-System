"""Configuration management for the barber queuing system."""
import os
from typing import Dict, Any
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Service ports
BOOKING_SERVICE_PORT = int(os.getenv("BOOKING_SERVICE_PORT", "8000"))
CLIENT_SERVICE_PORT = int(os.getenv("CLIENT_SERVICE_PORT", "8001"))
FEEDBACK_SERVICE_PORT = int(os.getenv("FEEDBACK_SERVICE_PORT", "8002"))
NOTIFICATION_SERVICE_PORT = int(os.getenv("NOTIFICATION_SERVICE_PORT", "8003"))
BARBER_SERVICE_PORT = int(os.getenv("BARBER_SERVICE_PORT", "8004"))
ADMIN_SERVICE_PORT = int(os.getenv("ADMIN_SERVICE_PORT", "8005"))
ANALYTICS_SERVICE_PORT = int(os.getenv("ANALYTICS_SERVICE_PORT", "8006"))

# Kafka configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Rate limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

# Service URLs
SERVICE_URLS: Dict[str, str] = {
    "booking": f"http://localhost:{BOOKING_SERVICE_PORT}",
    "client": f"http://localhost:{CLIENT_SERVICE_PORT}",
    "feedback": f"http://localhost:{FEEDBACK_SERVICE_PORT}",
    "notification": f"http://localhost:{NOTIFICATION_SERVICE_PORT}",
    "barber": f"http://localhost:{BARBER_SERVICE_PORT}",
    "admin": f"http://localhost:{ADMIN_SERVICE_PORT}",
    "analytics": f"http://localhost:{ANALYTICS_SERVICE_PORT}",
}

# Data file paths
DATA_FILES: Dict[str, Path] = {
    "bookings": DATA_DIR / "bookings.json",
    "queue": DATA_DIR / "queue.json",
    "clients": DATA_DIR / "clients.json",
    "feedback": DATA_DIR / "feedback.json",
    "barbers": DATA_DIR / "barbers.json",
    "services": DATA_DIR / "services.json",
    "notifications": DATA_DIR / "notifications.json",
}

# Logging configuration
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

