import logging
import re
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from telegram.constants import ParseMode
from bot.config import SUPPORT_GROUP, SUPPORT_CHANNEL, OWNER_USERNAME
from bot.utils.fancy_text import generate_fancy_text
from bot.modules.ai_service import get_ai_response

logger = logging.getLogger(__name__)

def register_utility_handlers(application: Application):
    """Register all utility handlers."""
    # Fancy name generator
    application.add_handler(CommandHandler("fancy_name", fancy_name))
    
    # Bio generator
    application.add_handler(CommandHandler("bio", generate_bio))
    
    # Community links
    application.add_handler(CommandHandler("links", community_links))
    
    # Callback handler for utility features
    application.add_handler(CallbackQueryHandler(handle_utility_callback, pattern="^util_"))

async def fancy_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a fancy name with stylish fonts and emojis."""
    # Check if user provided a name
    if not context.args:
        await update.message.reply_text(
            "Please provide a name to make fancy!\nExample: /fancy_name John"
        )
        return
    
    # Get the name from arguments
    name = " ".join(context.args)
    
    # Generate fancy versions of the name
    fancy_names = generate_fancy_text(name)
    
    # Create message with all fancy names
    message = "🌟 *Fancy Name Generator* 🌟\n\n"
    for i, fancy_name in enumerate(fancy_names, 1):
        message += f"{i}. `{fancy_name}`\n\n"
    
    message += "Copy your favorite style! ✨"
    
    # Create buttons for additional options
    keyboard = [
        [
            InlineKeyboardButton("🔄 Generate More", callback_data=f"util_more_fancy_{name}"),
            InlineKeyboardButton("➕ Add Emojis", callback_data=f"util_emoji_fancy_{name}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def generate_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a bio based on the specified mood."""
    # Default mood is random
    mood = "random"
    
    # Check if user provided a mood
    if context.args:
        mood = context.args[0].lower()
    
    valid_moods = ["sad", "happy", "attitude", "romantic", "random"]
    
    if mood not in valid_moods:
        await update.message.reply_text(
            "Please specify a valid mood: sad, happy, attitude, romantic, or random."
        )
        return
    
    # If mood is random, pick one
    if mood == "random":
        mood = random.choice(["sad", "happy", "attitude", "romantic"])
    
    # Create prompt for AI
    prompt = f"Generate a short Instagram/social media bio (max 150 characters) with a {mood} mood. Make it creative and include some emojis. Don't use hashtags."
    
    try:
        # Get AI-generated bio
        bio = await get_ai_response(prompt, [], "en")
        
        # Create message with the bio
        message = f"✨ *{mood.capitalize()} Bio* ✨\n\n"
        message += f"`{bio}`\n\n"
        message += "Copy and use wherever you want! 📝"
        
        # Create buttons for additional options
        keyboard = [
            [
                InlineKeyboardButton("🔄 Generate Another", callback_data=f"util_bio_{mood}"),
                InlineKeyboardButton("🔀 Different Mood", callback_data="util_bio_mood")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    except Exception as e:
        logger.error(f"Error generating bio: {str(e)}")
        await update.message.reply_text(
            "Sorry, I'm having trouble generating a bio right now. Please try again later."
        )

async def community_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provide links to community resources."""
    message = (
        "🔗 *Community Links* 🔗\n\n"
        f"👤 *Owner:* @{OWNER_USERNAME}\n"
        f"👥 *Support Group:* [Join Here]({SUPPORT_GROUP})\n"
        f"📢 *Channel:* [Subscribe Here]({SUPPORT_CHANNEL})\n\n"
        "Feel free to reach out if you have any questions or need help! 😊"
    )
    
    # Create buttons for direct access
    keyboard = [
        [
            InlineKeyboardButton("👤 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}"),
            InlineKeyboardButton("👥 Support Group", url=SUPPORT_GROUP)
        ],
        [
            InlineKeyboardButton("📢 Channel", url=SUPPORT_CHANNEL)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def handle_utility_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for utility features."""
    query = update.callback_query
    await query.answer()
    
    # Extract callback data
    callback_data = query.data.replace("util_", "")
    
    if callback_data.startswith("more_fancy_"):
        # Extract the name from callback data
        name = callback_data.replace("more_fancy_", "")
        
        # Generate new fancy names
        fancy_names = generate_fancy_text(name)
        
        # Create message with all fancy names
        message = "🌟 *More Fancy Names* 🌟\n\n"
        for i, fancy_name in enumerate(fancy_names, 1):
            message += f"{i}. `{fancy_name}`\n\n"
        
        message += "Copy your favorite style! ✨"
        
        # Create buttons for additional options
        keyboard = [
            [
                InlineKeyboardButton("🔄 Generate More", callback_data=f"util_more_fancy_{name}"),
                InlineKeyboardButton("➕ Add Emojis", callback_data=f"util_emoji_fancy_{name}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    elif callback_data.startswith("emoji_fancy_"):
        # Extract the name from callback data
        name = callback_data.replace("emoji_fancy_", "")
        
        # Generate fancy names with emojis
        fancy_names = generate_fancy_text(name, add_emojis=True)
        
        # Create message with all fancy names
        message = "✨ *Fancy Names with Emojis* ✨\n\n"
        for i, fancy_name in enumerate(fancy_names, 1):
            message += f"{i}. `{fancy_name}`\n\n"
        
        message += "Copy your favorite style! 🌟"
        
        # Create buttons for additional options
        keyboard = [
            [
                InlineKeyboardButton("🔄 Generate More", callback_data=f"util_more_fancy_{name}"),
                InlineKeyboardButton("🚫 Remove Emojis", callback_data=f"util_fancy_name_{name}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    elif callback_data.startswith("bio_"):
        # Check if it's a mood selection or generation
        if callback_data == "bio_mood":
            # Show mood selection buttons
            keyboard = [
                [
                    InlineKeyboardButton("😔 Sad", callback_data="util_bio_sad"),
                    InlineKeyboardButton("😊 Happy", callback_data="util_bio_happy"),
                ],
                [
                    InlineKeyboardButton("😎 Attitude", callback_data="util_bio_attitude"),
                    InlineKeyboardButton("❤️ Romantic", callback_data="util_bio_romantic")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Choose a mood for your bio:",
                reply_markup=reply_markup
            )
        else:
            # Extract the mood from callback data
            mood = callback_data.replace("bio_", "")
            
            # Create prompt for AI
            prompt = f"Generate a short Instagram/social media bio (max 150 characters) with a {mood} mood. Make it creative and include some emojis. Don't use hashtags."
            
            try:
                # Get AI-generated bio
                bio = await get_ai_response(prompt, [], "en")
                
                # Create message with the bio
                message = f"✨ *{mood.capitalize()} Bio* ✨\n\n"
                message += f"`{bio}`\n\n"
                message += "Copy and use wherever you want! 📝"
                
                # Create buttons for additional options
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Generate Another", callback_data=f"util_bio_{mood}"),
                        InlineKeyboardButton("🔀 Different Mood", callback_data="util_bio_mood")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            
            except Exception as e:
                logger.error(f"Error generating bio from callback: {str(e)}")
                await query.edit_message_text(
                    "Sorry, I'm having trouble generating a bio right now. Please try again later."
                )
