import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, filters
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import Config
from models.user import User
from models.group import Group
from templates.welcome_messages import get_random_welcome_message

logger = logging.getLogger(__name__)

# Store admin commands in progress
admin_commands = {}

async def is_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if the user is a group admin"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Always allow bot owner
    if user_id == Config.OWNER_ID:
        return True
    
    # Get chat administrators
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members to the group"""
    if not update.message.new_chat_members:
        return
    
    for new_member in update.message.new_chat_members:
        # Skip if it's the bot itself
        if new_member.id == context.bot.id:
            # Register the group in database
            Group.create_or_update(
                group_id=update.effective_chat.id,
                name=update.effective_chat.title
            )
            
            # Send introduction message
            await update.message.reply_text(
                "Hello everyone! I'm Bestie, your flirty AI assistant! 💕\n\n"
                "You can tag me or reply to my messages to talk with me. I can also:\n"
                "• Help with group management (/admin_help)\n"
                "• Generate stylish names and bios (/fancy_name, /bio)\n"
                "• Play games with you (/games)\n"
                "• Send voice messages\n\n"
                "Tag me or mention my name to start a conversation!"
            )
            continue
        
        # Skip bots
        if new_member.is_bot:
            continue
        
        # Register the user in database
        User.create_or_update(
            user_id=new_member.id,
            username=new_member.username,
            first_name=new_member.first_name
        )
        
        # Get welcome message
        welcome_message = get_random_welcome_message(new_member.first_name)
        
        # Send welcome message
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Randomly promote owner
        if random.random() < 0.2:  # 20% chance
            await update.message.reply_text(
                f"By the way, you should check out @{Config.OWNER_USERNAME} for support! 😊"
            )

async def handle_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send message when a member leaves the group"""
    if not update.message.left_chat_member:
        return
    
    left_member = update.message.left_chat_member
    
    # Skip if it's the bot itself
    if left_member.id == context.bot.id:
        return
    
    # Skip bots
    if left_member.is_bot:
        return
    
    # Send leave message
    await update.message.reply_text(
        f"Goodbye, {left_member.first_name}! We'll miss you! 👋"
    )

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user from the group"""
    # Check if it's a group
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await update.message.reply_text("⚠️ This command is only available for group admins.")
        return
    
    # Check if the bot is admin
    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    if not bot_member.can_restrict_members:
        await update.message.reply_text(
            "⚠️ I don't have permission to ban members. Please give me the appropriate admin rights."
        )
        return
    
    # Parse command arguments
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "Please provide a user to ban.\n"
            "Usage: /ban [username or user ID] or reply to a message with /ban"
        )
        return
    
    # Get target user
    target_user = None
    reason = None
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        reason = " ".join(context.args) if context.args else "No reason provided"
    else:
        # Try to parse user ID or username
        user_identifier = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        try:
            # Try as user ID
            user_id = int(user_identifier)
            try:
                target_user = await context.bot.get_chat_member(update.effective_chat.id, user_id)
                target_user = target_user.user
            except BadRequest:
                await update.message.reply_text(f"User with ID {user_id} not found in this chat.")
                return
        except ValueError:
            # Try as username
            if user_identifier.startswith("@"):
                user_identifier = user_identifier[1:]
            
            # We can't directly get a user by username, so we need a workaround
            await update.message.reply_text(
                "Please reply to a message from the user you want to ban, or use their numeric user ID."
            )
            return
    
    if target_user is None:
        await update.message.reply_text("Could not identify the user to ban.")
        return
    
    # Don't allow banning the bot itself or the owner
    if target_user.id == context.bot.id:
        await update.message.reply_text("I can't ban myself! 😅")
        return
    
    if target_user.id == Config.OWNER_ID:
        await update.message.reply_text("I can't ban my owner! 😲")
        return
    
    # Don't allow banning other admins
    target_member = await context.bot.get_chat_member(update.effective_chat.id, target_user.id)
    if target_member.status in ["creator", "administrator"]:
        await update.message.reply_text("I can't ban admins! 😬")
        return
    
    # Ban the user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
        await update.message.reply_text(
            f"User {target_user.first_name} has been banned.\n"
            f"Reason: {reason}"
        )
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await update.message.reply_text(f"Failed to ban user: {str(e)}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user from the group"""
    # Check if it's a group
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await update.message.reply_text("⚠️ This command is only available for group admins.")
        return
    
    # Check if the bot is admin
    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    if not bot_member.can_restrict_members:
        await update.message.reply_text(
            "⚠️ I don't have permission to unban members. Please give me the appropriate admin rights."
        )
        return
    
    # Parse command arguments
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID to unban.\n"
            "Usage: /unban [user ID]"
        )
        return
    
    try:
        user_id = int(context.args[0])
        
        # Unban the user
        try:
            await context.bot.unban_chat_member(update.effective_chat.id, user_id)
            await update.message.reply_text(f"User with ID {user_id} has been unbanned.")
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            await update.message.reply_text(f"Failed to unban user: {str(e)}")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric ID.")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute a user in the group"""
    # Check if it's a group
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await update.message.reply_text("⚠️ This command is only available for group admins.")
        return
    
    # Check if the bot is admin
    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    if not bot_member.can_restrict_members:
        await update.message.reply_text(
            "⚠️ I don't have permission to mute members. Please give me the appropriate admin rights."
        )
        return
    
    # Parse command arguments
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "Please provide a user to mute.\n"
            "Usage: /mute [username or user ID] or reply to a message with /mute"
        )
        return
    
    # Get target user
    target_user = None
    reason = None
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        reason = " ".join(context.args) if context.args else "No reason provided"
    else:
        # Try to parse user ID or username
        user_identifier = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        try:
            # Try as user ID
            user_id = int(user_identifier)
            try:
                target_user = await context.bot.get_chat_member(update.effective_chat.id, user_id)
                target_user = target_user.user
            except BadRequest:
                await update.message.reply_text(f"User with ID {user_id} not found in this chat.")
                return
        except ValueError:
            # Try as username
            if user_identifier.startswith("@"):
                user_identifier = user_identifier[1:]
            
            # We can't directly get a user by username
            await update.message.reply_text(
                "Please reply to a message from the user you want to mute, or use their numeric user ID."
            )
            return
    
    if target_user is None:
        await update.message.reply_text("Could not identify the user to mute.")
        return
    
    # Don't allow muting the bot itself or the owner
    if target_user.id == context.bot.id:
        await update.message.reply_text("I can't mute myself! 😅")
        return
    
    if target_user.id == Config.OWNER_ID:
        await update.message.reply_text("I can't mute my owner! 😲")
        return
    
    # Don't allow muting other admins
    target_member = await context.bot.get_chat_member(update.effective_chat.id, target_user.id)
    if target_member.status in ["creator", "administrator"]:
        await update.message.reply_text("I can't mute admins! 😬")
        return
    
    # Mute the user
    try:
        # Restrict the user's permissions to send messages
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target_user.id,
            permissions={
                'can_send_messages': False,
                'can_send_media_messages': False,
                'can_send_other_messages': False,
                'can_add_web_page_previews': False
            }
        )
        await update.message.reply_text(
            f"User {target_user.first_name} has been muted.\n"
            f"Reason: {reason}"
        )
    except Exception as e:
        logger.error(f"Error muting user: {e}")
        await update.message.reply_text(f"Failed to mute user: {str(e)}")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute a user in the group"""
    # Check if it's a group
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await update.message.reply_text("⚠️ This command is only available for group admins.")
        return
    
    # Check if the bot is admin
    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    if not bot_member.can_restrict_members:
        await update.message.reply_text(
            "⚠️ I don't have permission to unmute members. Please give me the appropriate admin rights."
        )
        return
    
    # Parse command arguments
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "Please provide a user to unmute.\n"
            "Usage: /unmute [username or user ID] or reply to a message with /unmute"
        )
        return
    
    # Get target user
    target_user = None
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        # Try to parse user ID or username
        user_identifier = context.args[0]
        
        try:
            # Try as user ID
            user_id = int(user_identifier)
            try:
                target_user = await context.bot.get_chat_member(update.effective_chat.id, user_id)
                target_user = target_user.user
            except BadRequest:
                await update.message.reply_text(f"User with ID {user_id} not found in this chat.")
                return
        except ValueError:
            # Try as username
            if user_identifier.startswith("@"):
                user_identifier = user_identifier[1:]
            
            # We can't directly get a user by username
            await update.message.reply_text(
                "Please reply to a message from the user you want to unmute, or use their numeric user ID."
            )
            return
    
    if target_user is None:
        await update.message.reply_text("Could not identify the user to unmute.")
        return
    
    # Unmute the user
    try:
        # Restore the user's permissions
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target_user.id,
            permissions={
                'can_send_messages': True,
                'can_send_media_messages': True,
                'can_send_other_messages': True,
                'can_add_web_page_previews': True,
                'can_send_polls': True,
                'can_change_info': False,
                'can_invite_users': True,
                'can_pin_messages': False
            }
        )
        await update.message.reply_text(f"User {target_user.first_name} has been unmuted.")
    except Exception as e:
        logger.error(f"Error unmuting user: {e}")
        await update.message.reply_text(f"Failed to unmute user: {str(e)}")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kick a user from the group"""
    # Check if it's a group
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await update.message.reply_text("⚠️ This command is only available for group admins.")
        return
    
    # Check if the bot is admin
    bot_member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    if not bot_member.can_restrict_members:
        await update.message.reply_text(
            "⚠️ I don't have permission to kick members. Please give me the appropriate admin rights."
        )
        return
    
    # Parse command arguments
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "Please provide a user to kick.\n"
            "Usage: /kick [username or user ID] or reply to a message with /kick"
        )
        return
    
    # Get target user
    target_user = None
    reason = None
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        reason = " ".join(context.args) if context.args else "No reason provided"
    else:
        # Try to parse user ID or username
        user_identifier = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        try:
            # Try as user ID
            user_id = int(user_identifier)
            try:
                target_user = await context.bot.get_chat_member(update.effective_chat.id, user_id)
                target_user = target_user.user
            except BadRequest:
                await update.message.reply_text(f"User with ID {user_id} not found in this chat.")
                return
        except ValueError:
            # Try as username
            if user_identifier.startswith("@"):
                user_identifier = user_identifier[1:]
            
            # We can't directly get a user by username
            await update.message.reply_text(
                "Please reply to a message from the user you want to kick, or use their numeric user ID."
            )
            return
    
    if target_user is None:
        await update.message.reply_text("Could not identify the user to kick.")
        return
    
    # Don't allow kicking the bot itself or the owner
    if target_user.id == context.bot.id:
        await update.message.reply_text("I can't kick myself! 😅")
        return
    
    if target_user.id == Config.OWNER_ID:
        await update.message.reply_text("I can't kick my owner! 😲")
        return
    
    # Don't allow kicking other admins
    target_member = await context.bot.get_chat_member(update.effective_chat.id, target_user.id)
    if target_member.status in ["creator", "administrator"]:
        await update.message.reply_text("I can't kick admins! 😬")
        return
    
    # Kick the user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
        await update.message.reply_text(
            f"User {target_user.first_name} has been kicked.\n"
            f"Reason: {reason}"
        )
    except Exception as e:
        logger.error(f"Error kicking user: {e}")
        await update.message.reply_text(f"Failed to kick user: {str(e)}")

async def tag_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag all members in the group with a shayari/poetry"""
    # Check if it's a group
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_group_admin(update, context):
        await update.message.reply_text("⚠️ This command is only available for group admins.")
        return
    
    # Get the message to tag with
    message = " ".join(context.args) if context.args else "Hello everyone! 👋"
    
    try:
        # Get all members
        members = []
        async for member in context.bot.get_chat_members(update.effective_chat.id):
            if not member.user.is_bot:
                members.append(member.user)
        
        if not members:
            await update.message.reply_text("No members found to tag.")
            return
        
        # Split members into groups of 5 to avoid message length limits
        member_groups = [members[i:i+5] for i in range(0, len(members), 5)]
        
        # First message with the shayari/poetry
        await update.message.reply_text(f"📢 *Attention Everyone!*\n\n{message}", parse_mode=ParseMode.MARKDOWN)
        
        # Send tags in separate messages
        for group in member_groups:
            tag_text = " ".join([f"[​](@{m.username})" if m.username else f"[​](tg://user?id={m.id})" for m in group])
            await update.message.reply_text(tag_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error tagging all members: {e}")
        await update.message.reply_text(f"Failed to tag all members: {str(e)}")

async def admin_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help for admin commands"""
    admin_commands_text = (
        "🛡️ *Group Admin Commands* 🛡️\n\n"
        "*Moderation:*\n"
        "/ban - Ban a user (reply or user ID)\n"
        "/unban - Unban a user\n"
        "/mute - Mute a user (reply or user ID)\n"
        "/unmute - Unmute a user (reply or user ID)\n"
        "/kick - Kick a user (reply or user ID)\n\n"
        "*Utility:*\n"
        "/tag_all - Tag all members with a message\n"
        "/admin_help - Show this help message\n\n"
        "Note: These commands require admin privileges in the group."
    )
    
    await update.message.reply_text(admin_commands_text, parse_mode=ParseMode.MARKDOWN)

def register_group_management_handlers(application):
    """Register all group management handlers"""
    # Member updates
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_member))
    
    # Admin commands
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("kick", kick_command))
    application.add_handler(CommandHandler("tag_all", tag_all_command))
    application.add_handler(CommandHandler("admin_help", admin_help_command))



from telegram.ext import MessageHandler, filters
from telegram.helpers import mention_html
import re

async def process_smart_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    user = update.effective_user
    bot = context.bot
    chat_id = update.effective_chat.id
    user_id = user.id

    # Check bot is admin
    bot_member = await bot.get_chat_member(chat_id, bot.id)
    if bot_member.status not in ["administrator"]:
        return

    # Allow only group admins or bot owner
    is_admin = False
    if user_id == Config.OWNER_ID:
        is_admin = True
    else:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in ["administrator", "creator"]:
                is_admin = True
        except:
            return

    if not is_admin:
        return

    msg = update.message
    text = msg.text.lower()

    # Determine target user
    target_user = None
    if msg.reply_to_message:
        target_user = msg.reply_to_message.from_user
    elif msg.entities:
        for entity in msg.entities:
            if entity.type in ["mention", "text_mention"]:
                try:
                    username = msg.text[entity.offset: entity.offset + entity.length]
                    user_info = await bot.get_chat_member(chat_id, username.replace("@", ""))
                    target_user = user_info.user
                    break
                except:
                    pass

    if not target_user:
        return

    # Define action mapping
    if "ban" in text:
        await bot.ban_chat_member(chat_id, target_user.id)
        await msg.reply_text(f"✅ {mention_html(target_user.id, target_user.first_name)} has been banned.", parse_mode=ParseMode.HTML)
    elif "unban" in text:
        await bot.unban_chat_member(chat_id, target_user.id)
        await msg.reply_text(f"✅ {mention_html(target_user.id, target_user.first_name)} has been unbanned.", parse_mode=ParseMode.HTML)
    elif "mute" in text:
        from datetime import datetime, timedelta
        until_date = datetime.now() + timedelta(days=365)
        await bot.restrict_chat_member(chat_id, target_user.id, permissions=telegram.ChatPermissions(), until_date=until_date)
        await msg.reply_text(f"✅ {mention_html(target_user.id, target_user.first_name)} has been muted.", parse_mode=ParseMode.HTML)
    elif "unmute" in text:
        await bot.restrict_chat_member(chat_id, target_user.id, permissions=telegram.ChatPermissions(can_send_messages=True))
        await msg.reply_text(f"✅ {mention_html(target_user.id, target_user.first_name)} has been unmuted.", parse_mode=ParseMode.HTML)
    elif "pin" in text:
        try:
            await bot.pin_chat_message(chat_id, msg.reply_to_message.message_id)
            await msg.reply_text("✅ Message pinned.")
        except:
            pass
    elif "unpin" in text:
        await bot.unpin_chat_message(chat_id)
        await msg.reply_text("✅ Message unpinned.")
