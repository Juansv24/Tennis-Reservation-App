# Concurrent User Testing Suite

Comprehensive testing framework for simulating rush hour traffic and validating race condition fixes in the Tennis Reservation App.

## 📋 Overview

This test suite simulates multiple users making reservations simultaneously to:
- ✅ Validate race condition fixes (atomic database operations)
- ✅ Detect white screen crashes (real-time subscription errors)
- ✅ Measure system performance under load
- ✅ Generate detailed logs for debugging

**Key Features:**
- 🦊 **Firefox-based** - Uses GeckoDriver for better stability
- 👀 **Visible Mode** - Watch all 10 browser windows interact simultaneously
- 📐 **Auto-Grid Layout** - Windows arranged in 5x2 grid for easy viewing
- 👑 **All VIP Users** - Tests extended reservation hours (8 AM - 8 PM)
- 💰 **99 Credits Each** - Enables extensive multi-reservation testing
- 🧵 **Multi-threaded** - True concurrent user simulation
- 📊 **Comprehensive Logging** - Thread-safe detailed execution logs

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd Test
pip install -r requirements.txt
```

### 2. Install GeckoDriver (Firefox WebDriver)

The test suite uses **Firefox** for better stability and performance in headless mode.

**Windows:**
```bash
# Using Chocolatey
choco install selenium-gecko-driver

# Or download manually from:
# https://github.com/mozilla/geckodriver/releases
# Extract and add to PATH
```

**macOS:**
```bash
brew install geckodriver
```

**Linux:**
```bash
sudo apt-get install firefox-geckodriver

# Or download manually:
# wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz
# tar -xvzf geckodriver-v0.33.0-linux64.tar.gz
# sudo mv geckodriver /usr/local/bin/
```

**Verify Installation:**
```bash
geckodriver --version
```

### 3. Configure Environment

Create a `.env` file in the `Test/` directory:

```bash
# App URL
APP_URL=http://localhost:3000

# Supabase credentials
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 4. Create Test Users

```bash
python setup_test_users.py
```

This creates 10 test users:
- `testuser1@test.com` through `testuser10@test.com`
- Password: `TestUser2024!`
- **All 10 users are VIP** (can reserve until 8 PM)
- Each with **99 initial credits** for extensive testing

### 5. Run Tests

```bash
# Run with 10 concurrent users (default)
python concurrent_test.py

# Run with custom number of users
python concurrent_test.py --users 5

# Run with custom stagger delay
python concurrent_test.py --users 10 --delay 1.0

# Test against deployed app
python concurrent_test.py --url https://your-app.vercel.app
```

---

## 📊 Test Scenarios

### Scenario 1: Basic Concurrent Reservations
- 10 users login simultaneously
- Each attempts 1-3 random reservations
- Tests race condition handling

### Scenario 2: Rush Hour Simulation
- All 10 VIP users target the same popular time slots
- Maximum concurrency to stress test atomic operations
- Tests extended VIP hours (8 AM - 8 PM window)
- Validates "first come, first served" semantics
- With 99 credits each, users can make many reservation attempts

### Scenario 3: Real-time Update Testing
- Users make reservations while others are browsing
- Tests real-time subscription stability
- Detects white screen crashes

---

## 📁 Output Files

### Log Files (`test_logs/`)

**Main Log:** `test_YYYYMMDD_HHMMSS.log`
```
2025-12-18 10:30:15 - User1 - INFO - ✅ Login successful
2025-12-18 10:30:16 - User2 - INFO - ✅ Login successful
2025-12-18 10:30:17 - User1 - INFO - ✅ Reservation confirmed successfully
2025-12-18 10:30:18 - User2 - WARNING - ⚠️  Race condition: El slot 14:00 del 2025-12-19 ya está reservado
```

**Screenshots:** `screenshot_User{N}_{error}_{timestamp}.png`
- Captured on errors for debugging
- Includes error overlays, timeout screens

---

## 📈 Interpreting Results

### Success Metrics

```
📊 TEST RESULTS SUMMARY
⏱️  Total Duration: 45.32 seconds
👥 Total Users: 10

🔐 Authentication:
   ✅ Successful logins: 10
   ❌ Failed logins: 0

📅 Reservations:
   ✅ Successful: 18
   ❌ Failed: 2

🐛 Errors:
   ⚠️  Race conditions (409): 0    ← Should be 0 after fix!
   🚨 White screen crashes: 0    ← Should be 0 after fix!
   ❌ Other errors: 0

✨ Reservation Success Rate: 90.0%
⚡ Race Condition Rate: 0.0%      ← Target: 0%
```

### What to Look For

#### ✅ GOOD (After Fixes):
- **Race Condition Rate: 0%** - Atomic operations working
- **White Screen Crashes: 0** - Real-time subscriptions stable
- **Success Rate: 70-90%+** - High throughput under load
- **Consistent behavior** - No sporadic failures

#### ❌ BAD (Before Fixes):
- **Race Condition Rate: 10-30%** - TOCTOU race window
- **White Screen Crashes: 1+** - Unhandled subscription errors
- **Success Rate: <60%** - System unstable under load
- **Sporadic failures** - Unpredictable behavior

---

## 🔧 Troubleshooting

### Issue: GeckoDriver not found
```bash
# Make sure GeckoDriver is in PATH
geckodriver --version

# If not found, download and install:
# https://github.com/mozilla/geckodriver/releases

# Or specify path in code:
# webdriver.Firefox(executable_path='/path/to/geckodriver')
```

### Issue: Firefox not installed
```bash
# Install Firefox browser
# Windows: Download from mozilla.org
# macOS: brew install --cask firefox
# Linux: sudo apt-get install firefox
```

### Issue: Test users not logging in
```bash
# Verify test users exist in Supabase
python setup_test_users.py

# Check credentials in .env
cat .env
```

### Issue: No available slots
```bash
# Clear existing reservations (dev only)
# Via Supabase SQL Editor:
DELETE FROM reservations WHERE created_at < NOW();
```

### Issue: Too many browser windows
```bash
# The test opens 10 visible Firefox windows by default
# If you want headless mode (background), edit concurrent_test.py:
# Uncomment line 93:
firefox_options.add_argument('--headless')

# Or reduce number of concurrent users:
python concurrent_test.py --users 5
```

### Issue: Windows not visible / overlapping
```bash
# Windows are auto-arranged in a 5x2 grid
# Adjust your screen resolution or window sizes in concurrent_test.py:
# Line 123: window_width = 380  # Make smaller/larger
# Line 124: window_height = 450
```

---

## 🧪 Advanced Testing

### Custom Test Scenarios

Create `custom_scenarios.py`:

```python
from concurrent_test import UserSimulator, run_concurrent_test

# Test specific time slots
def test_popular_times():
    # All users target 2 PM slot
    pass

# Test VIP vs Regular users
def test_vip_behavior():
    # VIP users can reserve until 8 PM
    pass

# Load test
def test_high_load():
    run_concurrent_test(num_users=50, stagger_delay=0.1)
```

### Performance Benchmarking

```bash
# Baseline (before fixes)
python concurrent_test.py --users 20 > baseline_results.txt

# After fixes
python concurrent_test.py --users 20 > fixed_results.txt

# Compare
diff baseline_results.txt fixed_results.txt
```

---

## 📚 Test User Management

### List Test Users
```bash
# Via Supabase SQL Editor
SELECT email, full_name, credits, is_vip
FROM users
WHERE email LIKE 'testuser%@test.com'
ORDER BY email;
```

### Reset Test User Credits
```bash
# Via Supabase SQL Editor - Reset to 99 credits
UPDATE users
SET credits = 99
WHERE email LIKE 'testuser%@test.com';
```

### Delete Test Users
```bash
# Clean up test users
python setup_test_users.py cleanup
```

### Add More Test Users
```bash
# Edit setup_test_users.py, add to TEST_USERS list:
{"email": "testuser11@test.com", "name": "Test User 11 VIP", "is_vip": True}

# Run setup again
python setup_test_users.py

# Note: All test users should be VIP with 99 credits for consistency
```

---

## 📖 Code Structure

```
Test/
├── concurrent_test.py          # Main test runner (Firefox-based)
├── setup_test_users.py         # User creation script (10 VIP users, 99 credits)
├── create_test_users.sql       # SQL alternative for user creation
├── requirements.txt            # Python dependencies (includes GeckoDriver notes)
├── .env.example                # Environment template
├── run_tests.bat               # Windows quick start
├── run_tests.sh                # Linux/macOS quick start
├── README.md                   # This file
├── .env                        # Environment configuration (create this)
└── test_logs/                  # Test output (auto-created)
    ├── test_YYYYMMDD_HHMMSS.log
    └── screenshot_*.png
```

---

## 🎯 Testing Checklist

Before deploying fixes to production:

- [ ] Run baseline test (10 users)
- [ ] Verify 0% race condition rate
- [ ] Verify 0 white screen crashes
- [ ] Test with 20 users (stress test)
- [ ] Test against staging environment
- [ ] Review all error logs
- [ ] Clear test data before prod deployment

---

## 🔒 Security Notes

- ⚠️ **Never commit `.env` file** (contains service role key)
- ⚠️ **Delete test users from production** database
- ⚠️ **Test users are VIP with 99 credits** - For testing only!
- ⚠️ Use separate Supabase project for testing
- ⚠️ **10 browser windows will open** - Make sure you have screen space!
- ✅ Test users have weak passwords by design (dev only)
- ✅ Windows auto-arrange in grid layout for easy viewing

---

## 📞 Support

If tests fail unexpectedly:
1. Check log files in `test_logs/`
2. Review screenshots for visual errors
3. Verify app is running (`npm run dev`)
4. Check Supabase connection
5. Ensure ChromeDriver version matches Chrome browser

---

## 🎉 Expected Results (After Fixes)

With the atomic batch reservation function and real-time error handling:

```
✅ Race Condition Rate: 0%
✅ White Screen Crashes: 0
✅ Success Rate: 85-95%
✅ Predictable, consistent behavior
✅ True "first come, first served"
```

Before fixes, you would see:
```
❌ Race Condition Rate: 10-30%
❌ White Screen Crashes: 1-3
❌ Success Rate: 40-70%
❌ Sporadic, unpredictable failures
```

---

## 📝 License

This test suite is part of the Tennis Reservation App project.
For internal use only.
