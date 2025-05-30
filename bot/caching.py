#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Caching system for the Telegram Bot
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Union

from bot.config import CACHE_EXPIRY, MAX_CACHE_ITEMS

logger = logging.getLogger(__name__)

# Main cache dictionary
# Structure: {key: {"data": value, "expiry": timestamp}}
_response_cache: Dict[str, Dict[str, Any]] = {}

# Conversation history cache
# Structure: {user_id: [{"role": "user", "content": "message"}, ...]}
_conversation_history: Dict[int, List[Dict[str, str]]] = {}

def get_cached_response(key: str) -> Optional[str]:
    """
    Get a response from cache if it exists and is not expired
    
    Args:
        key: Cache key
        
    Returns:
        Cached response or None if not found/expired
    """
    if key not in _response_cache:
        return None
    
    cache_item = _response_cache[key]
    current_time = time.time()
    
    # Check if expired
    if cache_item["expiry"] < current_time:
        # Remove expired item
        del _response_cache[key]
        return None
    
    # Return cached data
    return cache_item["data"]

def set_cached_response(key: str, value: str, expiry: int = CACHE_EXPIRY) -> bool:
    """
    Store a response in cache
    
    Args:
        key: Cache key
        value: Data to cache
        expiry: Cache expiry time in seconds (default from config)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if cache is full
        if len(_response_cache) >= MAX_CACHE_ITEMS:
            # Remove oldest item (by expiry)
            oldest_key = min(_response_cache, key=lambda k: _response_cache[k]["expiry"])
            del _response_cache[oldest_key]
        
        # Set expiry time
        expiry_time = time.time() + expiry
        
        # Store in cache
        _response_cache[key] = {
            "data": value,
            "expiry": expiry_time
        }
        
        return True
    except Exception as e:
        logger.error(f"Error setting cache: {e}")
        return False

def clear_cache() -> int:
    """
    Clear all cached responses
    
    Returns:
        Number of items cleared
    """
    count = len(_response_cache)
    _response_cache.clear()
    return count

def get_conversation_history(user_id: int, limit: int = 10) -> List[Dict[str, str]]:
    """
    Get conversation history for a user
    
    Args:
        user_id: Telegram user ID
        limit: Maximum number of history items to return
        
    Returns:
        List of conversation messages
    """
    if user_id not in _conversation_history:
        return []
    
    # Return last 'limit' messages
    return _conversation_history[user_id][-limit:]

def add_to_conversation_history(user_id: int, message: Dict[str, str]) -> bool:
    """
    Add a message to conversation history
    
    Args:
        user_id: Telegram user ID
        message: Message dict with role and content
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if user_id not in _conversation_history:
            _conversation_history[user_id] = []
        
        # Keep only last 20 messages
        if len(_conversation_history[user_id]) >= 20:
            _conversation_history[user_id].pop(0)
        
        _conversation_history[user_id].append(message)
        return True
    except Exception as e:
        logger.error(f"Error adding to conversation history: {e}")
        return False

def clear_conversation_history(user_id: Optional[int] = None) -> int:
    """
    Clear conversation history for a user or all users
    
    Args:
        user_id: Optional Telegram user ID (if None, clear all)
        
    Returns:
        Number of user histories cleared
    """
    if user_id is not None:
        if user_id in _conversation_history:
            del _conversation_history[user_id]
            return 1
        return 0
    else:
        count = len(_conversation_history)
        _conversation_history.clear()
        return count

def get_all_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the cache
    
    Returns:
        Dictionary with cache statistics
    """
    current_time = time.time()
    
    # Count expired items
    expired_count = sum(1 for item in _response_cache.values() if item["expiry"] < current_time)
    
    # Calculate average expiry time remaining
    remaining_times = [item["expiry"] - current_time for item in _response_cache.values() 
                      if item["expiry"] > current_time]
    avg_remaining = sum(remaining_times) / len(remaining_times) if remaining_times else 0
    
    return {
        "total_items": len(_response_cache),
        "expired_items": expired_count,
        "valid_items": len(_response_cache) - expired_count,
        "avg_expiry_remaining": int(avg_remaining),
        "conversation_users": len(_conversation_history),
        "max_capacity": MAX_CACHE_ITEMS,
        "utilization": len(_response_cache) / MAX_CACHE_ITEMS * 100 if MAX_CACHE_ITEMS > 0 else 0
    }
