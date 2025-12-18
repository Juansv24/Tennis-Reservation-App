"""
Concurrent User Testing for Tennis Reservation App
Simulates rush hour with multiple users making reservations simultaneously
Tests race condition fixes and system stability under load
"""

import os
import time
import random
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
APP_URL = os.getenv('APP_URL', 'http://localhost:3000')
TEST_USERS = [
    {"email": "testuser1@test.com", "password": "TestUser2024!", "name": "Test User 1 VIP"},
    {"email": "testuser2@test.com", "password": "TestUser2024!", "name": "Test User 2 VIP"},
    {"email": "testuser3@test.com", "password": "TestUser2024!", "name": "Test User 3 VIP"},
    {"email": "testuser4@test.com", "password": "TestUser2024!", "name": "Test User 4 VIP"},
    {"email": "testuser5@test.com", "password": "TestUser2024!", "name": "Test User 5 VIP"},
    {"email": "testuser6@test.com", "password": "TestUser2024!", "name": "Test User 6 VIP"},
    {"email": "testuser7@test.com", "password": "TestUser2024!", "name": "Test User 7 VIP"},
    {"email": "testuser8@test.com", "password": "TestUser2024!", "name": "Test User 8 VIP"},
    {"email": "testuser9@test.com", "password": "TestUser2024!", "name": "Test User 9 VIP"},
    {"email": "testuser10@test.com", "password": "TestUser2024!", "name": "Test User 10 VIP"},
]

# Logging configuration
LOG_DIR = "test_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Create logger
logger = logging.getLogger('ConcurrentTest')
logger.setLevel(logging.DEBUG)

# File handler with timestamp
log_filename = f"{LOG_DIR}/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Thread-safe results storage
results_lock = threading.Lock()
test_results = {
    'total_users': 0,
    'successful_logins': 0,
    'failed_logins': 0,
    'successful_reservations': 0,
    'failed_reservations': 0,
    'race_condition_errors': 0,
    'white_screen_crashes': 0,
    'other_errors': 0,
    'errors': []
}


class UserSimulator:
    """Simulates a single user interacting with the app"""

    def __init__(self, user_config: Dict, user_index: int):
        self.user_config = user_config
        self.user_index = user_index
        self.driver: Optional[webdriver.Firefox] = None
        self.thread_name = f"User{user_index}"

    def setup_driver(self):
        """Initialize Firefox WebDriver"""
        try:
            firefox_options = Options()
            # firefox_options.add_argument('--headless')  # Disabled - Show browser windows for visibility
            firefox_options.add_argument('--no-sandbox')
            firefox_options.add_argument('--disable-dev-shm-usage')
            firefox_options.add_argument('--window-size=1200,800')

            # Set Firefox profile to avoid conflicts between concurrent instances
            firefox_options.set_preference('browser.cache.disk.enable', False)
            firefox_options.set_preference('browser.cache.memory.enable', False)
            firefox_options.set_preference('browser.cache.offline.enable', False)
            firefox_options.set_preference('network.http.use-cache', False)

            self.driver = webdriver.Firefox(options=firefox_options)
            self.driver.implicitly_wait(10)

            # Position windows in a grid for better visibility
            screen_position = self._calculate_window_position(self.user_index)
            self.driver.set_window_position(screen_position['x'], screen_position['y'])
            self.driver.set_window_size(screen_position['width'], screen_position['height'])

            logger.info(f"{self.thread_name}: Firefox browser initialized (visible mode)")
            return True
        except Exception as e:
            logger.error(f"{self.thread_name}: Failed to initialize Firefox browser: {e}")
            self._record_error('browser_init', str(e))
            return False

    def _calculate_window_position(self, user_index: int) -> dict:
        """Calculate window position for grid layout"""
        # Arrange windows in a grid (e.g., 5 columns x 2 rows for 10 users)
        columns = 5
        window_width = 380
        window_height = 450

        row = (user_index - 1) // columns
        col = (user_index - 1) % columns

        return {
            'x': col * window_width,
            'y': row * window_height,
            'width': window_width,
            'height': window_height
        }

    def login(self) -> bool:
        """Log in to the application"""
        try:
            logger.info(f"{self.thread_name}: Navigating to {APP_URL}/login")
            self.driver.get(f"{APP_URL}/login")

            # Wait for login form
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )

            password_input = self.driver.find_element(By.NAME, "password")
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Iniciar')]")

            # Enter credentials
            email_input.send_keys(self.user_config['email'])
            password_input.send_keys(self.user_config['password'])

            logger.debug(f"{self.thread_name}: Credentials entered")

            # Click login
            login_button.click()

            # Wait for redirect to home/reservations page
            WebDriverWait(self.driver, 15).until(
                EC.url_contains('/reservas')
            )

            logger.info(f"{self.thread_name}: ✅ Login successful")
            self._record_success('login')
            return True

        except TimeoutException:
            logger.error(f"{self.thread_name}: ❌ Login timeout")
            self._record_error('login_timeout', 'Login form did not load or redirect failed')
            self._take_screenshot('login_timeout')
            return False
        except Exception as e:
            logger.error(f"{self.thread_name}: ❌ Login failed: {e}")
            self._record_error('login_failed', str(e))
            self._take_screenshot('login_error')
            return False

    def select_random_slot(self) -> Optional[tuple]:
        """Select a random available slot"""
        try:
            # Wait for reservation grid to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "reservation-grid"))
            )

            # Find all available slots
            available_slots = self.driver.find_elements(
                By.XPATH, "//button[contains(@class, 'available') or contains(@class, 'bg-green')]"
            )

            if not available_slots:
                logger.warning(f"{self.thread_name}: No available slots found")
                return None

            # Select random slot
            slot = random.choice(available_slots)
            slot_text = slot.text
            logger.debug(f"{self.thread_name}: Clicking slot: {slot_text}")

            slot.click()
            time.sleep(0.5)  # Brief pause for UI update

            return (slot_text, slot)

        except Exception as e:
            logger.error(f"{self.thread_name}: Error selecting slot: {e}")
            self._record_error('slot_selection', str(e))
            return None

    def confirm_reservation(self) -> bool:
        """Confirm the reservation"""
        try:
            # Wait for confirmation modal
            confirm_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirmar')]"))
            )

            logger.debug(f"{self.thread_name}: Clicking confirm button")
            confirm_button.click()

            # Wait for success or error
            try:
                # Check for success modal
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Reserva confirmada') or contains(text(), 'exitosa')]"))
                )
                logger.info(f"{self.thread_name}: ✅ Reservation confirmed successfully")
                self._record_success('reservation')
                return True

            except TimeoutException:
                # Check for error message
                try:
                    error_msg = self.driver.find_element(By.XPATH, "//*[contains(@class, 'error') or contains(text(), 'Error') or contains(text(), 'ya está reservado')]")
                    error_text = error_msg.text

                    if '409' in error_text or 'ya está reservado' in error_text:
                        logger.warning(f"{self.thread_name}: ⚠️  Race condition: {error_text}")
                        self._record_race_condition(error_text)
                    else:
                        logger.error(f"{self.thread_name}: ❌ Reservation failed: {error_text}")
                        self._record_error('reservation_failed', error_text)

                    return False
                except NoSuchElementException:
                    logger.error(f"{self.thread_name}: ❌ Unknown reservation result")
                    self._record_error('reservation_unknown', 'No success or error message found')
                    self._take_screenshot('reservation_unknown')
                    return False

        except Exception as e:
            logger.error(f"{self.thread_name}: ❌ Confirmation failed: {e}")
            self._record_error('confirmation_failed', str(e))
            self._take_screenshot('confirmation_error')
            return False

    def check_for_crashes(self) -> bool:
        """Check if the app has crashed (white screen)"""
        try:
            # Check for Next.js error overlay or white screen
            error_overlay = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'nextjs-error') or contains(text(), 'Error')]")

            if error_overlay:
                logger.error(f"{self.thread_name}: 🚨 WHITE SCREEN CRASH DETECTED!")
                self._record_crash()
                self._take_screenshot('crash')
                return True

            return False

        except Exception:
            return False

    def run_test_scenario(self):
        """Execute the full test scenario"""
        try:
            logger.info(f"{self.thread_name}: Starting test scenario")

            # Setup browser
            if not self.setup_driver():
                return

            # Login
            if not self.login():
                return

            # Small random delay to simulate real user behavior
            time.sleep(random.uniform(0.5, 2.0))

            # Check for crash after login
            if self.check_for_crashes():
                return

            # Navigate to reservations page
            self.driver.get(f"{APP_URL}/reservas")
            time.sleep(1)

            # Try to make 1-3 reservations
            num_attempts = random.randint(1, 3)
            logger.info(f"{self.thread_name}: Attempting {num_attempts} reservation(s)")

            for i in range(num_attempts):
                # Select slot
                slot_info = self.select_random_slot()
                if not slot_info:
                    logger.warning(f"{self.thread_name}: No slots available")
                    break

                # Check for crash after slot selection
                if self.check_for_crashes():
                    return

                # Random delay before confirming
                time.sleep(random.uniform(0.3, 1.5))

                # Confirm reservation
                self.confirm_reservation()

                # Check for crash after confirmation
                if self.check_for_crashes():
                    return

                # Wait between reservations
                if i < num_attempts - 1:
                    time.sleep(random.uniform(1, 3))

            logger.info(f"{self.thread_name}: Test scenario completed")

        except WebDriverException as e:
            logger.error(f"{self.thread_name}: Browser error: {e}")
            self._record_error('browser_error', str(e))
        except Exception as e:
            logger.error(f"{self.thread_name}: Unexpected error: {e}")
            self._record_error('unexpected_error', str(e))
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug(f"{self.thread_name}: Browser closed")
            except Exception as e:
                logger.error(f"{self.thread_name}: Error closing browser: {e}")

    def _record_success(self, action: str):
        """Record successful action"""
        with results_lock:
            if action == 'login':
                test_results['successful_logins'] += 1
            elif action == 'reservation':
                test_results['successful_reservations'] += 1

    def _record_error(self, error_type: str, message: str):
        """Record error"""
        with results_lock:
            if error_type.startswith('login'):
                test_results['failed_logins'] += 1
            elif error_type in ['reservation_failed', 'confirmation_failed']:
                test_results['failed_reservations'] += 1
            else:
                test_results['other_errors'] += 1

            test_results['errors'].append({
                'user': self.thread_name,
                'type': error_type,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })

    def _record_race_condition(self, message: str):
        """Record race condition occurrence"""
        with results_lock:
            test_results['race_condition_errors'] += 1
            test_results['failed_reservations'] += 1
            test_results['errors'].append({
                'user': self.thread_name,
                'type': 'race_condition',
                'message': message,
                'timestamp': datetime.now().isoformat()
            })

    def _record_crash(self):
        """Record app crash"""
        with results_lock:
            test_results['white_screen_crashes'] += 1

    def _take_screenshot(self, name: str):
        """Take screenshot for debugging"""
        try:
            screenshot_path = f"{LOG_DIR}/screenshot_{self.thread_name}_{name}_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.debug(f"{self.thread_name}: Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"{self.thread_name}: Failed to take screenshot: {e}")


def run_concurrent_test(num_users: int = 10, stagger_delay: float = 0.5):
    """
    Run concurrent user test

    Args:
        num_users: Number of concurrent users to simulate
        stagger_delay: Delay in seconds between starting each user
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 Starting Concurrent Test")
    logger.info(f"   Users: {num_users}")
    logger.info(f"   Stagger delay: {stagger_delay}s")
    logger.info(f"   App URL: {APP_URL}")
    logger.info(f"   Log file: {log_filename}")
    logger.info(f"{'='*80}\n")

    # Initialize results
    with results_lock:
        test_results['total_users'] = num_users

    # Create threads for each user
    threads = []
    simulators = []

    for i in range(num_users):
        user_config = TEST_USERS[i % len(TEST_USERS)]
        simulator = UserSimulator(user_config, i + 1)
        simulators.append(simulator)

        thread = threading.Thread(
            target=simulator.run_test_scenario,
            name=f"User{i+1}"
        )
        threads.append(thread)

    # Start all threads with staggered delays
    start_time = time.time()

    for i, thread in enumerate(threads):
        thread.start()
        if i < len(threads) - 1:  # Don't delay after last user
            time.sleep(stagger_delay)

    # Wait for all threads to complete
    logger.info(f"\n⏳ Waiting for all {num_users} users to complete...\n")

    for thread in threads:
        thread.join()

    end_time = time.time()
    duration = end_time - start_time

    # Print results
    print_results(duration)


def print_results(duration: float):
    """Print test results summary"""
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 TEST RESULTS SUMMARY")
    logger.info(f"{'='*80}\n")

    logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
    logger.info(f"👥 Total Users: {test_results['total_users']}")
    logger.info(f"\n🔐 Authentication:")
    logger.info(f"   ✅ Successful logins: {test_results['successful_logins']}")
    logger.info(f"   ❌ Failed logins: {test_results['failed_logins']}")

    logger.info(f"\n📅 Reservations:")
    logger.info(f"   ✅ Successful: {test_results['successful_reservations']}")
    logger.info(f"   ❌ Failed: {test_results['failed_reservations']}")

    logger.info(f"\n🐛 Errors:")
    logger.info(f"   ⚠️  Race conditions (409): {test_results['race_condition_errors']}")
    logger.info(f"   🚨 White screen crashes: {test_results['white_screen_crashes']}")
    logger.info(f"   ❌ Other errors: {test_results['other_errors']}")

    # Calculate success rate
    total_attempts = test_results['successful_reservations'] + test_results['failed_reservations']
    if total_attempts > 0:
        success_rate = (test_results['successful_reservations'] / total_attempts) * 100
        logger.info(f"\n✨ Reservation Success Rate: {success_rate:.1f}%")

    # Race condition rate
    if total_attempts > 0:
        race_rate = (test_results['race_condition_errors'] / total_attempts) * 100
        logger.info(f"⚡ Race Condition Rate: {race_rate:.1f}%")

    # List errors
    if test_results['errors']:
        logger.info(f"\n❌ Error Details:")
        for i, error in enumerate(test_results['errors'][:10], 1):  # Show first 10
            logger.info(f"   {i}. [{error['user']}] {error['type']}: {error['message'][:100]}")
        if len(test_results['errors']) > 10:
            logger.info(f"   ... and {len(test_results['errors']) - 10} more errors")

    logger.info(f"\n{'='*80}")
    logger.info(f"📄 Full log saved to: {log_filename}")
    logger.info(f"{'='*80}\n")

    # Return results for programmatic use
    return test_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run concurrent user tests')
    parser.add_argument('--users', type=int, default=10, help='Number of concurrent users (default: 10)')
    parser.add_argument('--delay', type=float, default=0.5, help='Stagger delay between users in seconds (default: 0.5)')
    parser.add_argument('--url', type=str, help='App URL (default: http://localhost:3000)')

    args = parser.parse_args()

    if args.url:
        APP_URL = args.url

    try:
        run_concurrent_test(num_users=args.users, stagger_delay=args.delay)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"\n🚨 Fatal error: {e}")
