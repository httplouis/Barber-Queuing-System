# ✂️ Barber Queuing System - Enhanced Edition

## Complete Production-Ready Microservices-Based Queue Management System

This is a fully functional, production-ready barber shop queuing system built with FastAPI, Kafka, CustomTkinter, and modern best practices.

---

## 🏗️ Architecture

### Microservices:
- **Booking Service** (Port 8000) - Handles appointments and queue entries with persistence
- **Client Service** (Port 8001) - User authentication with JWT tokens
- **Feedback Service** (Port 8002) - Customer feedback management
- **Notification Service** (Port 8003) - Real-time notifications via FastAPI
- **Barber Service** (Port 8004) - Barber and service management
- **Admin Service** (Port 8005) - Administrative operations
- **Analytics Service** (Port 8006) - Analytics and reporting
- **Queue Service** - Kafka consumer for queue processing

### Client Applications:
- **GUI Client** (`client_app.py`) - Modern CustomTkinter interface with JWT authentication
- **Admin Dashboard** (`admin_dashboard.py`) - Comprehensive admin interface

---

## ✨ New Features (Enhanced Edition)

### 🔐 Security
- **JWT Authentication** - Secure token-based authentication
- **Password Hashing** - Bcrypt password hashing
- **Rate Limiting** - API rate limiting to prevent abuse
- **Input Sanitization** - Protection against injection attacks
- **CORS Configuration** - Proper cross-origin resource sharing

### 💾 Data Persistence
- **JSON File Storage** - All data persists across service restarts
- **Atomic Writes** - Prevents data corruption
- **Auto-save** - Automatic data saving on changes
- **Data Directory** - Organized data storage in `data/` folder

### 📊 Analytics & Reporting
- **Popular Services** - Track most booked services
- **Barber Performance** - Ratings and booking statistics
- **Revenue Reports** - Financial analytics
- **Daily Bookings** - Booking trends over time
- **Queue Statistics** - Real-time queue metrics

### 👨‍💼 Admin Dashboard
- **Dashboard Overview** - Real-time statistics
- **Queue Management** - View and manage queue
- **Barber Management** - Add/edit barbers
- **Booking Management** - View all bookings
- **User Management** - Manage client accounts
- **Analytics View** - Comprehensive reports

### 🎨 UI/UX Enhancements
- **Modern Design** - Improved visual appearance
- **Progress Bars** - Queue position visualization
- **Icons & Emojis** - Better visual feedback
- **Smooth Transitions** - Frame switching animations
- **Loading States** - Better user feedback
- **Toast Notifications** - Success/error messages

### 🔧 Code Quality
- **Type Hints** - Full type annotation
- **Comprehensive Docstrings** - Google-style documentation
- **Structured Logging** - File and console logging
- **Error Handling** - Graceful error management
- **Health Checks** - Service health monitoring
- **Retry Logic** - Automatic connection retries

### 🧪 Testing
- **Unit Tests** - Service endpoint tests
- **Integration Tests** - End-to-end testing
- **Test Fixtures** - Reusable test data

---

## 📋 Prerequisites

1. **Python 3.8+**
2. **Kafka** running on `localhost:9092`
3. **Required Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Quick Start

### Option 1: Use the Batch Script (Windows)
```bash
start_all_services.bat
```

This will start all services in separate windows. Then run:
```bash
# Client Application
python client_app.py

# Admin Dashboard
python admin_dashboard.py
```

### Option 2: Manual Start

**1. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**2. Start Kafka** (if not already running)

**3. Start each service in separate terminals:**

```bash
# Terminal 1 - Booking Service
python booking_service.py

# Terminal 2 - Client Service
python client_service.py

# Terminal 3 - Feedback Service
python feedback_service.py

# Terminal 4 - Notification Service
python notification_service.py

# Terminal 5 - Barber Service
python barber_service.py

# Terminal 6 - Admin Service
python admin_service.py

# Terminal 7 - Analytics Service
python analytics_service.py

# Terminal 8 - Queue Service
python queue_service.py

# Terminal 9 - Client GUI
python client_app.py

# Terminal 10 - Admin Dashboard
python admin_dashboard.py
```

---

## 🔑 Default Credentials

### Admin Account
- **Username:** `admin`
- **Password:** `admin123`

This account is automatically created on first run.

---

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

---

## 🎯 Features

### Client Features
✅ User Registration & Login with JWT  
✅ Book Appointments  
✅ Join Queue (Walk-ins)  
✅ Real-time Queue Updates  
✅ Queue Position Progress Bar  
✅ Notifications  
✅ Feedback System  
✅ View Appointments  
✅ Cancel Appointments  

### Admin Features
✅ Dashboard Overview  
✅ Queue Management  
✅ Barber Management  
✅ Booking Management  
✅ User Management  
✅ Analytics & Reports  
✅ Real-time Statistics  

### System Features
✅ Data Persistence  
✅ JWT Authentication  
✅ Rate Limiting  
✅ Structured Logging  
✅ Health Checks  
✅ Error Handling  
✅ Retry Logic  

---

## 🔄 Kafka Topics

- `booking-created` - New bookings/queue entries
- `queue-updated` - Queue status changes
- `feedback-submitted` - Feedback submissions
- `client-logged-in` - Login events
- `notification-updated` - Notification events
- `barber-feedback` - Barber feedback

---

## 📁 File Structure

```
lastna/
├── booking_service.py          # Booking & Queue API
├── client_service.py           # Authentication API
├── feedback_service.py         # Feedback API
├── notification_service.py     # Notifications API
├── barber_service.py           # Barber & Services API
├── admin_service.py            # Admin API
├── analytics_service.py        # Analytics API
├── queue_service.py            # Queue Processor
├── client_app.py               # GUI Client
├── admin_dashboard.py          # Admin Dashboard
├── start_all_services.bat      # Startup script
├── requirements.txt             # Dependencies
├── utils/                      # Utility modules
│   ├── config.py               # Configuration
│   ├── data_persistence.py     # Data persistence
│   ├── logger_config.py        # Logging setup
│   ├── security.py             # Security utilities
│   └── models.py               # Shared models
├── data/                       # Data storage (auto-created)
│   ├── bookings.json
│   ├── clients.json
│   ├── feedback.json
│   ├── barbers.json
│   ├── services.json
│   ├── queue.json
│   └── notifications.json
├── logs/                       # Log files (auto-created)
└── tests/                      # Test suite
    ├── conftest.py
    ├── test_client_service.py
    └── test_booking_service.py
```

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (services must be running)
pytest tests/
```

---

## 📝 Configuration

Configuration is managed through environment variables and `utils/config.py`:

- `BOOKING_SERVICE_PORT` - Booking service port (default: 8000)
- `CLIENT_SERVICE_PORT` - Client service port (default: 8001)
- `KAFKA_BROKER` - Kafka broker address (default: localhost:9092)
- `JWT_SECRET_KEY` - JWT secret key (change in production!)
- `LOG_LEVEL` - Logging level (default: INFO)

---

## 🐛 Troubleshooting

**Issue: Services won't start**
- Check if Kafka is running on `localhost:9092`
- Verify all Python packages are installed: `pip install -r requirements.txt`
- Check if ports 8000-8006 are available
- Check logs in `logs/` directory

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
- Check service URLs in `client_app.py`
- Verify network connectivity
- Check firewall settings

**Issue: Queue not updating**
- Verify queue_service.py is running
- Check Kafka connection
- Ensure booking service is sending events
- Check queue service logs

---

## 🔒 Security Notes

- **Change JWT_SECRET_KEY** in production
- **Use HTTPS** in production
- **Set strong passwords** for admin account
- **Enable rate limiting** (already configured)
- **Review CORS settings** for production
- **Secure data directory** permissions

---

## 📊 Data Persistence

All data is automatically saved to JSON files in the `data/` directory:
- Data persists across service restarts
- Atomic writes prevent corruption
- Automatic backup on changes
- Easy to backup and restore

---

## 🚀 Production Deployment

For production deployment:
1. Set environment variables for configuration
2. Use a production WSGI server (e.g., Gunicorn)
3. Set up proper database (PostgreSQL/MySQL)
4. Configure HTTPS
5. Set up monitoring and logging
6. Use process manager (systemd, supervisor)
7. Configure reverse proxy (Nginx)
8. Set up Kafka cluster
9. Enable authentication for all services
10. Configure backup strategy

---

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

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing style
- Tests are included
- Documentation is updated
- All services remain functional

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review service logs in `logs/` directory
3. Verify all prerequisites are met
4. Check Kafka connectivity

---

**Version:** 2.0.0 (Enhanced Edition)  
**Last Updated:** 2024
