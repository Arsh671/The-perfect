import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from bot.modules.ai_service import get_ai_response
from bot.modules.voice_service import text_to_speech
from bot.modules.content_filter import is_content_appropriate
from bot.config import ENABLE_VOICE, OWNER_ID
from bot.utils.helpers import is_bot_mentioned, extract_text_from_message
from langdetect import detect

logger = logging.getLogger(__name__)

def register_conversation_handlers(application: Application):
    """Register all conversation-related handlers."""
    # Start command
    application.add_handler(CommandHandler("start", start_command))
    
    # Help command
    application.add_handler(CommandHandler("help", help_command))
    
    # Voice toggle command
    application.add_handler(CommandHandler("voice", toggle_voice))
    
    # Regular conversation handlers
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, 
        handle_private_message
    ))
    
    # Group message handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, 
        handle_group_message
    ))
    
    # Voice message in private
    application.add_handler(MessageHandler(
        filters.VOICE & filters.ChatType.PRIVATE,
        handle_voice_message
    ))
    
    # Callback for conversation buttons
    application.add_handler(CallbackQueryHandler(handle_conversation_callback, pattern="^conv_"))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user = update.effective_user
    
    welcome_message = (
        f"👋 Hello {user.first_name}! I'm Mia, your friendly AI assistant.\n\n"
        f"I'm here to chat, help with your group, and have fun! Feel free to talk to me about anything.\n\n"
        f"Use /help to see what I can do for you!"
    )
    
    # Create keyboard with helpful buttons
    keyboard = [
        [
            InlineKeyboardButton("💬 Chat with me", callback_data="conv_chat"),
            InlineKeyboardButton("🎮 Play games", callback_data="conv_games")
        ],
        [
            InlineKeyboardButton("📱 Fancy name", callback_data="conv_fancy_name"),
            InlineKeyboardButton("🔖 Bio generator", callback_data="conv_bio")
        ],
        [
            InlineKeyboardButton("👥 Support Group", url="https://t.me/+5e44PSnDdFNlMGM1"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/promotionandsupport")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    help_text = (
        "🤖 *Mia Bot Help* 🤖\n\n"
        "*Chat Commands*\n"
        "Just chat with me in private! In groups, tag me or reply to my messages.\n"
        "/voice - Toggle voice messages on/off\n\n"
        
        "*Utility Commands*\n"
        "/fancy_name - Generate a stylish name with fonts and emojis\n"
        "/bio [mood] - Generate a bio (moods: sad, happy, attitude)\n"
        "/links - Get community links\n\n"
        
        "*Game Commands*\n"
        "/tictactoe - Play Tic Tac Toe\n"
        "/truth - Get a truth question\n"
        "/dare - Get a dare challenge\n"
        "/guess - Play guess the number\n\n"
        
        "*Group Admin Commands*\n"
        "/ban - Ban a user\n"
        "/unban - Unban a user\n"
        "/mute - Mute a user\n"
        "/unmute - Unmute a user\n"
        "/kick - Kick a user\n"
        "/tag - Tag all members with a message\n\n"
        
        "Feel free to ask me if you need help with anything specific!"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def toggle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle voice messages on/off."""
    if not ENABLE_VOICE:
        await update.message.reply_text("Voice messages are disabled globally by the bot owner.")
        return
    
    user_id = update.effective_user.id
    current_setting = context.user_data.get("voice_enabled", True)
    context.user_data["voice_enabled"] = not current_setting
    
    if context.user_data["voice_enabled"]:
        await update.message.reply_text("🔊 Voice messages enabled! I'll send both text and voice responses.")
    else:
        await update.message.reply_text("🔇 Voice messages disabled! I'll only send text responses.")

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle private messages sent to the bot."""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Check content appropriateness
    if not await is_content_appropriate(message_text):
        await update.message.reply_text(
            "I'm sorry, but I can't respond to messages containing inappropriate content. "
            "Please keep our conversation respectful. 😊"
        )
        return
    
    # Get AI response
    try:
        # Try to detect language
        try:
            language = detect(message_text)
        except:
            language = "en"
        
        # Get user's conversation history
        if user_id not in context.user_data.get("ai_history", {}):
            context.user_data.setdefault("ai_history", {})[user_id] = []
        
        history = context.user_data["ai_history"][user_id]
        
        # Add user message to history
        history.append({"role": "user", "content": message_text})
        
        # Limit history to last 10 messages to prevent token overload
        if len(history) > 10:
            history = history[-10:]
        
        # Get AI response
        ai_response = await get_ai_response(message_text, history, language)
        
        # Add AI response to history
        history.append({"role": "assistant", "content": ai_response})
        context.user_data["ai_history"][user_id] = history
        
        # Send text response
        await update.message.reply_text(ai_response)
        
        # Send voice response if enabled
        if ENABLE_VOICE and context.user_data.get("voice_enabled", True):
            voice_file = await text_to_speech(ai_response, language)
            if voice_file:
                await update.message.reply_voice(voice=voice_file)
                # Clean up the temporary file
                import os
                os.remove(voice_file.name)
    
    except Exception as e:
        logger.error(f"Error in AI conversation: {str(e)}")
        await update.message.reply_text(
            "Sorry, I'm having trouble processing your message right now. Please try again in a moment."
        )

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in group chats."""
    # Check if the bot is mentioned or replied to
    if not is_bot_mentioned(update, context):
        return
    
    # Extract the actual message text (removing the mention)
    message_text = extract_text_from_message(update, context)
    
    # If no text after removing mention, return
    if not message_text:
        return
    
    # Check content appropriateness
    if not await is_content_appropriate(message_text):
        await update.message.reply_text(
            "I'm sorry, but I can't respond to messages containing inappropriate content. "
            "Please keep our conversation respectful. 😊"
        )
        return
    
    # Process the message similarly to private messages
    try:
        # Try to detect language
        try:
            language = detect(message_text)
        except:
            language = "en"
        
        # In groups, we don't maintain conversation history to avoid confusion
        ai_response = await get_ai_response(message_text, [], language)
        
        # Send text response
        await update.message.reply_text(ai_response)
        
    except Exception as e:
        logger.error(f"Error in group conversation: {str(e)}")
        await update.message.reply_text(
            "Sorry, I'm having trouble processing your message right now. Please try again in a moment."
        )

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages sent to the bot."""
    # This would require speech-to-text which isn't in the requirements
    # So we'll just respond with a message
    await update.message.reply_text(
        "I can hear that you sent me a voice message, but I can't transcribe it yet. "
        "Please type your message instead so I can understand you better! 😊"
    )

async def handle_conversation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from conversation inline buttons."""
    query = update.callback_query
    await query.answer()
    
    # Extract the specific callback data
    action = query.data.replace("conv_", "")
    
    if action == "chat":
        await query.message.reply_text(
            "I'd love to chat with you! What's on your mind? You can talk to me about anything. "
            "I'm your friendly AI assistant, here to help and keep you company. 😊"
        )
    
    elif action == "games":
        games_message = (
            "🎮 *Available Games* 🎮\n\n"
            "• /tictactoe - Play Tic Tac Toe against me\n"
            "• /truth - Get a truth question\n"
            "• /dare - Get a dare challenge\n"
            "• /guess - Play guess the number game\n\n"
            "Which one would you like to play?"
        )
        await query.message.reply_text(games_message, parse_mode="Markdown")
    
    elif action == "fancy_name":
        await query.message.reply_text(
            "Let me create a fancy stylish name for you! What's your name? "
            "Use /fancy_name [your name] to get started."
        )
    
    elif action == "bio":
        bio_message = (
            "I can generate a creative bio for your profile! Choose a mood:\n\n"
            "• /bio sad - For a sad, emotional bio\n"
            "• /bio happy - For a cheerful, positive bio\n"
            "• /bio attitude - For a fierce, attitude-filled bio\n"
            "• /bio romantic - For a romantic, loving bio\n\n"
            "Or just use /bio for a random style!"
        )
        await query.message.reply_text(bio_message)
