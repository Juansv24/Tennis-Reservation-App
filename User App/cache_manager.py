"""
ABOUTME: Simple in-memory cache manager for frequently accessed data
ABOUTME: Uses timestamps for automatic TTL-based invalidation, no external dependencies
"""
import time
from typing import Any, Optional, Callable


class CacheManager:
    """Simple in-memory cache with TTL support

    Features:
    - Automatic expiration based on TTL
    - Thread-safe (via GIL for small operations)
    - No external dependencies
    - Configurable per-key TTL
    """

    def __init__(self):
        self._cache = {}  # {key: {'value': any, 'expires_at': float}}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired

        Returns: Value if cached and not expired, None otherwise
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry['expires_at']:
            # Expired - remove and return None
            del self._cache[key]
            return None

        return entry['value']

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Store value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default 5 minutes)
        """
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl_seconds
        }

    def get_or_compute(self, key: str, compute_fn: Callable, ttl_seconds: int = 300) -> Any:
        """Get from cache or compute and cache the value

        Args:
            key: Cache key
            compute_fn: Function that returns the value if not cached
            ttl_seconds: TTL for cached value

        Returns: Cached or computed value
        """
        # Try to get from cache first
        cached = self.get(key)
        if cached is not None:
            return cached

        # Not in cache - compute value
        value = compute_fn()

        # Store in cache
        self.set(key, value, ttl_seconds)

        return value

    def invalidate(self, key: str):
        """Manually invalidate a cache entry

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern

        Args:
            pattern: Pattern like 'user:*' invalidates 'user:1', 'user:2', etc.
        """
        if not pattern.endswith('*'):
            self.invalidate(pattern)
            return

        prefix = pattern[:-1]  # Remove the '*'
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()

    def get_stats(self):
        """Get cache statistics

        Returns: Dict with cache size and entry count
        """
        now = time.time()
        expired = sum(1 for e in self._cache.values() if e['expires_at'] < now)
        return {
            'total_entries': len(self._cache),
            'expired_entries': expired,
            'active_entries': len(self._cache) - expired
        }


# Global cache instance - shared across all users in this session
_cache_manager = CacheManager()


def get_cache() -> CacheManager:
    """Get the global cache manager instance"""
    return _cache_manager
