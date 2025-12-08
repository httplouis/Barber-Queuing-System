"""Client service for user authentication and management."""
import json
import uvicorn
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import utilities
from utils.config import (
    KAFKA_BROKER, CLIENT_SERVICE_PORT, SERVICE_URLS
)
from utils.data_persistence import load_dict_data, save_dict_data
from utils.logger_config import setup_logger
from utils.security import (
    hash_password, verify_password, sanitize_input,
    create_access_token, create_refresh_token, verify_token
)
from utils.models import ClientRegister, ClientLogin, TokenResponse

# Setup logger
logger = setup_logger(__name__, "client_service.log")

# Define FastAPI app
app = FastAPI(
    title="Client Service",
    description="Service for user authentication and management",
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
                logger.error("Failed to connect to Kafka after retries. Continuing without Kafka.")
                return None

producer = create_kafka_producer()

# Load data from persistence
def load_data():
    """Load clients data from JSON file."""
    global clients_db, client_id_counter
    
    clients_db = load_dict_data("clients")
    
    # Calculate next client_id from existing data
    if clients_db:
        max_id = 1000
        for cid in clients_db.keys():
            if cid.startswith("C") and len(cid) > 1:
                try:
                    num = int(cid[1:])
                    max_id = max(max_id, num)
                except ValueError:
                    pass
        client_id_counter = max_id + 1
    else:
        client_id_counter = 1000
    
    # Create default admin user if not exists
    admin_exists = any(
        client.get("is_admin", False) for client in clients_db.values()
    )
    if not admin_exists:
        admin_id = "C0001"
        clients_db[admin_id] = {
            "client_id": admin_id,
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "name": "System Administrator",
            "email": "admin@barbershop.com",
            "phone": "0000000000",
            "is_admin": True,
            "registered_at": datetime.now().isoformat()
        }
        save_clients()
        logger.info("Default admin user created (username: admin, password: admin123)")
    
    logger.info(f"Loaded {len(clients_db)} clients")

def save_clients():
    """Save clients to JSON file."""
    if save_dict_data("clients", clients_db):
        logger.debug("Clients saved successfully")
    else:
        logger.error("Failed to save clients")

# Initialize data
clients_db: Dict[str, Any] = {}
client_id_counter: int = 1000

# Load on startup
load_data()

# Dependency for token verification
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Verify JWT token and return current user.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        User information from token
    """
    try:
        payload = verify_token(credentials.credentials, token_type="access")
        client_id = payload.get("sub")
        if client_id not in clients_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return clients_db[client_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
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
        "service": "client",
        "timestamp": datetime.now().isoformat(),
        "clients_count": len(clients_db)
    }

# Client endpoints
@app.post("/register/", response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def register_client(request: Request, client: ClientRegister):
    """
    Register a new client.
    
    Args:
        client: Client registration information
        
    Returns:
        Registration confirmation with client ID
    """
    global clients_db, client_id_counter
    try:
        # Sanitize inputs
        username = sanitize_input(client.username)
        name = sanitize_input(client.name)
        email = sanitize_input(client.email)
        phone = sanitize_input(client.phone)
        
        logger.info(f"Registration attempt for username: {username}")
        
        # Check if username already exists
        for existing_client in clients_db.values():
            if existing_client.get("username") == username:
                logger.warning(f"Registration failed: username {username} already exists")
                raise HTTPException(
                    status_code=400,
                    detail="Username already exists"
                )
        
        # Validate password strength
        if len(client.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters"
            )
        
        # Generate client ID
        client_id = f"C{client_id_counter:04d}"
        client_id_counter += 1
        
        # Hash password
        hashed_password = hash_password(client.password)
        
        # Create client entry
        client_data = {
            "client_id": client_id,
            "username": username,
            "password_hash": hashed_password,
            "name": name,
            "email": email,
            "phone": phone,
            "is_admin": client.is_admin if hasattr(client, 'is_admin') else False,
            "registered_at": datetime.now().isoformat()
        }
        
        # Save to local DB
        clients_db[client_id] = client_data
        save_clients()
        
        # Send event for client registration
        if producer:
            try:
                producer.send('client-logged-in', {
                    "event_type": "client_registered",
                    "data": {
                        "client_id": client_id,
                        "username": username,
                        "name": name,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                producer.flush()
            except KafkaError as e:
                logger.error(f"Failed to send Kafka message: {e}")
        
        logger.info(f"Client {client_id} registered successfully")
        
        # Return success with client ID (no password)
        client_info = {k: v for k, v in client_data.items() if k != "password_hash"}
        return {
            "client_id": client_id,
            "client": client_info,
            "message": "Registration successful"
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/login/", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_client(request: Request, login: ClientLogin):
    """
    Authenticate a client and return JWT tokens.
    
    Args:
        login: Login credentials
        
    Returns:
        JWT access and refresh tokens
    """
    try:
        username = sanitize_input(login.username)
        logger.info(f"Login attempt for username: {username}")
        
        # Find client by username
        client = None
        client_id = None
        
        for c_id, c_data in clients_db.items():
            if c_data.get("username") == username:
                client = c_data
                client_id = c_id
                break
        
        if not client:
            logger.warning(f"Login failed: username {username} not found")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(login.password, client.get("password_hash", "")):
            logger.warning(f"Login failed: invalid password for {username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Create JWT tokens
        token_data = {
            "sub": client_id,
            "username": client.get("username"),
            "is_admin": client.get("is_admin", False)
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Send login event
        if producer:
            try:
                producer.send('client-logged-in', {
                    "event_type": "client_logged_in",
                    "data": {
                        "client_id": client_id,
                        "username": client.get("username"),
                        "name": client.get("name"),
                        "timestamp": datetime.now().isoformat()
                    }
                })
                producer.flush()
            except KafkaError as e:
                logger.error(f"Failed to send Kafka message: {e}")
        
        logger.info(f"Client {client_id} logged in successfully")
        
        # Return client data (without password) and tokens
        client_info = {k: v for k, v in client.items() if k != "password_hash"}
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            client_id=client_id,
            client=client_info
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/refresh/")
async def refresh_token_endpoint(refresh_token: str):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Refresh token string
        
    Returns:
        New access token
    """
    try:
        payload = verify_token(refresh_token, token_type="refresh")
        client_id = payload.get("sub")
        
        if client_id not in clients_db:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        
        client = clients_db[client_id]
        token_data = {
            "sub": client_id,
            "username": client.get("username"),
            "is_admin": client.get("is_admin", False)
        }
        
        new_access_token = create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

@app.get("/client/{client_id}")
async def get_client(client_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Get client information.
    
    Args:
        client_id: Client ID
        current_user: Current authenticated user
        
    Returns:
        Client information
    """
    client_id = sanitize_input(client_id)
    
    # Allow users to view their own profile or admins to view any profile
    if client_id != current_user.get("client_id") and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this client"
        )
    
    if client_id not in clients_db:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )
    
    # Return client data (without password)
    client_info = {
        k: v for k, v in clients_db[client_id].items()
        if k != "password_hash"
    }
    return client_info

@app.get("/clients/")
async def get_all_clients(current_user: Dict = Depends(get_current_user)):
    """
    Get all clients (admin only).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of all clients
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    # Return all clients (without passwords)
    clients = [
        {k: v for k, v in client.items() if k != "password_hash"}
        for client in clients_db.values()
    ]
    
    return {"clients": clients}

@app.get("/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        Current user information
    """
    client_info = {
        k: v for k, v in current_user.items()
        if k != "password_hash"
    }
    return client_info

# Graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Handle graceful shutdown."""
    logger.info("Shutting down client service")
    save_clients()
    if producer:
        producer.close()

# Run the service
if __name__ == "__main__":
    logger.info(f"Starting client service on port {CLIENT_SERVICE_PORT}")
    uvicorn.run(
        "client_service:app",
        host="0.0.0.0",
        port=CLIENT_SERVICE_PORT,
        reload=True
    )
