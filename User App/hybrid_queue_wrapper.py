"""
Hybrid Queue Wrapper - Intelligently routes operations to write or read queue

Automatically determines if operation is a READ or WRITE:
- WRITES (login, reservation, delete, email verify): Serial queue (1 at a time)
- READS (credits, availability, reservations): Parallel queue (5 concurrent)
"""

import time
from typing import Callable, Any, Optional
from functools import wraps


class HybridQueuedOperationWrapper:
    """Wraps database operations with intelligent read/write queue routing"""

    # Operations that are WRITES (must serialize)
    WRITE_OPERATIONS = {
        "[AUTH:LOGIN]",
        "[WRITE:RESERVATION]",
        "[WRITE:ATOMIC_RESERVATION]",
        "[WRITE:DOUBLE_RESERVATION]",
        "[WRITE:DELETE_RESERVATION]",
        "[WRITE:VERIFICATION_CODE]",
        "[WRITE:VERIFY_EMAIL]",
        "[WRITE:CLEANUP]",
    }

    def __init__(self, queue_manager):
        self.queue = queue_manager

    def is_write_operation(self, operation_name: str) -> bool:
        """Determine if operation is a write (must serialize)"""
        return operation_name in self.WRITE_OPERATIONS

    def execute_protected(
        self,
        user_email: str,
        operation_name: str,
        func: Callable,
        timeout: float = 60.0
    ) -> Any:
        """
        Execute a database operation with intelligent queue routing.

        Args:
            user_email: Email of user performing operation
            operation_name: Name of operation for routing decision
            func: Callable that performs the database operation
            timeout: Max time to wait for queue slot

        Returns:
            Result of the function call
        """
        start_time = time.time()
        is_write = self.is_write_operation(operation_name)

        # Route to appropriate queue
        if is_write:
            self.queue.acquire_write_slot(user_email, operation_name, timeout=timeout)
        else:
            self.queue.acquire_read_slot(user_email, operation_name, timeout=timeout)

        try:
            result = func()
            duration = time.time() - start_time

            if is_write:
                self.queue.release_write_slot(user_email, operation_name, duration)
            else:
                self.queue.release_read_slot(user_email, operation_name, duration)

            return result

        except Exception as e:
            duration = time.time() - start_time
            if is_write:
                self.queue.release_write_slot(user_email, operation_name, duration)
            else:
                self.queue.release_read_slot(user_email, operation_name, duration)
            raise

    def create_method_wrapper(self, original_method: Callable, operation_name: str):
        """Create a wrapped version of a method that uses the hybrid queue"""

        def wrapped_method(user_email: str, *args, **kwargs):
            return self.execute_protected(
                user_email,
                operation_name,
                lambda: original_method(*args, **kwargs)
            )

        return wrapped_method


class HybridQueuedDatabaseManagerAdapter:
    """
    Adapter that wraps database manager with intelligent read/write queue protection.

    Routes operations intelligently:
    - WRITES: Serial queue (prevent race conditions)
    - READS: Parallel queue (improve performance)
    """

    def __init__(self, db_manager, queue_manager):
        """
        Args:
            db_manager: Original DatabaseManager instance
            queue_manager: HybridSupabaseQueue instance
        """
        self.db = db_manager
        self.queue = queue_manager
        self.wrapper = HybridQueuedOperationWrapper(queue_manager)

    def _get_user_email_from_context(self):
        """Helper to get current user email from Streamlit context if available"""
        try:
            import streamlit as st
            if hasattr(st, "session_state") and "user_email" in st.session_state:
                return st.session_state.user_email
            return "system"
        except:
            return "system"

    # ========================================================================
    # READ OPERATIONS (Parallel - up to 5 concurrent)
    # ========================================================================

    def is_vip_user(self, email: str) -> bool:
        """Check if user is VIP (READ - parallel)"""
        return self.wrapper.execute_protected(
            email, "[READ:VIP]", lambda: self.db.is_vip_user(email)
        )

    def get_user_credits(self, email: str) -> int:
        """Get user's available credits (READ - parallel)"""
        return self.wrapper.execute_protected(
            email, "[READ:CREDITS]", lambda: self.db.get_user_credits(email)
        )

    def get_date_reservations_summary(self, dates: list, email: str) -> dict:
        """Get summary of reservations for dates (READ - parallel)"""
        return self.wrapper.execute_protected(
            email,
            "[READ:RESERVATIONS_SUMMARY]",
            lambda: self.db.get_date_reservations_summary(dates, email),
        )

    def is_slot_still_available(self, date, hour: int) -> bool:
        """Check if a time slot is still available (READ - parallel)"""
        return self.wrapper.execute_protected(
            self._get_user_email_from_context(),
            "[READ:SLOT_AVAILABLE]",
            lambda: self.db.is_slot_still_available(date, hour),
        )

    def get_reservations_with_names_for_date(self, date) -> list:
        """Get all reservations for a date with user names (READ - parallel)"""
        return self.wrapper.execute_protected(
            self._get_user_email_from_context(),
            "[READ:RESERVATIONS_WITH_NAMES]",
            lambda: self.db.get_reservations_with_names_for_date(date),
        )

    def get_user_reservations_for_date(self, email: str, date) -> list:
        """Get user's reservations for a specific date (READ - parallel)"""
        return self.wrapper.execute_protected(
            email,
            "[READ:USER_RESERVATIONS_DATE]",
            lambda: self.db.get_user_reservations_for_date(email, date),
        )

    def get_maintenance_slots_for_date(self, date) -> list:
        """Get maintenance slots for a date (READ - parallel)"""
        return self.wrapper.execute_protected(
            self._get_user_email_from_context(),
            "[READ:MAINTENANCE_SLOTS]",
            lambda: self.db.get_maintenance_slots_for_date(date),
        )

    def get_current_lock_code(self) -> Optional[str]:
        """Get current court lock code (READ - parallel)"""
        return self.wrapper.execute_protected(
            self._get_user_email_from_context(),
            "[READ:LOCK_CODE]",
            lambda: self.db.get_current_lock_code(),
        )

    def is_hour_available(self, date, hour: int) -> bool:
        """Check if an hour is available for reservation (READ - parallel)"""
        return self.wrapper.execute_protected(
            self._get_user_email_from_context(),
            "[READ:HOUR_AVAILABLE]",
            lambda: self.db.is_hour_available(date, hour),
        )

    def get_all_reservations(self, date) -> list:
        """Get all reservations for a date (READ - parallel)"""
        return self.wrapper.execute_protected(
            self._get_user_email_from_context(),
            "[READ:ALL_RESERVATIONS]",
            lambda: self.db.get_all_reservations(date),
        )

    def invalidate_user_cache(self, email: str):
        """Invalidate user's cache (READ - parallel, non-blocking)"""
        return self.wrapper.execute_protected(
            email, "[READ:CACHE_INVALIDATE]", lambda: self.db.invalidate_user_cache(email)
        )

    # ========================================================================
    # WRITE OPERATIONS (Serial - 1 at a time)
    # ========================================================================

    def save_reservation(self, date, hour: int, user_name: str, user_email: str) -> tuple:
        """Save a new reservation (WRITE - serial)"""
        return self.wrapper.execute_protected(
            user_email,
            "[WRITE:RESERVATION]",
            lambda: self.db.save_reservation(date, hour, user_name, user_email),
        )

    def create_atomic_reservation(
        self, date, hour: int, user_name: str, user_email: str
    ) -> tuple:
        """Create atomic reservation with credit deduction (WRITE - serial)"""
        return self.wrapper.execute_protected(
            user_email,
            "[WRITE:ATOMIC_RESERVATION]",
            lambda: self.db.create_atomic_reservation(date, hour, user_name, user_email),
        )

    def create_atomic_double_reservation(
        self, date, hour1: int, hour2: int, user_name: str, user_email: str
    ) -> tuple:
        """Create atomic double reservation with credit deduction (WRITE - serial)"""
        return self.wrapper.execute_protected(
            user_email,
            "[WRITE:DOUBLE_RESERVATION]",
            lambda: self.db.create_atomic_double_reservation(
                date, hour1, hour2, user_name, user_email
            ),
        )

    def delete_reservation(self, reservation_id: int, user_email: str) -> tuple:
        """Delete a reservation and refund credits (WRITE - serial)"""
        return self.wrapper.execute_protected(
            user_email,
            "[WRITE:DELETE_RESERVATION]",
            lambda: self.db.delete_reservation(reservation_id, user_email),
        )

    def save_verification_code(self, email: str, code: str) -> bool:
        """Save email verification code (WRITE - serial)"""
        return self.wrapper.execute_protected(
            email,
            "[WRITE:VERIFICATION_CODE]",
            lambda: self.db.save_verification_code(email, code),
        )

    def verify_email_code(self, email: str, code: str) -> tuple:
        """Verify email code (WRITE - serial)"""
        return self.wrapper.execute_protected(
            email, "[WRITE:VERIFY_EMAIL]", lambda: self.db.verify_email_code(email, code)
        )

    def cleanup_expired_data(self) -> tuple:
        """Clean up expired verification codes and other temp data (WRITE - serial)"""
        return self.wrapper.execute_protected(
            "system",
            "[WRITE:CLEANUP]",
            lambda: self.db.cleanup_expired_data(),
        )

    # Pass through other methods that don't need queue protection
    def __getattr__(self, name):
        """Forward any other method calls to the original db_manager"""
        attr = getattr(self.db, name)
        return attr
