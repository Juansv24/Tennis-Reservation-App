"""
Configuration for load testing Tennis Reservation App User App
Centralized settings for URLs, credentials, timeouts, and test parameters
"""
from datetime import datetime, timedelta

# ============================================================================
# APP CONFIGURATION
# ============================================================================

# User App URL (local development)
USER_APP_URL = "http://localhost:8501"

# Timeouts (seconds)
PAGE_LOAD_TIMEOUT = 15
ELEMENT_WAIT_TIMEOUT = 10
LOGIN_TIMEOUT = 20
RESERVATION_TIMEOUT = 15

# ============================================================================
# TEST USER CREDENTIALS
# ============================================================================

# Test users that should be pre-created in Supabase with email verification done
TEST_USERS = {
    "user1": {
        "email": "testuser01@example.com",
        "password": "Juansebastian24",
        "profile": "A"  # Browser profile
    },
    "user2": {
        "email": "testuser02@example.com",
        "password": "Juansebastian24",
        "profile": "A"  # Browser profile
    },
    "user3": {
        "email": "testuser03@example.com",
        "password": "Juansebastian24",
        "profile": "A"  # Browser profile
    },
    "user4": {
        "email": "testuser04@example.com",
        "password": "Juansebastian24",
        "profile": "B"  # Maker (8am)
    },
    "user5": {
        "email": "testuser05@example.com",
        "password": "Juansebastian24",
        "profile": "B"  # Maker (11am)
    },
    "user6": {
        "email": "testuser06@example.com",
        "password": "Juansebastian24",
        "profile": "B"  # Maker (2pm)
    },
    "user7": {
        "email": "testuser07@example.com",
        "password": "Juansebastian24",
        "profile": "C"  # Competitive (10-11am)
    },
    "user8": {
        "email": "testuser08@example.com",
        "password": "Juansebastian24",
        "profile": "C"  # Competitive (10-11am)
    },
    "user9": {
        "email": "testuser09@example.com",
        "password": "Juansebastian24",
        "profile": "D"  # Info checker
    },
    "user10": {
        "email": "testuser10@example.com",
        "password": "Juansebastian24",
        "profile": "D"  # Info checker
    },
}

# ============================================================================
# TEST DATA CONFIGURATION
# ============================================================================

# Reservation test date (use tomorrow or a future date to avoid past dates)
# Default: tomorrow
RESERVATION_DATE = (datetime.now() + timedelta(days=1)).date()

# Court hours for testing (based on your app's available hours)
# Format: hour as integer (6 = 6am, 10 = 10am, 14 = 2pm, etc.)
AVAILABLE_HOURS = {
    "user4_profile_b": 8,      # User 4 reserves 8am
    "user5_profile_b": 11,     # User 5 reserves 11am
    "user6_profile_b": 14,     # User 6 reserves 2pm
    "user7_competitive": 10,   # User 7 tries 10-11am (competitive)
    "user8_competitive": 10,   # User 8 tries 10-11am (competitive)
}

# ============================================================================
# SELENIUM CONFIGURATION
# ============================================================================

# Browser settings
BROWSER_TYPE = "chrome"  # or "firefox"
HEADLESS_MODE = False    # Set to True to run without opening browser windows
WINDOW_SIZE = "1920,1080"

# Selenium wait strategy
IMPLICIT_WAIT = 5  # seconds (fallback, explicit waits preferred)

# ============================================================================
# LOAD TEST EXECUTION CONFIGURATION
# ============================================================================

# Number of concurrent users
NUM_CONCURRENT_USERS = 10

# Number of parallel workers for ThreadPoolExecutor
# (typically same as NUM_CONCURRENT_USERS)
MAX_WORKERS = 10

# Start delay between users (seconds)
# 0 = all start simultaneously, 0.1 = slight stagger
USER_START_DELAY = 0

# Max duration for entire load test (seconds)
# Test will stop after this time if still running
MAX_TEST_DURATION = 300  # 5 minutes

# ============================================================================
# METRICS & REPORTING
# ============================================================================

# Output directory for test results
RESULTS_DIR = "load_tests/results"

# Report file names
METRICS_CSV = "metrics.csv"
ERROR_LOG = "errors.log"
SUMMARY_JSON = "summary.json"
REPORT_HTML = "report.html"

# Enable real-time console output
VERBOSE_MODE = True

# ============================================================================
# STREAMLIT-SPECIFIC SETTINGS
# ============================================================================

# Wait for Streamlit to be ready (check if it's running)
WAIT_FOR_APP = True
APP_READY_TIMEOUT = 30  # seconds

# Expected elements to look for after login (to verify successful login)
LOGIN_SUCCESS_INDICATORS = [
    "text:📋 Información de tu Cuenta",  # Dashboard heading
    "text:Tus Reservas",                  # Your Reservations section
    "text:Créditos disponibles",          # Credits display
]

# Streamlit-specific waits (Streamlit reruns dynamically)
STREAMLIT_RERUN_WAIT = 2  # seconds to wait for rerun after interaction

# ============================================================================
# DEBUG & LOGGING
# ============================================================================

# Enable debug logging
DEBUG_MODE = False

# Capture screenshots on error
SCREENSHOT_ON_ERROR = True

# Screenshots directory
SCREENSHOTS_DIR = "load_tests/results/screenshots"
