# Load Testing Framework for Tennis Reservation App

Complete load testing suite for the Tennis Reservation App User App with 10 concurrent users.

## Overview

This framework simulates 10 concurrent users with mixed behaviors to test your app's performance and stability:

- **Profile A (3 users)**: Browser - Login → View dashboard → View reservations → Logout
- **Profile B (3 users)**: Maker - Login → Browse slots → Make reservation (different hours) → Logout
- **Profile C (2 users)**: Competitive - Login → Try same hour (10-11am) → Logout (tests contention)
- **Profile D (2 users)**: Info - Login → Check credits → View account → Logout

## Requirements

### Prerequisites

1. **Python 3.7+** with pip
2. **Streamlit app running locally** on http://localhost:8501
3. **10 test users pre-created in Supabase** with email verification completed

### Install Dependencies

```bash
# From the project root directory
pip install selenium webdriver-manager requests
```

## Setup Instructions

### Step 1: Create Test Users in Supabase

Create 10 test users in your Supabase database:

```
Email: user1@test.local, Password: TestPassword123!
Email: user2@test.local, Password: TestPassword123!
Email: user3@test.local, Password: TestPassword123!
... (through user10)
```

**IMPORTANT**: Ensure email verification is marked as completed for all users, so they can login directly.

### Step 2: Update Configuration

Edit `load_tests/config.py` and update:

1. **Test user passwords** (line ~30):
   ```python
   "password": "YOUR_ACTUAL_TEST_PASSWORD",  # Change from TestPassword123!
   ```

2. **User App URL** (line ~7) - if not running on localhost:8501:
   ```python
   USER_APP_URL = "http://localhost:8501"
   ```

3. **Reservation date** (line ~83):
   ```python
   RESERVATION_DATE = (datetime.now() + timedelta(days=7)).date()  # Test next week
   ```

### Step 3: Prepare Your Local Environment

```bash
# Terminal 1 - Start the Streamlit app
cd "User App"
streamlit run app.py

# You should see:
# Local URL: http://localhost:8501
```

## Running the Load Test

### Quick Start

```bash
# Terminal 2 - Run load test
cd load_tests
python load_test_user_app.py
```

### Expected Output

```
================================================================================
LOAD TEST: Tennis Reservation App User App
================================================================================
Number of Users: 10
Max Workers: 10
App URL: http://localhost:8501
================================================================================

⏳ Waiting for app at http://localhost:8501...
✅ App is ready!

👤 Starting user1 (Profile A)...
👤 Starting user2 (Profile A)...
👤 Starting user3 (Profile A)...
👤 Starting user4 (Profile B)...
...

✅ user1 (Profile A) completed
✅ user2 (Profile A) completed
...

================================================================================
LOAD TEST SUMMARY
================================================================================
Total Operations: 150
Successful: 148
Failed: 2
Success Rate: 98.67%

Timing (successful operations):
  Average: 1,234.56ms
  Min: 450.23ms
  Max: 8,956.78ms

Test Duration: 45.32s
Operations/Second: 3.31
================================================================================
```

## Test Results

Results are saved to `load_tests/results/`:

### Files Generated

1. **metrics.csv** - Raw metrics data
   - Timestamp, user_id, user_profile, operation, status, duration_ms, error details
   - Open in Excel/Python for analysis

2. **summary.json** - Summary statistics
   - Success rate, average response times, error counts, operation counts

3. **errors.log** - Detailed error information (if errors occur)

4. **screenshots/** - Error screenshots (if SCREENSHOT_ON_ERROR enabled)

### Analyzing Results

#### View Summary
```bash
# In Python
import json
with open("results/summary.json") as f:
    summary = json.load(f)
    print(f"Success Rate: {summary['success_rate_percent']:.2f}%")
    print(f"Avg Response Time: {summary['avg_duration_ms']:.2f}ms")
```

#### View Raw Metrics
```bash
# In Python
import pandas as pd
metrics = pd.read_csv("results/metrics.csv")

# Filter by operation type
logins = metrics[metrics['operation'] == 'login']
print(f"Login avg time: {logins['duration_ms'].mean():.2f}ms")

# Filter by status
failures = metrics[metrics['status'] != 'success']
print(f"Failed operations: {len(failures)}")
for _, row in failures.iterrows():
    print(f"  {row['user_id']}: {row['error_type']} - {row['error_message']}")
```

## Configuration Reference

Edit `config.py` to customize:

### Timeouts
```python
PAGE_LOAD_TIMEOUT = 15      # Max wait for page load
LOGIN_TIMEOUT = 20          # Max wait for login to complete
ELEMENT_WAIT_TIMEOUT = 10   # Max wait for elements to appear
```

### Test Parameters
```python
NUM_CONCURRENT_USERS = 10   # Number of concurrent users
MAX_WORKERS = 10            # Parallel workers (usually same as users)
USER_START_DELAY = 0        # Seconds between user starts (0 = simultaneous)
MAX_TEST_DURATION = 300     # Max test duration (5 minutes)
```

### Browser Settings
```python
BROWSER_TYPE = "chrome"     # or "firefox"
HEADLESS_MODE = False       # Set True to hide browser windows
```

### Output
```python
RESULTS_DIR = "load_tests/results"  # Where to save results
VERBOSE_MODE = True                 # Print detailed logs
```

## Troubleshooting

### Test Won't Start

**Problem**: "App not ready after 30 seconds"
- **Solution**: Make sure Streamlit app is running on localhost:8501

```bash
cd "User App"
streamlit run app.py
```

### Login Failures

**Problem**: All users fail to login
- **Solution 1**: Verify test users exist in Supabase with email verification done
- **Solution 2**: Check that passwords in `config.py` match actual passwords
- **Solution 3**: Verify form element selectors in `user_scenarios.py` match your app's HTML

### Selenium Errors

**Problem**: "ChromeDriver not found"
- **Solution**: Reinstall webdriver-manager
```bash
pip install --upgrade webdriver-manager
```

**Problem**: "Element not found" or "TimeoutException"
- **Solution**: App UI selectors may need adjustment. Update `user_scenarios.py` with correct XPath/CSS selectors

### Memory Issues (many browser windows)

**Problem**: Computer slows down with 10 browser windows
- **Solution 1**: Set `HEADLESS_MODE = True` in `config.py`
- **Solution 2**: Reduce `NUM_CONCURRENT_USERS` for initial testing
- **Solution 3**: Increase browser close time to avoid memory buildup

## Advanced Usage

### Run Subset of Users
```python
# In config.py
NUM_CONCURRENT_USERS = 3  # Test with fewer users
```

### Run Specific Profiles Only
```python
# Modify load_test_user_app.py to select specific users:
user_keys = list(self.test_users.keys())[:3]  # Only first 3 users
```

### Extend Test Duration
```python
# In config.py
MAX_TEST_DURATION = 600  # 10 minutes instead of 5
```

### Generate HTML Report
```python
# After running test, generate report with:
python generate_report.py
# (if report generation module is available)
```

## Performance Targets

After fixing all 6 concurrent user issues, your app should achieve:

| Metric | Target | Expected |
|--------|--------|----------|
| Success Rate | > 98% | ✅ 98-100% |
| Avg Login Time | < 2000ms | ✅ 1000-1500ms |
| Avg Reservation Time | < 3000ms | ✅ 1500-2500ms |
| Failed Operations | 0-2 | ✅ 0-5 |
| Errno 11 Errors | 0 | ✅ 0 |
| Concurrent User Capacity | 10-15 users | ✅ Achievable |

## Next Steps

1. **Run the test** and collect baseline metrics
2. **Analyze results** - Identify slow operations or errors
3. **Optimize** - Use results to fix bottlenecks
4. **Rerun test** - Verify improvements
5. **Scale up** - Test with 15+ concurrent users

## Support

For issues or questions:
1. Check error messages in `results/errors.log`
2. Review HTML screenshots in `results/screenshots/`
3. Check Streamlit app logs (Terminal 1)
4. Review test execution logs (Terminal 2)

---

**Last Updated**: 2024-11-28
**Version**: 1.0
