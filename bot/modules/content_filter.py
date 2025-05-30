import logging
import re
import string
from bot.modules.cache import get_cached_response, cache_response

logger = logging.getLogger(__name__)

# Simple profanity list (can be expanded)
PROFANITY_LIST = {
    'fuck', 'shit', 'ass', 'bitch', 'dick', 'pussy', 'cock', 'whore', 
    'slut', 'bastard', 'asshole', 'cunt', 'damn', 'hoe'
}

# Regex patterns for sensitive content
PHONE_PATTERN = r'\b(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
URL_PATTERN = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

async def is_content_appropriate(text):
    """Check if the content is appropriate."""
    if not text:
        return True
    
    # Check cache first
    cache_key = f"content_filter_{text}"
    cached_result = get_cached_response(cache_key)
    if cached_result is not None:
        return cached_result == "true"
    
    # Check for profanity
    if contains_profanity(text):
        logger.warning(f"Content filter: profanity detected in '{text}'")
        cache_response(cache_key, "false")
        return False
    
    # Check for personal information
    if contains_personal_info(text):
        logger.warning(f"Content filter: personal info detected in '{text}'")
        cache_response(cache_key, "false")
        return False
    
    # Check for suspicious patterns
    if contains_suspicious_patterns(text):
        logger.warning(f"Content filter: suspicious pattern detected in '{text}'")
        cache_response(cache_key, "false")
        return False
    
    # Content is appropriate
    cache_response(cache_key, "true")
    return True

def contains_profanity(text):
    """Check if the text contains profanity."""
    # Convert to lowercase and remove punctuation
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Split into words
    words = text.split()
    
    # Check for exact matches with profanity list
    for word in words:
        if word in PROFANITY_LIST:
            return True
        # Check for obfuscated profanity (e.g., f*ck, s**t)
        for profanity in PROFANITY_LIST:
            if len(word) == len(profanity) and word[0] == profanity[0] and '*' in word:
                return True
    
    return False

def contains_personal_info(text):
    """Check if the text contains personal information like phone numbers or emails."""
    # Check for phone numbers
    if re.search(PHONE_PATTERN, text):
        return True
    
    # Check for email addresses
    if re.search(EMAIL_PATTERN, text):
        return True
    
    return False

def contains_suspicious_patterns(text):
    """Check for suspicious patterns like excessive URLs, cryptocurrency addresses, etc."""
    # Count URLs
    urls = re.findall(URL_PATTERN, text)
    if len(urls) > 2:  # More than 2 URLs is suspicious
        return True
    
    # Check for cryptocurrency addresses (simple patterns)
    btc_pattern = r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b'  # Bitcoin
    eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'  # Ethereum
    
    if re.search(btc_pattern, text) or re.search(eth_pattern, text):
        return True
    
    return False
