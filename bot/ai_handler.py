#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI conversation handler for the Telegram Bot
"""

import logging
import time
import re
import random
import json
import httpx
from typing import Dict, Any, Optional, List, Tuple

from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError

from bot.config import (OWNER_ID, OWNER_USERNAME, SYSTEM_PROMPT, BOT_PERSONALITY, 
                       AI_MODELS, get_current_api_key, DEFAULT_GREETING, 
                       DEFAULT_ERROR_MESSAGE, GROQ_API_KEYS)
from bot.database import (add_or_update_user, add_or_update_group, log_message, 
                         update_daily_stats, is_user_banned, is_group_banned,
                         get_user_mood, update_user_mood, get_stickers_by_mood, 
                         get_random_sticker, increment_sticker_usage, get_taught_fact)
from bot.caching import (get_cached_response, set_cached_response, 
                        get_conversation_history, add_to_conversation_history)
from bot.voice_handler import text_to_voice
from bot.moderation import is_content_appropriate
from bot.helpers import detect_language, translate_text
from bot.sticker_handler import detect_mood_from_text

logger = logging.getLogger(__name__)

# Track API key rotation
CURRENT_KEY_INDEX = 0
CONSECUTIVE_ERRORS = 0
MAX_CONSECUTIVE_ERRORS = 3

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command - entry point for users interacting with the bot"""
    logger.info("Received /start command, processing...")
    try:
        if update.effective_chat is None or update.effective_user is None:
            logger.warning("Missing effective_chat or effective_user in start_command")
            return
        
        user = update.effective_user
        chat = update.effective_chat
        
        logger.info(f"Start command from user: {user.id}, username: {user.username}")
        
        # Check if this is a new user
        is_new_user = False
        
        # Register user in database
        user_added = add_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code
        )
        
        if user_added:
            is_new_user = True
            logger.info(f"New user registered: {user.id}")
        
        # Update stats for new users
        from bot.database import update_daily_stats
        update_daily_stats(users=1 if is_new_user else 0)
    except Exception as e:
        logger.error(f"Error in start_command: {str(e)}", exc_info=True)
    try:
        # Build inline keyboard with commands
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Personalized greeting
        greeting = DEFAULT_GREETING.format(name=user.first_name)
        
        # Create buttons in multiple rows for better organization
        keyboard = [
            # Row 1: Main features
            [
                InlineKeyboardButton("💬 Chat", callback_data="chat"),
                InlineKeyboardButton("🎮 Games", callback_data="games"),
                InlineKeyboardButton("🔊 Voice", callback_data="voice")
            ],
            # Row 2: Utilities
            [
                InlineKeyboardButton("📝 Name Generator", callback_data="name"),
                InlineKeyboardButton("🌟 Bio Generator", callback_data="bio")
            ],
            # Row 3: Support and help
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
                InlineKeyboardButton("👥 Support Group", url="https://t.me/+5e44PSnDdFNlMGM1"),
                InlineKeyboardButton("📢 Channel", url="https://t.me/promotionandsupport")
            ]
        ]
        
        # Additional row for owner commands if the user is the owner
        if user.id == OWNER_ID:
            keyboard.append([
                InlineKeyboardButton("🔄 Broadcast", callback_data="owner_broadcast"),
                InlineKeyboardButton("🚫 Global Ban", callback_data="owner_gban"),
                InlineKeyboardButton("📊 Stats", callback_data="owner_stats"),
                InlineKeyboardButton("📝 Logs", callback_data="owner_logs")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        logger.info("Created inline keyboard for start command")
    except Exception as e:
        logger.error(f"Error creating keyboard: {e}", exc_info=True)
        reply_markup = None
    
    try:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"{greeting}\n\nClick on any button below to get started:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Sent welcome message to user: {user.id}")
        
        # If this is a new user, notify the owner
        if is_new_user and user.id != OWNER_ID:
            from bot.admin_handler import notify_owner_new_user
            await notify_owner_new_user(context.bot, user)
            
        # Additionally, send a welcome sticker
        if is_new_user:
            try:
                # Get a greeting sticker
                stickers = get_random_sticker(category="greeting", limit=1)
                if not stickers:
                    stickers = get_random_sticker(category="love", limit=1)
                
                if stickers and len(stickers) > 0:
                    # Update stats and send sticker
                    from bot.database import update_daily_stats
                    update_daily_stats(stickers_sent=1)
                    
                    await context.bot.send_sticker(
                        chat_id=chat.id,
                        sticker=stickers[0]["file_id"]
                    )
                    logger.info(f"Sent welcome sticker to user: {user.id}")
            except Exception as e:
                logger.error(f"Error sending welcome sticker: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending welcome message: {str(e)}", exc_info=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all incoming messages"""
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    
    # Register user in database
    add_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code
    )
    
    # Check if user is banned
    if is_user_banned(user.id):
        logger.info(f"Ignored message from banned user: {user.id}")
        return
    
    # If it's a group chat, register the group and check if it's banned
    if chat.type in ["group", "supergroup"]:
        add_or_update_group(group_id=chat.id, title=chat.title)
        
        if is_group_banned(chat.id):
            logger.info(f"Ignored message from banned group: {chat.id}")
            return
        
        # For groups, route to specific handler
        await handle_group_message(update, context)
    else:
        # For private chats, route to specific handler
        await handle_private_message(update, context)

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages in private chats"""
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    
    # Check for voice message
    if message.voice:
        # Voice message handling is done in voice_handler.py
        return
    
    # Check for text content
    if not message.text:
        return
    
    # If user is owner and waiting for admin action, handle differently
    if user.id == OWNER_ID and context.user_data.get("awaiting_admin_message"):
        target_id = context.user_data.get("admin_message_target")
        if target_id and message.text != "/cancel":
            try:
                # Send the message to the target user
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"\n\n{message.text}",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Confirm to the owner
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"✅ Message sent to User ID: {target_id}"
                )
                
                # Clear the state
                del context.user_data["awaiting_admin_message"]
                if "admin_message_target" in context.user_data:
                    del context.user_data["admin_message_target"]
                
            except Exception as e:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"❌ Failed to send message: {str(e)}"
                )
            return
        
        elif message.text == "/cancel":
            # Cancel the admin message action
            await context.bot.send_message(
                chat_id=chat.id,
                text="❌ Action cancelled."
            )
            # Clear the state
            del context.user_data["awaiting_admin_message"]
            if "admin_message_target" in context.user_data:
                del context.user_data["admin_message_target"]
            return
    
    # Check content moderation
    from bot.moderation import is_content_appropriate
    if not is_content_appropriate(message.text):
        await context.bot.send_message(
            chat_id=chat.id,
            text="I'm sorry, but I can't respond to that type of content. Let's talk about something else! 😊"
        )
        return
    
    # Check if the text contains "voice me bolo" to enable voice response
    voice_requested = "voice me bolo" in message.text.lower()
    
    # Update stats
    try:
        from bot.database import update_daily_stats
        update_daily_stats(messages=1)
        logger.info(f"Updated message stats for user: {user.id}")
    except Exception as e:
        logger.error(f"Error updating message stats: {str(e)}", exc_info=True)
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=chat.id, 
        action="record_audio" if voice_requested else "typing"
    )
    
    # Generate AI response
    response_text = await generate_ai_response(
        user_id=user.id,
        user_name=user.first_name,
        message_text=message.text,
        chat_history=get_conversation_history(user.id)
    )
    
    # Log the message
    log_message(user.id, None, message.text, response_text)
    
    # Add to conversation history
    add_to_conversation_history(user.id, {"role": "user", "content": message.text})
    add_to_conversation_history(user.id, {"role": "assistant", "content": response_text})
    
    # Detect and update user mood
    from bot.sticker_handler import detect_mood_from_text
    detected_mood = detect_mood_from_text(message.text)
    if detected_mood:
        update_user_mood(user.id, detected_mood)
    
    # Try to get appropriate sticker based on mood
    send_sticker = False
    sticker_file_id = None
    
    # 30% chance of sending a sticker with response
    if random.random() < 0.3:
        try:
            # Get stickers based on mood or random ones
            if detected_mood:
                stickers = get_stickers_by_mood(detected_mood, limit=1)
            else:
                current_mood = get_user_mood(user.id)
                if current_mood:
                    stickers = get_stickers_by_mood(current_mood, limit=1)
                else:
                    stickers = get_random_sticker(limit=1)
                
            if stickers and len(stickers) > 0:
                sticker_file_id = stickers[0]["file_id"]
                increment_sticker_usage(stickers[0]["sticker_id"])
                send_sticker = True
        except Exception as e:
            logger.error(f"Error getting sticker: {str(e)}")
            send_sticker = False
    
    # Send response
    if voice_requested:
        # Convert text to voice and send as voice message
        voice_file = await text_to_voice(response_text)
        if voice_file:
            with open(voice_file, "rb") as audio:
                await context.bot.send_voice(
                    chat_id=chat.id,
                    voice=audio,
                    caption=f"{response_text[:100]}..." if len(response_text) > 100 else response_text
                )
        else:
            # Fall back to text if voice conversion fails
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"{response_text}\n\n(Voice conversion failed, sending as text)",
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        # Send as regular text message
        await context.bot.send_message(
            chat_id=chat.id,
            text=response_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Send a sticker if available
    if send_sticker and sticker_file_id:
        try:
            await context.bot.send_sticker(
                chat_id=chat.id,
                sticker=sticker_file_id
            )
        except Exception as e:
            logger.error(f"Error sending sticker: {str(e)}")
    
    # Log message to owner for monitoring if not the owner
    if user.id != OWNER_ID:
        from bot.admin_handler import log_message_to_owner
        await log_message_to_owner(context.bot, user, message.text, response_text)

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages in group chats"""
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    
    # Handle new members joining the group
    if message.new_chat_members:
        for new_member in message.new_chat_members:
            if new_member.id == context.bot.id:
                # Bot was added to a group
                await group_welcome_message(context.bot, chat)
                
                # Notify owner about the new group
                from bot.admin_handler import notify_owner_new_group
                await notify_owner_new_group(context.bot, chat, user)
                return
        return
    
    # Handle the bot being removed from the group
    if message.left_chat_member and message.left_chat_member.id == context.bot.id:
        logger.info(f"Bot was removed from group {chat.id} by {user.id}")
        return
    
    # Check for owner actions in the group
    if user.id == OWNER_ID and context.user_data.get("awaiting_admin_announce"):
        target_group_id = context.user_data.get("admin_announce_target")
        if target_group_id and message.text != "/cancel":
            try:
                if target_group_id == chat.id:
                    # Send the announcement in this group
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=f"📢 *ANNOUNCEMENT*\n\n{message.text}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    # Send the announcement to a different group
                    await context.bot.send_message(
                        chat_id=target_group_id,
                        text=f"📢 *ANNOUNCEMENT*\n\n{message.text}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # Confirm to the owner
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=f"✅ Announcement sent to Group ID: {target_group_id}"
                    )
                
                # Clear the state
                del context.user_data["awaiting_admin_announce"]
                if "admin_announce_target" in context.user_data:
                    del context.user_data["admin_announce_target"]
                
            except Exception as e:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"❌ Failed to send announcement: {str(e)}"
                )
            return
        
        elif message.text == "/cancel":
            # Cancel the admin announce action
            await context.bot.send_message(
                chat_id=chat.id,
                text="❌ Action cancelled."
            )
            # Clear the state
            del context.user_data["awaiting_admin_announce"]
            if "admin_announce_target" in context.user_data:
                del context.user_data["admin_announce_target"]
            return
    
    # Check for text content
    if not message.text:
        return
    
    # Get bot user
    bot_user = await context.bot.get_me()
    
    # Only respond if the bot is mentioned or replied to
    is_mentioned = False
    is_replied_to = False
    
    # Check if bot is mentioned
    if bot_user.username and f"@{bot_user.username}" in message.text:
        is_mentioned = True
    
    # Check if bot is replied to
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot_user.id:
            is_replied_to = True
    
    # Only process if bot is mentioned or replied to
    if not (is_mentioned or is_replied_to):
        return
    
    # Check if the text contains "voice me bolo" to enable voice response
    voice_requested = "voice me bolo" in message.text.lower()
    
    # Check content moderation
    from bot.moderation import is_content_appropriate
    if not is_content_appropriate(message.text):
        await context.bot.send_message(
            chat_id=chat.id,
            text="I'm sorry, but I can't respond to that type of content. Let's talk about something else! 😊",
            reply_to_message_id=message.message_id
        )
        return
    
    # Update stats
    try:
        from bot.database import update_daily_stats
        update_daily_stats(messages=1)
        logger.info(f"Updated message stats for group: {chat.id}")
    except Exception as e:
        logger.error(f"Error updating message stats: {str(e)}", exc_info=True)
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=chat.id, 
        action="record_audio" if voice_requested else "typing"
    )
    
    # Clean up the message text if bot was mentioned
    cleaned_text = message.text
    if is_mentioned and bot_user.username:
        cleaned_text = cleaned_text.replace(f"@{bot_user.username}", "").strip()
    
    # Generate AI response
    response_text = await generate_ai_response(
        user_id=user.id,
        user_name=user.first_name,
        message_text=cleaned_text,
        chat_history=get_conversation_history(chat.id, limit=5)  # Limited history for groups
    )
    
    # Log the message
    log_message(user.id, chat.id, cleaned_text, response_text)
    
    # Add to group conversation history
    add_to_conversation_history(chat.id, {"role": "user", "name": user.first_name, "content": cleaned_text})
    add_to_conversation_history(chat.id, {"role": "assistant", "content": response_text})
    
    # Detect and update user mood
    from bot.sticker_handler import detect_mood_from_text
    detected_mood = detect_mood_from_text(cleaned_text)
    if detected_mood:
        update_user_mood(user.id, detected_mood)
    
    # Try to get appropriate sticker based on mood
    send_sticker = False
    sticker_file_id = None
    
    # 20% chance of sending a sticker with response in groups (lower than in private to avoid spam)
    if random.random() < 0.2:
        try:
            # Get stickers based on mood or random ones
            if detected_mood:
                stickers = get_stickers_by_mood(detected_mood, limit=1)
            else:
                current_mood = get_user_mood(user.id)
                if current_mood:
                    stickers = get_stickers_by_mood(current_mood, limit=1)
                else:
                    stickers = get_random_sticker(limit=1)
                
            if stickers and len(stickers) > 0:
                sticker_file_id = stickers[0]["file_id"]
                increment_sticker_usage(stickers[0]["sticker_id"])
                send_sticker = True
        except Exception as e:
            logger.error(f"Error getting sticker: {str(e)}")
            send_sticker = False
    
    # Send response
    if voice_requested and chat.type in ("group", "supergroup"):
        # Convert text to voice and send as voice message
        voice_file = await text_to_voice(response_text)
        if voice_file:
            with open(voice_file, "rb") as audio:
                await context.bot.send_voice(
                    chat_id=chat.id,
                    voice=audio,
                    caption=f"{response_text[:100]}..." if len(response_text) > 100 else response_text,
                    reply_to_message_id=message.message_id
                )
        else:
            # Fall back to text if voice conversion fails
            await context.bot.send_message(
                chat_id=chat.id,
                text=response_text,
                reply_to_message_id=message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        # Send as regular text message
        await context.bot.send_message(
            chat_id=chat.id,
            text=response_text,
            reply_to_message_id=message.message_id,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Send a sticker if available
    if send_sticker and sticker_file_id:
        try:
            await context.bot.send_sticker(
                chat_id=chat.id,
                sticker=sticker_file_id,
                reply_to_message_id=message.message_id
            )
        except Exception as e:
            logger.error(f"Error sending sticker: {str(e)}")
    
    # Log message to owner for monitoring if not the owner
    if user.id != OWNER_ID:
        from bot.admin_handler import log_message_to_owner
        await log_message_to_owner(context.bot, user, cleaned_text, response_text, chat)

async def group_welcome_message(bot, chat):
    """Send a welcome message when the bot is added to a group"""
    try:
        welcome_text = f"""
👋 Hello everyone! I'm {BOT_PERSONALITY.get('name', 'Bestie AI')} 💕

Thanks for adding me to this group! I'm here to chat and have fun with everyone. 

Here's what I can do:
• Answer questions and chat with you (just mention me or reply to my messages)
• Generate voice replies (add "voice me bolo" to your message)
• Play fun games (use /game command)
• Provide name and bio suggestions

Send /start to see all my features! 😊

Made with love by @{OWNER_USERNAME}
Join our support group: https://t.me/+5e44PSnDdFNlMGM1
        """
        
        await bot.send_message(
            chat_id=chat.id,
            text=welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Sent welcome message to group {chat.id}")
    except Exception as e:
        logger.error(f"Failed to send welcome message to group {chat.id}: {e}")
    
    # Register the group in the database
    try:
        from bot.database import add_or_update_group, update_daily_stats
        add_or_update_group(group_id=chat.id, title=chat.title)
        update_daily_stats(groups=1)
        logger.info(f"Registered new group: {chat.id}")
    except Exception as e:
        logger.error(f"Error registering group: {str(e)}", exc_info=True)

async def generate_ai_response(user_id: int, user_name: str, message_text: str, 
                              chat_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Generate AI response using Groq API with comprehensive error handling and logging"""
    logger.info(f"Generating AI response for user: {user_id}, message length: {len(message_text)}")
    global CURRENT_KEY_INDEX, CONSECUTIVE_ERRORS
    
    # Check cache first
    cache_key = f"{user_id}:{message_text}"
    cached_response = get_cached_response(cache_key)
    if cached_response:
        logger.info("Using cached response")
        return cached_response
    
    # Prepare system prompt
    name = BOT_PERSONALITY.get("name", "Amelia")
    system_prompt = SYSTEM_PROMPT.format(name=name)
    
    # Import language detection
    from langdetect import detect as langdetect_detect
    
    # Detect language
    try:
        detected_lang = langdetect_detect(message_text)
    except:
        detected_lang = "en"  # Default to English if detection fails
        
    # Check for taught facts from owner
    taught_fact = None
    words = message_text.lower().split()
    for word in words:
        # Strip punctuation for matching
        clean_word = word.strip(",.!?;:")
        if len(clean_word) > 2:  # Skip very short words
            fact = get_taught_fact(clean_word)
            if fact:
                taught_fact = {
                    "keyword": clean_word,
                    "fact": fact
                }
                break
    
    # Build messages for API
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add taught fact as context if found
    if taught_fact:
        messages.append({
            "role": "system",
            "content": f"When asked about '{taught_fact['keyword']}', you must mention: \"My owner told me that {taught_fact['fact']}\". Include this exact phrase in your response."
        })
    
    # Add language context if not English
    if detected_lang and detected_lang != "en":
        lang_name = {"hi": "Hindi", "es": "Spanish", "fr": "French"}.get(detected_lang, detected_lang)
        messages.append({
            "role": "system", 
            "content": f"The user is speaking in {lang_name}. Please respond in the same language."
        })
    
    # Add chat history if available
    if chat_history:
        # Only add the last few messages to not exceed token limits
        for item in chat_history[-6:]:
            messages.append(item)
    
    # Add current message
    messages.append({"role": "user", "content": message_text})
    
    # API parameters
    api_key = get_current_api_key(CURRENT_KEY_INDEX)
    model = AI_MODELS.get("default", "llama3-8b-8192")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": messages,
        "model": model,
        "temperature": 0.7,
        "max_tokens": 512,
        "top_p": 0.9,
        "stop": None
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                ai_response = data["choices"][0]["message"]["content"].strip()
                
                # Cache the response
                set_cached_response(cache_key, ai_response)
                
                # Reset error counter on success
                CONSECUTIVE_ERRORS = 0
                
                # Update stats
                try:
                    from bot.database import update_daily_stats
                    update_daily_stats(ai_calls=1)
                    logger.info(f"Updated AI call stats for user: {user_id}")
                except Exception as e:
                    logger.error(f"Error updating AI call stats: {str(e)}", exc_info=True)
                
                return ai_response
            else:
                logger.error(f"Invalid response format from Groq API: {data}")
                CONSECUTIVE_ERRORS += 1
                return DEFAULT_ERROR_MESSAGE
                
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error calling Groq API: {e}")
        CONSECUTIVE_ERRORS += 1
        
        # Rotate API key if too many consecutive errors
        if CONSECUTIVE_ERRORS >= MAX_CONSECUTIVE_ERRORS:
            CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GROQ_API_KEYS)
            CONSECUTIVE_ERRORS = 0
            logger.info(f"Rotated to API key index {CURRENT_KEY_INDEX} due to consecutive errors")
        
        # Try with backup model if available
        if AI_MODELS.get("backup") and AI_MODELS.get("backup") != model:
            logger.info(f"Attempting with backup model {AI_MODELS.get('backup')}")
            try:
                payload["model"] = AI_MODELS.get("backup")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    backup_response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    
                    backup_response.raise_for_status()
                    backup_data = backup_response.json()
                    
                    if "choices" in backup_data and len(backup_data["choices"]) > 0:
                        backup_ai_response = backup_data["choices"][0]["message"]["content"].strip()
                        set_cached_response(cache_key, backup_ai_response)
                        return backup_ai_response
            except Exception as backup_error:
                logger.error(f"Backup model also failed: {backup_error}")
        
        return "Sorry, I'm having trouble connecting right now. Please try again in a moment! 🙏"

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks from inline keyboards"""
    if update.callback_query is None or update.effective_chat is None or update.effective_user is None:
        return
    
    query = update.callback_query
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Acknowledge the button click to remove loading indicator
    await query.answer()
    
    # Import required components
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Process different callback data
    if callback_data == "chat":
        # Get bot info
        bot_user = await context.bot.get_me()
        bot_username = bot_user.username if bot_user else "the bot"
        
        await query.edit_message_text(
            text=f"💬 *Chat with me!*\n\nJust send any message and I'll respond. I can talk about anything!\n\n"
                 f"In groups, mention me with @{bot_username} or reply to my messages to chat.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "games":
        # Create game selection buttons
        keyboard = [
            [
                InlineKeyboardButton("🎮 Tic-Tac-Toe", callback_data="ttt_new"),
                InlineKeyboardButton("🎲 Truth or Dare", callback_data="tod_choice")
            ],
            [
                InlineKeyboardButton("🔢 Number Guess", callback_data="guess_number_new"),
                InlineKeyboardButton("🔤 Word Guess", callback_data="guess_word_new")
            ],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="🎮 *Fun Games*\n\nChoose a game to play:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "voice":
        # Create voice command instructions
        await query.edit_message_text(
            text="🔊 *Voice Messages*\n\nTo convert text to speech, use:\n\n"
                 "`/voice your text here`\n\n"
                 "I'll convert your text into a voice message. You can also specify the language:\n\n"
                 "`/voice -l hi` for Hindi\n"
                 "`/voice -l es` for Spanish\n\n"
                 "Send `/voice help` for more options.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "stats":
        # Get user statistics
        user_messages = 0
        user_games = 0
        # TODO: Implement actual stats from database
        
        await query.edit_message_text(
            text=f"📊 *Your Stats*\n\n"
                 f"Messages sent: {user_messages}\n"
                 f"Games played: {user_games}\n\n"
                 f"Use /stats for more detailed statistics.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "help":
        # Create help menu with command list
        keyboard = [
            [
                InlineKeyboardButton("💬 Chat Commands", callback_data="help_chat"),
                InlineKeyboardButton("🎮 Game Commands", callback_data="help_games")
            ],
            [
                InlineKeyboardButton("🔊 Voice Commands", callback_data="help_voice"),
                InlineKeyboardButton("⚙️ Utility Commands", callback_data="help_utility")
            ],
            [
                InlineKeyboardButton("👥 Group Commands", callback_data="help_group"),
                InlineKeyboardButton("👑 Owner Commands", callback_data="help_owner")
            ],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="❓ *Help Menu*\n\nSelect a category to view commands:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "name":
        # Show stylish name generator
        await query.edit_message_text(
            text="📝 *Stylish Name Generator*\n\n"
                 "To generate stylish name suggestions, use:\n\n"
                 "`/name your name`\n\n"
                 "Example: `/name John`\n\n"
                 "I'll generate creative and stylish variations of your name.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "bio":
        # Show bio generator
        keyboard = [
            [
                InlineKeyboardButton("😎 Attitude", callback_data="bio_attitude"),
                InlineKeyboardButton("❤️ Love", callback_data="bio_love")
            ],
            [
                InlineKeyboardButton("😂 Funny", callback_data="bio_funny"),
                InlineKeyboardButton("🔥 Motivational", callback_data="bio_motivation")
            ],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="🌟 *Profile Bio Generator*\n\n"
                 "Select a category for your bio:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Owner commands
    elif callback_data.startswith("owner_") and user_id == OWNER_ID:
        if callback_data == "owner_broadcast":
            # Show broadcast instructions
            await query.edit_message_text(
                text="🔄 *Broadcast Message*\n\n"
                     "To send a broadcast message to all users/groups, use:\n\n"
                     "`/broadcast your message`\n\n"
                     "You'll be asked to confirm before sending.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif callback_data == "owner_gban":
            # Show global ban instructions
            await query.edit_message_text(
                text="🚫 *Global Ban*\n\n"
                     "To globally ban a user, use:\n\n"
                     "`/gban user_id reason`\n\n"
                     "To unban a user, use:\n\n"
                     "`/ungban user_id`",
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif callback_data == "owner_stats":
            # Show admin stats
            await query.edit_message_text(
                text="📈 *Admin Statistics*\n\n"
                     "To view detailed admin statistics, use:\n\n"
                     "`/adminstats`\n\n"
                     "This will show user counts, message counts, and more.",
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif callback_data == "owner_logs":
            # Show logging options
            from bot.database import get_setting
            message_logging = get_setting("message_logging", "False") == "True"
            
            keyboard = [
                [InlineKeyboardButton(
                    "🔴 Disable Logging" if message_logging else "🟢 Enable Logging", 
                    callback_data="toggle_logging"
                )],
                [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"📝 *Message Logging*\n\n"
                     f"Current status: {'Enabled' if message_logging else 'Disabled'}\n\n"
                     f"When enabled, all user messages will be forwarded to you.\n"
                     f"Use `/logging` to quickly toggle this feature.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    # Handle toggle logging callback
    elif callback_data == "toggle_logging" and user_id == OWNER_ID:
        from bot.database import get_setting, set_setting
        message_logging = get_setting("message_logging", "False") == "True"
        
        # Toggle the setting
        new_status = not message_logging
        set_setting("message_logging", str(new_status))
        
        # Update button and message
        keyboard = [
            [InlineKeyboardButton(
                "🔴 Disable Logging" if new_status else "🟢 Enable Logging", 
                callback_data="toggle_logging"
            )],
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"📝 *Message Logging*\n\n"
                 f"Status updated: {'Enabled' if new_status else 'Disabled'}\n\n"
                 f"When enabled, all user messages will be forwarded to you.\n"
                 f"Use `/logging` to quickly toggle this feature.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
    # Forward game callbacks to their respective handlers
    elif callback_data.startswith("ttt_"):
        # Forward to the tic-tac-toe game handler
        from bot.games_handler import tictactoe_callback
        await tictactoe_callback(update, context)
        
    elif callback_data.startswith("tod_"):
        # Forward to the truth or dare game handler
        from bot.games_handler import truth_or_dare_callback
        await truth_or_dare_callback(update, context)
        
    elif callback_data.startswith("guess_"):
        # Forward to the guessing game handler
        from bot.games_handler import guess_callback
        await guess_callback(update, context)
    
    # Go back to main menu
    elif callback_data == "main_menu":
        # Build main menu again
        keyboard = [
            # Row 1: Main features
            [
                InlineKeyboardButton("💬 Chat", callback_data="chat"),
                InlineKeyboardButton("🎮 Games", callback_data="games"),
                InlineKeyboardButton("🔊 Voice", callback_data="voice")
            ],
            # Row 2: Utilities
            [
                InlineKeyboardButton("📊 Stats", callback_data="stats"),
                InlineKeyboardButton("📝 Name Generator", callback_data="name"),
                InlineKeyboardButton("🌟 Bio Generator", callback_data="bio")
            ],
            # Row 3: Support and help
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
                InlineKeyboardButton("👥 Support Group", url="https://t.me/+5e44PSnDdFNlMGM1"),
                InlineKeyboardButton("📢 Channel", url="https://t.me/promotionandsupport")
            ]
        ]
        
        # Additional row for owner commands if the user is the owner
        if user_id == OWNER_ID:
            keyboard.append([
                InlineKeyboardButton("🔄 Broadcast", callback_data="owner_broadcast"),
                InlineKeyboardButton("🚫 Global Ban", callback_data="owner_gban"),
                InlineKeyboardButton("📈 Admin Stats", callback_data="owner_stats"),
                InlineKeyboardButton("📝 Logs", callback_data="owner_logs")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="Welcome to the main menu! Click on any button to get started:",
            reply_markup=reply_markup
        )
    
    # Help subcategories
    elif callback_data.startswith("help_"):
        help_category = callback_data.replace("help_", "")
        
        # Define help text based on category
        help_text = ""
        if help_category == "chat":
            help_text = "💬 *Chat Commands*\n\n" \
                        "/start - Start the bot and show main menu\n" \
                        "Just type a message to chat with me directly\n" \
                        "In groups, mention me with @username or reply to my messages"
        elif help_category == "games":
            help_text = "🎮 *Game Commands*\n\n" \
                        "/game - Show the games menu\n" \
                        "/tictactoe - Start a Tic-Tac-Toe game\n" \
                        "/truthdare - Play Truth or Dare\n" \
                        "/guess - Start a guessing game"
        elif help_category == "voice":
            help_text = "🔊 *Voice Commands*\n\n" \
                        "/voice [text] - Convert text to voice\n" \
                        "/voice -l [lang] [text] - Voice in specific language\n" \
                        "/voice help - Show voice command help"
        elif help_category == "utility":
            help_text = "⚙️ *Utility Commands*\n\n" \
                        "/stats - Show your statistics\n" \
                        "/name [your name] - Generate stylish names\n" \
                        "/bio - Generate profile bio suggestions\n" \
                        "/help - Show this help menu"
        elif help_category == "group":
            help_text = "👥 *Group Commands*\n\n" \
                        "/ban - Ban a user from the group\n" \
                        "/unban - Unban a user\n" \
                        "/mute - Mute a user\n" \
                        "/unmute - Unmute a user\n" \
                        "/kick - Kick a user from the group\n" \
                        "/masstag - Tag all users in the group"
        elif help_category == "owner":
            help_text = "👑 *Owner Commands*\n\n" \
                        "/broadcast - Send message to all users/groups\n" \
                        "/gban - Globally ban a user\n" \
                        "/ungban - Globally unban a user\n" \
                        "/adminstats - Show detailed statistics\n" \
                        "/logging - Toggle message logging"
        
        # Add back button
        keyboard = [[InlineKeyboardButton("⬅️ Back to Help Menu", callback_data="help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_ai_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Error handler for the AI responses"""
    try:
        # Log detailed error information
        logger.error(f"Bot error: {context.error}", exc_info=context.error)
        
        # Get more information about the update that caused the error
        update_info = ""
        if update:
            if update.effective_chat:
                update_info += f"Chat ID: {update.effective_chat.id}, Type: {update.effective_chat.type}\n"
            if update.effective_user:
                update_info += f"User: {update.effective_user.id} (@{update.effective_user.username})\n"
            if update.effective_message:
                update_info += f"Message: {update.effective_message.text}\n"
                
        logger.error(f"Error context: {update_info}")
        
        # Try to notify the user about the error
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, something went wrong. Please try again later!"
            )
            logger.info(f"Sent error notification to chat: {update.effective_chat.id}")
    except Exception as e:
        logger.error(f"Error in error handler: {e}", exc_info=True)
