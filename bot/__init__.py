#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Bot Package
"""

import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from bot.config import BOT_TOKEN, OWNER_ID
from bot.database import init_db
from bot.ai_handler import (start_command, handle_message, handle_private_message, 
                           handle_group_message, handle_ai_error, button_callback)
from bot.voice_handler import send_voice_message, handle_voice_message
from bot.group_handler import (handle_group_join, handle_group_leave, 
                              ban_command, unban_command, mute_command, 
                              unmute_command, kick_command, masstag_command,
                              tag_command, tagshayri_command, gmtag_command,
                              gntag_command, tagvc_command, cancel_command)
from bot.utility_handler import (name_generator_command, bio_generator_command, 
                                help_command, stats_command, community_links_command)
from bot.games_handler import (game_command, guess_command, tictactoe_callback, 
                              truth_or_dare_callback, guess_callback)
from bot.admin_handler import (broadcast_command, gban_command, ungban_command,
                              toggle_logging_command, admin_stats_command, admin_action_callback,
                              broadcast_callback, teach_command, facts_command, forget_command)
from bot.sticker_handler import handle_sticker
from bot.scheduled_tasks import setup_scheduler

logger = logging.getLogger(__name__)

def create_bot():
    """Initialize and configure the bot application"""
    
    # Initialize database
    init_db()
    
    # Create application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("voice", send_voice_message))
    application.add_handler(CommandHandler("name", name_generator_command))
    application.add_handler(CommandHandler("bio", bio_generator_command))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("guess", guess_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("links", community_links_command))
    
    # Group admin commands
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("kick", kick_command))
    application.add_handler(CommandHandler("masstag", masstag_command))
    
    # Group tagging commands
    application.add_handler(CommandHandler("tag", tag_command))
    application.add_handler(CommandHandler("tagshayri", tagshayri_command))
    application.add_handler(CommandHandler("gmtag", gmtag_command))
    application.add_handler(CommandHandler("gntag", gntag_command))
    application.add_handler(CommandHandler("tagvc", tagvc_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Bot owner commands
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("gban", gban_command))
    application.add_handler(CommandHandler("logging", toggle_logging_command))
    application.add_handler(CommandHandler("adminstats", admin_stats_command))
    
    # Teaching/Memory commands (owner only)
    application.add_handler(CommandHandler("teach", teach_command))
    application.add_handler(CommandHandler("facts", facts_command))
    application.add_handler(CommandHandler("forget", forget_command))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT, handle_private_message))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT, handle_group_message))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(admin_action_callback, pattern="^admin_|^confirm_ban"))  # Admin action buttons
    application.add_handler(CallbackQueryHandler(broadcast_callback, pattern="^broadcast_"))  # Broadcast confirmation buttons
    application.add_handler(CallbackQueryHandler(button_callback))  # Main menu and interactive buttons
    application.add_handler(CallbackQueryHandler(tictactoe_callback, pattern="^ttt_"))
    application.add_handler(CallbackQueryHandler(truth_or_dare_callback, pattern="^tod_"))
    application.add_handler(CallbackQueryHandler(guess_callback, pattern="^guess_"))
    
    # Group event handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_group_join))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_group_leave))
    
    # Error handler
    application.add_error_handler(handle_ai_error)
    
    # Set up scheduler for periodic tasks
    setup_scheduler(application)
    
    logger.info("Bot initialized successfully!")
    return application
