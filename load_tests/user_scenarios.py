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
                 driver: webdriver.Chrome, metrics: MetricsCollector):
        """Initialize user scenario

        Args:
            user_id: User identifier (user1, user2, etc.)
            email: Login email
            password: Login password
            profile: User profile (A, B, C, or D)
            driver: Selenium WebDriver instance
            metrics: MetricsCollector for recording metrics
        """
        self.user_id = user_id
        self.email = email
        self.password = password
        self.profile = profile
        self.driver = driver
        self.metrics = metrics
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
            print(f"[{self.user_id}] Navigated to app in {duration:.2f}s")
        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.PAGE_LOAD,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
            raise

    def login(self):
        """Login to User App with email and password"""
        try:
            start = time.time()

            # Find and fill email field
            email_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            email_input.clear()
            email_input.send_keys(self.email)

            # Find and fill password field
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_input.clear()
            password_input.send_keys(self.password)

            # Find and click login button
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Ingresar')]")
            login_button.click()

            # Wait for dashboard to load
            WebDriverWait(self.driver, LOGIN_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Información de tu Cuenta') or contains(text(), 'Dashboard')]"))
            )

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.LOGIN,
                OperationStatus.SUCCESS, duration * 1000
            )
            print(f"[{self.user_id}] Login successful in {duration:.2f}s")

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

            # Wait for dashboard to be visible
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Información de tu Cuenta')]"))
            )

            # Take a screenshot to verify dashboard loaded
            time.sleep(1)  # Wait for any dynamic content

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_DASHBOARD,
                OperationStatus.SUCCESS, duration * 1000
            )
            print(f"[{self.user_id}] Viewed dashboard in {duration:.2f}s")

        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_DASHBOARD,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
            raise

    def view_account_info(self):
        """View account information (name, email, credits, VIP status)"""
        try:
            start = time.time()

            # Look for account info section
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Créditos disponibles')]"))
            )

            time.sleep(0.5)  # Wait for rendering

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_ACCOUNT_INFO,
                OperationStatus.SUCCESS, duration * 1000
            )
            print(f"[{self.user_id}] Viewed account info in {duration:.2f}s")

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
            print(f"[{self.user_id}] Viewed reservations in {duration:.2f}s")

        except TimeoutException as e:
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.VIEW_RESERVATIONS,
                OperationStatus.TIMEOUT, 0, str(e), "TimeoutException"
            )
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
            print(f"[{self.user_id}] Browsed slots in {duration:.2f}s")

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

            # Look for reservation button or form
            # This is simplified - adjust based on actual app UI
            reserve_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Reservar')]")

            if reserve_buttons:
                # Click first available reservation button
                reserve_buttons[0].click()
                time.sleep(1)

                # Wait for success message or confirmation
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'exitosa') or contains(text(), 'success')]"))
                )

                duration = time.time() - start
                self.metrics.record_operation(
                    self.user_id, self.profile, OperationType.MAKE_RESERVATION,
                    OperationStatus.SUCCESS, duration * 1000,
                    additional_data={"hour": hour, "date": str(RESERVATION_DATE)}
                )
                print(f"[{self.user_id}] Made reservation for {hour}:00 in {duration:.2f}s")
            else:
                raise Exception("No reservation buttons found")

        except TimeoutException as e:
            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.MAKE_RESERVATION,
                OperationStatus.TIMEOUT, duration * 1000, str(e), "TimeoutException",
                additional_data={"hour": hour}
            )
            print(f"[{self.user_id}] Reservation timeout for {hour}:00")
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
            print(f"[{self.user_id}] Reservation failed for {hour}:00: {error_msg}")

    def check_credits(self):
        """Check user credits"""
        try:
            start = time.time()

            # Look for credits display
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Créditos')]"))
            )

            time.sleep(0.5)

            duration = time.time() - start
            self.metrics.record_operation(
                self.user_id, self.profile, OperationType.CHECK_CREDITS,
                OperationStatus.SUCCESS, duration * 1000
            )
            print(f"[{self.user_id}] Checked credits in {duration:.2f}s")

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
            logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Cerrar sesión')]")
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
            print(f"[{self.user_id}] Logged out in {duration:.2f}s")

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
            print(f"[{self.user_id}] Profile A completed successfully")
        except Exception as e:
            print(f"[{self.user_id}] Profile A failed: {str(e)}")
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
        """Execute Profile B scenario"""
        try:
            self.navigate_to_app()
            self.login()
            self.view_dashboard()
            self.browse_slots()
            self.make_reservation(self.hour)
            self.logout()
            print(f"[{self.user_id}] Profile B completed for hour {self.hour}")
        except Exception as e:
            print(f"[{self.user_id}] Profile B failed: {str(e)}")
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
            print(f"[{self.user_id}] Profile C completed")
        except Exception as e:
            print(f"[{self.user_id}] Profile C failed: {str(e)}")
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
            print(f"[{self.user_id}] Profile D completed successfully")
        except Exception as e:
            print(f"[{self.user_id}] Profile D failed: {str(e)}")
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
    if profile == "A":
        return ProfileA(user_id, email, password, profile, driver, metrics)
    elif profile == "B":
        hour = kwargs.get('hour', 8)
        return ProfileB(user_id, email, password, profile, driver, metrics, hour=hour)
    elif profile == "C":
        return ProfileC(user_id, email, password, profile, driver, metrics)
    elif profile == "D":
        return ProfileD(user_id, email, password, profile, driver, metrics)
    else:
        raise ValueError(f"Unknown profile: {profile}")
