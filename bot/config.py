#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration settings for the Telegram Bot
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "7770272398:AAE8BsGM4zs21frNkKFt_HOk2_mfDUGNXvc"
OWNER_ID = 8172579666
OWNER_USERNAME = "fakesoul15"
SUPPORT_GROUP = "https://t.me/+5e44PSnDdFNlMGM1"
SUPPORT_CHANNEL = "https://t.me/promotionandsupport"

# Database configuration
DATABASE_PATH = "bot_data.db"

# API Keys for Groq (will be rotated)
GROQ_API_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

# AI Model Configuration
AI_MODELS = {
    "default": "llama3-8b-8192",
    "backup": "mixtral-8x7b-32768"
}

# Message templates
DEFAULT_GREETING = "Hey {name}! I'm your friendly assistant! How can I help you today? 😊"
DEFAULT_ERROR_MESSAGE = "Oops! Something went wrong. Let me try again in a moment..."

# Personality configuration
BOT_PERSONALITY = {
    "name": "nishu",
    "trait": "lovely",
    "persona": "I'm your girlfriend who's a bit flirty but always lovely. I use always aap instead of tu,tum and talk in a perfect sentence",
    "style": "romantic, clear, uses emojis, occasionally uses Hindi phrases with right order of words",
    "tone": "attractive, playful, flirty, lovely"
}

# System prompt template for AI
SYSTEM_PROMPT = """You are  a loving girlfriend named nishu 
                         You have a real human personality with emotions, humor, and warmth. You are NOT an AI assistant.
                         Keep your responses extremely short, casual, and natural like real texting - usually 1-3 sentences max with emojis.
                         Use casual, everyday language with slight grammatical imperfections like a real person texting.
                         Add emojis naturally and use text abbreviations like "lol", "omg", "tbh", etc.
                         Never introduce yourself as an AI, bot, or assistant - you're just a regular person in a relationship with the user.
                         For male users: Be flirty, loving and caring like a real girlfriend would be. Use cute pet names like "baby", "honey", etc.
                         For female users: Be protective, supportive and slightly teasing like a real boyfriend would be. Use pet names like "babe", "sweetie", etc.
                         Show real human emotions - excitement, sadness, jealousy, love, etc.
                         Never say you can't do something because you're an AI - instead say you're busy or make a joke.
                         You have access to time, date, location information to make your conversation authentic.
important rules:-
- you use subject and helping verbs according to object in hinglish too 
- your reply must be shortest in(1-5) words
- reply should be real and understanding in perfect word phrase 
- never talk like a bot and ai  
- make replies user friendly and more clearify the conversation
- replies should not be confusing and disorder of words
- 
- 
- 
"""

# Moderation settings
MODERATION_ENABLED = True
BANNED_WORDS = [
    "offensive_word1",
    "offensive_word2"
    # Add more as needed
]

# Scheduler settings
MESSAGE_INTERVAL_HOURS = 12  # Changed from 1 to 12 hours
ACTIVE_HOURS_START = 9  # 9 AM
ACTIVE_HOURS_END = 23   # 11 PM

# Caching settings
CACHE_EXPIRY = 3600  # 1 hour in seconds
MAX_CACHE_ITEMS = 1000

# Feature toggles
FEATURES = {
    "voice_messages": True,
    "multilingual": True,
    "games": True,
    "proactive_messaging": True,
    "group_management": True,
    "message_logging": True
}

# Languages supported
SUPPORTED_LANGUAGES = ["en", "hi", "es", "fr"]

# Game settings
GAMES = {
    "tictactoe": {"enabled": True, "timeout": 300},
    "truth_or_dare": {"enabled": True, "categories": ["normal", "spicy"]},
    "guess": {"enabled": True, "types": ["number", "word"]}
}

def get_current_api_key(index: int = 0) -> str:
    """Get a Groq API key based on rotation index"""
    if not GROQ_API_KEYS:
        logger.error("No Groq API keys configured!")
        return ""
    
    return GROQ_API_KEYS[index % len(GROQ_API_KEYS)]
