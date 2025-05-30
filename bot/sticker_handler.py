#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sticker handling for the Telegram Bot
"""

import logging
import random
import re
from typing import Dict, Any, Optional, List, Tuple

from telegram import Update, Sticker, StickerSet, User
from telegram.ext import ContextTypes
from telegram.constants import StickerFormat

from bot.config import OWNER_ID
from bot.database import (save_sticker, increment_sticker_usage, 
                        get_random_sticker, update_user_mood, 
                        get_user_mood, is_sticker_explicit, update_daily_stats)

logger = logging.getLogger(__name__)

# Common emotion keywords for mood detection
MOOD_KEYWORDS = {
    "happy": ["happy", "joy", "glad", "cheerful", "great", "excellent", "amazing", "wonderful", "excited", "thrilled"],
    "love": ["love", "crush", "adore", "fancy", "affection", "romantic", "heart", "kiss", "darling", "dear"],
    "sad": ["sad", "upset", "unhappy", "depressed", "disappointed", "sorry", "regret", "miserable", "hurt", "crying"],
    "angry": ["angry", "mad", "annoyed", "irritated", "furious", "frustrated", "hate", "rage", "damn", "pissed"],
    "surprised": ["surprised", "wow", "omg", "shocked", "astonished", "unexpected", "amazed", "startled", "woah", "wtf"],
    "confused": ["confused", "unsure", "don't understand", "what", "why", "how", "puzzled", "perplexed", "baffled", "weird"],
    "flirty": ["flirt", "sexy", "attractive", "cute", "gorgeous", "beautiful", "handsome", "date", "wink", "flirting"]
}

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sticker messages from users"""
    if update.effective_chat is None or update.effective_user is None or update.message is None or update.message.sticker is None:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    sticker = update.message.sticker
    
    # Don't process stickers in banned users/groups (handled at the message handler level already)
    
    # Extract sticker info
    sticker_id = sticker.file_id
    file_id = sticker.file_unique_id
    set_name = sticker.set_name if sticker.set_name else ""
    emoji = sticker.emoji if sticker.emoji else "🙂"
    is_animated = sticker.is_animated
    is_video = sticker.is_video
    
    # Determine sticker category
    category = determine_sticker_category(emoji, set_name)
    
    # Check if sticker might be explicit
    if is_sticker_explicit(file_id, sticker_id, set_name):
        logger.warning(f"Potential explicit sticker detected from user {user.id}: {file_id}")
        return
    
    # Save sticker to database
    try:
        save_sticker(
            sticker_id=file_id,
            file_id=sticker_id,
            set_name=set_name,
            emoji=emoji,
            category=category,
            is_animated=is_animated,
            is_video=is_video,
            added_by=user.id
        )
        
        # Update daily stats for received sticker
        update_daily_stats(stickers_received=1)
        
        logger.info(f"Saved sticker {file_id} from user {user.id} in category {category}")
    except Exception as e:
        logger.error(f"Error saving sticker: {str(e)}")
    
    # If in a private chat, respond occasionally with another sticker
    if chat.type == "private" and random.random() < 0.3:
        try:
            # Get a random sticker based on the category
            stickers = get_random_sticker(category=category, limit=1)
            if stickers and len(stickers) > 0:
                response_sticker = stickers[0]["file_id"]
                increment_sticker_usage(stickers[0]["sticker_id"])
                
                # Update stats
                update_daily_stats(stickers_sent=1)
                
                # Send the sticker
                await context.bot.send_sticker(
                    chat_id=chat.id,
                    sticker=response_sticker
                )
        except Exception as e:
            logger.error(f"Error sending sticker response: {str(e)}")

def determine_sticker_category(emoji: Optional[str], set_name: Optional[str]) -> str:
    """Determine the appropriate category for a sticker based on emoji and set name"""
    
    if not emoji and not set_name:
        return "other"
    
    # Map common emojis to categories
    emoji_map = {
        "❤️": "love",
        "💕": "love",
        "😍": "love",
        "💋": "love",
        "😘": "love",
        "😻": "love",
        "🥰": "love",
        "💞": "love",
        "💓": "love",
        "💗": "love",
        "💖": "love",
        "💘": "love",
        "🙏": "thank",
        "👋": "greeting",
        "😂": "funny",
        "🤣": "funny",
        "😭": "sad",
        "😢": "sad",
        "😤": "angry",
        "😡": "angry",
        "🤬": "angry",
        "🎉": "celebration",
        "🎊": "celebration",
        "🎂": "celebration",
        "🤔": "thinking",
        "😎": "cool",
        "👍": "approval",
        "👎": "disapproval",
        "🙄": "annoyed",
        "😒": "annoyed",
        "😏": "flirty",
        "😉": "flirty",
        "💯": "approval",
    }
    
    # Check if emoji is in our map
    if emoji and emoji in emoji_map:
        return emoji_map[emoji]
    
    # Check set name for keywords
    if set_name:
        set_name_lower = set_name.lower()
        keywords = {
            "love": ["love", "heart", "romantic", "kiss", "valentine"],
            "cute": ["cute", "kawaii", "adorable"],
            "funny": ["funny", "joke", "meme", "lol", "haha"],
            "anime": ["anime", "manga", "otaku", "waifu"],
            "animals": ["animal", "cat", "dog", "pet", "bunny", "kitten", "puppy"],
            "mood": ["mood", "feel", "emotion", "react", "reaction"],
            "celebration": ["party", "celebrate", "birthday", "congrats", "win", "yay"],
            "sad": ["sad", "cry", "tear", "unhappy", "depression"],
            "angry": ["angry", "mad", "rage", "fury", "hate"],
            "flirty": ["flirt", "sexy", "hot", "wink", "babe"]
        }
        
        for category, terms in keywords.items():
            for term in terms:
                if term in set_name_lower:
                    return category
    
    # Default category
    return "other"

def detect_mood_from_text(text: str) -> Optional[str]:
    """Detect user's mood from message text"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Check for mood keywords in the text
    mood_scores = {}
    for mood, keywords in MOOD_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # Look for whole word matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, text_lower)
            score += len(matches)
        
        if score > 0:
            mood_scores[mood] = score
    
    # Get the mood with the highest score
    if mood_scores:
        max_mood = max(mood_scores, key=mood_scores.get)
        return max_mood
    
    return None

async def maybe_send_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str) -> bool:
    """Maybe send a sticker based on user's mood and random chance"""
    if update.effective_chat is None:
        return False
    
    chat = update.effective_chat
    send_sticker = False
    
    # 15% chance of sending a sticker with a text response
    if random.random() < 0.15:
        try:
            from bot.database import (get_stickers_by_mood, update_user_mood, 
                                    get_user_mood, get_random_sticker, increment_sticker_usage)
            
            # Detect mood from message
            mood = detect_mood_from_text(text)
            
            # Get appropriate stickers
            if mood:
                stickers = get_stickers_by_mood(mood, limit=1)
                update_user_mood(user_id, mood)  # Update user's mood
            else:
                # Use user's stored mood if available
                current_mood = get_user_mood(user_id)
                if current_mood:
                    stickers = get_stickers_by_mood(current_mood, limit=1)
                else:
                    stickers = get_random_sticker(limit=1)
            
            # Send sticker if available
            if stickers and len(stickers) > 0:
                sticker_file_id = stickers[0]["file_id"]
                increment_sticker_usage(stickers[0]["sticker_id"])
                
                # Update daily stats
                from bot.database import update_daily_stats
                update_daily_stats(stickers_sent=1)
                
                await context.bot.send_sticker(
                    chat_id=chat.id,
                    sticker=sticker_file_id
                )
                send_sticker = True
                
        except Exception as e:
            logger.error(f"Error sending mood-based sticker: {str(e)}")
    
    return send_sticker