import logging
import re
import string
from config import Config

logger = logging.getLogger(__name__)

# Common profanity lists
PROFANITY_WORDS = {
    'anal', 'anus', 'arse', 'ass', 'ballsack', 'balls', 'bastard', 'bitch', 'biatch', 
    'bloody', 'blowjob', 'bollock', 'bollok', 'boner', 'boob', 'bugger', 'bum', 
    'butt', 'buttplug', 'clitoris', 'cock', 'coon', 'crap', 'cunt', 'damn', 'dick', 
    'dildo', 'dyke', 'fag', 'feck', 'fellate', 'fellatio', 'felching', 'fuck', 
    'fudgepacker', 'flange', 'goddamn', 'hell', 'homo', 'jerk', 'jizz', 'knobend', 
    'labia', 'muff', 'nigger', 'nigga', 'penis', 'piss', 'poop', 'prick', 'pube', 'pussy', 
    'queer', 'scrotum', 'sex', 'shit', 'sh1t', 'slut', 'smegma', 'spunk', 'tit', 'tosser', 
    'turd', 'twat', 'vagina', 'wank', 'whore'
}

# Adult content patterns
ADULT_PATTERNS = [
    r'porn', r'xxx', r'adult content', r'onlyfans', r'escort', r'prostitut', 
    r'nud(e|es|ity)', r'cam\s?(girl|model|show)', r'masturbat', r'seduction',
    r'horny', r'hook\s?up', r'one night stand', r'sex\s?chat', r'strip\s?(club|tease)',
    r'f[u\*]ck\s?me', r'suck\s?my', r'blow\s?job', r'pussy', r'ass\s?hole'
]

async def check_message_content(text):
    """
    Check if the message content is appropriate
    Returns True if appropriate, False if inappropriate
    """
    if not Config.CONTENT_MODERATION_ENABLED:
        return True
    
    try:
        # Convert to lowercase for easier matching
        text_lower = text.lower()
        
        # Normalize text by removing punctuation
        translator = str.maketrans('', '', string.punctuation)
        normalized_text = text_lower.translate(translator)
        
        # Check for profanity by word
        words = normalized_text.split()
        for word in words:
            if word in PROFANITY_WORDS:
                logger.info(f"Content moderation: Found profanity word '{word}'")
                return False
        
        # Check for adult content patterns
        for pattern in ADULT_PATTERNS:
            if re.search(pattern, text_lower):
                logger.info(f"Content moderation: Found adult pattern '{pattern}'")
                return False
        
        # Check for explicit requests
        explicit_requests = [
            r'send\s(me\s)?(your\s)?(nudes|nude\spics|naked\spics)',
            r'show\s(me\s)?(your\s)?(body|boobs|tits|ass)',
            r'can\s(we|i)?\s(have\s)?sex',
            r'(let\'?s|we\scan)\s(have\s)?sex',
            r'sext(ing)?',
            r'cyber\s?sex',
            r'sex\s?chat',
            r'how\s(big|large)\s(is|are)\s(your)',
            r'you\s(look|are)\s(hot|sexy)',
            r'i\s(want|wanna)\s(to\s)?f[u\*]ck\s(you|u)'
        ]
        
        for pattern in explicit_requests:
            if re.search(pattern, text_lower):
                logger.info(f"Content moderation: Found explicit request pattern '{pattern}'")
                return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error in content moderation: {e}")
        # In case of error, we allow the message to be processed
        return True
