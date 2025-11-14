"""
🎾 Request Queue Manager with Circuit Breaker Pattern
Prevents socket exhaustion and Supabase overflows under extreme concurrent load
"""

import asyncio
import time
from typing import Callable, Any, Optional, Dict, Tuple
from enum import Enum
from datetime import datetime, timedelta
import threading


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RequestQueueConfig:
    """Configuration for request queue manager"""

    def __init__(
        self,
        max_queue_size: int = 100,
        max_concurrent_requests: int = 10,
        timeout_seconds: float = 30.0,
        circuit_breaker_threshold: int = 5,  # Failures before opening
        circuit_breaker_timeout: float = 30.0,  # How long to stay open
        rate_limit_requests_per_second: int = 100,
    ):
        self.max_queue_size = max_queue_size
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout_seconds = timeout_seconds
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.rate_limit_requests_per_second = rate_limit_requests_per_second


class CircuitBreaker:
    """Implements Circuit Breaker pattern to prevent cascading failures"""

    def __init__(self, failure_threshold: int = 5, timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()

    def record_success(self):
        """Record successful request"""
        with self.lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                print("✅ Circuit breaker CLOSED (recovered)")

    def record_failure(self):
        """Record failed request"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                print(f"🔴 Circuit breaker OPEN (after {self.failure_count} failures)")

    def can_execute(self) -> Tuple[bool, Optional[str]]:
        """Check if request can be executed"""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True, None

            if self.state == CircuitState.OPEN:
                # Check if timeout expired, try half-open
                if (self.last_failure_time and
                    datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout)):
                    self.state = CircuitState.HALF_OPEN
                    self.failure_count = 0
                    print("🟡 Circuit breaker HALF_OPEN (testing recovery)")
                    return True, None
                else:
                    return False, "Circuit breaker OPEN: service unavailable"

            if self.state == CircuitState.HALF_OPEN:
                return True, None

        return False, "Circuit breaker error"

    def get_state(self) -> str:
        with self.lock:
            return self.state.value


class RateLimiter:
    """Implements token bucket rate limiter"""

    def __init__(self, requests_per_second: int = 100):
        self.capacity = requests_per_second
        self.tokens = requests_per_second
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self, num_tokens: int = 1) -> bool:
        """Try to acquire tokens from bucket"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill

            # Refill tokens based on elapsed time
            tokens_to_add = elapsed * self.capacity
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

            if self.tokens >= num_tokens:
                self.tokens -= num_tokens
                return True
            return False

    def wait_for_token(self) -> float:
        """Wait until token is available, return wait time"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.capacity
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0

            wait_time = (1 - self.tokens) / self.capacity
            self.tokens = 0
            return wait_time


class RequestQueueManager:
    """
    Manages request queue to prevent socket exhaustion

    Features:
    - Queue-based request processing (prevents socket pool overflow)
    - Circuit breaker pattern (prevents cascading failures)
    - Rate limiting (prevents Supabase overload)
    - Timeout handling (prevents hanging requests)
    - Metrics tracking (monitor system health)
    """

    def __init__(self, config: Optional[RequestQueueConfig] = None):
        self.config = config or RequestQueueConfig()
        self.request_queue: asyncio.Queue = None
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            timeout=self.config.circuit_breaker_timeout
        )
        self.rate_limiter = RateLimiter(
            requests_per_second=self.config.rate_limit_requests_per_second
        )

        # Metrics
        self.total_queued = 0
        self.total_processed = 0
        self.total_rejected = 0
        self.total_errors = 0
        self.metrics_lock = threading.Lock()

    async def initialize(self):
        """Initialize async queue"""
        self.request_queue = asyncio.Queue(maxsize=self.config.max_queue_size)

    async def execute_with_queue(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute function with queue management and circuit breaker

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Tuple of (success, result, error_message)
        """

        # Check circuit breaker
        can_execute, error = self.circuit_breaker.can_execute()
        if not error:
            error = None

        if not can_execute:
            self._record_rejection()
            return False, None, error or "Circuit breaker open"

        # Check rate limiting
        wait_time = self.rate_limiter.wait_for_token()
        if wait_time > 0:
            await asyncio.sleep(wait_time)

        # Acquire semaphore slot
        async with self.semaphore:
            try:
                self._record_queued()

                # Execute with timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout_seconds
                )

                self.circuit_breaker.record_success()
                self._record_processed()
                return True, result, None

            except asyncio.TimeoutError:
                self.circuit_breaker.record_failure()
                self._record_error()
                return False, None, f"Request timeout (>{self.config.timeout_seconds}s)"

            except Exception as e:
                self.circuit_breaker.record_failure()
                self._record_error()
                error_msg = str(e)
                return False, None, error_msg

    def _record_queued(self):
        with self.metrics_lock:
            self.total_queued += 1

    def _record_processed(self):
        with self.metrics_lock:
            self.total_processed += 1

    def _record_rejection(self):
        with self.metrics_lock:
            self.total_rejected += 1

    def _record_error(self):
        with self.metrics_lock:
            self.total_errors += 1

    def get_metrics(self) -> Dict:
        """Get current metrics"""
        with self.metrics_lock:
            return {
                "total_queued": self.total_queued,
                "total_processed": self.total_processed,
                "total_rejected": self.total_rejected,
                "total_errors": self.total_errors,
                "circuit_breaker_state": self.circuit_breaker.get_state(),
                "available_semaphore_slots": self.semaphore._value,
            }


# Global instance (singleton pattern)
_queue_manager: Optional[RequestQueueManager] = None


async def get_request_queue_manager(
    config: Optional[RequestQueueConfig] = None
) -> RequestQueueManager:
    """Get or create global request queue manager"""
    global _queue_manager

    if _queue_manager is None:
        _queue_manager = RequestQueueManager(config)
        await _queue_manager.initialize()

    return _queue_manager


async def execute_with_queue(
    func: Callable,
    *args,
    **kwargs
) -> Tuple[bool, Any, Optional[str]]:
    """
    Helper function to execute with queue management

    Usage:
        success, result, error = await execute_with_queue(db_function, arg1, arg2)
    """
    manager = await get_request_queue_manager()
    return await manager.execute_with_queue(func, *args, **kwargs)


# Example usage/testing
if __name__ == "__main__":
    async def test_request_queue():
        """Test the request queue manager"""
        config = RequestQueueConfig(
            max_concurrent_requests=5,
            rate_limit_requests_per_second=50,
            circuit_breaker_threshold=3,
        )

        manager = RequestQueueManager(config)
        await manager.initialize()

        print("🎾 Testing Request Queue Manager")
        print("-" * 80)

        # Simulate some async operations
        async def dummy_db_call(user_id: int, delay: float = 0.1) -> str:
            await asyncio.sleep(delay)
            if user_id % 5 == 0:  # Simulate occasional failures
                raise Exception(f"Database error for user {user_id}")
            return f"User {user_id} result"

        # Run concurrent requests
        tasks = []
        for i in range(20):
            task = manager.execute_with_queue(dummy_db_call, i, delay=0.05)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        print(f"\nResults:")
        successes = sum(1 for r in results if r[0])
        failures = sum(1 for r in results if not r[0])
        print(f"  Successes: {successes}")
        print(f"  Failures: {failures}")

        print(f"\nMetrics:")
        metrics = manager.get_metrics()
        for key, value in metrics.items():
            print(f"  {key}: {value}")

    asyncio.run(test_request_queue())
