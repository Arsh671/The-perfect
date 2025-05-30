#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper functions for the Telegram Bot
"""

import logging
import random
import re
from typing import List, Dict, Any, Optional, Tuple

from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# Emojis by category for random selection
EMOJIS = {
    "happy": ["😊", "😄", "😁", "😃", "😀", "🙂", "😉", "😍", "🥰", "😘", "😚", "😗", "☺️", "😌", "😏"],
    "love": ["❤️", "💗", "💓", "💕", "💖", "💘", "💝", "💞", "💟", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍"],
    "nature": ["🌸", "🌺", "🌹", "🌷", "🌻", "🌼", "🌱", "🌲", "🌳", "🌴", "🌵", "🌾", "🌿", "☘️", "🍀", "🍁", "🍂", "🍃"],
    "animals": ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🙈", "🙉", "🙊"],
    "food": ["🍏", "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍈", "🍒", "🍑", "🥭", "🍍", "🥥", "🥝", "🍅", "🍆"],
    "activity": ["✨", "💫", "🌟", "⭐", "🌈", "🔥", "💥", "⚡", "☄️", "🌠", "🎉", "🎊", "🎈", "🎁", "🎀", "🎯", "🏆", "🥇"],
    "symbols": ["✅", "☑️", "✔️", "❌", "❓", "❕", "❗", "〽️", "⚠️", "🔱", "📛", "🔰", "⭕", "✖️", "➕", "➖", "➗", "♾️"],
    "misc": ["🎵", "🎶", "👑", "💎", "🔮", "🧿", "🧸", "🎭", "🎨", "🎬", "🎤", "📱", "💻", "⌚", "📷", "🔋", "💡", "🔍"]
}

def detect_language(text: str) -> Optional[str]:
    """
    Detect the language of a text string
    
    Args:
        text: Text to analyze
        
    Returns:
        ISO language code (e.g., 'en', 'hi', 'es') or None if detection fails
    """
    if not text or len(text.strip()) < 3:
        return None
    
    try:
        return detect(text)
    except LangDetectException:
        logger.debug(f"Could not detect language for: {text[:20]}...")
        return None

def translate_text(text: str, target_lang: str = 'en') -> Optional[str]:
    """
    Translate text to the target language
    
    Note: This is a stub - implementation would require a translation API
    
    Args:
        text: Text to translate
        target_lang: Target language code
        
    Returns:
        Translated text or None if translation fails
    """
    # This would normally use a translation API like Google Translate
    # For now, we'll just return the original text
    logger.info(f"Translation requested (not implemented): {text[:20]}... to {target_lang}")
    return text

def add_emojis(text: str, min_count: int = 1, max_count: int = 3) -> str:
    """
    Add random emojis to a text string
    
    Args:
        text: Original text
        min_count: Minimum number of emojis to add
        max_count: Maximum number of emojis to add
        
    Returns:
        Text with added emojis
    """
    if not text:
        return text
    
    # Get all emojis
    all_emojis = []
    for category in EMOJIS.values():
        all_emojis.extend(category)
    
    # Select random emojis
    count = random.randint(min_count, max_count)
    selected_emojis = random.sample(all_emojis, min(count, len(all_emojis)))
    
    # Add emojis to text
    return text + " " + " ".join(selected_emojis)

def get_emojis_by_mood(mood: str, count: int = 2) -> List[str]:
    """
    Get emojis that match a specific mood
    
    Args:
        mood: Mood name (happy, love, etc.)
        count: Number of emojis to return
        
    Returns:
        List of emojis
    """
    if mood.lower() in EMOJIS:
        emoji_list = EMOJIS[mood.lower()]
    else:
        # Default to misc category if mood not found
        emoji_list = EMOJIS["misc"]
    
    # Select random emojis
    return random.sample(emoji_list, min(count, len(emoji_list)))

def format_number(num: int) -> str:
    """
    Format a number with commas for thousands
    
    Args:
        num: Number to format
        
    Returns:
        Formatted number string
    """
    return "{:,}".format(num)

def shorten_text(text: str, max_length: int = 100) -> str:
    """
    Shorten text to a maximum length with ellipsis
    
    Args:
        text: Text to shorten
        max_length: Maximum length
        
    Returns:
        Shortened text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text
    
    Args:
        text: Text to analyze
        
    Returns:
        List of found URLs
    """
    if not text:
        return []
    
    # URL pattern
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    
    # Find all matches
    return re.findall(url_pattern, text)

def extract_usernames(text: str) -> List[str]:
    """
    Extract Telegram usernames from text
    
    Args:
        text: Text to analyze
        
    Returns:
        List of found usernames
    """
    if not text:
        return []
    
    # Username pattern (starts with @ followed by at least 5 chars)
    username_pattern = r'@([a-zA-Z0-9_]{5,})'
    
    # Find all matches
    matches = re.findall(username_pattern, text)
    
    return ["@" + username for username in matches]

def create_progress_bar(progress: float, total: int = 10) -> str:
    """
    Create a text-based progress bar
    
    Args:
        progress: Progress value between 0 and 1
        total: Total number of segments
        
    Returns:
        Progress bar as string
    """
    if progress < 0:
        progress = 0
    elif progress > 1:
        progress = 1
    
    filled = int(progress * total)
    empty = total - filled
    
    return "█" * filled + "▒" * empty

def is_valid_user_id(user_id: str) -> bool:
    """
    Check if a string is a valid Telegram user ID
    
    Args:
        user_id: User ID to check
        
    Returns:
        True if valid, False otherwise
    """
    # Telegram user IDs are large positive integers
    try:
        uid = int(user_id)
        return uid > 0
    except (ValueError, TypeError):
        return False

def is_valid_group_id(group_id: str) -> bool:
    """
    Check if a string is a valid Telegram group ID
    
    Args:
        group_id: Group ID to check
        
    Returns:
        True if valid, False otherwise
    """
    # Telegram group IDs are large negative integers
    try:
        gid = int(group_id)
        return gid < 0
    except (ValueError, TypeError):
        return False
