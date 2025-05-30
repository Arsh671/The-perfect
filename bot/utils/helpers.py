import logging
from telegram import Update, User, Message
from telegram.ext import ContextTypes
import asyncio

logger = logging.getLogger(__name__)

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the chat."""
    if not update.effective_chat:
        return False
    
    if update.effective_chat.type == "private":
        return True
    
    user_id = update.effective_user.id
    
    try:
        chat_member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return chat_member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        return False

def get_mention(user: User) -> str:
    """Get a markdown mention for a user."""
    if user.username:
        return f"@{user.username}"
    else:
        return f"[{user.first_name}](tg://user?id={user.id})"

def is_bot_mentioned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the bot is mentioned or replied to in the message."""
    message = update.effective_message
    
    if not message:
        return False
    
    # Check if message is a reply to the bot
    if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
        return True
    
    # Check if bot is mentioned
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention = message.text[entity.offset:entity.offset + entity.length]
                if mention == f"@{context.bot.username}":
                    return True
            elif entity.type == "text_mention" and entity.user and entity.user.id == context.bot.id:
                return True
    
    return False

def extract_text_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Extract the actual message text, removing the bot mention if present."""
    message = update.effective_message
    
    if not message or not message.text:
        return ""
    
    # If it's a reply to the bot, return the full message
    if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
        return message.text
    
    # If the bot is mentioned, remove the mention
    text = message.text
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention = text[entity.offset:entity.offset + entity.length]
                if mention == f"@{context.bot.username}":
                    # Remove the mention and any leading/trailing whitespace
                    text = text[:entity.offset] + text[entity.offset + entity.length:]
                    break
    
    return text.strip()

async def send_typing_action(chat_id, context: ContextTypes.DEFAULT_TYPE, duration=1.0):
    """Send a typing action to the chat for the specified duration."""
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(duration)
    except Exception as e:
        logger.error(f"Error sending typing action: {str(e)}")

def split_message(text, max_length=4096):
    """Split a message into multiple parts if it exceeds the maximum length."""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    for i in range(0, len(text), max_length):
        parts.append(text[i:i + max_length])
    
    return parts

async def handle_db_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update user and group info in the database."""
    from bot.modules.db import add_or_update_user, add_or_update_group, log_message
    from bot.config import MESSAGE_LOGGING_ENABLED
    
    try:
        # Update user information
        user = update.effective_user
        if user:
            await add_or_update_user(
                user.id,
                user.username or "",
                user.first_name or "",
                user.last_name or ""
            )
        
        # Update group information if message is from a group
        chat = update.effective_chat
        if chat and chat.type in ["group", "supergroup"]:
            await add_or_update_group(
                chat.id,
                chat.title or "Unknown Group"
            )
        
        # Log message if enabled
        if MESSAGE_LOGGING_ENABLED and user and update.message and update.message.text:
            await log_message(
                user.id,
                chat.id if chat else user.id,
                update.message.text
            )
    
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
