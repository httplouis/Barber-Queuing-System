"""Shared Pydantic models for the barber queuing system."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

class QueueRequest(BaseModel):
    """Request model for joining queue."""
    client_id: str = Field(..., min_length=1, max_length=50)
    service_type: Optional[str] = None
    barber_id: Optional[str] = None

class BookingRequest(BaseModel):
    """Request model for creating a booking."""
    client_id: str = Field(..., min_length=1, max_length=50)
    barber_id: str = Field(..., min_length=1, max_length=50)
    service_type: str = Field(..., min_length=1, max_length=50)
    booking_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    booking_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    
    @field_validator('booking_date')
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Invalid date format. Use YYYY-MM-DD')
    
    @field_validator('booking_time')
    @classmethod
    def validate_time(cls, v):
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('Invalid time format. Use HH:MM')

class ClientRegister(BaseModel):
    """Request model for client registration."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    is_admin: bool = False

class ClientLogin(BaseModel):
    """Request model for client login."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

class FeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    client_id: str = Field(..., min_length=1, max_length=50)
    barber_id: str = Field(..., min_length=1, max_length=50)
    service_id: str = Field(..., min_length=1, max_length=50)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)

class BarberCreate(BaseModel):
    """Request model for creating a barber."""
    name: str = Field(..., min_length=1, max_length=100)
    specialties: List[str] = Field(default_factory=list)
    available: bool = True

class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    client_id: str
    client: dict

