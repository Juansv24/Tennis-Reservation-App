@echo off
REM Quick start script for Windows

echo ========================================
echo Tennis Reservation App - Concurrent Tests
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it.
    echo.
    pause
    exit /b 1
)

REM Run setup (create test users if needed)
echo Setting up test users...
python setup_test_users.py
echo.

REM Run tests
echo Starting concurrent tests...
echo.
python concurrent_test.py %*

echo.
echo ========================================
echo Tests completed!
echo Check test_logs/ folder for detailed results
echo ========================================
pause
