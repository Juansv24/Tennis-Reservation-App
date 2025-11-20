"""
ABOUTME: Thin adapter to integrate request queue manager with database operations
ABOUTME: Provides convenience methods for queuing critical DB operations
"""
import streamlit as st
from request_queue_manager import RequestQueueManager

# Global instance - created once per Streamlit session
_queue_manager = None

def get_queue_manager():
    """Get or create the request queue manager for this session"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = RequestQueueManager(
            max_queued=100,          # Max 100 operations in queue
            max_concurrent=10,       # Max 10 concurrent operations
            max_retries=2,           # Try twice before giving up
            timeout_seconds=30       # 30 second timeout per operation
        )
    return _queue_manager


def queue_atomic_reservation(db_manager, date, hour, name, email):
    """Queue a reservation operation through the request manager

    Returns: (success: bool, message: str)
    """
    queue_mgr = get_queue_manager()

    def reservation_op():
        return db_manager.create_atomic_reservation(date, hour, name, email)

    try:
        result = queue_mgr.enqueue_request(reservation_op)
        if result is not None:
            success, message = result
            return success, message
        else:
            return False, "Request queue is full - please try again"
    except Exception as e:
        return False, f"System overload - please try again: {str(e)}"


def queue_double_reservation(db_manager, date, hour1, hour2, name, email):
    """Queue a 2-hour reservation operation"""
    queue_mgr = get_queue_manager()

    def reservation_op():
        return db_manager.create_atomic_double_reservation(date, hour1, hour2, name, email)

    try:
        result = queue_mgr.enqueue_request(reservation_op)
        if result is not None:
            success, message = result
            return success, message
        else:
            return False, "Request queue is full - please try again"
    except Exception as e:
        return False, f"System overload - please try again: {str(e)}"


def is_system_overloaded():
    """Check if system is experiencing extreme load

    Returns: bool - True if circuit breaker is open
    """
    queue_mgr = get_queue_manager()
    return queue_mgr.is_circuit_breaker_open()
