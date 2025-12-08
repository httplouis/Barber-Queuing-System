# ✂️ BarberQue - Barber Shop Queuing System

A modern, production-ready microservices-based barber shop queue management system built with FastAPI, CustomTkinter, and Kafka.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Overview

BarberQue is a comprehensive queue management system designed for barber shops, featuring:
- **Real-time queue management** with position tracking
- **Appointment booking system** with calendar integration
- **Admin dashboard** for comprehensive management
- **Customer mobile-friendly interface**
- **Analytics and reporting** for business insights
- **JWT-based authentication** for secure access

## 🏗️ Architecture

### Microservices Architecture

The system is built using a microservices architecture with the following services:

- **Booking Service** (Port 8000) - Handles appointments and queue entries
- **Client Service** (Port 8001) - User authentication with JWT tokens
- **Feedback Service** (Port 8002) - Customer feedback management
- **Notification Service** (Port 8003) - Real-time notifications
- **Barber Service** (Port 8004) - Barber and service management
- **Admin Service** (Port 8005) - Administrative operations
- **Analytics Service** (Port 8006) - Analytics and reporting
- **Queue Service** - Background queue processing

### Client Applications

- **Customer App** (`gui/client_app.py`) - Modern GUI for customers
- **Admin Dashboard** (`gui/admin_dashboard.py`) - Comprehensive admin interface

## ✨ Features

### Customer Features
- ✅ User Registration & Login with JWT
- ✅ Book Appointments
- ✅ Join Queue (Walk-ins)
- ✅ Real-time Queue Updates
- ✅ Queue Position Progress Bar
- ✅ Notifications
- ✅ Feedback System
- ✅ View & Cancel Appointments

### Admin Features
- ✅ Dashboard Overview with Real-time Statistics
- ✅ Queue Management
- ✅ Barber Management
- ✅ Booking Management
- ✅ User Management
- ✅ Analytics & Reports
- ✅ Revenue Tracking

### System Features
- ✅ Data Persistence (JSON-based)
- ✅ JWT Authentication
- ✅ Rate Limiting
- ✅ Structured Logging
- ✅ Health Checks
- ✅ Error Handling
- ✅ Retry Logic
- ✅ CORS Configuration

## 📋 Prerequisites

1. **Python 3.8+**
2. **Kafka** (optional - system works without it)
3. **Required Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Option 1: Use the Batch Script (Windows)
```bash
scripts/start_all_services.bat
```

Then run the GUI applications:
```bash
# Customer Application
python gui/client_app.py

# Admin Dashboard
python gui/admin_dashboard.py
```

### Option 2: Manual Start

**1. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**2. Start Services:**
```bash
# Terminal 1 - Booking Service
python services/booking_service.py

# Terminal 2 - Client Service
python services/client_service.py

# Terminal 3 - Feedback Service
python services/feedback_service.py

# Terminal 4 - Notification Service
python services/notification_service.py

# Terminal 5 - Barber Service
python services/barber_service.py

# Terminal 6 - Admin Service
python services/admin_service.py

# Terminal 7 - Analytics Service
python services/analytics_service.py

# Terminal 8 - Queue Service (optional)
python services/queue_service.py
```

**3. Start GUI Applications:**
```bash
# Customer App
python gui/client_app.py

# Admin Dashboard
python gui/admin_dashboard.py
```

## 🔑 Default Credentials

### Admin Account
- **Username:** `admin`
- **Password:** `admin123`

This account is automatically created on first run.

## 📡 API Endpoints

### Booking Service (Port 8000)
- `GET /health` - Health check
- `POST /booking/` - Create appointment
- `POST /queue/` - Join queue
- `GET /queue/` - Get queue status
- `GET /queue/{queue_id}` - Get queue entry
- `GET /bookings/` - Get all bookings
- `GET /booking/client/{client_id}` - Get client bookings
- `DELETE /booking/{booking_id}` - Cancel booking

### Client Service (Port 8001)
- `GET /health` - Health check
- `POST /register/` - Register new user
- `POST /login/` - User login (returns JWT tokens)
- `POST /refresh/` - Refresh access token
- `GET /client/{client_id}` - Get client info (requires auth)
- `GET /clients/` - Get all clients (admin only)
- `GET /me` - Get current user info

### Feedback Service (Port 8002)
- `GET /health` - Health check
- `POST /feedback/` - Submit feedback
- `GET /feedback/` - Get all feedback
- `GET /feedback/client/{client_id}` - Get client feedback
- `GET /feedback/barber/{barber_id}` - Get barber feedback

### Notification Service (Port 8003)
- `GET /health` - Health check
- `GET /notifications?client_id={id}` - Get notifications
- `PUT /notifications/{notification_id}/read` - Mark as read

### Barber Service (Port 8004)
- `GET /health` - Health check
- `GET /barbers/` - List all barbers
- `GET /barbers/{barber_id}` - Get barber info
- `POST /barbers/` - Create barber
- `PUT /barbers/{barber_id}/availability` - Update availability
- `GET /services/` - List all services

### Admin Service (Port 8005)
- `GET /health` - Health check
- `GET /dashboard/stats` - Dashboard statistics (admin only)
- `GET /queue/manage` - Queue management (admin only)
- `GET /bookings/all` - All bookings (admin only)
- `GET /clients/all` - All clients (admin only)

### Analytics Service (Port 8006)
- `GET /health` - Health check
- `GET /analytics/popular-services` - Popular services (admin only)
- `GET /analytics/barber-performance` - Barber performance (admin only)
- `GET /analytics/revenue` - Revenue statistics (admin only)
- `GET /analytics/queue-stats` - Queue statistics (admin only)
- `GET /analytics/daily-bookings` - Daily bookings (admin only)

## 📁 Project Structure

```
Barber-Queuing-System/
├── services/                  # Microservices
│   ├── booking_service.py
│   ├── client_service.py
│   ├── feedback_service.py
│   ├── notification_service.py
│   ├── barber_service.py
│   ├── admin_service.py
│   ├── analytics_service.py
│   └── queue_service.py
├── gui/                      # GUI Applications
│   ├── client_app.py
│   └── admin_dashboard.py
├── scripts/                  # Utility Scripts
│   ├── start_all_services.bat
│   ├── capture_gui.py
│   ├── simple_screenshot.py
│   └── take_screenshots.py
├── utils/                    # Utility Modules
│   ├── config.py
│   ├── data_persistence.py
│   ├── logger_config.py
│   ├── security.py
│   └── models.py
├── data/                     # Data Storage (auto-created)
│   ├── bookings.json
│   ├── clients.json
│   ├── feedback.json
│   ├── barbers.json
│   ├── services.json
│   ├── queue.json
│   └── notifications.json
├── logs/                     # Log Files (auto-created)
├── tests/                    # Test Suite
│   ├── conftest.py
│   ├── test_client_service.py
│   └── test_booking_service.py
├── requirements.txt          # Python Dependencies
└── README.md                 # This File
```

## 🔄 Kafka Topics (Optional)

The system can work without Kafka, but supports the following topics for enhanced functionality:
- `booking-created` - New bookings/queue entries
- `queue-updated` - Queue status changes
- `feedback-submitted` - Feedback submissions
- `client-logged-in` - Login events
- `notification-updated` - Notification events
- `barber-feedback` - Barber feedback

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (services must be running)
pytest tests/
```

## 📝 Configuration

Configuration is managed through environment variables and `utils/config.py`:

- `BOOKING_SERVICE_PORT` - Booking service port (default: 8000)
- `CLIENT_SERVICE_PORT` - Client service port (default: 8001)
- `KAFKA_BROKER` - Kafka broker address (default: localhost:9092)
- `JWT_SECRET_KEY` - JWT secret key (change in production!)
- `LOG_LEVEL` - Logging level (default: INFO)

## 🐛 Troubleshooting

**Issue: Services won't start**
- Check if ports 8000-8006 are available
- Verify all Python packages are installed: `pip install -r requirements.txt`
- Check logs in `logs/` directory
- Note: Kafka is optional - services will work without it

**Issue: Authentication fails**
- Verify JWT_SECRET_KEY is set (if using custom)
- Check that client service is running
- Ensure tokens are being sent in Authorization header

**Issue: Data not persisting**
- Check `data/` directory exists and is writable
- Verify file permissions
- Check logs for persistence errors

**Issue: Client app can't connect**
- Ensure all services are running
- Check service URLs in `gui/client_app.py`
- Verify network connectivity
- Check firewall settings

## 🔒 Security Notes

- **Change JWT_SECRET_KEY** in production
- **Use HTTPS** in production
- **Set strong passwords** for admin account
- **Enable rate limiting** (already configured)
- **Review CORS settings** for production
- **Secure data directory** permissions

## 📊 Data Persistence

All data is automatically saved to JSON files in the `data/` directory:
- Data persists across service restarts
- Atomic writes prevent corruption
- Automatic backup on changes
- Easy to backup and restore

## 🚀 Production Deployment

For production deployment:

1. Set environment variables for configuration
2. Use a production WSGI server (e.g., Gunicorn)
3. Set up proper database (PostgreSQL/MySQL)
4. Configure HTTPS
5. Set up monitoring and logging
6. Use process manager (systemd, supervisor)
7. Configure reverse proxy (Nginx)
8. Set up Kafka cluster (optional)
9. Enable authentication for all services
10. Configure backup strategy

## ✅ Status: PRODUCTION-READY

This system is fully enhanced with:
- ✅ Data persistence
- ✅ JWT authentication
- ✅ Comprehensive logging
- ✅ Admin dashboard
- ✅ Analytics & reporting
- ✅ Enhanced UI/UX
- ✅ Security features
- ✅ Error handling
- ✅ Health checks
- ✅ Testing framework

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing style
- Tests are included
- Documentation is updated
- All services remain functional

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review service logs in `logs/` directory
3. Verify all prerequisites are met
4. Check service connectivity

---

**Version:** 2.0.0 (Enhanced Edition)  
**Last Updated:** 2024  
**Repository:** [https://github.com/httplouis/Barber-Queuing-System](https://github.com/httplouis/Barber-Queuing-System)
