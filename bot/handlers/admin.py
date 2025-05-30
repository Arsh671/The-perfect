import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode

from config import Config
from models.user import User
from models.group import Group
from models.conversation import Conversation
from utils.api_key_manager import APIKeyManager

logger = logging.getLogger(__name__)

# Admin command permissions check
def is_owner(user_id):
    """Check if user is the bot owner"""
    return user_id == Config.OWNER_ID

async def admin_required(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Decorator to check if user is admin"""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⚠️ This command is only available for the bot owner.")
        return False
    return True

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    if not await admin_required(update, context):
        return
    
    # Get statistics
    total_users = User.count_all()
    total_groups = Group.count_all()
    banned_users = User.count_banned()
    banned_groups = Group.count_banned()
    total_conversations = Conversation.count_all()
    
    # Get top users
    top_users = User.get_top_users(5)
    top_users_text = "\n".join([f"- {user['first_name']} (@{user['username'] or 'no username'}): {user['chat_count']} messages" for user in top_users])
    
    # Current API key info
    current_key = APIKeyManager.get_current_key_info()
    
    stats_text = (
        "📊 *Bot Statistics* 📊\n\n"
        f"👥 *Users*: {total_users} total, {banned_users} banned\n"
        f"👪 *Groups*: {total_groups} total, {banned_groups} banned\n"
        f"💬 *Conversations*: {total_conversations} total\n\n"
        f"*Top Users:*\n{top_users_text}\n\n"
        f"*API Key:* Currently using key #{current_key['index'] + 1} with {current_key['usage']} uses"
    )
    
    # Create keyboard for admin actions
    keyboard = [
        [
            InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("🔄 Rotate API Key", callback_data="admin_rotate_key")
        ],
        [
            InlineKeyboardButton("👮 Ban User", callback_data="admin_ban_user"),
            InlineKeyboardButton("👪 Ban Group", callback_data="admin_ban_group")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_text, 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast a message to all users or groups"""
    if not await admin_required(update, context):
        return
    
    # Check if there's a message to broadcast
    if not context.args:
        await update.message.reply_text(
            "Please provide a message to broadcast.\n"
            "Usage: /broadcast [message] or /broadcast_groups [message]"
        )
        return
    
    # Determine if we're broadcasting to users or groups
    is_groups = update.message.text.startswith("/broadcast_groups")
    
    # Get the message to broadcast
    message = " ".join(context.args)
    
    # Get targets
    if is_groups:
        targets = Group.get_all_active()
        target_type = "groups"
    else:
        targets = User.get_all_active()
        target_type = "users"
    
    # Send confirmation message
    await update.message.reply_text(
        f"You are about to broadcast this message to {len(targets)} {target_type}:\n\n"
        f"{message}\n\n"
        f"Are you sure?",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm_broadcast_{target_type}_{len(targets)}"),
                InlineKeyboardButton("❌ No", callback_data="cancel_broadcast")
            ]
        ])
    )
    
    # Store message in context for later use
    context.user_data["broadcast_message"] = message

async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user from using the bot"""
    if not await admin_required(update, context):
        return
    
    # Check if there's a user ID to ban
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID to ban.\n"
            "Usage: /ban_user [user_id] [reason]"
        )
        return
    
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        # Check if user exists
        user = User.get(user_id)
        if not user:
            await update.message.reply_text(f"User with ID {user_id} does not exist in the database.")
            return
        
        # Ban the user
        User.ban(user_id, update.effective_user.id, reason)
        
        await update.message.reply_text(
            f"User {user['first_name']} (@{user['username'] or 'no username'}) has been banned.\n"
            f"Reason: {reason}"
        )
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric ID.")

async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    if not await admin_required(update, context):
        return
    
    # Check if there's a user ID to unban
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID to unban.\n"
            "Usage: /unban_user [user_id]"
        )
        return
    
    try:
        user_id = int(context.args[0])
        
        # Check if user exists and is banned
        user = User.get(user_id)
        if not user:
            await update.message.reply_text(f"User with ID {user_id} does not exist in the database.")
            return
        
        if not user.get('is_banned', 0):
            await update.message.reply_text(f"User with ID {user_id} is not banned.")
            return
        
        # Unban the user
        User.unban(user_id)
        
        await update.message.reply_text(
            f"User {user['first_name']} (@{user['username'] or 'no username'}) has been unbanned."
        )
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric ID.")

async def admin_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin action button callbacks"""
    query = update.callback_query
    await query.answer()
    
    # Only allow the owner to use these buttons
    if not is_owner(query.from_user.id):
        await query.edit_message_text("⚠️ These actions are only available for the bot owner.")
        return
    
    action = query.data
    
    if action == "admin_broadcast":
        await query.edit_message_text(
            "Please send a message to broadcast to all users.\n"
            "Use /broadcast [message] to send to all users, or\n"
            "/broadcast_groups [message] to send to all groups."
        )
    elif action == "admin_rotate_key":
        # Rotate to the next API key
        old_key_index = APIKeyManager.get_current_key_info()['index']
        APIKeyManager.rotate_key()
        new_key_index = APIKeyManager.get_current_key_info()['index']
        
        await query.edit_message_text(
            f"API key rotated from key #{old_key_index + 1} to key #{new_key_index + 1}."
        )
    elif action == "admin_ban_user":
        await query.edit_message_text(
            "To ban a user, use the command:\n"
            "/ban_user [user_id] [reason]"
        )
    elif action == "admin_ban_group":
        await query.edit_message_text(
            "To ban a group, use the command:\n"
            "/ban_group [group_id] [reason]"
        )
    elif action.startswith("confirm_broadcast_"):
        # Extract target type and count
        _, target_type, count = action.split("_", 2)
        message = context.user_data.get("broadcast_message", "")
        
        if not message:
            await query.edit_message_text("Broadcast cancelled: No message found.")
            return
        
        # Prepare for broadcast
        sent_count = 0
        failed_count = 0
        
        # Start the broadcast with feedback
        status_message = await query.edit_message_text(
            f"Broadcasting message to {count} {target_type}... (0%)"
        )
        
        # Get the targets
        if target_type == "users":
            targets = User.get_all_active()
        else:
            targets = Group.get_all_active()
        
        # Broadcast the message
        for i, target in enumerate(targets):
            try:
                target_id = target['user_id'] if target_type == "users" else target['group_id']
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"📣 *BROADCAST MESSAGE*\n\n{message}\n\n_Sent by the bot owner_",
                    parse_mode=ParseMode.MARKDOWN
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {target_id}: {e}")
                failed_count += 1
            
            # Update status every 10 targets or at the end
            if (i + 1) % 10 == 0 or i == len(targets) - 1:
                percentage = round((i + 1) / len(targets) * 100)
                await status_message.edit_text(
                    f"Broadcasting message to {count} {target_type}... ({percentage}%)"
                )
        
        # Final report
        await status_message.edit_text(
            f"✅ Broadcast completed!\n\n"
            f"Sent to: {sent_count} {target_type}\n"
            f"Failed: {failed_count} {target_type}"
        )
    elif action == "cancel_broadcast":
        await query.edit_message_text("Broadcast cancelled.")

async def ban_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a group from using the bot"""
    if not await admin_required(update, context):
        return
    
    # Check if there's a group ID to ban
    if not context.args:
        await update.message.reply_text(
            "Please provide a group ID to ban.\n"
            "Usage: /ban_group [group_id] [reason]"
        )
        return
    
    try:
        group_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        # Check if group exists
        group = Group.get(group_id)
        if not group:
            await update.message.reply_text(f"Group with ID {group_id} does not exist in the database.")
            return
        
        # Ban the group
        Group.ban(group_id, update.effective_user.id, reason)
        
        # Try to leave the group
        try:
            await context.bot.leave_chat(group_id)
        except Exception as e:
            logger.error(f"Failed to leave group {group_id}: {e}")
        
        await update.message.reply_text(
            f"Group {group['name']} has been banned and the bot will attempt to leave it.\n"
            f"Reason: {reason}"
        )
    except ValueError:
        await update.message.reply_text("Invalid group ID. Please provide a numeric ID.")

async def unban_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a group"""
    if not await admin_required(update, context):
        return
    
    # Check if there's a group ID to unban
    if not context.args:
        await update.message.reply_text(
            "Please provide a group ID to unban.\n"
            "Usage: /unban_group [group_id]"
        )
        return
    
    try:
        group_id = int(context.args[0])
        
        # Check if group exists and is banned
        group = Group.get(group_id)
        if not group:
            await update.message.reply_text(f"Group with ID {group_id} does not exist in the database.")
            return
        
        if not group.get('is_banned', 0):
            await update.message.reply_text(f"Group with ID {group_id} is not banned.")
            return
        
        # Unban the group
        Group.unban(group_id)
        
        await update.message.reply_text(
            f"Group {group['name']} has been unbanned."
        )
    except ValueError:
        await update.message.reply_text("Invalid group ID. Please provide a numeric ID.")

def register_admin_handlers(application):
    """Register all admin-related handlers"""
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("broadcast_groups", broadcast_command))
    application.add_handler(CommandHandler("ban_user", ban_user_command))
    application.add_handler(CommandHandler("unban_user", unban_user_command))
    application.add_handler(CommandHandler("ban_group", ban_group_command))
    application.add_handler(CommandHandler("unban_group", unban_group_command))
    application.add_handler(CallbackQueryHandler(admin_button_callback, pattern=r'^admin_|^confirm_broadcast_|^cancel_broadcast'))
