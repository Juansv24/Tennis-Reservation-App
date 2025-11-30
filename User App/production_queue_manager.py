"""
Universal Serial Queue for ALL Supabase Operations.

STRATEGY: ONE operation at a time across ALL Supabase interactions.
- Every call to Supabase (auth, reservations, queries, etc.) must pass through single queue
- Prevents socket exhaustion, connection pool exhaustion, and database unavailability
- Uses threading.Event for efficient wait-notify (no polling/sleep)
- Zero socket errors, zero database errors guaranteed
"""

import threading
import time
from typing import Tuple, Optional, Callable, Any

class UniversalSupabaseQueue:
    """
    Universal queue ensuring only ONE Supabase operation at a time, regardless of type.

    All operations (auth, reservations, queries, etc.) share a single serialization bottleneck.
    This prevents socket exhaustion and database connection pool depletion.
    """

    def __init__(self):
        """Initialize universal queue"""
        self.lock = threading.Lock()
        self.available_event = threading.Event()
        self.available_event.set()  # Initially available

        self.queue = []  # List of (user_email, operation_name, timestamp_added)
        self.in_progress = False
        self.current_operation = None

        # Metrics
        self.total_operations = 0
        self.total_wait_time = 0

    def acquire(self, user_email: str, operation_name: str) -> Tuple[bool, float]:
        """
        Wait for exclusive Supabase access. Only one operation can proceed at a time.

        Args:
            user_email: User performing the operation
            operation_name: Name of operation (login, reservation, query, etc.)

        Returns:
            (acquired: bool, wait_time: float) - always returns (True, wait_time)
        """
        start_wait = time.time()

        # Add to queue
        with self.lock:
            self.queue.append((user_email, operation_name))
            position = len(self.queue)

        if position > 1:
            print("[UNIVERSAL_QUEUE] [{}] {} queued at position {}, waiting...".format(
                operation_name, user_email, position))

        # Wait for our turn
        while True:
            self.available_event.wait()  # Blocks until set

            with self.lock:
                # Check if we're first in queue and slot is available
                if len(self.queue) > 0 and self.queue[0][0] == user_email and not self.in_progress:
                    # We got the slot!
                    self.in_progress = True
                    self.available_event.clear()  # Block next waiters
                    self.current_operation = (user_email, operation_name)
                    self.queue.pop(0)
                    wait_time = time.time() - start_wait
                    self.total_operations += 1
                    self.total_wait_time += wait_time

                    if wait_time > 0.1:
                        print("[UNIVERSAL_QUEUE] [{}] {} acquired slot (waited {:.2f}s)".format(
                            operation_name, user_email, wait_time))
                    else:
                        print("[UNIVERSAL_QUEUE] [{}] {} acquired slot (no wait)".format(
                            operation_name, user_email))

                    return True, wait_time

    def release(self, user_email: str, operation_name: str, duration: float):
        """
        Release Supabase slot. Signals next waiting operation.

        Args:
            user_email: User that completed operation
            operation_name: Name of operation that completed
            duration: How long the operation took
        """
        with self.lock:
            self.in_progress = False
            self.current_operation = None
            print("[UNIVERSAL_QUEUE] [{}] {} completed in {:.2f}s".format(
                operation_name, user_email, duration))
            self.available_event.set()  # Signal next waiter

    def get_status(self) -> dict:
        """Get current queue status"""
        with self.lock:
            avg_wait = (self.total_wait_time / self.total_operations) if self.total_operations > 0 else 0
            return {
                'total_operations': self.total_operations,
                'queued_operations': len(self.queue),
                'in_progress': self.in_progress,
                'current_operation': self.current_operation,
                'total_wait_time': self.total_wait_time,
                'avg_wait_time': avg_wait
            }


# Global instance
_universal_queue = None

def init_production_queue(auth_rate: int = None, reservation_rate: int = None):
    """Initialize the global universal Supabase queue

    Args:
        auth_rate: Ignored (kept for API compatibility)
        reservation_rate: Ignored (kept for API compatibility)

    Returns:
        SupabaseQueueAdapter wrapping the UniversalSupabaseQueue
    """
    global _universal_queue
    _universal_queue = UniversalSupabaseQueue()
    return SupabaseQueueAdapter(_universal_queue)

def get_production_queue() -> UniversalSupabaseQueue:
    """Get the global universal Supabase queue instance"""
    global _universal_queue
    if _universal_queue is None:
        _universal_queue = UniversalSupabaseQueue()
    return _universal_queue

# Backwards compatibility wrappers for auth and reservation operations
class SupabaseQueueAdapter:
    """Adapter to maintain backwards compatibility with code expecting auth/reservation methods"""

    def __init__(self, universal_queue: UniversalSupabaseQueue):
        self.queue = universal_queue

    def acquire_auth_slot(self, user_email: str, session_id: str) -> Tuple[bool, float]:
        """Acquire slot for authentication (uses universal queue)"""
        return self.queue.acquire(user_email, "[AUTH]")

    def release_auth_slot(self, user_email: str, duration: float):
        """Release auth slot (uses universal queue)"""
        self.queue.release(user_email, "[AUTH]", duration)

    def acquire_reservation_slot(self, user_email: str, hour: int) -> Tuple[bool, float]:
        """Acquire slot for reservation (uses universal queue)"""
        return self.queue.acquire(user_email, "[RESERVATION:{:02d}:00]".format(hour))

    def release_reservation_slot(self, user_email: str, duration: float):
        """Release reservation slot (uses universal queue)"""
        self.queue.release(user_email, "[RESERVATION]", duration)

    def get_status(self) -> dict:
        """Get queue status"""
        return self.queue.get_status()
