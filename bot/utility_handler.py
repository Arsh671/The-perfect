#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility features for the Telegram Bot
"""

import logging
import random
from typing import List, Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.config import (OWNER_USERNAME, SUPPORT_GROUP, SUPPORT_CHANNEL, FEATURES)
from bot.database import (get_user_stats, get_group_stats, get_message_stats)
from bot.templates import (get_stylish_name_templates, get_bio_templates)
from bot.helpers import add_emojis

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - show available commands"""
    if update.effective_chat is None:
        return
    
    chat = update.effective_chat
    
    help_text = """
🌟 *Commands List* 🌟

*General Commands:*
/start - Start a conversation with me
/help - Show this help message
/voice [text] - Convert text to voice message
/name [your name] - Generate a stylish name
/bio [mood] - Generate a bio based on mood (sad/angry/attitude)
/game - Play games (tic-tac-toe, truth or dare, guess)
/stats - Show bot statistics
/links - Show community links

*Group Management Commands (Admin only):*
/ban - Ban a user from the group
/unban - Unban a user from the group
/mute - Mute a user in the group
/unmute - Unmute a user in the group
/kick - Kick a user from the group
/masstag - Tag all users with a shayri/poem

*How to use me in groups:*
- Tag me or reply to my messages
- I'll respond with friendly conversation
- I can help manage your group with admin commands

*Need more help?*
Contact my owner @{owner} or join the support group.
"""
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=help_text.format(owner=OWNER_USERNAME),
        parse_mode=ParseMode.MARKDOWN
    )

async def name_generator_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate stylish name with fancy fonts and emojis"""
    if update.effective_chat is None:
        return
    
    chat = update.effective_chat
    
    # Get base name from arguments or use a default
    base_name = "User"
    if context.args and len(context.args) > 0:
        base_name = " ".join(context.args)
    
    # Get name templates
    templates = get_stylish_name_templates()
    
    # Generate 5 stylish names
    stylish_names = []
    used_templates = random.sample(templates, min(5, len(templates)))
    
    for template in used_templates:
        # Replace placeholder with actual name
        stylish_name = template.replace("{name}", base_name)
        
        # Add random emojis if not already in template
        if "emoji" not in template.lower():
            stylish_name = add_emojis(stylish_name, 1, 3)
        
        stylish_names.append(stylish_name)
    
    # Create response message
    response = f"✨ *Stylish Names for {base_name}* ✨\n\n"
    for i, name in enumerate(stylish_names, 1):
        response += f"{i}. `{name}`\n\n"
    
    response += "Copy your favorite name by tapping on it!"
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=response,
        parse_mode=ParseMode.MARKDOWN
    )

async def bio_generator_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a bio based on mood (sad, angry, attitude)"""
    if update.effective_chat is None:
        return
    
    chat = update.effective_chat
    
    # Get mood from arguments or use a default
    mood = "attitude"
    if context.args and len(context.args) > 0:
        mood = context.args[0].lower()
    
    # Validate mood
    valid_moods = ["sad", "angry", "attitude", "happy", "love"]
    if mood not in valid_moods:
        mood = "attitude"  # Default to attitude if invalid
    
    # Get bio templates for the mood
    templates = get_bio_templates(mood)
    
    # Generate 3 random bios
    bios = random.sample(templates, min(3, len(templates)))
    
    # Create response message
    response = f"📝 *{mood.capitalize()} Bio Suggestions* 📝\n\n"
    for i, bio in enumerate(bios, 1):
        response += f"{i}. `{bio}`\n\n"
    
    response += "Copy your favorite bio by tapping on it!"
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=response,
        parse_mode=ParseMode.MARKDOWN
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics"""
    if update.effective_chat is None:
        return
    
    chat = update.effective_chat
    
    # Get stats from database
    user_stats = get_user_stats()
    group_stats = get_group_stats()
    message_stats = get_message_stats()
    
    stats_text = f"""
📊 *Bot Statistics* 📊

👥 *Users:*
• Total: {user_stats['total']}
• Active (7d): {user_stats['active']}

👥 *Groups:*
• Total: {group_stats['total']}
• Active (7d): {group_stats['active']}

💬 *Messages:*
• Total: {message_stats['total']}
• Today: {message_stats['today']}
• This week: {message_stats['week']}

*Features Available:*
• Voice Messages: {'✅' if FEATURES.get('voice_messages', True) else '❌'}
• Multilingual: {'✅' if FEATURES.get('multilingual', True) else '❌'}
• Games: {'✅' if FEATURES.get('games', True) else '❌'}
• Group Management: {'✅' if FEATURES.get('group_management', True) else '❌'}

Made with ❤️ by @{OWNER_USERNAME}
"""
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=stats_text,
        parse_mode=ParseMode.MARKDOWN
    )

async def community_links_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show community links (owner/group/channel)"""
    if update.effective_chat is None:
        return
    
    chat = update.effective_chat
    
    # Create inline keyboard with links
    keyboard = [
        [
            InlineKeyboardButton("👤 Owner", url=f"https://t.me/{OWNER_USERNAME}")
        ],
        [
            InlineKeyboardButton("👥 Support Group", url=SUPPORT_GROUP)
        ],
        [
            InlineKeyboardButton("📢 Channel", url=SUPPORT_CHANNEL)
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat.id,
        text="🔗 *Community Links* 🔗\n\nJoin our community to stay updated and get support!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
