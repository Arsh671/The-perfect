#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Voice message handling for the Telegram Bot
"""

import logging
import os
import tempfile
from typing import Optional

from gtts import gTTS
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import FEATURES
from bot.database import update_daily_stats
from bot.caching import get_conversation_history
from bot.helpers import detect_language

logger = logging.getLogger(__name__)

async def text_to_voice(text: str, language: str = None) -> Optional[str]:
    """Convert text to voice using gTTS - using a sweet girl voice"""
    if not FEATURES.get("voice_messages", True):
        logger.info("Voice messages feature is disabled")
        return None
    
    try:
        # Detect language if not provided
        if language is None:
            language = detect_language(text) or 'en'
        
        # Limit text length to avoid errors
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        # Create temporary file for voice message
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Use female voice for a sweet girl voice effect
        # Note: gTTS doesn't have explicit gender options, but we're using the
        # standard voice which is typically feminine for most languages
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(temp_path)
        
        logger.info(f"Generated voice message in {language} language")
        return temp_path
    except Exception as e:
        logger.error(f"Error generating voice message: {e}")
        return None

async def send_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /voice command - convert text to voice message"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if there's text after the command
    text_to_convert = ""
    if context.args and len(context.args) > 0:
        text_to_convert = " ".join(context.args)
    else:
        # Get the last assistant message from history
        history = get_conversation_history(user.id)
        if history:
            for msg in reversed(history):
                if msg.get("role") == "assistant":
                    text_to_convert = msg.get("content", "")
                    break
    
    if not text_to_convert:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide some text after the /voice command, or I'll convert my last message."
        )
        return
    
    # Show recording action
    await context.bot.send_chat_action(chat_id=chat.id, action="record_voice")
    
    # Detect language
    language = detect_language(text_to_convert) or 'en'
    
    # Convert to voice
    voice_file = await text_to_voice(text_to_convert, language)
    
    if voice_file:
        try:
            # Update stats
            try:
                from bot.database import update_daily_stats
                update_daily_stats(voice_messages=1)
                logger.info(f"Updated voice message stats for user: {chat.id}")
            except Exception as e:
                logger.error(f"Error updating voice message stats: {str(e)}", exc_info=True)
            
            # Send voice message
            with open(voice_file, 'rb') as audio:
                await context.bot.send_voice(
                    chat_id=chat.id,
                    voice=audio,
                    caption="Here's your voice message!"
                )
        finally:
            # Clean up temp file
            try:
                os.unlink(voice_file)
            except (OSError, FileNotFoundError):
                pass
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Sorry, I couldn't generate a voice message. Please try again later."
        )

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages"""
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    # Currently we don't have voice-to-text capability
    # Just respond with a fixed message about it, but make it sound flirty/sweet
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat.id, action="typing")
    
    # Get a personality-appropriate response
    from bot.config import BOT_PERSONALITY, OWNER_ID
    
    responses = [
        "I love hearing your voice, sweetheart! 💕 But I can't quite understand it yet. Could you type it for me?",
        "Your voice sounds so nice! But I'm still learning to understand voice messages. Can you text me instead? 💋",
        "Ooh, a voice note! I wish I could understand it, but I'm still learning. Text me? Pretty please? 😘",
        "I bet your voice sounds amazing, but I can't quite understand voice messages yet. Can you type it out for me, cutie? 💖",
        "I'd love to hear what you're saying, but I'm still learning to understand voice messages. Mind typing it for me? 💕",
        "Voice messages are like sweet whispers I can't quite catch yet. Could you send it as text? 🎧💋"
    ]
    
    import random
    response_text = random.choice(responses)
    
    # Send response with a voice option
    voice_requested = True  # Always try to respond with voice to a voice message
    
    if voice_requested:
        # Show recording action
        await context.bot.send_chat_action(chat_id=chat.id, action="record_voice")
        
        # Convert to voice
        voice_file = await text_to_voice(response_text)
        
        if voice_file:
            try:
                # Update stats
                try:
                    from bot.database import update_daily_stats
                    update_daily_stats(voice_messages=1)
                    logger.info(f"Updated voice message stats for user: {chat.id}")
                except Exception as e:
                    logger.error(f"Error updating voice message stats: {str(e)}", exc_info=True)
                
                # Send voice message
                with open(voice_file, 'rb') as audio:
                    await context.bot.send_voice(
                        chat_id=chat.id,
                        voice=audio,
                        caption=response_text,
                        reply_to_message_id=message.message_id
                    )
            finally:
                # Clean up temp file
                try:
                    os.unlink(voice_file)
                except (OSError, FileNotFoundError):
                    pass
            
            # Log to owner
            if user.id != OWNER_ID:
                try:
                    from bot.admin_handler import log_message_to_owner
                    await log_message_to_owner(
                        context.bot, 
                        user, 
                        "[Voice Message]", 
                        response_text,
                        chat
                    )
                except Exception as e:
                    logger.error(f"Failed to log voice message to owner: {e}")
                    
            return
    
    # Fallback to text if voice fails
    await context.bot.send_message(
        chat_id=chat.id,
        text=response_text,
        reply_to_message_id=message.message_id
    )
