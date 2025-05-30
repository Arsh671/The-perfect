import logging
import json
import asyncio
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode

from config import Config
from models.user import User
from models.conversation import Conversation
from utils.api_key_manager import APIKeyManager
from utils.text_generator import generate_ai_response, check_if_bot_mentioned
from utils.content_moderation import check_message_content
from utils.voice_generator import generate_voice_message
from utils.cache_manager import get_cache, set_cache

logger = logging.getLogger(__name__)

# Store conversation contexts
conversation_contexts = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and generate AI responses"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_text = update.message.text
    
    # Check if it's a private chat or if the bot was mentioned/replied to in a group
    is_private = update.effective_chat.type == "private"
    is_mentioned = is_private or check_if_bot_mentioned(update, context)
    
    if not is_mentioned:
        return
    
    # Check for content moderation
    if Config.CONTENT_MODERATION_ENABLED:
        is_appropriate = await check_message_content(message_text)
        if not is_appropriate:
            await update.message.reply_text(
                "I'm sorry, but I can't respond to messages with inappropriate content. "
                "Please keep our conversation respectful. 💕"
            )
            return
    
    # Update user's last active timestamp
    User.update_last_active(user_id)
    
    # Get or create conversation context
    if chat_id not in conversation_contexts:
        conversation_contexts[chat_id] = []
    
    # Add user message to context
    conversation_contexts[chat_id].append({
        "role": "user",
        "content": message_text
    })
    
    # Trim context if it gets too long
    if len(conversation_contexts[chat_id]) > Config.MAX_CONTEXT_LENGTH * 2:
        conversation_contexts[chat_id] = conversation_contexts[chat_id][-Config.MAX_CONTEXT_LENGTH*2:]
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # Try to get response from cache
    cache_key = f"response_{user_id}_{message_text}"
    cached_response = get_cache(cache_key)
    
    if cached_response:
        response_text = cached_response
    else:
        # Generate AI response
        response_text = await generate_ai_response(
            conversation_contexts[chat_id],
            user_id=user_id,
            username=update.effective_user.username or "",
            first_name=update.effective_user.first_name
        )
        
        # Cache the response
        set_cache(cache_key, response_text)
    
    # Add AI response to context
    conversation_contexts[chat_id].append({
        "role": "assistant",
        "content": response_text
    })
    
    # Store conversation in database
    Conversation.store(
        user_id=user_id,
        message=message_text,
        response=response_text
    )
    
    # Update user chat count
    User.increment_chat_count(user_id)
    
    # Create keyboard with voice option
    
    keyboard = [
        [
            InlineKeyboardButton("💬 Chat", callback_data="chat"),
            InlineKeyboardButton("🎮 Games", callback_data="games"),
            InlineKeyboardButton("🎤 Voice", callback_data="voice")
        ],
        [
            InlineKeyboardButton("📝 Name Generator", callback_data="name_gen"),
            InlineKeyboardButton("🌟 Bio Generator", callback_data="bio_gen"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ],
        [
            InlineKeyboardButton("👥 Support Gr", url="https://t.me/YourSupportGroup"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/YourChannel"),
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ],
        [
            InlineKeyboardButton("📤 Broadc", callback_data="broadcast"),
            InlineKeyboardButton("🚫 Global", callback_data="global"),
            InlineKeyboardButton("📝 Logs", callback_data="logs")
        ]
    ]
)-1}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send response
    await update.message.reply_text(
        f"{response_text}\n\n{Config.BOT_SIGNATURE}",
        reply_markup=reply_markup
    )

async def voice_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice button callback"""
    query = update.callback_query
    await query.answer()
    
    # Extract message index from callback data
    data = query.data.split("_")[1]
    chat_id = update.effective_chat.id
    
    try:
        msg_index = int(data)
        if chat_id in conversation_contexts and msg_index < len(conversation_contexts[chat_id]):
            message_text = conversation_contexts[chat_id][msg_index]['content']
            
            # Send processing message
            processing_msg = await context.bot.send_message(
                chat_id=chat_id, 
                text="Generating voice message... 🎙️"
            )
            
            # Generate and send voice message
            await context.bot.send_chat_action(chat_id=chat_id, action="record_voice")
            voice_file = await generate_voice_message(message_text)
            
            with open(voice_file, 'rb') as audio:
                await context.bot.send_voice(
                    chat_id=chat_id,
                    voice=audio,
                    caption=f"Voice message from {Config.BOT_SIGNATURE}"
                )
            
            # Delete the processing message
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=processing_msg.message_id
            )
            
            # Remove the voice file after sending
            import os
            os.remove(voice_file)
    except Exception as e:
        logger.error(f"Error generating voice message: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, I couldn't generate a voice message at the moment. Please try again later. 🙁"
        )

def register_conversation_handlers(application):
    """Register all conversation-related handlers"""
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(voice_button_callback, pattern=r'^voice_'))
