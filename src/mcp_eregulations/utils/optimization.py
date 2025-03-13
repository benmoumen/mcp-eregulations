"""
Performance optimization for the MCP eRegulations server.
"""
from typing import Dict, Any, Optional, List, Callable
import time
import asyncio
import logging
import functools
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Cache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize the cache.
        
        Args:
            ttl_seconds: Time-to-live in seconds for cache entries
        """
        self.cache = {}
        self.ttl_seconds = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if datetime.now() > entry["expiry"]:
            # Entry has expired, remove it
            del self.cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL in seconds
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        expiry = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            "value": value,
            "expiry": expiry
        }
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        self.cache.clear()
    
    def cleanup(self) -> int:
        """
        Remove expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry["expiry"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)


# Create a global cache instance
cache = Cache()


def cached(ttl_seconds: Optional[int] = None) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Optional custom TTL in seconds
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a cache key based on function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Check if result is in cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Call the function
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    
    return decorator


class RateLimiter:
    """Rate limiter to prevent API abuse."""
    
    def __init__(self, max_calls: int = 10, time_window: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = {}
    
    async def acquire(self, key: str) -> bool:
        """
        Acquire permission to make a call.
        
        Args:
            key: Identifier for the caller (e.g., IP address, API key)
            
        Returns:
            True if the call is allowed, False otherwise
        """
        now = time.time()
        
        # Initialize call history for the key if not exists
        if key not in self.calls:
            self.calls[key] = []
        
        # Remove calls outside the time window
        self.calls[key] = [
            timestamp for timestamp in self.calls[key]
            if now - timestamp <= self.time_window
        ]
        
        # Check if the call is allowed
        if len(self.calls[key]) >= self.max_calls:
            return False
        
        # Add the call
        self.calls[key].append(now)
        return True
    
    def reset(self, key: str) -> None:
        """
        Reset call history for a key.
        
        Args:
            key: Identifier for the caller
        """
        if key in self.calls:
            del self.calls[key]


# Create a global rate limiter instance
rate_limiter = RateLimiter()


class ConnectionPool:
    """Connection pool for reusing connections."""
    
    def __init__(self, max_size: int = 10, timeout: float = 30.0):
        """
        Initialize the connection pool.
        
        Args:
            max_size: Maximum number of connections in the pool
            timeout: Connection timeout in seconds
        """
        self.max_size = max_size
        self.timeout = timeout
        self.pool = asyncio.Queue(maxsize=max_size)
        self.active_connections = 0
    
    async def get_connection(self):
        """
        Get a connection from the pool.
        
        Returns:
            A connection object
        """
        # Try to get a connection from the pool
        try:
            connection = self.pool.get_nowait()
            logger.debug("Reusing connection from pool")
            return connection
        except asyncio.QueueEmpty:
            # No connections available in the pool
            pass
        
        # Check if we can create a new connection
        if self.active_connections < self.max_size:
            logger.debug("Creating new connection")
            self.active_connections += 1
            # In a real implementation, this would create a new connection
            # For now, we'll just return a placeholder
            return {"id": self.active_connections, "created_at": time.time()}
        
        # Wait for a connection to become available
        logger.debug("Waiting for connection")
        return await self.pool.get()
    
    async def release_connection(self, connection):
        """
        Release a connection back to the pool.
        
        Args:
            connection: The connection to release
        """
        logger.debug("Releasing connection back to pool")
        await self.pool.put(connection)
    
    async def close_all(self):
        """Close all connections in the pool."""
        logger.debug("Closing all connections")
        while not self.pool.empty():
            connection = await self.pool.get()
            # In a real implementation, this would close the connection
            self.active_connections -= 1


# Create a global connection pool instance
connection_pool = ConnectionPool()


def rate_limited(func: Callable) -> Callable:
    """
    Decorator to apply rate limiting to a function.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with rate limiting
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Get the API key from kwargs or use a default key
        api_key = kwargs.get("api_key", "default")
        
        # Check if the call is allowed
        if not await rate_limiter.acquire(api_key):
            return "Rate limit exceeded. Please try again later."
        
        # Call the function
        return await func(*args, **kwargs)
    
    return wrapper


def timed(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with timing
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Call the function
        result = await func(*args, **kwargs)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
        
        return result
    
    return wrapper


async def cleanup_task():
    """Background task to clean up expired cache entries."""
    while True:
        try:
            # Clean up expired cache entries
            removed = cache.cleanup()
            if removed > 0:
                logger.info(f"Removed {removed} expired cache entries")
            
            # Wait for the next cleanup
            await asyncio.sleep(300)  # 5 minutes
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)  # Wait a bit before retrying


def start_background_tasks():
    """Start background tasks for maintenance."""
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_task())
    logger.info("Started background maintenance tasks")
