import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode
from bot.config import OWNER_ID, MESSAGE_LOGGING_ENABLED
from bot.modules.db import (
    get_all_users,
    get_all_groups,
    get_user,
    get_group,
    ban_user,
    unban_user,
    is_user_banned,
    get_banned_users,
    get_user_count,
    get_group_count
)

logger = logging.getLogger(__name__)

def register_owner_handlers(application: Application):
    """Register all owner-specific handlers."""
    # Owner commands
    application.add_handler(CommandHandler("broadcast", broadcast_command, filters=filters.User(OWNER_ID)))
    application.add_handler(CommandHandler("stats", stats_command, filters=filters.User(OWNER_ID)))
    application.add_handler(CommandHandler("gban", global_ban, filters=filters.User(OWNER_ID)))
    application.add_handler(CommandHandler("ungban", global_unban, filters=filters.User(OWNER_ID)))
    application.add_handler(CommandHandler("gbanned", list_banned, filters=filters.User(OWNER_ID)))
    application.add_handler(CommandHandler("toggle_logging", toggle_logging, filters=filters.User(OWNER_ID)))
    
    # Callback handler for owner panel
    application.add_handler(CallbackQueryHandler(handle_owner_callback, pattern="^owner_"))

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a broadcast message to all users or groups."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a message to broadcast.\n"
            "Usage: `/broadcast [users/groups] [message]`\n"
            "Example: `/broadcast users Hello everyone!`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    target = context.args[0].lower()
    message = " ".join(context.args[1:])
    
    if not message:
        await update.message.reply_text(
            "Please provide a message to broadcast.\n"
            "Usage: `/broadcast [users/groups] [message]`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if target not in ["users", "groups", "all"]:
        await update.message.reply_text(
            "Please specify a valid target: users, groups, or all.\n"
            "Usage: `/broadcast [users/groups/all] [message]`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"owner_broadcast_{target}_{message}"),
            InlineKeyboardButton("❌ Cancel", callback_data="owner_broadcast_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"You are about to broadcast the following message to all {target}:\n\n"
        f"{message}\n\n"
        f"Are you sure you want to continue?",
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics."""
    user_count = await get_user_count()
    group_count = await get_group_count()
    banned_users = await get_banned_users()
    
    stats_message = (
        "📊 *Bot Statistics* 📊\n\n"
        f"👤 *Users:* {user_count}\n"
        f"👥 *Groups:* {group_count}\n"
        f"🚫 *Banned Users:* {len(banned_users)}\n\n"
    )
    
    # Create keyboard with additional options
    keyboard = [
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="owner_broadcast_menu"),
            InlineKeyboardButton("🚫 Banned Users", callback_data="owner_banned_list")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="owner_settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def global_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Globally ban a user."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID to ban.\n"
            "Usage: `/gban [user_id] [reason]`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        # Check if user is already banned
        if await is_user_banned(user_id):
            await update.message.reply_text(
                f"User {user_id} is already banned."
            )
            return
        
        # Ban the user
        await ban_user(user_id, reason)
        
        await update.message.reply_text(
            f"User {user_id} has been globally banned.\n"
            f"Reason: {reason}"
        )
    
    except ValueError:
        await update.message.reply_text(
            "Please provide a valid user ID.\n"
            "Usage: `/gban [user_id] [reason]`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    except Exception as e:
        logger.error(f"Error banning user: {str(e)}")
        await update.message.reply_text(
            f"Error banning user: {str(e)}"
        )

async def global_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Globally unban a user."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID to unban.\n"
            "Usage: `/ungban [user_id]`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        user_id = int(context.args[0])
        
        # Check if user is banned
        if not await is_user_banned(user_id):
            await update.message.reply_text(
                f"User {user_id} is not banned."
            )
            return
        
        # Unban the user
        await unban_user(user_id)
        
        await update.message.reply_text(
            f"User {user_id} has been globally unbanned."
        )
    
    except ValueError:
        await update.message.reply_text(
            "Please provide a valid user ID.\n"
            "Usage: `/ungban [user_id]`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    except Exception as e:
        logger.error(f"Error unbanning user: {str(e)}")
        await update.message.reply_text(
            f"Error unbanning user: {str(e)}"
        )

async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all banned users."""
    banned_users = await get_banned_users()
    
    if not banned_users:
        await update.message.reply_text(
            "There are no banned users."
        )
        return
    
    message = "🚫 *Banned Users* 🚫\n\n"
    
    for i, user in enumerate(banned_users, 1):
        message += f"{i}. User ID: `{user['user_id']}`\n"
        message += f"   Reason: {user['reason']}\n"
        message += f"   Banned on: {user['banned_at']}\n\n"
    
    # Split message if it's too long
    if len(message) > 4000:
        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for chunk in chunks:
            await update.message.reply_text(
                chunk,
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )

async def toggle_logging(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle message logging."""
    global MESSAGE_LOGGING_ENABLED
    
    MESSAGE_LOGGING_ENABLED = not MESSAGE_LOGGING_ENABLED
    
    if MESSAGE_LOGGING_ENABLED:
        await update.message.reply_text(
            "Message logging has been enabled."
        )
    else:
        await update.message.reply_text(
            "Message logging has been disabled."
        )

async def handle_owner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries for owner panel."""
    query = update.callback_query
    await query.answer()
    
    # Extract callback data
    data = query.data.replace("owner_", "")
    
    if data == "broadcast_menu":
        # Show broadcast menu
        keyboard = [
            [
                InlineKeyboardButton("📢 Broadcast to Users", callback_data="owner_broadcast_users_menu"),
                InlineKeyboardButton("📢 Broadcast to Groups", callback_data="owner_broadcast_groups_menu")
            ],
            [
                InlineKeyboardButton("📢 Broadcast to All", callback_data="owner_broadcast_all_menu"),
                InlineKeyboardButton("🔙 Back", callback_data="owner_back_to_stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📢 *Broadcast Menu* 📢\n\n"
            "Choose where to send your broadcast message:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    elif data.startswith("broadcast_users_menu") or data.startswith("broadcast_groups_menu") or data.startswith("broadcast_all_menu"):
        # Show broadcast message input instructions
        target = data.split("_")[1]
        
        await query.edit_message_text(
            f"To send a broadcast to all {target}, use the command:\n\n"
            f"`/broadcast {target} Your message here`\n\n"
            f"The message will be sent as-is to all {target}.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("broadcast_"):
        # Handle broadcast confirmation or cancellation
        parts = data.split("_")
        
        if parts[1] == "cancel":
            await query.edit_message_text(
                "Broadcast cancelled."
            )
            return
        
        target = parts[1]
        message = "_".join(parts[2:])
        
        # Replace underscores with spaces in the message
        message = message.replace("_", " ")
        
        success_count = 0
        failed_count = 0
        
        # Send status message
        status_message = await query.edit_message_text(
            "Broadcasting message... 0% complete"
        )
        
        if target == "users" or target == "all":
            # Broadcast to users
            users = await get_all_users()
            total = len(users)
            
            for i, user in enumerate(users):
                try:
                    await context.bot.send_message(
                        chat_id=user["user_id"],
                        text=message
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error sending broadcast to user {user['user_id']}: {str(e)}")
                    failed_count += 1
                
                # Update status every 10 users
                if i % 10 == 0:
                    percentage = round((i / total) * 100)
                    await status_message.edit_text(
                        f"Broadcasting message to users... {percentage}% complete\n"
                        f"Success: {success_count}, Failed: {failed_count}"
                    )
        
        if target == "groups" or target == "all":
            # Broadcast to groups
            groups = await get_all_groups()
            total = len(groups)
            
            for i, group in enumerate(groups):
                try:
                    await context.bot.send_message(
                        chat_id=group["chat_id"],
                        text=message
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error sending broadcast to group {group['chat_id']}: {str(e)}")
                    failed_count += 1
                
                # Update status every 10 groups
                if i % 10 == 0:
                    percentage = round((i / total) * 100)
                    await status_message.edit_text(
                        f"Broadcasting message to groups... {percentage}% complete\n"
                        f"Success: {success_count}, Failed: {failed_count}"
                    )
        
        # Final status
        await status_message.edit_text(
            f"Broadcast complete!\n"
            f"Successfully sent: {success_count}\n"
            f"Failed: {failed_count}"
        )
    
    elif data == "banned_list":
        # Show list of banned users
        banned_users = await get_banned_users()
        
        if not banned_users:
            await query.edit_message_text(
                "There are no banned users.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="owner_back_to_stats")]])
            )
            return
        
        message = "🚫 *Banned Users* 🚫\n\n"
        
        for i, user in enumerate(banned_users[:10], 1):  # Show only first 10
            message += f"{i}. User ID: `{user['user_id']}`\n"
            message += f"   Reason: {user['reason']}\n"
            message += f"   Banned on: {user['banned_at']}\n\n"
        
        if len(banned_users) > 10:
            message += f"\nShowing 10 of {len(banned_users)} banned users."
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="owner_back_to_stats")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    elif data == "settings":
        # Show settings menu
        keyboard = [
            [
                InlineKeyboardButton(
                    f"Message Logging: {'✅ ON' if MESSAGE_LOGGING_ENABLED else '❌ OFF'}", 
                    callback_data="owner_toggle_logging"
                )
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="owner_back_to_stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ *Bot Settings* ⚙️\n\n"
            "Toggle various bot settings:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    elif data == "toggle_logging":
        # Toggle message logging
        global MESSAGE_LOGGING_ENABLED
        MESSAGE_LOGGING_ENABLED = not MESSAGE_LOGGING_ENABLED
        
        # Update settings menu
        keyboard = [
            [
                InlineKeyboardButton(
                    f"Message Logging: {'✅ ON' if MESSAGE_LOGGING_ENABLED else '❌ OFF'}", 
                    callback_data="owner_toggle_logging"
                )
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="owner_back_to_stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ *Bot Settings* ⚙️\n\n"
            "Toggle various bot settings:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    elif data == "back_to_stats":
        # Go back to stats
        user_count = await get_user_count()
        group_count = await get_group_count()
        banned_users = await get_banned_users()
        
        stats_message = (
            "📊 *Bot Statistics* 📊\n\n"
            f"👤 *Users:* {user_count}\n"
            f"👥 *Groups:* {group_count}\n"
            f"🚫 *Banned Users:* {len(banned_users)}\n\n"
        )
        
        # Create keyboard with additional options
        keyboard = [
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="owner_broadcast_menu"),
                InlineKeyboardButton("🚫 Banned Users", callback_data="owner_banned_list")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="owner_settings")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
