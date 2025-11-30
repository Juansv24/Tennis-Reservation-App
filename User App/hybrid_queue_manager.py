"""
Hybrid Queue Manager - Optimized for both performance and data consistency

STRATEGY:
- WRITES (logins, reservations, deletes): Serialized (1 operation at a time)
- READS (credits, available hours, reservations): Parallelized (up to 5 concurrent)

This provides:
- Data consistency: No race conditions on writes
- Performance: Fast parallel reads, only writes wait
- Scalability: Handles 20 concurrent users efficiently
"""

import threading
import time
from typing import Tuple, Optional

class HybridSupabaseQueue:
    """
    Hybrid queue system for Supabase operations.
    - Write operations (auth, reservations, deletes): Serial queue (1 at a time)
    - Read operations (queries): Semaphore-based (5 concurrent)
    """

    def __init__(self, max_concurrent_reads: int = 5):
        """
        Initialize hybrid queue

        Args:
            max_concurrent_reads: Maximum concurrent read operations (default 5)
        """
        # Write queue - strictly serial
        self.write_lock = threading.Lock()
        self.write_available_event = threading.Event()
        self.write_available_event.set()  # Initially available
        self.write_queue = []
        self.in_write_progress = False
        self.current_write_op = None

        # Read semaphore - allows up to N concurrent reads
        self.read_semaphore = threading.Semaphore(max_concurrent_reads)

        # Metrics
        self.total_writes = 0
        self.total_reads = 0
        self.total_write_wait_time = 0
        self.total_read_wait_time = 0

    # ========================================================================
    # WRITE OPERATIONS (Serial Queue - 1 at a time)
    # ========================================================================

    def acquire_write_slot(self, user_email: str, operation_name: str, timeout: float = 60.0) -> Tuple[bool, float]:
        """
        Wait for exclusive write access (serial queue).
        Only one write operation can proceed at a time.

        Args:
            user_email: User performing the operation
            operation_name: Name of operation (login, reservation, delete, etc.)
            timeout: Maximum time to wait (default 60 seconds)

        Returns:
            (acquired: bool, wait_time: float)

        Raises:
            TimeoutError: If queue slot not acquired within timeout
        """
        start_wait = time.time()

        # Add to queue
        with self.write_lock:
            self.write_queue.append((user_email, operation_name))
            position = len(self.write_queue)

        if position > 1:
            print(f"[HYBRID_QUEUE] [WRITE] [{operation_name}] {user_email} queued at position {position}, waiting...")

        # Wait for our turn with timeout
        while True:
            # Wait with timeout
            acquired = self.write_available_event.wait(timeout=5.0)

            # Check if we've exceeded total timeout
            elapsed = time.time() - start_wait
            if elapsed > timeout:
                with self.write_lock:
                    if (user_email, operation_name) in self.write_queue:
                        self.write_queue.remove((user_email, operation_name))
                raise TimeoutError(f"Write queue timeout after {elapsed:.1f}s - system overloaded")

            with self.write_lock:
                # Check if we're first in queue and slot is available
                if len(self.write_queue) > 0 and self.write_queue[0][0] == user_email and not self.in_write_progress:
                    # We got the slot!
                    self.in_write_progress = True
                    self.write_available_event.clear()  # Block next waiters
                    self.current_write_op = (user_email, operation_name)
                    self.write_queue.pop(0)
                    wait_time = time.time() - start_wait
                    self.total_writes += 1
                    self.total_write_wait_time += wait_time

                    if wait_time > 0.1:
                        print(f"[HYBRID_QUEUE] [WRITE] [{operation_name}] {user_email} acquired slot (waited {wait_time:.2f}s)")
                    else:
                        print(f"[HYBRID_QUEUE] [WRITE] [{operation_name}] {user_email} acquired slot (no wait)")

                    return True, wait_time

    def release_write_slot(self, user_email: str, operation_name: str, duration: float):
        """
        Release write slot. Signals next waiting operation.

        Args:
            user_email: User that completed operation
            operation_name: Name of operation that completed
            duration: How long the operation took
        """
        with self.write_lock:
            self.in_write_progress = False
            self.current_write_op = None
            print(f"[HYBRID_QUEUE] [WRITE] [{operation_name}] {user_email} completed in {duration:.2f}s")
            self.write_available_event.set()  # Signal next waiter

    # ========================================================================
    # READ OPERATIONS (Parallel - up to 5 concurrent)
    # ========================================================================

    def acquire_read_slot(self, user_email: str, operation_name: str, timeout: float = 10.0) -> Tuple[bool, float]:
        """
        Acquire read access (parallel semaphore - up to 5 concurrent).

        Args:
            user_email: User performing the read
            operation_name: Name of operation (read_credits, check_availability, etc.)
            timeout: Maximum time to wait (default 10 seconds)

        Returns:
            (acquired: bool, wait_time: float)

        Raises:
            TimeoutError: If semaphore slot not acquired within timeout
        """
        start_wait = time.time()

        # Try to acquire semaphore slot
        acquired = self.read_semaphore.acquire(timeout=timeout)

        if not acquired:
            elapsed = time.time() - start_wait
            raise TimeoutError(f"Read slot timeout after {elapsed:.1f}s - too many concurrent reads")

        wait_time = time.time() - start_wait
        self.total_reads += 1
        self.total_read_wait_time += wait_time

        if wait_time > 0.05:
            print(f"[HYBRID_QUEUE] [READ] [{operation_name}] {user_email} acquired slot (waited {wait_time:.3f}s)")

        return True, wait_time

    def release_read_slot(self, user_email: str, operation_name: str, duration: float):
        """
        Release read slot. Allows next waiting read to proceed.

        Args:
            user_email: User that completed read
            operation_name: Name of operation that completed
            duration: How long the operation took
        """
        self.read_semaphore.release()
        # Only log slow reads
        if duration > 1.0:
            print(f"[HYBRID_QUEUE] [READ] [{operation_name}] {user_email} completed in {duration:.2f}s")

    # ========================================================================
    # STATUS AND METRICS
    # ========================================================================

    def get_status(self) -> dict:
        """Get current queue status"""
        with self.write_lock:
            avg_write_wait = (self.total_write_wait_time / self.total_writes) if self.total_writes > 0 else 0
            avg_read_wait = (self.total_read_wait_time / self.total_reads) if self.total_reads > 0 else 0

            return {
                'write_queue_length': len(self.write_queue),
                'write_in_progress': self.in_write_progress,
                'current_write_op': self.current_write_op,
                'total_writes': self.total_writes,
                'avg_write_wait': avg_write_wait,
                'total_reads': self.total_reads,
                'avg_read_wait': avg_read_wait
            }


# Global instance
_hybrid_queue = None

def init_hybrid_queue(max_concurrent_reads: int = 5) -> 'HybridSupabaseQueue':
    """Initialize the global hybrid queue"""
    global _hybrid_queue
    _hybrid_queue = HybridSupabaseQueue(max_concurrent_reads=max_concurrent_reads)
    return _hybrid_queue

def get_hybrid_queue() -> 'HybridSupabaseQueue':
    """Get the global hybrid queue instance"""
    global _hybrid_queue
    if _hybrid_queue is None:
        _hybrid_queue = HybridSupabaseQueue()
    return _hybrid_queue
