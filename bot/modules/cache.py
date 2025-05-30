import logging
import time
from collections import OrderedDict
from bot.config import CACHE_EXPIRY, MAX_CACHE_ITEMS

logger = logging.getLogger(__name__)

# Simple in-memory cache with LRU eviction
cache = OrderedDict()
cache_times = {}

def get_cached_response(key):
    """Get a cached response if it exists and hasn't expired."""
    if key in cache:
        # Check if the cached item has expired
        if time.time() - cache_times[key] > CACHE_EXPIRY:
            # Remove expired item
            cache.pop(key)
            cache_times.pop(key)
            return None
        
        # Move to end of OrderedDict to mark as recently used
        cache.move_to_end(key)
        
        return cache[key]
    
    return None

def cache_response(key, response):
    """Cache a response."""
    # If cache is full, remove the least recently used item
    if len(cache) >= MAX_CACHE_ITEMS:
        oldest_key, _ = cache.popitem(last=False)
        cache_times.pop(oldest_key)
    
    # Add to cache
    cache[key] = response
    cache_times[key] = time.time()

def clear_cache():
    """Clear the cache."""
    cache.clear()
    cache_times.clear()

def get_cache_stats():
    """Get cache statistics."""
    return {
        "size": len(cache),
        "max_size": MAX_CACHE_ITEMS,
        "hit_rate": calculate_hit_rate()
    }

# For tracking cache performance
cache_hits = 0
cache_misses = 0

def calculate_hit_rate():
    """Calculate the cache hit rate."""
    total = cache_hits + cache_misses
    if total == 0:
        return 0
    return cache_hits / total
