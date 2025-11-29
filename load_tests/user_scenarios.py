import sys
import os

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

"""
User scenario implementations for load testing
Profiles A, B, C, D - different user behaviors in the User App
"""
import time
from typing import Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import (
    USER_APP_URL, LOGIN_TIMEOUT, PAGE_LOAD_TIMEOUT, ELEMENT_WAIT_TIMEOUT,
    AVAILABLE_HOURS, RESERVATION_DATE
)
from metrics_collector import MetricsCollector, OperationType, OperationStatus


class UserScenario:
    """Base class for user scenarios"""

    def __init__(self, user_id: str, email: str, password: str, profile: str,
                 driver: webdriver.Chrome, metrics: MetricsCollector, auth_queue=None):
        """Initialize user scenario

        Args:
            user_id: User identifier (user1, user2, etc.)
            email: Login email
            password: Login password
            profile: User profile (A, B, C, or D)
            driver: Selenium WebDriver instance
            metrics: MetricsCollector for recording metrics
            auth_queue: Optional AuthQueueManager for staggered authentication
        """
        self.user_id = user_id
        self.email = email
        self.password = password
        self.profile = profile
        self.driver = driver
        self.metrics = metrics
        self.auth_queue = auth_queue
        self.wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)

    def navigate_to_app(self):
        """Navigate to User App"""
        try:
            start = time.time()
            self.driver.get(USER_APP_URL)
            # Wait for page to load
            WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
            )
            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.PAGE_LOAD,
                OperationStatus.SUCCESS, duration * 1000
            )
            print("[{}] Page load completed in {:.2f}s".format(self.user_id, duration))
        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.PAGE_LOAD,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
            raise

    def login(self):
        """Login to User App with email and password"""
        try:
            # Request auth slot from queue to stagger Supabase requests
            if self.auth_queue:
                self.auth_queue.acquire_auth_slot(self.user_id)

            start = time.time()

            # Wait for inputs to be present and clickable
            time.sleep(0.5)

            # Find and fill email field
            email_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            email_input.clear()
            email_input.send_keys(self.email)
            time.sleep(0.3)

            # Find and fill password field
            password_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(0.3)

            # Find and click the form submit button - wait for it to be clickable
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='stBaseButton-primaryFormSubmit']"))
            )
            login_button.click()
            time.sleep(3)  # Wait longer for page to process login

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.LOGIN,
                OperationStatus.SUCCESS, duration * 1000
            )
            print("[{}] Login successful in {:.2f}s".format(self.user_id, duration))

        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.LOGIN,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
            raise
        except Exception as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.LOGIN,
                OperationStatus.ERROR, 0, str(e), type(e).__name__
            )
            raise

    def view_dashboard(self):
        """View dashboard information"""
        try:
            start = time.time()

            # Just wait for page to fully render after login
            time.sleep(3)

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_DASHBOARD,
                OperationStatus.SUCCESS, duration * 1000
            )
            print("[{}] Dashboard ready in {:.2f}s".format(self.user_id, duration))

        except Exception as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_DASHBOARD,
                OperationStatus.ERROR, 0, str(e), type(e).__name__
            )
            raise

    def view_account_info(self):
        """View account information (name, email, credits, VIP status)"""
        try:
            start = time.time()

            # Look for account info section
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Creditos disponibles')]"))
            )

            time.sleep(0.5)  # Wait for rendering

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_ACCOUNT_INFO,
                OperationStatus.SUCCESS, duration * 1000
            )
            print("[{}] Account info viewed in {:.2f}s".format(self.user_id, duration))

        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_ACCOUNT_INFO,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
            raise

    def view_reservations(self):
        """View user's existing reservations"""
        try:
            start = time.time()

            # Look for reservations section
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Tus Reservas') or contains(text(), 'Your Reservations')]"))
            )

            time.sleep(0.5)

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_RESERVATIONS,
                OperationStatus.SUCCESS, duration * 1000
            )
            print("[{}] Reservations viewed in {:.2f}s".format(self.user_id, duration))

        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_RESERVATIONS,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
            raise

    def select_hour(self, hour_to_select):
        """Select a specific hour button by CSS selector

        Args:
            hour_to_select (int or str): Hour to select (e.g., 12 or "12")
        """
        # Create dynamic CSS selector for the hour button
        css_selector = "div[class*='st-key-hour'][class*='_{0}'] button".format(hour_to_select)

        try:
            print("[{0}] Looking for hour: {1}...".format(self.user_id, hour_to_select))

            # Wait for the element to be present in the DOM
            button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            # Scroll the button into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)

            # Wait for it to be clickable after scrolling
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
            )

            # Click using JavaScript (safest for Streamlit buttons)
            self.driver.execute_script("arguments[0].click();", button)
            print("[{0}] Clicked button for hour {1}".format(self.user_id, hour_to_select))

        except Exception as e:
            print("[{0}] Could not find or click hour {1}. Error: {2}".format(self.user_id, hour_to_select, str(e)))
            raise

    def browse_slots(self):
        """Browse available reservation slots"""
        try:
            start = time.time()

            # Look for slot selection UI (adjust selectors based on actual app)
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Reservar') or contains(text(), 'Make Reservation')]"))
            )

            time.sleep(1)  # Wait for slots to load

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.BROWSE_SLOTS,
                OperationStatus.SUCCESS, duration * 1000
            )
            print("[{}] Slots browsed in {:.2f}s".format(self.user_id, duration))

        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.BROWSE_SLOTS,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
            raise

    def make_reservation(self, hour: int):
        """Make a reservation for specified hour

        Args:
            hour: Hour to reserve (6-22 based on app)
        """
        try:
            start = time.time()

            print("[{0}] Starting reservation for hour {1}".format(self.user_id, hour))

            # Scroll down to find the reservation buttons
            print("[{0}] Scrolling down to find buttons...".format(self.user_id))
            self.driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1)

            # Format hour string (12:00 Disponible)
            hour_str = "{0:02d}:00 Disponible".format(hour)

            # Locate the button by text
            print("[{0}] Looking for button: {1}".format(self.user_id, hour_str))
            button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[.//p[contains(text(), '{0}')]]".format(hour_str))
                )
            )

            # Scroll it into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(0.5)

            print("[{0}] Found hour button, clicking...".format(self.user_id))
            button.click()
            time.sleep(1)

            print("[{0}] Looking for confirmation button...".format(self.user_id))
            # Find confirmation button - look for primary form submit button
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='stBaseButton-primaryFormSubmit']"))
            )
            print("[{0}] Found confirmation button, clicking...".format(self.user_id))
            confirm_button.click()
            time.sleep(1)

            print("[{0}] Waiting for success message...".format(self.user_id))
            # Wait for success message or confirmation
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'exitosa') or contains(text(), 'success') or contains(text(), 'confirmada')]"))
            )
            print("[{0}] Reservation success!".format(self.user_id))

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.MAKE_RESERVATION,
                OperationStatus.SUCCESS, duration * 1000,
                additional_data={"hour": hour, "date": str(RESERVATION_DATE)}
            )
            print("[{}] Reservation made for hour {} in {:.2f}s".format(self.user_id, hour, duration))

        except TimeoutException as e:
            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.MAKE_RESERVATION,
                OperationStatus.TIMEOUT, duration * 1000, str(e), "TimeoutException",
                additional_data={"hour": hour}
            )
            print("[{}] Reservation timeout for hour {}".format(self.user_id, hour))
        except Exception as e:
            duration = time.time() - start
            error_msg = str(e)
            if "slot" in error_msg.lower() or "no disponible" in error_msg.lower():
                status = OperationStatus.FAILED
            else:
                status = OperationStatus.ERROR

            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.MAKE_RESERVATION,
                status, duration * 1000, error_msg, type(e).__name__,
                additional_data={"hour": hour}
            )
            print("[{}] Reservation failed for hour {}: {}".format(self.user_id, hour, error_msg))

    def check_credits(self):
        """Check user credits"""
        try:
            start = time.time()

            # Look for credits display
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Creditos')]"))
            )

            time.sleep(0.5)

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.CHECK_CREDITS,
                OperationStatus.SUCCESS, duration * 1000
            )
            print("[{}] Credits checked in {:.2f}s".format(self.user_id, duration))

        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.CHECK_CREDITS,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
            raise

    def logout(self):
        """Logout from User App"""
        try:
            start = time.time()

            # Find logout button
            logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Cerrar sesion')]")
            logout_button.click()

            # Wait for login page to reappear
            WebDriverWait(self.driver, ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Ingresar')]"))
            )

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.LOGOUT,
                OperationStatus.SUCCESS, duration * 1000
            )
            print("[{}] Logout successful in {:.2f}s".format(self.user_id, duration))

        except Exception as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.LOGOUT,
                OperationStatus.ERROR, 0, str(e), type(e).__name__
            )
            # Don't raise - logout failures aren't critical

    def close_driver(self):
        """Close Selenium WebDriver"""
        try:
            self.driver.quit()
        except:
            pass


# ============================================================================
# Profile Implementations
# ============================================================================

class ProfileA(UserScenario):
    """Profile A: Browser - Login, view dashboard, view reservations, logout"""

    def run(self):
        """Execute Profile A scenario"""
        try:
            self.navigate_to_app()
            self.login()
            self.view_dashboard()
            self.view_account_info()
            self.view_reservations()
            self.logout()
            print("[{}] Profile A completed successfully".format(self.user_id))
        except Exception as e:
            print("[{}] Profile A failed: {}".format(self.user_id, str(e)))
        finally:
            self.close_driver()


class ProfileB(UserScenario):
    """Profile B: Maker - Login, browse slots, make reservation, logout"""

    def __init__(self, *args, hour: int = 8, **kwargs):
        """Initialize with reservation hour

        Args:
            hour: Hour to make reservation (8, 11, 14, etc.)
        """
        super().__init__(*args, **kwargs)
        self.hour = hour

    def run(self):
        """Execute Profile B scenario - Login and make reservation"""
        try:
            self.navigate_to_app()
            self.login()
            # Select the hour button
            self.select_hour(self.hour)
            print("[{}] Profile B completed for hour {}".format(self.user_id, self.hour))
        except Exception as e:
            print("[{}] Profile B failed: {}".format(self.user_id, str(e)))
        finally:
            self.close_driver()


class ProfileC(UserScenario):
    """Profile C: Competitive - Login, try same hour, logout"""

    def run(self):
        """Execute Profile C scenario (both users try 10-11am)"""
        try:
            self.navigate_to_app()
            self.login()
            self.view_dashboard()
            self.browse_slots()
            self.make_reservation(10)  # Competitive hour
            self.logout()
            print("[{}] Profile C completed".format(self.user_id))
        except Exception as e:
            print("[{}] Profile C failed: {}".format(self.user_id, str(e)))
        finally:
            self.close_driver()


class ProfileD(UserScenario):
    """Profile D: Info Checker - Login, check credits, view info, logout"""

    def run(self):
        """Execute Profile D scenario"""
        try:
            self.navigate_to_app()
            self.login()
            self.view_dashboard()
            self.check_credits()
            self.view_account_info()
            self.logout()
            print("[{}] Profile D completed successfully".format(self.user_id))
        except Exception as e:
            print("[{}] Profile D failed: {}".format(self.user_id, str(e)))
        finally:
            self.close_driver()


def create_scenario(user_id: str, email: str, password: str, profile: str,
                    driver: webdriver.Chrome, metrics: MetricsCollector,
                    **kwargs) -> UserScenario:
    """Factory function to create appropriate scenario based on profile

    Args:
        user_id: User identifier
        email: Login email
        password: Login password
        profile: Profile type (A, B, C, D)
        driver: Selenium WebDriver
        metrics: MetricsCollector
        **kwargs: Additional arguments (e.g., hour for Profile B)

    Returns:
        UserScenario instance
    """
    auth_queue = kwargs.pop('auth_queue', None)

    if profile == "A":
        return ProfileA(user_id, email, password, profile, driver, metrics, auth_queue=auth_queue)
    elif profile == "B":
        hour = kwargs.get('hour', 8)
        return ProfileB(user_id, email, password, profile, driver, metrics, hour=hour, auth_queue=auth_queue)
    elif profile == "C":
        return ProfileC(user_id, email, password, profile, driver, metrics, auth_queue=auth_queue)
    elif profile == "D":
        return ProfileD(user_id, email, password, profile, driver, metrics, auth_queue=auth_queue)
    else:
        raise ValueError("Unknown profile: {}".format(profile))
