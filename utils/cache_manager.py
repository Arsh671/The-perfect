import time
import logging
from functools import lru_cache
from collections import OrderedDict
from config import Config

logger = logging.getLogger(__name__)

# In-memory cache with TTL
class TTLCache:
    def __init__(self, max_size=1000, ttl=3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl  # Time-to-live in seconds
    
    def get(self, key):
        """Get an item from the cache if it exists and is not expired"""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            # Item has expired
            del self.cache[key]
            return None
        
        # Move the item to the end (recently used)
        self.cache.move_to_end(key)
        return value
    
    def set(self, key, value):
        """Add an item to the cache with current timestamp"""
        if key in self.cache:
            # Update existing entry
            del self.cache[key]
        
        # Check if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            self.cache.popitem(last=False)
        
        # Add new item
        self.cache[key] = (value, time.time())
    
    def clear(self):
        """Clear the entire cache"""
        self.cache.clear()
    
    def remove_expired(self):
        """Remove all expired items from the cache"""
        current_time = time.time()
        keys_to_remove = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl
        ]
        
        for key in keys_to_remove:
            del self.cache[key]
        
        return len(keys_to_remove)

# Singleton cache instance
_cache = None

def setup_cache():
    """Initialize the cache with configuration settings"""
    global _cache
    _cache = TTLCache(
        max_size=Config.MAX_CACHE_SIZE,
        ttl=Config.CACHE_EXPIRATION
    )
    logger.info(f"Cache initialized with max size {Config.MAX_CACHE_SIZE} and TTL {Config.CACHE_EXPIRATION}s")
    
    # Schedule cache cleanup
    import threading
    def clean_cache_periodically():
        while True:
            time.sleep(3600)  # Clean every hour
            if _cache:
                removed = _cache.remove_expired()
                logger.info(f"Cache cleanup: removed {removed} expired items")
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=clean_cache_periodically, daemon=True)
    cleanup_thread.start()

def get_cache(key):
    """Get a value from the cache"""
    global _cache
    if _cache is None:
        setup_cache()
    
    return _cache.get(key)

def set_cache(key, value):
    """Set a value in the cache"""
    global _cache
    if _cache is None:
        setup_cache()
    
    _cache.set(key, value)

def clear_cache():
    """Clear the entire cache"""
    global _cache
    if _cache is not None:
        _cache.clear()
        logger.info("Cache cleared")

# Function decorators for easy caching
def cached(ttl=None):
    """Decorator to cache function results"""
    def decorator(func):
        @lru_cache(maxsize=128)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = get_cache(key)
            if cached_result is not None:
                return cached_result
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            set_cache(key, result)
            
            return result
        return wrapper
    return decorator
