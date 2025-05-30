#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Admin commands and functionalities for the bot owner
"""

import logging
import datetime
from typing import List, Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, User, Chat
from telegram.ext import ContextTypes, Application
from telegram.constants import ParseMode, ChatType
from telegram.error import TelegramError

from bot.config import OWNER_ID, OWNER_USERNAME, BOT_PERSONALITY
from bot.database import (ban_user, unban_user, ban_group, unban_group, 
                         get_user_stats, get_group_stats, get_message_stats,
                         get_all_users, get_all_groups, get_active_users,
                         get_active_groups, get_setting, set_setting,
                         add_taught_fact, get_taught_fact, get_all_taught_facts,
                         delete_taught_fact)

logger = logging.getLogger(__name__)

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a broadcast message to all users/groups (owner only)"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🔒 This command is for the bot owner only."
        )
        return
    
    # Check if there's a message to broadcast
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a message to broadcast.\n\nUsage:\n"
                 "/broadcast [target] [message]\n\n"
                 "Targets: all, users, groups"
        )
        return
    
    # Parse target and message
    target = context.args[0].lower()
    if target not in ["all", "users", "groups"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Invalid target. Please use one of: all, users, groups"
        )
        return
    
    message = " ".join(context.args[1:])
    if not message:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a message to broadcast."
        )
        return
    
    # Get targets based on selection
    targets = []
    
    if target == "all" or target == "users":
        users = get_all_users()
        targets.extend([user["user_id"] for user in users])
    
    if target == "all" or target == "groups":
        groups = get_all_groups()
        targets.extend([group["group_id"] for group in groups])
    
    if not targets:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"No {target} found to broadcast to."
        )
        return
    
    # Confirm broadcast
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"broadcast_confirm_{target}_{len(targets)}"),
            InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=f"🔊 *Broadcast Preview*\n\n"
             f"Target: {target} ({len(targets)})\n"
             f"Message:\n\n"
             f"{message}\n\n"
             f"Are you sure you want to send this broadcast?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    
    # Store broadcast info in context
    context.chat_data["broadcast_message"] = message
    context.chat_data["broadcast_targets"] = targets

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle broadcast confirmation/cancellation"""
    if update.effective_chat is None or update.effective_user is None or update.callback_query is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await query.answer("This action is for the bot owner only.")
        return
    
    # Acknowledge the callback
    await query.answer()
    
    if query.data == "broadcast_cancel":
        await query.edit_message_text(
            text="🚫 Broadcast cancelled."
        )
        return
    
    elif query.data.startswith("broadcast_confirm_"):
        # Get broadcast info from context
        message = context.chat_data.get("broadcast_message", "")
        targets = context.chat_data.get("broadcast_targets", [])
        
        if not message or not targets:
            await query.edit_message_text(
                text="❌ Broadcast data not found. Please try again."
            )
            return
        
        # Start broadcasting
        await query.edit_message_text(
            text=f"📤 Broadcasting message to {len(targets)} recipients...\n\n"
                 f"This may take some time."
        )
        
        # Send messages
        success_count = 0
        fail_count = 0
        
        progress_message = await context.bot.send_message(
            chat_id=chat.id,
            text=f"Progress: 0/{len(targets)} (0%)"
        )
        
        for i, target_id in enumerate(targets, 1):
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"\n\n{message}",
                    parse_mode=ParseMode.MARKDOWN
                )
                success_count += 1
            except TelegramError as e:
                logger.error(f"Error broadcasting to {target_id}: {e}")
                fail_count += 1
            
            # Update progress every 10 recipients or at the end
            if i % 10 == 0 or i == len(targets):
                progress_percent = int((i / len(targets)) * 100)
                await progress_message.edit_text(
                    text=f"Progress: {i}/{len(targets)} ({progress_percent}%)"
                )
        
        # Final report
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"📊 *Broadcast Completed*\n\n"
                 f"✅ Successfully sent: {success_count}\n"
                 f"❌ Failed: {fail_count}\n"
                 f"📝 Total: {len(targets)}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Clear context data
        if "broadcast_message" in context.chat_data:
            del context.chat_data["broadcast_message"]
        if "broadcast_targets" in context.chat_data:
            del context.chat_data["broadcast_targets"]

async def gban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Globally ban a user from all groups and the bot (owner only)"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🔒 This command is for the bot owner only."
        )
        return
    
    # Check if there's a user ID to ban
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a user ID to ban.\n\nUsage:\n"
                 "/gban [user_id] [reason]"
        )
        return
    
    # Parse user ID and reason
    try:
        target_id = int(context.args[0])
    except ValueError:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a valid user ID."
        )
        return
    
    reason = "No reason provided"
    if len(context.args) > 1:
        reason = " ".join(context.args[1:])
    
    # Don't allow banning the owner
    if target_id == OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="You cannot ban yourself!"
        )
        return
    
    # Ban the user
    success = ban_user(target_id, reason)
    
    if success:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"🚫 User ID: {target_id} has been globally banned.\n"
                 f"Reason: {reason}"
        )
        
        # Try to notify the user
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🚫 You have been globally banned from using this bot.\n"
                     f"Reason: {reason}\n\n"
                     f"If you believe this is in error, contact the bot owner."
            )
        except TelegramError:
            # User may have blocked the bot or never started a chat
            pass
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"❌ Failed to ban user ID: {target_id}. The user may not exist in the database."
        )

async def ungban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Globally unban a user (owner only)"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🔒 This command is for the bot owner only."
        )
        return
    
    # Check if there's a user ID to unban
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a user ID to unban.\n\nUsage:\n"
                 "/ungban [user_id]"
        )
        return
    
    # Parse user ID
    try:
        target_id = int(context.args[0])
    except ValueError:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a valid user ID."
        )
        return
    
    # Unban the user
    success = unban_user(target_id)
    
    if success:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"✅ User ID: {target_id} has been globally unbanned."
        )
        
        # Try to notify the user
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"✅ You have been unbanned and can now use the bot again."
            )
        except TelegramError:
            # User may have blocked the bot or never started a chat
            pass
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"❌ Failed to unban user ID: {target_id}. The user may not exist in the database."
        )

async def toggle_logging_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle message logging feature (owner only)"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🔒 This command is for the bot owner only."
        )
        return
    
    # Get current logging status
    current_status = get_setting("message_logging", True)
    
    # Toggle status
    new_status = not current_status
    success = set_setting("message_logging", new_status)
    
    if success:
        status_text = "enabled" if new_status else "disabled"
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"✅ Message logging has been {status_text}."
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text="❌ Failed to update logging settings."
        )

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed admin statistics (owner only)"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🔒 This command is for the bot owner only."
        )
        return
    
    # Get detailed stats
    user_stats = get_user_stats()
    group_stats = get_group_stats()
    message_stats = get_message_stats()
    
    # Get active users and groups
    active_users = get_active_users(5)  # Get top 5 active users
    active_groups = get_active_groups(5)  # Get top 5 active groups
    
    # Format active users list
    active_users_text = ""
    for i, user_data in enumerate(active_users, 1):
        name = user_data["first_name"] or "Unknown"
        if user_data["username"]:
            name += f" (@{user_data['username']})"
        active_users_text += f"{i}. {name} - {user_data['message_count']} messages\n"
    
    if not active_users_text:
        active_users_text = "No active users found."
    
    # Format active groups list
    active_groups_text = ""
    for i, group_data in enumerate(active_groups, 1):
        title = group_data["title"] or "Unknown Group"
        active_groups_text += f"{i}. {title} - {group_data['message_count']} messages\n"
    
    if not active_groups_text:
        active_groups_text = "No active groups found."
    
    # Feature settings
    message_logging = get_setting("message_logging", True)
    
    stats_text = f"""
📊 *Detailed Admin Statistics* 📊

👥 *Users:*
• Total: {user_stats['total']}
• Active (7d): {user_stats['active']}
• Banned: {user_stats['banned']}

👥 *Groups:*
• Total: {group_stats['total']}
• Active (7d): {group_stats['active']}
• Banned: {group_stats['banned']}

💬 *Messages:*
• Total: {message_stats['total']}
• Today: {message_stats['today']}
• This week: {message_stats['week']}

🏆 *Top Active Users:*
{active_users_text}

🏆 *Top Active Groups:*
{active_groups_text}

⚙️ *Settings:*
• Message Logging: {'Enabled' if message_logging else 'Disabled'}
"""
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=stats_text,
        parse_mode=ParseMode.MARKDOWN
    )

# Owner notification functions
async def notify_owner_new_user(bot, user: User) -> None:
    """Notify the owner when a new user starts the bot"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        user_info = f"👤 *New User Alert* 👤\n\n"
        user_info += f"ID: `{user.id}`\n"
        user_info += f"Name: {user.first_name}"
        
        if user.last_name:
            user_info += f" {user.last_name}"
        
        if user.username:
            user_info += f"\nUsername: @{user.username}"
            
        if user.language_code:
            user_info += f"\nLanguage: {user.language_code}"
            
        user_info += f"\nTime: {timestamp}"
            
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{user.id}"),
                InlineKeyboardButton("💬 Message", callback_data=f"admin_msg_{user.id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(
            chat_id=OWNER_ID,
            text=user_info,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        logger.info(f"Notified owner about new user: {user.id}")
        
    except TelegramError as e:
        logger.error(f"Failed to notify owner about new user: {e}")

async def notify_owner_new_group(bot, group: Chat, added_by: User) -> None:
    """Notify the owner when the bot is added to a new group"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        group_info = f"👥 *New Group Alert* 👥\n\n"
        group_info += f"Group ID: `{group.id}`\n"
        group_info += f"Group Name: {group.title}\n"
        group_info += f"Members: {group.get_member_count() if hasattr(group, 'get_member_count') else 'Unknown'}\n"
        group_info += f"Added by: {added_by.first_name}"
        
        if added_by.username:
            group_info += f" (@{added_by.username})"
            
        group_info += f"\nTime: {timestamp}"
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🚫 Ban Group", callback_data=f"admin_ban_group_{group.id}"),
                InlineKeyboardButton("🗣️ Announce", callback_data=f"admin_announce_{group.id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.send_message(
            chat_id=OWNER_ID,
            text=group_info,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        logger.info(f"Notified owner about new group: {group.id}")
        
    except TelegramError as e:
        logger.error(f"Failed to notify owner about new group: {e}")

async def log_message_to_owner(bot, user: User, message_text: str, 
                              response_text: str, chat: Chat = None) -> None:
    """Log user messages to the owner if message_logging is enabled"""
    try:
        # Check if message logging is enabled
        if not get_setting("message_logging", True):
            return
        
        # Don't log the owner's own messages
        if user.id == OWNER_ID:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        chat_type = "Private"
        chat_name = "Direct Message"
        
        if chat and chat.type != ChatType.PRIVATE:
            chat_type = "Group"
            chat_name = chat.title or "Unknown Group"
        
        log_text = f"📩 *New Message Log* 📩\n\n"
        log_text += f"From: {user.first_name}"
        
        if user.username:
            log_text += f" (@{user.username})"
            
        log_text += f"\nUser ID: `{user.id}`\n"
        log_text += f"Chat: {chat_name} ({chat_type})\n"
        log_text += f"Time: {timestamp}\n\n"
        
        log_text += f"💬 *User Message:*\n{message_text}\n\n"
        log_text += f"🤖 *Bot Response:*\n{response_text}"
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🚫 Ban User", callback_data=f"admin_ban_{user.id}"),
                InlineKeyboardButton("💬 Reply", callback_data=f"admin_reply_{user.id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send log to owner
        await bot.send_message(
            chat_id=OWNER_ID,
            text=log_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        logger.debug(f"Logged message to owner: {user.id}")
        
    except TelegramError as e:
        logger.error(f"Failed to log message to owner: {e}")

async def teach_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Teach the bot a fact (owner only)"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🔒 This command is for the bot owner only."
        )
        return
    
    # Check usage
    if not context.args or len(context.args) < 2:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a keyword and fact to teach.\n\nUsage:\n"
                 "/teach [keyword] [fact]\n\n"
                 "Example: /teach birthday My birthday is on January 1st"
        )
        return
    
    # Parse keyword and fact
    keyword = context.args[0].lower()
    fact = " ".join(context.args[1:])
    
    # Save the fact
    success = add_taught_fact(keyword, fact)
    
    if success:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"✅ I've learned about '{keyword}'!\n\n"
                 f"When someone asks about this, I'll mention: \"{fact}\""
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"❌ Failed to save fact about '{keyword}'. Please try again."
        )

async def facts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all taught facts (owner only)"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🔒 This command is for the bot owner only."
        )
        return
    
    # Get all facts
    facts = get_all_taught_facts()
    
    if not facts:
        await context.bot.send_message(
            chat_id=chat.id,
            text="You haven't taught me any facts yet.\n\n"
                 "Use /teach [keyword] [fact] to teach me something!"
        )
        return
    
    # Format facts listing
    facts_list = "\n\n".join([
        f"🔑 *{fact['keyword']}*\n{fact['fact']}" 
        for fact in facts[:10]  # Limit to 10 most recent facts to avoid too long message
    ])
    
    total_count = len(facts)
    shown_count = min(10, total_count)
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=f"📚 *Taught Facts ({shown_count}/{total_count})*\n\n"
             f"{facts_list}",
        parse_mode=ParseMode.MARKDOWN
    )

async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a taught fact (owner only)"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="🔒 This command is for the bot owner only."
        )
        return
    
    # Check usage
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a keyword to forget.\n\nUsage:\n"
                 "/forget [keyword]"
        )
        return
    
    # Parse keyword
    keyword = context.args[0].lower()
    
    # Delete the fact
    success = delete_taught_fact(keyword)
    
    if success:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"✅ I've forgotten about '{keyword}'."
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"❌ I don't know anything about '{keyword}' or failed to forget it."
        )

async def admin_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin action callbacks from owner notifications"""
    if update.effective_chat is None or update.effective_user is None or update.callback_query is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    
    # Check if user is the owner
    if user.id != OWNER_ID:
        await query.answer("This action is for the bot owner only.")
        return
    
    # Acknowledge the callback
    await query.answer()
    
    if query.data.startswith("admin_ban_"):
        # Ban user action
        target_id = int(query.data.replace("admin_ban_", ""))
        
        # Show ban confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Ban", callback_data=f"confirm_ban_{target_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_admin_action")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🚫 Ban Confirmation\n\nAre you sure you want to ban User ID: {target_id}?",
            reply_markup=reply_markup
        )
        
    elif query.data.startswith("admin_ban_group_"):
        # Ban group action
        group_id = int(query.data.replace("admin_ban_group_", ""))
        
        # Show ban confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Ban", callback_data=f"confirm_ban_group_{group_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_admin_action")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🚫 Ban Confirmation\n\nAre you sure you want to ban Group ID: {group_id}?",
            reply_markup=reply_markup
        )
        
    elif query.data.startswith("admin_msg_") or query.data.startswith("admin_reply_"):
        # Message user action
        target_id = int(query.data.replace("admin_msg_", "").replace("admin_reply_", ""))
        
        # Store target ID in context for later use
        context.user_data["admin_message_target"] = target_id
        
        await query.edit_message_text(
            text=f"💬 Message Composition\n\nSend your next message to be delivered to User ID: {target_id}.\n\n"
                 f"Type /cancel to cancel this action."
        )
        
        # Set conversation state (handled in group_handler.py)
        context.user_data["awaiting_admin_message"] = True
        
    elif query.data.startswith("admin_announce_"):
        # Announce to group action
        group_id = int(query.data.replace("admin_announce_", ""))
        
        # Store group ID in context for later use
        context.user_data["admin_announce_target"] = group_id
        
        await query.edit_message_text(
            text=f"🗣️ Announcement Composition\n\nSend your next message to be announced in Group ID: {group_id}.\n\n"
                 f"Type /cancel to cancel this action."
        )
        
        # Set conversation state (handled in group_handler.py)
        context.user_data["awaiting_admin_announce"] = True
        
    elif query.data.startswith("confirm_ban_"):
        # Confirm user ban
        target_id = int(query.data.replace("confirm_ban_", ""))
        
        # Ban the user
        success = ban_user(target_id, reason="Banned by admin via notification")
        
        if success:
            await query.edit_message_text(
                text=f"✅ User ID: {target_id} has been banned successfully."
            )
            
            # Try to notify the user
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"🚫 You have been banned from using this bot by an administrator."
                )
            except TelegramError:
                # User may have blocked the bot or never started a chat
                pass
                
        else:
            await query.edit_message_text(
                text=f"❌ Failed to ban User ID: {target_id}."
            )
            
    elif query.data.startswith("confirm_ban_group_"):
        # Confirm group ban
        group_id = int(query.data.replace("confirm_ban_group_", ""))
        
        # Ban the group
        success = ban_group(group_id, reason="Banned by admin via notification")
        
        if success:
            await query.edit_message_text(
                text=f"✅ Group ID: {group_id} has been banned successfully.\n\n"
                     f"The bot will leave this group automatically."
            )
            
            # Try to leave the group
            try:
                await context.bot.leave_chat(group_id)
            except TelegramError as e:
                logger.error(f"Failed to leave banned group {group_id}: {e}")
                
        else:
            await query.edit_message_text(
                text=f"❌ Failed to ban Group ID: {group_id}."
            )
            
    elif query.data == "cancel_admin_action":
        # Cancel admin action
        await query.edit_message_text(
            text="❌ Action cancelled."
        )
