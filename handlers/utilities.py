import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

from config import Config
from templates.fancy_fonts import generate_fancy_text, FANCY_FONTS
from utils.text_generator import generate_bio

logger = logging.getLogger(__name__)

async def fancy_name_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate fancy stylish names with fonts and emojis"""
    # Get the name to stylize
    name = " ".join(context.args) if context.args else update.effective_user.first_name
    
    # Generate multiple fancy variations
    fancy_variations = []
    
    # Use different fonts
    for i, font_name in enumerate(random.sample(list(FANCY_FONTS.keys()), min(5, len(FANCY_FONTS)))):
        fancy_name = generate_fancy_text(name, font_name)
        
        # Add random emojis
        emojis = ["✨", "💖", "💫", "💎", "👑", "🌟", "🔥", "💯", "🌈", "⚡", "🦋", "🌺", "🍒", "🌹", "🌻"]
        random_emojis = random.sample(emojis, min(3, len(emojis)))
        
        # Format with emojis
        formatted_name = f"{random_emojis[0]} {fancy_name} {random_emojis[1]}"
        
        fancy_variations.append(formatted_name)
    
    # Create keyboard for refreshing
    keyboard = [
        [InlineKeyboardButton("♻️ Refresh", callback_data=f"refresh_fancy_{name}")],
        [InlineKeyboardButton("👤 Generate Bio", callback_data="generate_bio")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the variations
    await update.message.reply_text(
        "✨ *Fancy Name Styles* ✨\n\n" + "\n\n".join(fancy_variations) + "\n\n" +
        "_Click Refresh for more styles or Generate Bio to create a matching bio!_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def fancy_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fancy name refresh button callback"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action.startswith("refresh_fancy_"):
        # Extract the name from callback data
        name = action.replace("refresh_fancy_", "")
        
        # Generate new fancy variations
        fancy_variations = []
        
        # Use different fonts
        for i, font_name in enumerate(random.sample(list(FANCY_FONTS.keys()), min(5, len(FANCY_FONTS)))):
            fancy_name = generate_fancy_text(name, font_name)
            
            # Add random emojis
            emojis = ["✨", "💖", "💫", "💎", "👑", "🌟", "🔥", "💯", "🌈", "⚡", "🦋", "🌺", "🍒", "🌹", "🌻"]
            random_emojis = random.sample(emojis, min(3, len(emojis)))
            
            # Format with emojis
            formatted_name = f"{random_emojis[0]} {fancy_name} {random_emojis[1]}"
            
            fancy_variations.append(formatted_name)
        
        # Create keyboard for refreshing
        keyboard = [
            [InlineKeyboardButton("♻️ Refresh", callback_data=f"refresh_fancy_{name}")],
            [InlineKeyboardButton("👤 Generate Bio", callback_data="generate_bio")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit the message with new variations
        await query.edit_message_text(
            "✨ *Fancy Name Styles* ✨\n\n" + "\n\n".join(fancy_variations) + "\n\n" +
            "_Click Refresh for more styles or Generate Bio to create a matching bio!_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    elif action == "generate_bio":
        # Show bio options
        keyboard = [
            [
                InlineKeyboardButton("😊 Happy", callback_data="bio_happy"),
                InlineKeyboardButton("😔 Sad", callback_data="bio_sad")
            ],
            [
                InlineKeyboardButton("😎 Attitude", callback_data="bio_attitude"),
                InlineKeyboardButton("💔 Broken", callback_data="bio_broken")
            ],
            [
                InlineKeyboardButton("💕 Love", callback_data="bio_love"),
                InlineKeyboardButton("🔮 Mystical", callback_data="bio_mystical")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🌟 *Select a Bio Mood* 🌟\n\n"
            "Choose the mood for your bio and I'll generate something awesome!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

async def bio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a bio based on mood"""
    # Show bio options directly
    keyboard = [
        [
            InlineKeyboardButton("😊 Happy", callback_data="bio_happy"),
            InlineKeyboardButton("😔 Sad", callback_data="bio_sad")
        ],
        [
            InlineKeyboardButton("😎 Attitude", callback_data="bio_attitude"),
            InlineKeyboardButton("💔 Broken", callback_data="bio_broken")
        ],
        [
            InlineKeyboardButton("💕 Love", callback_data="bio_love"),
            InlineKeyboardButton("🔮 Mystical", callback_data="bio_mystical")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌟 *Select a Bio Mood* 🌟\n\n"
        "Choose the mood for your bio and I'll generate something awesome!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def bio_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bio mood selection callback"""
    query = update.callback_query
    await query.answer()
    
    mood = query.data.replace("bio_", "")
    
    # Generate bio based on mood
    bio_text = await generate_bio(mood)
    
    # Create keyboard for refreshing or trying another mood
    keyboard = [
        [InlineKeyboardButton("♻️ Refresh", callback_data=f"refresh_bio_{mood}")],
        [InlineKeyboardButton("🔙 Other Moods", callback_data="generate_bio")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the bio
    await query.edit_message_text(
        f"🌟 *Your {mood.capitalize()} Bio* 🌟\n\n{bio_text}\n\n"
        "_Click Refresh for a different bio or Other Moods to change the mood._",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def refresh_bio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bio refresh button callback"""
    query = update.callback_query
    await query.answer()
    
    # Extract the mood from callback data
    mood = query.data.replace("refresh_bio_", "")
    
    # Generate a new bio
    bio_text = await generate_bio(mood)
    
    # Create keyboard for refreshing or trying another mood
    keyboard = [
        [InlineKeyboardButton("♻️ Refresh", callback_data=f"refresh_bio_{mood}")],
        [InlineKeyboardButton("🔙 Other Moods", callback_data="generate_bio")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit the message with the new bio
    await query.edit_message_text(
        f"🌟 *Your {mood.capitalize()} Bio* 🌟\n\n{bio_text}\n\n"
        "_Click Refresh for a different bio or Other Moods to change the mood._",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def links_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show links to the bot owner, support group, and channel"""
    links_text = (
        "🔗 *Community Links* 🔗\n\n"
        f"👤 *Owner*: @{Config.OWNER_USERNAME}\n"
        f"👥 *Support Group*: [Join Here]({Config.SUPPORT_GROUP})\n"
        f"📢 *Channel*: [Subscribe]({Config.SUPPORT_CHANNEL})\n\n"
        "Feel free to reach out if you need any help or have suggestions! 💕"
    )
    
    await update.message.reply_text(
        links_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message with all available commands"""
    help_text = (
        "🌟 *Bestie AI Help* 🌟\n\n"
        "*Basic Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        
        "*Utility Features:*\n"
        "/fancy_name [name] - Generate stylish fancy names\n"
        "/bio - Generate profile bios based on mood\n"
        "/links - Get community links\n\n"
        
        "*Games:*\n"
        "/games - View available games to play\n"
        "/tictactoe - Play Tic-Tac-Toe\n"
        "/truthordare - Play Truth or Dare\n"
        "/guess - Guess the number game\n\n"
        
        "*Group Management:*\n"
        "/admin_help - Show admin commands\n\n"
        
        "🗣️ *To chat with me:*\n"
        "In private chat: Just send a message!\n"
        "In groups: Tag me or reply to my messages\n\n"
        
        "I can send voice messages too! Just tap the 🔊 Listen button after I respond."
    )
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def register_utility_handlers(application):
    """Register all utility-related handlers"""
    application.add_handler(CommandHandler("fancy_name", fancy_name_command))
    application.add_handler(CommandHandler("bio", bio_command))
    application.add_handler(CommandHandler("links", links_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Register callback handlers
    application.add_handler(CallbackQueryHandler(fancy_button_callback, pattern=r'^refresh_fancy_'))
    application.add_handler(CallbackQueryHandler(bio_button_callback, pattern=r'^bio_'))
    application.add_handler(CallbackQueryHandler(refresh_bio_callback, pattern=r'^refresh_bio_'))
    application.add_handler(CallbackQueryHandler(fancy_button_callback, pattern=r'^generate_bio$'))
