import sys
import os

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

"""
Main load test orchestrator for Tennis Reservation App User App
Runs 10 concurrent users with different profiles and collects metrics
"""
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from queue import Queue
import threading
import requests

from config import (
    USER_APP_URL, NUM_CONCURRENT_USERS, MAX_WORKERS, USER_START_DELAY,
    MAX_TEST_DURATION, TEST_USERS, VERBOSE_MODE, WAIT_FOR_APP,
    APP_READY_TIMEOUT, AVAILABLE_HOURS, RESULTS_DIR, BROWSER_TYPE, HEADLESS_MODE
)
from metrics_collector import MetricsCollector
from user_scenarios import create_scenario
from production_queue_manager import init_production_queue, get_production_queue

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
except ImportError:
    print("ERROR: Selenium not installed. Install with: pip install selenium webdriver-manager")
    sys.exit(1)


class AuthQueueManager:
    """Manages adaptive staggered authentication to avoid Supabase socket errors"""

    def __init__(self, auth_delay_seconds: float = 2.5, min_delay: float = 1.0, max_delay: float = 5.0):
        """Initialize auth queue manager with adaptive delays

        Args:
            auth_delay_seconds: Base delay between auth attempts
            min_delay: Minimum delay to enforce (safety threshold)
            max_delay: Maximum delay to allow (safety ceiling)
        """
        self.queue = Queue()
        self.auth_delay = auth_delay_seconds
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.lock = threading.Lock()
        self.last_auth_time = 0
        self.last_auth_duration = 0
        self.auth_count = 0

    def acquire_auth_slot(self, user_id: str) -> None:
        """Wait until it's this user's turn to authenticate with adaptive delay"""
        with self.lock:
            self.auth_count += 1
            time_since_last_auth = time.time() - self.last_auth_time

            # Calculate adaptive delay based on previous auth duration
            # If previous auth was fast, wait less. If it was slow, wait more.
            if self.auth_count == 1:
                # First user, no wait needed
                adaptive_delay = 0
            else:
                # Adaptive: use previous auth duration + safety margin
                # This ensures auth completes before next one starts
                adaptive_delay = max(self.min_delay, min(self.last_auth_duration + 1.0, self.max_delay))

            if time_since_last_auth < adaptive_delay:
                wait_time = adaptive_delay - time_since_last_auth
                if VERBOSE_MODE:
                    print("[AUTH_QUEUE] {0} waiting {1:.2f}s for auth slot (adaptive based on {2:.2f}s auth)".format(
                        user_id, wait_time, self.last_auth_duration))
                time.sleep(wait_time)

            self.last_auth_time = time.time()
            if VERBOSE_MODE:
                print("[AUTH_QUEUE] {0} acquired auth slot (attempt #{1})".format(user_id, self.auth_count))

    def record_auth_completion(self, duration: float) -> None:
        """Record how long the authentication took for adaptive adjustment"""
        with self.lock:
            self.last_auth_duration = duration
            if VERBOSE_MODE:
                print("[AUTH_QUEUE] Auth completed in {0:.2f}s, next users will wait {1:.2f}s".format(
                    duration, max(self.min_delay, min(duration + 1.0, self.max_delay))))


class LoadTestOrchestrator:
    """Orchestrates concurrent load testing of User App"""

    def __init__(self):
        """Initialize load test orchestrator with rate limiter"""
        self.metrics = MetricsCollector(RESULTS_DIR)
        self.test_users = TEST_USERS
        self.start_time = None
        self.end_time = None
        # Initialize rate limiter: 5 auth ops/sec, 10 reservation ops/sec
        self.production_queue = init_production_queue(auth_rate=5, reservation_rate=10)
        # Pre-cache webdriver to avoid GitHub rate limiting
        self.geckodriver_path = None
        self._cache_webdriver()

    def wait_for_app(self) -> bool:
        """Wait for Streamlit app to be ready

        Returns:
            True if app is ready, False if timeout
        """
        if not WAIT_FOR_APP:
            return True

        print("Waiting for app at {0}...".format(USER_APP_URL))
        start = time.time()

        while time.time() - start < APP_READY_TIMEOUT:
            try:
                response = requests.get(USER_APP_URL, timeout=5)
                if response.status_code == 200:
                    print("App is ready!")
                    return True
            except:
                pass

            time.sleep(1)

        print("App not ready after {0} seconds".format(APP_READY_TIMEOUT))
        return False

    def _cache_webdriver(self):
        """Use cached geckodriver to avoid GitHub rate limiting"""
        import os
        if VERBOSE_MODE:
            print("Looking for cached geckodriver...")
        try:
            if BROWSER_TYPE.lower() == "firefox":
                home = os.path.expanduser("~")
                cached_driver = os.path.join(home, ".wdm/drivers/geckodriver/win64/v0.36.0/geckodriver.exe")
                if os.path.exists(cached_driver):
                    self.geckodriver_path = cached_driver
                    print("Using cached geckodriver: {0}".format(self.geckodriver_path))
                else:
                    print("Cached geckodriver not found, will try to download...")
                    self.geckodriver_path = GeckoDriverManager().install()
                    print("Geckodriver cached at: {0}".format(self.geckodriver_path))
        except Exception as e:
            print("Could not setup geckodriver: {0}".format(str(e)))
            print("Will attempt to use system geckodriver or download later")

    def create_webdriver(self):
        """Create and configure Selenium WebDriver for Firefox or Chrome

        Returns:
            Configured WebDriver instance
        """
        if BROWSER_TYPE.lower() == "firefox":
            options = FirefoxOptions()
            if HEADLESS_MODE:
                options.add_argument("--headless")
            options.add_argument("--width=1920")
            options.add_argument("--height=1080")

            if self.geckodriver_path:
                service = FirefoxService(self.geckodriver_path)
            else:
                service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
        else:  # Chrome
            options = ChromeOptions()
            if HEADLESS_MODE:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")

            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

        return driver

    def run_user_scenario(self, user_key: str, user_num: int):
        """Run scenario for a single user

        Args:
            user_key: User key from TEST_USERS (user1, user2, etc.)
            user_num: User number for staggered start
        """
        # Stagger user starts
        if USER_START_DELAY > 0:
            time.sleep(USER_START_DELAY * user_num)

        user_data = self.test_users[user_key]
        email = user_data['email']
        password = user_data['password']
        profile = user_data['profile']

        if VERBOSE_MODE:
            print("Starting {0} (Profile {1})...".format(user_key, profile))

        try:
            # Create WebDriver
            driver = self.create_webdriver()

            # Create scenario based on profile
            additional_kwargs = {}
            # Get hour from config for this user
            hour_key = f"{user_key}_profile_{'a' if profile == 'A' else profile.lower()}"
            if hour_key in AVAILABLE_HOURS:
                additional_kwargs['hour'] = AVAILABLE_HOURS[hour_key]
            else:
                # Fallback hour if not found in config
                additional_kwargs['hour'] = 14  # Default to 2pm

            # Add production queue manager to scenario kwargs
            additional_kwargs['production_queue'] = self.production_queue

            scenario = create_scenario(
                user_id=user_key,
                email=email,
                password=password,
                profile=profile,
                driver=driver,
                metrics=self.metrics,
                **additional_kwargs
            )

            # Run scenario
            scenario.run()

            if VERBOSE_MODE:
                print("{0} (Profile {1}) completed".format(user_key, profile))

        except Exception as e:
            print("{0} (Profile {1}) failed: {2}".format(user_key, profile, str(e)))

    def run_load_test(self):
        """Run the load test with all concurrent users"""
        print("\n" + "=" * 80)
        print("LOAD TEST: Tennis Reservation App User App")
        print("=" * 80)
        print("Number of Users: {0}".format(NUM_CONCURRENT_USERS))
        print("Max Workers: {0}".format(MAX_WORKERS))
        print("App URL: {0}".format(USER_APP_URL))
        print("=" * 80 + "\n")

        # Wait for app to be ready
        if not self.wait_for_app():
            print("Cannot start load test - app not ready")
            return False

        self.start_time = time.time()

        # Create ThreadPoolExecutor for concurrent execution
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}

            # Submit all users to thread pool
            user_keys = list(self.test_users.keys())[:NUM_CONCURRENT_USERS]
            for i, user_key in enumerate(user_keys):
                future = executor.submit(self.run_user_scenario, user_key, i)
                futures[future] = user_key

            # Wait for all to complete
            completed = 0
            for future in as_completed(futures, timeout=MAX_TEST_DURATION):
                user_key = futures[future]
                try:
                    future.result()
                    completed += 1
                except Exception as e:
                    print("Exception for {0}: {1}".format(user_key, str(e)))

                if VERBOSE_MODE:
                    print("Progress: {0}/{1} users completed".format(completed, NUM_CONCURRENT_USERS))

        self.end_time = time.time()
        self.metrics.finalize()

        return True

    def print_results(self):
        """Print and save test results"""
        # Print summary
        self.metrics.print_summary()

        # Save metrics
        self.metrics.save_to_csv()
        self.metrics.save_summary()

        print("\nTest Results:")
        print("  Test Duration: {0:.2f} seconds".format(self.end_time - self.start_time))
        print("  Results saved to: {0}/".format(RESULTS_DIR))

    def run(self):
        """Run complete load test"""
        success = self.run_load_test()
        if success:
            self.print_results()
            return 0
        else:
            return 1


def main():
    """Main entry point"""
    orchestrator = LoadTestOrchestrator()
    exit_code = orchestrator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
