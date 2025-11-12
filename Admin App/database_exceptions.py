"""
Custom exceptions for database operations
"""


class DatabaseError(Exception):
    """Base exception for database errors"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails or is lost"""
    pass


class DatabaseOperationError(DatabaseError):
    """Raised when a database operation fails"""
    pass


class InvalidResponseError(DatabaseError):
    """Raised when database returns an invalid response"""
    pass


class AtomicOperationError(DatabaseError):
    """Raised when an atomic operation (RPC) fails"""
    pass
