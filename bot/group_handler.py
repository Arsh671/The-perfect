#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Group management features for the Telegram Bot
"""

import logging
import random
import time
from typing import List, Optional

from telegram import Update, ChatMember, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from telegram.constants import ParseMode

from bot.config import OWNER_ID, OWNER_USERNAME
from bot.database import add_or_update_user, add_or_update_group, update_daily_stats
from bot.ai_handler import generate_ai_response
from bot.templates import (get_random_welcome_message, get_random_leave_message, 
                          get_random_shayri, get_random_promotion_message)

logger = logging.getLogger(__name__)

async def handle_group_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when users join a group"""
    if (update.effective_chat is None or 
        update.effective_message is None or 
        not update.effective_message.new_chat_members):
        return
    
    chat = update.effective_chat
    new_members = update.effective_message.new_chat_members
    
    # Register group in database
    add_or_update_group(group_id=chat.id, title=chat.title)
    
    # Get bot user
    bot_user = await context.bot.get_me()
    
    # Check if the bot itself joined
    for member in new_members:
        if member.id == bot_user.id:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"Hello everyone! I'm {bot_user.first_name}, your friendly assistant! 👋\n\n"
                     f"You can tag me or reply to my messages to chat with me.\n"
                     f"Use /help to see what I can do!"
            )
            
            # Notify owner of new group
            try:
                group_link = await context.bot.create_chat_invite_link(chat.id)
                invite_link = group_link.invite_link
            except TelegramError:
                invite_link = "link unavailable"
            
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"🔔 I was added to a new group!\n\n"
                     f"Group: {chat.title}\n"
                     f"ID: {chat.id}\n"
                     f"Link: {invite_link}"
            )
            return
    
    # For regular users joining
    welcome_users = []
    
    for member in new_members:
        # Register user in database
        add_or_update_user(
            user_id=member.id,
            username=member.username,
            first_name=member.first_name,
            last_name=member.last_name,
            language_code=member.language_code
        )
        
        # Add to welcome list
        if not member.is_bot:
            welcome_users.append(f"[{member.first_name}](tg://user?id={member.id})")
    
    if welcome_users:
        # Create mention string
        mentions = ", ".join(welcome_users)
        
        # Get AI-generated welcome message
        welcome_template = get_random_welcome_message()
        welcome_message = welcome_template.format(mentions=mentions, group_name=chat.title)
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_group_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when users leave a group"""
    if (update.effective_chat is None or 
        update.effective_message is None or 
        not update.effective_message.left_chat_member):
        return
    
    chat = update.effective_chat
    left_member = update.effective_message.left_chat_member
    
    # Get bot user
    bot_user = await context.bot.get_me()
    
    # Check if the bot itself was removed
    if left_member.id == bot_user.id:
        # Notify owner that bot was removed
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"⚠️ I was removed from a group:\n\n"
                 f"Group: {chat.title}\n"
                 f"ID: {chat.id}"
        )
        return
    
    # For regular users leaving
    if not left_member.is_bot:
        # Get leave message
        leave_template = get_random_leave_message()
        leave_message = leave_template.format(
            user=f"[{left_member.first_name}](tg://user?id={left_member.id})",
            group_name=chat.title
        )
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=leave_message,
            parse_mode=ParseMode.MARKDOWN
        )

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user from a group"""
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="You need to be an admin to use this command."
            )
            return
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Check if there's a target (mentioned user or replied message)
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif context.args and len(context.args) > 0:
        # Try to get username from args
        username = context.args[0].replace("@", "")
        try:
            # This only works if the bot has seen the user before in the group
            # A more robust approach would be to use Telegram's getChatMember API
            chat_members = await context.bot.get_chat_administrators(chat.id)
            for member in chat_members:
                if member.user.username and member.user.username.lower() == username.lower():
                    target_user = member.user
                    break
        except TelegramError as e:
            logger.error(f"Error finding user by username: {e}")
    
    if not target_user:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please specify a user to ban by replying to their message or mentioning them."
        )
        return
    
    # Don't allow banning the bot owner
    if target_user.id == OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="I cannot ban my owner. Nice try though! 😏"
        )
        return
    
    # Get ban reason
    reason = ""
    if context.args and len(context.args) > (0 if message.reply_to_message else 1):
        start_idx = 0 if message.reply_to_message else 1
        reason = " ".join(context.args[start_idx:])
    
    # Try to ban the user
    try:
        await context.bot.ban_chat_member(chat.id, target_user.id)
        
        ban_message = f"🚫 User [{target_user.first_name}](tg://user?id={target_user.id}) has been banned."
        if reason:
            ban_message += f"\nReason: {reason}"
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=ban_message,
            parse_mode=ParseMode.MARKDOWN
        )
    except TelegramError as e:
        logger.error(f"Error banning user: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to ban user: {e}"
        )

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unban a user from a group"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="You need to be an admin to use this command."
            )
            return
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Check if there's a target user id
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please specify a user ID to unban."
        )
        return
    
    try:
        target_id = int(context.args[0])
    except ValueError:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a valid user ID."
        )
        return
    
    # Try to unban the user
    try:
        await context.bot.unban_chat_member(chat.id, target_id)
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"✅ User ID {target_id} has been unbanned."
        )
    except TelegramError as e:
        logger.error(f"Error unbanning user: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to unban user: {e}"
        )

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mute a user in a group"""
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="You need to be an admin to use this command."
            )
            return
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Check if there's a target (mentioned user or replied message)
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif context.args and len(context.args) > 0:
        # Try to get username from args
        username = context.args[0].replace("@", "")
        try:
            chat_members = await context.bot.get_chat_administrators(chat.id)
            for member in chat_members:
                if member.user.username and member.user.username.lower() == username.lower():
                    target_user = member.user
                    break
        except TelegramError as e:
            logger.error(f"Error finding user by username: {e}")
    
    if not target_user:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please specify a user to mute by replying to their message or mentioning them."
        )
        return
    
    # Don't allow muting the bot owner
    if target_user.id == OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="I cannot mute my owner. Nice try though! 😏"
        )
        return
    
    # Determine mute duration
    mute_time = None
    reason = ""
    
    if context.args and len(context.args) > (0 if message.reply_to_message else 1):
        start_idx = 0 if message.reply_to_message else 1
        
        # Check if first arg is a duration
        if context.args[start_idx].lower().endswith(('m', 'h', 'd')):
            duration_str = context.args[start_idx].lower()
            duration_value = duration_str[:-1]
            duration_unit = duration_str[-1]
            
            try:
                duration_value = int(duration_value)
                
                if duration_unit == 'm':  # minutes
                    mute_time = time.time() + duration_value * 60
                elif duration_unit == 'h':  # hours
                    mute_time = time.time() + duration_value * 3600
                elif duration_unit == 'd':  # days
                    mute_time = time.time() + duration_value * 86400
                
                reason = " ".join(context.args[start_idx+1:])
            except ValueError:
                reason = " ".join(context.args[start_idx:])
        else:
            reason = " ".join(context.args[start_idx:])
    
    # Create permissions with no message rights
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )
    
    # Try to mute the user
    try:
        await context.bot.restrict_chat_member(chat.id, target_user.id, permissions, until_date=mute_time)
        
        mute_message = f"🔇 User [{target_user.first_name}](tg://user?id={target_user.id}) has been muted."
        
        if mute_time:
            # Calculate duration for display
            duration = mute_time - time.time()
            if duration < 3600:
                duration_str = f"{int(duration / 60)} minutes"
            elif duration < 86400:
                duration_str = f"{int(duration / 3600)} hours"
            else:
                duration_str = f"{int(duration / 86400)} days"
            
            mute_message += f"\nDuration: {duration_str}"
        
        if reason:
            mute_message += f"\nReason: {reason}"
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=mute_message,
            parse_mode=ParseMode.MARKDOWN
        )
    except TelegramError as e:
        logger.error(f"Error muting user: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to mute user: {e}"
        )

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unmute a user in a group"""
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="You need to be an admin to use this command."
            )
            return
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Check if there's a target (mentioned user or replied message)
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif context.args and len(context.args) > 0:
        # Try to get username from args
        username = context.args[0].replace("@", "")
        try:
            chat_members = await context.bot.get_chat_administrators(chat.id)
            for member in chat_members:
                if member.user.username and member.user.username.lower() == username.lower():
                    target_user = member.user
                    break
        except TelegramError as e:
            logger.error(f"Error finding user by username: {e}")
    
    if not target_user:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please specify a user to unmute by replying to their message or mentioning them."
        )
        return
    
    # Create permissions with message rights
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    
    # Try to unmute the user
    try:
        await context.bot.restrict_chat_member(chat.id, target_user.id, permissions)
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"🔊 User [{target_user.first_name}](tg://user?id={target_user.id}) has been unmuted.",
            parse_mode=ParseMode.MARKDOWN
        )
    except TelegramError as e:
        logger.error(f"Error unmuting user: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to unmute user: {e}"
        )

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kick a user from a group"""
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="You need to be an admin to use this command."
            )
            return
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Check if there's a target (mentioned user or replied message)
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif context.args and len(context.args) > 0:
        # Try to get username from args
        username = context.args[0].replace("@", "")
        try:
            chat_members = await context.bot.get_chat_administrators(chat.id)
            for member in chat_members:
                if member.user.username and member.user.username.lower() == username.lower():
                    target_user = member.user
                    break
        except TelegramError as e:
            logger.error(f"Error finding user by username: {e}")
    
    if not target_user:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please specify a user to kick by replying to their message or mentioning them."
        )
        return
    
    # Don't allow kicking the bot owner
    if target_user.id == OWNER_ID:
        await context.bot.send_message(
            chat_id=chat.id,
            text="I cannot kick my owner. Nice try though! 😏"
        )
        return
    
    # Get kick reason
    reason = ""
    if context.args and len(context.args) > (0 if message.reply_to_message else 1):
        start_idx = 0 if message.reply_to_message else 1
        reason = " ".join(context.args[start_idx:])
    
    # Try to kick the user
    try:
        # Ban and then unban to kick
        await context.bot.ban_chat_member(chat.id, target_user.id)
        await context.bot.unban_chat_member(chat.id, target_user.id)
        
        kick_message = f"👢 User [{target_user.first_name}](tg://user?id={target_user.id}) has been kicked."
        if reason:
            kick_message += f"\nReason: {reason}"
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=kick_message,
            parse_mode=ParseMode.MARKDOWN
        )
    except TelegramError as e:
        logger.error(f"Error kicking user: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to kick user: {e}"
        )

async def masstag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tag all users in a group with a shayri/poem"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="You need to be an admin to use this command."
            )
            return
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Check if there's a custom message
    custom_message = ""
    if context.args and len(context.args) > 0:
        custom_message = " ".join(context.args)
    
    # Get all users from the group
    try:
        # Since we can't get all members directly, we'll use admins for now
        # A more complete solution would need to track members over time
        admins = await context.bot.get_chat_administrators(chat.id)
        
        # Get random shayri
        shayri = get_random_shayri()
        if custom_message:
            shayri = custom_message
        
        # Create mentions
        mentions = []
        for admin in admins:
            if not admin.user.is_bot:  # Skip bots
                mentions.append(f"[{admin.user.first_name}](tg://user?id={admin.user.id})")
        
        if mentions:
            # Tag message with shayri
            message = f"{shayri}\n\n{' '.join(mentions)}"
            
            await context.bot.send_message(
                chat_id=chat.id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await context.bot.send_message(
                chat_id=chat.id,
                text="No users found to tag."
            )
    except TelegramError as e:
        logger.error(f"Error in masstag: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to tag users: {e}"
        )

# Dictionary to store active tagging sessions
ACTIVE_TAGGING = {}

async def tag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tag all members in a group with a custom message"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in ['creator', 'administrator']
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="Only group admins can use this command."
            )
            return
    except TelegramError:
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Check if there's a custom message
    custom_message = ""
    if context.args and len(context.args) > 0:
        custom_message = " ".join(context.args)
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text="Please provide a message after /tag command."
        )
        return
    
    # Get all users from the group
    try:
        # Since we can't get all members directly, we'll use admins for now
        # A more complete solution would need to track members over time
        admins = await context.bot.get_chat_administrators(chat.id)
        
        # Store members for tagging
        members = []
        for admin in admins:
            if not admin.user.is_bot:  # Skip bots
                members.append(admin.user)
        
        if members:
            # Start tagging process
            ACTIVE_TAGGING[chat.id] = {
                "members": members,
                "current_index": 0,
                "message": custom_message,
                "type": "custom"
            }
            
            # Start tagging
            await tag_next_member(context, chat.id)
            
            # Send instructions to stop
            await context.bot.send_message(
                chat_id=chat.id,
                text="Tagging in progress... Use /cancel to stop tagging."
            )
        else:
            await context.bot.send_message(
                chat_id=chat.id,
                text="No users found to tag."
            )
    except TelegramError as e:
        logger.error(f"Error in tag command: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to tag users: {e}"
        )

async def tagshayri_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tag all members with a shayri"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in ['creator', 'administrator']
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="Only group admins can use this command."
            )
            return
    except TelegramError:
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Get random shayri
    shayri = get_random_shayri()
    
    # Get all users from the group
    try:
        # Since we can't get all members directly, we'll use admins for now
        # A more complete solution would need to track members over time
        admins = await context.bot.get_chat_administrators(chat.id)
        
        # Store members for tagging
        members = []
        for admin in admins:
            if not admin.user.is_bot:  # Skip bots
                members.append(admin.user)
        
        if members:
            # Start tagging process
            ACTIVE_TAGGING[chat.id] = {
                "members": members,
                "current_index": 0,
                "message": shayri,
                "type": "shayri"
            }
            
            # Start tagging
            await tag_next_member(context, chat.id)
            
            # Send instructions to stop
            await context.bot.send_message(
                chat_id=chat.id,
                text="Tagging with shayri in progress... Use /cancel to stop tagging."
            )
        else:
            await context.bot.send_message(
                chat_id=chat.id,
                text="No users found to tag."
            )
    except TelegramError as e:
        logger.error(f"Error in tagshayri command: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to tag users: {e}"
        )

async def gmtag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tag all members with good morning message"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in ['creator', 'administrator']
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="Only group admins can use this command."
            )
            return
    except TelegramError:
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Good morning message
    gm_message = "🌞 Good morning! Rise and shine! Hope you have a wonderful day ahead. ☀️"
    
    # Get all users from the group
    try:
        # Since we can't get all members directly, we'll use admins for now
        # A more complete solution would need to track members over time
        admins = await context.bot.get_chat_administrators(chat.id)
        
        # Store members for tagging
        members = []
        for admin in admins:
            if not admin.user.is_bot:  # Skip bots
                members.append(admin.user)
        
        if members:
            # Start tagging process
            ACTIVE_TAGGING[chat.id] = {
                "members": members,
                "current_index": 0,
                "message": gm_message,
                "type": "gm"
            }
            
            # Start tagging
            await tag_next_member(context, chat.id)
            
            # Send instructions to stop
            await context.bot.send_message(
                chat_id=chat.id,
                text="Good morning tagging in progress... Use /cancel to stop tagging."
            )
        else:
            await context.bot.send_message(
                chat_id=chat.id,
                text="No users found to tag."
            )
    except TelegramError as e:
        logger.error(f"Error in gmtag command: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to tag users: {e}"
        )

async def gntag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tag all members with good night message"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in ['creator', 'administrator']
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="Only group admins can use this command."
            )
            return
    except TelegramError:
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Good night message
    gn_message = "🌙 Good night! Sweet dreams. Sleep tight and wake up fresh tomorrow. 😴✨"
    
    # Get all users from the group
    try:
        # Since we can't get all members directly, we'll use admins for now
        # A more complete solution would need to track members over time
        admins = await context.bot.get_chat_administrators(chat.id)
        
        # Store members for tagging
        members = []
        for admin in admins:
            if not admin.user.is_bot:  # Skip bots
                members.append(admin.user)
        
        if members:
            # Start tagging process
            ACTIVE_TAGGING[chat.id] = {
                "members": members,
                "current_index": 0,
                "message": gn_message,
                "type": "gn"
            }
            
            # Start tagging
            await tag_next_member(context, chat.id)
            
            # Send instructions to stop
            await context.bot.send_message(
                chat_id=chat.id,
                text="Good night tagging in progress... Use /cancel to stop tagging."
            )
        else:
            await context.bot.send_message(
                chat_id=chat.id,
                text="No users found to tag."
            )
    except TelegramError as e:
        logger.error(f"Error in gntag command: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to tag users: {e}"
        )

async def tagvc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tag all members to join voice chat"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is in a group
    if chat.type not in ["group", "supergroup"]:
        await context.bot.send_message(
            chat_id=chat.id,
            text="This command can only be used in groups."
        )
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in ['creator', 'administrator']
        
        if not is_admin and user.id != OWNER_ID:
            await context.bot.send_message(
                chat_id=chat.id,
                text="Only group admins can use this command."
            )
            return
    except TelegramError:
        await context.bot.send_message(
            chat_id=chat.id,
            text="An error occurred while checking permissions."
        )
        return
    
    # Voice chat message
    vc_message = "🎙️ Voice chat is active! Join us for a conversation. 🔊"
    
    # Get all users from the group
    try:
        # Since we can't get all members directly, we'll use admins for now
        # A more complete solution would need to track members over time
        admins = await context.bot.get_chat_administrators(chat.id)
        
        # Store members for tagging
        members = []
        for admin in admins:
            if not admin.user.is_bot:  # Skip bots
                members.append(admin.user)
        
        if members:
            # Start tagging process
            ACTIVE_TAGGING[chat.id] = {
                "members": members,
                "current_index": 0,
                "message": vc_message,
                "type": "vc"
            }
            
            # Start tagging
            await tag_next_member(context, chat.id)
            
            # Send instructions to stop
            await context.bot.send_message(
                chat_id=chat.id,
                text="Voice chat tagging in progress... Use /cancel to stop tagging."
            )
        else:
            await context.bot.send_message(
                chat_id=chat.id,
                text="No users found to tag."
            )
    except TelegramError as e:
        logger.error(f"Error in tagvc command: {e}")
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"Failed to tag users: {e}"
        )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel an ongoing tagging operation"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if there's an active tagging session for this chat
    if chat.id in ACTIVE_TAGGING:
        # Delete the tagging session
        del ACTIVE_TAGGING[chat.id]
        
        await context.bot.send_message(
            chat_id=chat.id,
            text="Tagging has been stopped."
        )
    else:
        await context.bot.send_message(
            chat_id=chat.id,
            text="There's no active tagging to cancel."
        )

async def tag_next_member(context, chat_id):
    """Tag the next member in the group"""
    # Check if there's an active tagging session
    if chat_id not in ACTIVE_TAGGING:
        return
    
    tagging_info = ACTIVE_TAGGING[chat_id]
    members = tagging_info["members"]
    current_index = tagging_info["current_index"]
    message = tagging_info["message"]
    
    # Check if we've tagged all members
    if current_index >= len(members):
        # Tagging complete
        del ACTIVE_TAGGING[chat_id]
        await context.bot.send_message(
            chat_id=chat_id,
            text="Tagging complete!"
        )
        return
    
    # Get the current member to tag
    member = members[current_index]
    
    # Create the tag message
    tag_message = f"{message}\n\n[{member.first_name}](tg://user?id={member.id})"
    
    # Send the tag message
    await context.bot.send_message(
        chat_id=chat_id,
        text=tag_message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Update the current index
    ACTIVE_TAGGING[chat_id]["current_index"] = current_index + 1
    
    # Wait for a second before tagging the next member
    # Schedule the next tag
    context.job_queue.run_once(
        lambda _: tag_next_member(context, chat_id),
        1.0  # 1 second delay
    )

async def promote_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Randomly promote the owner in groups"""
    if update.effective_chat is None or update.effective_message is None:
        return
    
    chat = update.effective_chat
    message = update.effective_message
    
    # Only in groups and with a small random chance (1%)
    if chat.type not in ["group", "supergroup"] or random.random() > 0.01:
        return
    
    # Get random promotion message
    promotion_message = get_random_promotion_message()
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=promotion_message.format(username=OWNER_USERNAME),
        parse_mode=ParseMode.MARKDOWN
    )
