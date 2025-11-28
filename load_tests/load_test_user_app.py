"""
Main load test orchestrator for Tennis Reservation App User App
Runs 10 concurrent users with different profiles and collects metrics
"""
import time
import sys
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
import requests

from config import (
    USER_APP_URL, NUM_CONCURRENT_USERS, MAX_WORKERS, USER_START_DELAY,
    MAX_TEST_DURATION, TEST_USERS, VERBOSE_MODE, WAIT_FOR_APP,
    APP_READY_TIMEOUT, AVAILABLE_HOURS, RESULTS_DIR
)
from metrics_collector import MetricsCollector
from user_scenarios import create_scenario

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("❌ Selenium not installed. Install with: pip install selenium webdriver-manager")
    sys.exit(1)


class LoadTestOrchestrator:
    """Orchestrates concurrent load testing of User App"""

    def __init__(self):
        """Initialize load test orchestrator"""
        self.metrics = MetricsCollector(RESULTS_DIR)
        self.test_users = TEST_USERS
        self.start_time = None
        self.end_time = None

    def wait_for_app(self) -> bool:
        """Wait for Streamlit app to be ready

        Returns:
            True if app is ready, False if timeout
        """
        if not WAIT_FOR_APP:
            return True

        print(f"⏳ Waiting for app at {USER_APP_URL}...")
        start = time.time()

        while time.time() - start < APP_READY_TIMEOUT:
            try:
                response = requests.get(USER_APP_URL, timeout=5)
                if response.status_code == 200:
                    print(f"✅ App is ready!")
                    return True
            except:
                pass

            time.sleep(1)

        print(f"❌ App not ready after {APP_READY_TIMEOUT} seconds")
        return False

    def create_webdriver(self) -> webdriver.Chrome:
        """Create and configure Selenium WebDriver for Chrome

        Returns:
            Configured Chrome WebDriver
        """
        options = Options()
        # options.add_argument("--headless")  # Uncomment for headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(ChromeDriverManager().install())
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
            print(f"👤 Starting {user_key} (Profile {profile})...")

        try:
            # Create WebDriver
            driver = self.create_webdriver()

            # Create scenario based on profile
            additional_kwargs = {}
            if profile == "B":
                # Profile B users get different hours
                if user_key == "user4":
                    additional_kwargs['hour'] = AVAILABLE_HOURS.get('user4_profile_b', 8)
                elif user_key == "user5":
                    additional_kwargs['hour'] = AVAILABLE_HOURS.get('user5_profile_b', 11)
                elif user_key == "user6":
                    additional_kwargs['hour'] = AVAILABLE_HOURS.get('user6_profile_b', 14)

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
                print(f"✅ {user_key} (Profile {profile}) completed")

        except Exception as e:
            print(f"❌ {user_key} (Profile {profile}) failed: {str(e)}")

    def run_load_test(self):
        """Run the load test with all concurrent users"""
        print("\n" + "=" * 80)
        print("LOAD TEST: Tennis Reservation App User App")
        print("=" * 80)
        print(f"Number of Users: {NUM_CONCURRENT_USERS}")
        print(f"Max Workers: {MAX_WORKERS}")
        print(f"App URL: {USER_APP_URL}")
        print("=" * 80 + "\n")

        # Wait for app to be ready
        if not self.wait_for_app():
            print("❌ Cannot start load test - app not ready")
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
                    print(f"❌ Exception for {user_key}: {str(e)}")

                if VERBOSE_MODE:
                    print(f"Progress: {completed}/{NUM_CONCURRENT_USERS} users completed")

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

        print("\n📊 Test Results:")
        print(f"  Test Duration: {self.end_time - self.start_time:.2f} seconds")
        print(f"  Results saved to: {RESULTS_DIR}/")

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
