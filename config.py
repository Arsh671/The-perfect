import os
from dataclasses import dataclass

@dataclass
class Config:
    # Bot configuration
    BOT_TOKEN = "7770272398:AAE8BsGM4zs21frNkKFt_HOk2_mfDUGNXvc"
    OWNER_ID = 8172579666
    OWNER_USERNAME = "fakesoul15"
    
    # Groq API Keys - will be rotated
    GROQ_API_KEYS = [
        # 5 API keys will be provided by the user
        # These are placeholders and should be replaced with actual keys
        "",  # Replace with actual key 1
        "",  # Replace with actual key 2
        "",  # Replace with actual key 3
        "",  # Replace with actual key 4
        ""   # Replace with actual key 5
    ]
    
    # Community links
    SUPPORT_GROUP = "https://t.me/+5e44PSnDdFNlMGM1"
    SUPPORT_CHANNEL = "https://t.me/promotionandsupport"
    
    # Database settings
    DATABASE_PATH = "bot_data.db"
    
    # Cache settings
    CACHE_EXPIRATION = 3600  # 1 hour
    MAX_CACHE_SIZE = 1000
    
    # AI configuration
    AI_MODEL = "llama3-70b-8192"  # Groq model
    MAX_TOKENS = 1000
    TEMPERATURE = 1.0
    
    # Voice settings
    TTS_LANGUAGE = "en"
    
    # Message settings
    PROACTIVE_MESSAGE_INTERVAL = 3600  # 1 hour
    MAX_CONTEXT_LENGTH = 10  # Number of messages to keep for context
    
    # Content moderation
    CONTENT_MODERATION_ENABLED = True
    MODERATION_THRESHOLD = 0.95
    
    # Message styling
    BOT_SIGNATURE = "💋 Bestie AI"
