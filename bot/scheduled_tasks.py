#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Scheduled tasks and periodic operations for the Telegram Bot
"""

import logging
import asyncio
import random
import time
import datetime as dt
from datetime import datetime
from typing import Dict, List, Any, Optional

from telegram.ext import Application
from telegram.error import TelegramError

from bot.config import (MESSAGE_INTERVAL_HOURS, ACTIVE_HOURS_START, 
                       ACTIVE_HOURS_END, FEATURES)
from bot.database import (get_active_users, get_active_groups, 
                         update_daily_stats, get_setting, get_user_mood,
                         get_stickers_by_mood, get_random_sticker, increment_sticker_usage)
from bot.ai_handler import generate_ai_response
from bot.templates import get_random_proactive_message
from bot.caching import clear_cache

logger = logging.getLogger(__name__)

# Track last proactive message times
_last_proactive_messages: Dict[int, float] = {}

def setup_scheduler(application: Application) -> None:
    """
    Set up scheduled tasks for the bot
    
    Args:
        application: The bot application instance
    """
    # Schedule proactive messaging
    if FEATURES.get("proactive_messaging", True):
        job_queue = application.job_queue
        
        # Check if job queue is available (requires python-telegram-bot[job-queue])
        if job_queue is None:
            logger.warning("JobQueue is not available. Scheduled tasks will not run.")
            logger.warning("Install python-telegram-bot[job-queue] to enable this feature.")
            return
        
        # Send proactive messages every hour
        job_queue.run_repeating(
            send_proactive_messages,
            interval=MESSAGE_INTERVAL_HOURS * 3600,  # Convert hours to seconds
            first=10  # Start after 10 seconds
        )
        
        # Update daily stats at midnight
        job_queue.run_daily(
            update_stats_daily,
            time=dt.time(0, 5),  # 00:05 AM
        )
        
        # Clear expired cache items every 6 hours
        job_queue.run_repeating(
            clear_expired_cache,
            interval=6 * 3600,  # 6 hours
            first=300  # Start after 5 minutes
        )
        
        logger.info("Scheduled tasks have been set up")

async def send_proactive_messages(context) -> None:
    """
    Send proactive messages to active users
    
    Args:
        context: The callback context
    """
    if not FEATURES.get("proactive_messaging", True):
        return
    
    current_hour = datetime.now().hour
    
    # Only send messages during active hours
    if not (ACTIVE_HOURS_START <= current_hour < ACTIVE_HOURS_END):
        logger.info(f"Outside active hours ({ACTIVE_HOURS_START}-{ACTIVE_HOURS_END}), skipping proactive messages")
        return
    
    logger.info("Starting proactive message sending")
    
    # Get active users (those who have interacted recently)
    active_users = get_active_users(limit=50)
    
    if not active_users:
        logger.info("No active users found for proactive messaging")
        return
    
    current_time = time.time()
    messages_sent = 0
    
    for user in active_users:
        user_id = user["user_id"]
        
        # Check if we've messaged this user recently
        if user_id in _last_proactive_messages:
            last_time = _last_proactive_messages[user_id]
            hours_since_last = (current_time - last_time) / 3600
            
            # Don't message users too frequently
            if hours_since_last < MESSAGE_INTERVAL_HOURS * 2:
                continue
        
        # 50% chance to skip a user to avoid being too chatty
        if random.random() < 0.5:
            continue
        
        try:
            # Get a message template
            message_template = get_random_proactive_message()
            
            # Fill in user name
            name = user["first_name"] or "there"
            message = message_template.format(name=name)
            
            # Generate AI response (optional - for more personalized messages)
            use_ai = random.random() < 0.3  # 30% chance to use AI
            
            if use_ai:
                prompt = f"[Generate a short, friendly message to check in with {name} who hasn't chatted with you for a while. Be casual and friendly like a best friend texting. Keep it under 50 words. Don't ask how they are doing explicitly.]"
                ai_message = await generate_ai_response(
                    user_id=user_id,
                    user_name=name,
                    message_text=prompt
                )
                message = ai_message if ai_message else message
            
            # Send the message
            await context.bot.send_message(
                chat_id=user_id,
                text=message
            )
            
            # Get user's mood from database or use default
            user_mood = get_user_mood(user_id)
            if not user_mood:
                # Default moods for sweet messages
                user_mood = random.choice(["love", "flirty", "happy"])
            
            # 70% chance to send a sticker with the sweet message
            if random.random() < 0.7:
                # Get stickers matching the mood
                stickers = get_stickers_by_mood(user_mood, limit=1)
                
                # If no mood-specific stickers, fall back to any random sticker
                if not stickers:
                    stickers = get_random_sticker(limit=1)
                
                # Send sticker if available
                if stickers:
                    sticker = stickers[0]
                    try:
                        await context.bot.send_sticker(
                            chat_id=user_id,
                            sticker=sticker["file_id"]
                        )
                        # Increment sticker usage count
                        increment_sticker_usage(sticker["sticker_id"])
                        # Small delay between message and sticker
                        await asyncio.sleep(0.5)
                    except TelegramError as e:
                        logger.error(f"Error sending sticker to user {user_id}: {e}")
            
            # Update tracking
            _last_proactive_messages[user_id] = current_time
            messages_sent += 1
            
            # Small delay to avoid hitting rate limits
            await asyncio.sleep(1)
            
        except TelegramError as e:
            logger.error(f"Error sending proactive message to user {user_id}: {e}")
    
    logger.info(f"Sent {messages_sent} proactive messages")

async def update_stats_daily(context) -> None:
    """
    Update daily statistics at midnight
    
    Args:
        context: The callback context
    """
    logger.info("Running daily stats update")
    
    # Reset daily counters in database
    update_daily_stats()
    
    # Log stats to database
    active_users = len(get_active_users())
    active_groups = len(get_active_groups())
    
    logger.info(f"Daily stats updated. Active users: {active_users}, Active groups: {active_groups}")
    
    # Send stats to owner (optional)
    try:
        send_stats_to_owner = get_setting("send_daily_stats", False)
        if send_stats_to_owner:
            # This is implemented in admin_handler.py
            pass
    except Exception as e:
        logger.error(f"Error sending daily stats: {e}")

async def clear_expired_cache(context) -> None:
    """
    Clear expired cache items
    
    Args:
        context: The callback context
    """
    logger.info("Clearing expired cache items")
    
    # Clear expired items
    cleared_count = clear_cache()
    
    logger.info(f"Cleared {cleared_count} expired cache items")

async def rotate_api_key(context) -> None:
    """
    Rotate API keys to avoid hitting rate limits
    
    Args:
        context: The callback context
    """
    # This functionality is implemented in the ai_handler.py module
    # when errors occur with the current API key
    pass

async def random_owner_promotion(context) -> None:
    """
    Occasionally promote the owner in random groups
    
    Args:
        context: The callback context
    """
    # This is triggered by regular messages in group_handler.py
    pass
