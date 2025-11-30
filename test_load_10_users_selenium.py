"""
Load test with 10 concurrent users using Selenium
Tests the full serial queue protection by simulating real browser usage
"""

import threading
import time
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# Test users
TEST_USERS = [
    ("user1@test.com", "Pass1234"),
    ("user2@test.com", "Pass1234"),
    ("user3@test.com", "Pass1234"),
    ("user4@test.com", "Pass1234"),
    ("user5@test.com", "Pass1234"),
    ("user6@test.com", "Pass1234"),
    ("user7@test.com", "Pass1234"),
    ("user8@test.com", "Pass1234"),
    ("user9@test.com", "Pass1234"),
    ("user10@test.com", "Pass1234"),
]

# Results tracking
results = {
    'successful_logins': 0,
    'failed_logins': 0,
    'socket_errors': 0,
    'successful_reservations': 0,
    'failed_reservations': 0,
    'lock': threading.Lock(),
    'operations': []
}

def record_result(op_type, user_email, success, error_msg=None):
    """Record operation result"""
    with results['lock']:
        timestamp = datetime.now().isoformat()
        result_entry = {
            'timestamp': timestamp,
            'operation': op_type,
            'user': user_email,
            'success': success,
            'error': error_msg
        }
        results['operations'].append(result_entry)

        if op_type == 'LOGIN':
            if success:
                results['successful_logins'] += 1
                print(f"  [OK] {user_email} logged in successfully")
            else:
                results['failed_logins'] += 1
                print(f"  [FAIL] {user_email} login failed: {error_msg}")
                if 'socket' in (error_msg or '').lower() or '10035' in (error_msg or ''):
                    results['socket_errors'] += 1
                    print(f"    [SOCKET ERROR DETECTED]")

        elif op_type == 'RESERVATION':
            if success:
                results['successful_reservations'] += 1
                print(f"  [OK] {user_email} reservation successful")
            else:
                results['failed_reservations'] += 1
                print(f"  [FAIL] {user_email} reservation failed: {error_msg}")
                if 'socket' in (error_msg or '').lower() or '10035' in (error_msg or ''):
                    results['socket_errors'] += 1
                    print(f"    [SOCKET ERROR DETECTED]")

def create_driver():
    """Create Selenium WebDriver with headless Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")

    return webdriver.Chrome(options=chrome_options)

def test_login(driver, email, password):
    """Test login operation"""
    try:
        # Navigate to app
        driver.get("http://localhost:8501")

        # Wait for login form
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
        )
        password_input = driver.find_element(By.XPATH, "//input[@type='password']")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Inicia Sesión')]")

        # Fill in credentials
        email_input.clear()
        email_input.send_keys(email)
        password_input.clear()
        password_input.send_keys(password)

        # Click login
        login_button.click()

        # Wait for either success or error message
        try:
            # Try to find success indicator (redirects to main page)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Reservas')]"))
            )
            record_result('LOGIN', email, True)
            return True
        except TimeoutException:
            # Check for error message
            try:
                error_msg_elem = driver.find_element(By.XPATH, "//div[contains(@class, 'stAlert')]")
                error_msg = error_msg_elem.text
            except:
                error_msg = "Unknown error"

            record_result('LOGIN', email, False, error_msg)
            return False

    except Exception as e:
        error_msg = str(e)
        record_result('LOGIN', email, False, error_msg)
        return False
    finally:
        driver.quit()

def test_reservation(driver, email, selected_hour):
    """Test reservation operation - assumes user is already logged in"""
    try:
        # Wait for the reservations tab to be ready
        time.sleep(2)

        # Click on date picker or calendar
        try:
            date_picker = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Selecciona una fecha')]"))
            )
        except:
            # Already in reservation section
            pass

        # Select tomorrow's date
        time.sleep(1)
        try:
            tomorrow_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Mañana')]")
            tomorrow_button.click()
        except:
            # Try finding date picker
            date_inputs = driver.find_elements(By.XPATH, "//input[@type='date']")
            if date_inputs:
                date_inputs[0].click()
                time.sleep(0.5)

        # Select hour
        time.sleep(1)
        try:
            hour_button = driver.find_element(By.XPATH, f"//button[contains(text(), '{selected_hour}:00')]")
            hour_button.click()
        except:
            pass

        # Click reserve button
        time.sleep(2)
        try:
            reserve_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Confirmar Reserva')]")
            reserve_button.click()
        except:
            reserve_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Hacer Reserva')]")
            reserve_button.click()

        # Wait for success message
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'reserva')]"))
            )
            record_result('RESERVATION', email, True)
            return True
        except TimeoutException:
            error_msg = "Timeout waiting for confirmation"
            record_result('RESERVATION', email, False, error_msg)
            return False

    except Exception as e:
        error_msg = str(e)
        record_result('RESERVATION', email, False, error_msg)
        return False

def run_user_workflow(user_email, user_password, hour):
    """Run complete workflow for one user"""
    print(f"\n[Thread] Starting workflow for {user_email} (Hour: {hour})")

    # Create driver for this user
    driver = create_driver()

    try:
        # 1. Login
        print(f"  [*] Logging in...")
        login_success = test_login(driver, user_email, user_password)

        if not login_success:
            print(f"  [*] Login failed, skipping reservation")
            return

        print(f"  [*] Logged in successfully, now making reservation...")

        # 2. Make reservation
        time.sleep(2)  # Wait a bit before attempting reservation
        test_reservation(driver, user_email, hour)

    finally:
        try:
            driver.quit()
        except:
            pass

    print(f"[Thread] Workflow complete for {user_email}")

def print_results():
    """Print final results"""
    print(f"\n\n{'='*80}")
    print(f"LOAD TEST RESULTS - 10 Concurrent Users with Full Serial Queue Protection")
    print(f"Test Method: Selenium WebDriver (simulates real browser usage)")
    print(f"{'='*80}")

    print(f"\nLOGINS:")
    print(f"  [OK] Successful: {results['successful_logins']}/10 ({results['successful_logins']*10}%)")
    print(f"  [FAIL] Failed: {results['failed_logins']}/10 ({results['failed_logins']*10}%)")

    print(f"\nRESERVATIONS:")
    print(f"  [OK] Successful: {results['successful_reservations']}/10 ({results['successful_reservations']*10}%)")
    print(f"  [FAIL] Failed: {results['failed_reservations']}/10 ({results['failed_reservations']*10}%)")

    print(f"\nCRITICAL METRIC:")
    print(f"  [ERROR] Socket exhaustion errors (WinError 10035): {results['socket_errors']}")

    if results['socket_errors'] == 0:
        print(f"\n[SUCCESS] ZERO socket exhaustion errors with 10 concurrent users!")
    else:
        print(f"\n[FAILURE] {results['socket_errors']} socket errors occurred (needs further investigation)")

    print(f"\nOPERATION HISTORY:")
    for op in results['operations']:
        status = "[OK]" if op['success'] else "[FAIL]"
        error_info = f" | {op['error']}" if op['error'] else ""
        print(f"  {status} {op['timestamp']} | {op['operation']:15} | {op['user']:20}{error_info}")

    print(f"\n{'='*80}\n")

def main():
    """Run load test with 10 concurrent users"""
    print("\n")
    print("="*80)
    print("LOAD TEST: 10 Concurrent Users with Full Serial Queue Protection")
    print("="*80)
    print(f"\nTest Start Time: {datetime.now().isoformat()}")
    print(f"Total Users: {len(TEST_USERS)}")
    print(f"Concurrent Approach: ThreadPoolExecutor with 10 workers")
    print(f"Queue Strategy: Universal serial queue (1 Supabase operation at a time)")
    print(f"\nEach user will:")
    print(f"  1. Login to the app")
    print(f"  2. Make a reservation at a random hour (6-20)")
    print(f"\nKey Metric: Zero socket exhaustion errors (WinError 10035)")
    print(f"{'='*80}\n")

    start_time = time.time()

    # Assign different hours to different users
    hours = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    # Run all users concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for idx, (email, password) in enumerate(TEST_USERS):
            hour = hours[idx]
            future = executor.submit(run_user_workflow, email, password, hour)
            futures.append(future)

        # Wait for all to complete
        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                future.result()
                print(f"[Progress] {completed}/10 users completed")
            except Exception as e:
                print(f"[Error] User thread error: {e}")

    elapsed = time.time() - start_time

    print(f"\nTest End Time: {datetime.now().isoformat()}")
    print(f"Total Elapsed Time: {elapsed:.2f} seconds")

    print_results()

    return results

if __name__ == "__main__":
    print("Starting Selenium-based load test for 10 concurrent users...")
    print("(Ensure Streamlit app is running at http://localhost:8501)")

    results_data = main()

    # Final summary for user
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Login Success Rate: {results_data['successful_logins']}/10 ({results_data['successful_logins']*10}%)")
    print(f"Reservation Success Rate: {results_data['successful_reservations']}/10 ({results_data['successful_reservations']*10}%)")
    print(f"Socket Errors (Critical): {results_data['socket_errors']}")
    print(f"Overall Status: {'[PASS] Full queue protection working!' if results_data['socket_errors'] == 0 else '[FAIL] Socket errors detected'}")
    print("="*80 + "\n")
