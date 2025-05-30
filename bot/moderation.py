#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Content moderation for the Telegram Bot
"""

import logging
import re
from typing import List, Set, Optional

from bot.config import MODERATION_ENABLED, BANNED_WORDS

logger = logging.getLogger(__name__)

# Initialize banned words set for efficient lookup
_banned_words_set: Set[str] = set(BANNED_WORDS)

# Common patterns to detect potentially inappropriate content
PATTERNS = {
    'sexually_explicit': r'(?i)(porn|sex|nsfw|explicit|naked|nude|xxx)',
    'violence': r'(?i)(kill|murder|attack|bomb|terror|shoot|gun|weapon)',
    'hate_speech': r'(?i)(racist|nazi|extremist|hate)',
    'personal_info': r'(?i)(credit\s*card|password|social\s*security|ssn|passport|address)'
}

def is_content_appropriate(text: str) -> bool:
    """
    Check if content is appropriate based on various checks
    
    Args:
        text: Text to check
        
    Returns:
        True if appropriate, False if inappropriate
    """
    if not MODERATION_ENABLED:
        return True
    
    # Empty text is fine
    if not text:
        return True
    
    text_lower = text.lower()
    
    # Check against banned words
    for word in _banned_words_set:
        word_lower = word.lower()
        if word_lower in text_lower:
            # Check if it's a whole word match using word boundaries
            pattern = r'\b' + re.escape(word_lower) + r'\b'
            if re.search(pattern, text_lower):
                logger.info(f"Content filtered: Banned word '{word}' detected")
                return False
    
    # Check against patterns
    for pattern_name, pattern in PATTERNS.items():
        if re.search(pattern, text):
            logger.info(f"Content filtered: Pattern '{pattern_name}' detected")
            return False
    
    # Content passed all checks
    return True

def add_banned_word(word: str) -> bool:
    """
    Add a word to the banned words list
    
    Args:
        word: Word to ban
        
    Returns:
        True if added, False if already exists
    """
    global _banned_words_set
    
    word = word.lower().strip()
    if not word:
        return False
    
    if word in _banned_words_set:
        return False
    
    _banned_words_set.add(word)
    return True

def remove_banned_word(word: str) -> bool:
    """
    Remove a word from the banned words list
    
    Args:
        word: Word to unban
        
    Returns:
        True if removed, False if not found
    """
    global _banned_words_set
    
    word = word.lower().strip()
    if not word or word not in _banned_words_set:
        return False
    
    _banned_words_set.remove(word)
    return True

def get_banned_words() -> List[str]:
    """
    Get the current list of banned words
    
    Returns:
        List of banned words
    """
    return sorted(list(_banned_words_set))

def filter_message(text: str) -> str:
    """
    Filter inappropriate content from text by replacing with asterisks
    
    Args:
        text: Text to filter
        
    Returns:
        Filtered text
    """
    if not MODERATION_ENABLED or not text:
        return text
    
    filtered_text = text
    
    # Replace banned words with asterisks
    for word in _banned_words_set:
        word_lower = word.lower()
        pattern = re.compile(r'\b' + re.escape(word_lower) + r'\b', re.IGNORECASE)
        filtered_text = pattern.sub('*' * len(word), filtered_text)
    
    return filtered_text

def is_external_link(text: str) -> bool:
    """
    Check if text contains external links (potential spam)
    
    Args:
        text: Text to check
        
    Returns:
        True if external links found, False otherwise
    """
    if not text:
        return False
    
    # Pattern to match URLs
    url_pattern = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'
    
    # Find all URLs
    urls = re.findall(url_pattern, text)
    
    if not urls:
        return False
    
    # Whitelist of allowed domains (e.g., telegram, trusted sites)
    whitelist = ['t.me', 'telegram.org', 'telegram.me', 'telegra.ph']
    
    # Check if any URL is not in whitelist
    for url in urls:
        is_whitelisted = any(domain in url.lower() for domain in whitelist)
        if not is_whitelisted:
            return True
    
    return False
