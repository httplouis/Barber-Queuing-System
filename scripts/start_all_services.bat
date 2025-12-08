@echo off
echo ========================================
echo Starting Barber Queuing System Services
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Kafka is running (optional check)
echo Checking services...
echo.

REM Start services in separate windows
echo Starting Booking Service (Port 8000)...
start "Booking Service" cmd /k "cd /d %~dp0\.. && python services/booking_service.py"

timeout /t 2 /nobreak >nul

echo Starting Client Service (Port 8001)...
start "Client Service" cmd /k "cd /d %~dp0\.. && python services/client_service.py"

timeout /t 2 /nobreak >nul

echo Starting Feedback Service (Port 8002)...
start "Feedback Service" cmd /k "cd /d %~dp0\.. && python services/feedback_service.py"

timeout /t 2 /nobreak >nul

echo Starting Notification Service (Port 8003)...
start "Notification Service" cmd /k "cd /d %~dp0\.. && python services/notification_service.py"

timeout /t 2 /nobreak >nul

echo Starting Barber Service (Port 8004)...
start "Barber Service" cmd /k "cd /d %~dp0\.. && python services/barber_service.py"

timeout /t 2 /nobreak >nul

echo Starting Admin Service (Port 8005)...
start "Admin Service" cmd /k "cd /d %~dp0\.. && python services/admin_service.py"

timeout /t 2 /nobreak >nul

echo Starting Analytics Service (Port 8006)...
start "Analytics Service" cmd /k "cd /d %~dp0\.. && python services/analytics_service.py"

timeout /t 2 /nobreak >nul

echo Starting Queue Service...
start "Queue Service" cmd /k "cd /d %~dp0\.. && python services/queue_service.py"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Services running on:
echo   - Booking Service:    http://localhost:8000
echo   - Client Service:     http://localhost:8001
echo   - Feedback Service:   http://localhost:8002
echo   - Notification Service: http://localhost:8003
echo   - Barber Service:     http://localhost:8004
echo   - Admin Service:       http://localhost:8005
echo   - Analytics Service:  http://localhost:8006
echo   - Queue Service:       (Background process)
echo.
echo To start the client application:
echo   python gui/client_app.py
echo.
echo To start the admin dashboard:
echo   python gui/admin_dashboard.py
echo.
echo Press any key to exit this window...
pause >nul
