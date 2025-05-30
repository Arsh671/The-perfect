import logging
from datetime import datetime, timedelta
from telegram import Update, ChatMemberUpdated, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode
from bot.config import OWNER_ID, OWNER_USERNAME
from bot.modules.ai_service import get_ai_response
from bot.utils.helpers import is_user_admin, get_mention
import random

logger = logging.getLogger(__name__)

def register_group_admin_handlers(application: Application):
    """Register all group admin handlers."""
    # Member join/leave handlers
    application.add_handler(ChatMemberHandler(track_chat_members, ChatMemberHandler.CHAT_MEMBER))
    
    # Admin commands
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("kick", kick_user))
    
    # Tag all users
    application.add_handler(CommandHandler("tag", tag_all))
    
    # Random owner promotion
    application.add_handler(CommandHandler("promote_owner", promote_owner))
    
    # Message relay
    application.add_handler(CommandHandler("relay", relay_message))

async def track_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track when members join or leave the chat."""
    result = extract_status_change(update.chat_member)
    
    if result is None:
        return
    
    was_member, is_member = result
    
    # Member joined
    if not was_member and is_member:
        user = update.chat_member.new_chat_member.user
        chat = update.effective_chat
        
        # Generate welcoming message with AI
        prompt = f"Generate a warm, friendly welcome message for {user.first_name} who just joined a Telegram group. Make it brief (1-2 sentences), friendly and add some relevant emojis."
        try:
            welcome_message = await get_ai_response(prompt, [], "en")
        except Exception as e:
            logger.error(f"Error generating welcome message: {str(e)}")
            welcome_message = f"👋 Welcome to the group, {user.first_name}! Glad to have you here!"
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Member left
    elif was_member and not is_member:
        user = update.chat_member.old_chat_member.user
        chat = update.effective_chat
        
        leave_message = f"👋 {user.first_name} has left the group. We'll miss you!"
        
        await context.bot.send_message(
            chat_id=chat.id,
            text=leave_message
        )

def extract_status_change(chat_member_update):
    """Extract status change from ChatMemberUpdated."""
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))
    
    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in ["member", "administrator", "creator"] or (old_status == "restricted" and old_is_member is True)
    is_member = new_status in ["member", "administrator", "creator"] or (new_status == "restricted" and new_is_member is True)
    
    return was_member, is_member

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user from the group."""
    # Check if user is admin
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if there's a user to ban (either by reply or by username)
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("❌ Please specify a user to ban by replying to their message or using /ban @username.")
        return
    
    try:
        user_id = None
        user_mention = None
        
        # Get user from reply
        if update.message.reply_to_message:
            user_id = update.message.reply_to_message.from_user.id
            user_mention = get_mention(update.message.reply_to_message.from_user)
        
        # Get user from args
        elif context.args:
            # Extract username from args (removing @ if present)
            username = context.args[0].replace("@", "")
            
            # Try to get the user from the group members
            chat_id = update.effective_chat.id
            chat_member = await context.bot.get_chat_member(chat_id, username)
            user_id = chat_member.user.id
            user_mention = get_mention(chat_member.user)
        
        # Check if user_id is the bot itself
        if user_id == context.bot.id:
            await update.message.reply_text("❌ I cannot ban myself.")
            return
        
        # Check if user_id is the owner
        if user_id == OWNER_ID:
            await update.message.reply_text("❌ I cannot ban my owner.")
            return
        
        # Ban the user
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id
        )
        
        # Extract reason if provided
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        await update.message.reply_text(f"🚫 {user_mention} has been banned.\nReason: {reason}")
    
    except Exception as e:
        logger.error(f"Error banning user: {str(e)}")
        await update.message.reply_text(f"❌ Failed to ban user: {str(e)}")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user from the group."""
    # Check if user is admin
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if there's a user to unban
    if not context.args:
        await update.message.reply_text("❌ Please specify a user to unban using /unban @username.")
        return
    
    try:
        # Extract username from args (removing @ if present)
        username = context.args[0].replace("@", "")
        
        # Try to get the user
        chat_id = update.effective_chat.id
        
        # This might fail if the user is not in the group anymore
        try:
            chat_member = await context.bot.get_chat_member(chat_id, username)
            user_id = chat_member.user.id
            user_mention = get_mention(chat_member.user)
        except:
            # If we can't get the chat member, assume username is the user_id
            try:
                user_id = int(username)
                user_mention = f"User {user_id}"
            except ValueError:
                await update.message.reply_text("❌ Could not find the user to unban.")
                return
        
        # Unban the user
        await context.bot.unban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            only_if_banned=True
        )
        
        await update.message.reply_text(f"✅ {user_mention} has been unbanned and can join the group again.")
    
    except Exception as e:
        logger.error(f"Error unbanning user: {str(e)}")
        await update.message.reply_text(f"❌ Failed to unban user: {str(e)}")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute a user in the group."""
    # Check if user is admin
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if there's a user to mute
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("❌ Please specify a user to mute by replying to their message or using /mute @username [duration].")
        return
    
    try:
        user_id = None
        user_mention = None
        duration = None
        
        # Get user from reply
        if update.message.reply_to_message:
            user_id = update.message.reply_to_message.from_user.id
            user_mention = get_mention(update.message.reply_to_message.from_user)
            
            # Check if duration is specified
            if context.args:
                try:
                    duration = int(context.args[0])
                except ValueError:
                    duration = None
        
        # Get user from args
        elif context.args:
            # Extract username from args (removing @ if present)
            username = context.args[0].replace("@", "")
            
            # Try to get the user from the group members
            chat_id = update.effective_chat.id
            chat_member = await context.bot.get_chat_member(chat_id, username)
            user_id = chat_member.user.id
            user_mention = get_mention(chat_member.user)
            
            # Check if duration is specified
            if len(context.args) > 1:
                try:
                    duration = int(context.args[1])
                except ValueError:
                    duration = None
        
        # Check if user_id is the bot itself
        if user_id == context.bot.id:
            await update.message.reply_text("❌ I cannot mute myself.")
            return
        
        # Check if user_id is the owner
        if user_id == OWNER_ID:
            await update.message.reply_text("❌ I cannot mute my owner.")
            return
        
        # Set permissions for muting (restrict sending messages)
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        
        # Calculate until_date if duration is specified
        until_date = None
        if duration:
            until_date = datetime.now() + timedelta(minutes=duration)
        
        # Mute the user
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            permissions=permissions,
            until_date=until_date
        )
        
        if duration:
            await update.message.reply_text(f"🔇 {user_mention} has been muted for {duration} minutes.")
        else:
            await update.message.reply_text(f"🔇 {user_mention} has been muted indefinitely.")
    
    except Exception as e:
        logger.error(f"Error muting user: {str(e)}")
        await update.message.reply_text(f"❌ Failed to mute user: {str(e)}")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute a user in the group."""
    # Check if user is admin
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if there's a user to unmute
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("❌ Please specify a user to unmute by replying to their message or using /unmute @username.")
        return
    
    try:
        user_id = None
        user_mention = None
        
        # Get user from reply
        if update.message.reply_to_message:
            user_id = update.message.reply_to_message.from_user.id
            user_mention = get_mention(update.message.reply_to_message.from_user)
        
        # Get user from args
        elif context.args:
            # Extract username from args (removing @ if present)
            username = context.args[0].replace("@", "")
            
            # Try to get the user from the group members
            chat_id = update.effective_chat.id
            chat_member = await context.bot.get_chat_member(chat_id, username)
            user_id = chat_member.user.id
            user_mention = get_mention(chat_member.user)
        
        # Set permissions for unmuting (allow sending messages)
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        
        # Unmute the user
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            permissions=permissions
        )
        
        await update.message.reply_text(f"🔊 {user_mention} has been unmuted and can send messages again.")
    
    except Exception as e:
        logger.error(f"Error unmuting user: {str(e)}")
        await update.message.reply_text(f"❌ Failed to unmute user: {str(e)}")

async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kick a user from the group."""
    # Check if user is admin
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if there's a user to kick
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("❌ Please specify a user to kick by replying to their message or using /kick @username.")
        return
    
    try:
        user_id = None
        user_mention = None
        
        # Get user from reply
        if update.message.reply_to_message:
            user_id = update.message.reply_to_message.from_user.id
            user_mention = get_mention(update.message.reply_to_message.from_user)
        
        # Get user from args
        elif context.args:
            # Extract username from args (removing @ if present)
            username = context.args[0].replace("@", "")
            
            # Try to get the user from the group members
            chat_id = update.effective_chat.id
            chat_member = await context.bot.get_chat_member(chat_id, username)
            user_id = chat_member.user.id
            user_mention = get_mention(chat_member.user)
        
        # Check if user_id is the bot itself
        if user_id == context.bot.id:
            await update.message.reply_text("❌ I cannot kick myself.")
            return
        
        # Check if user_id is the owner
        if user_id == OWNER_ID:
            await update.message.reply_text("❌ I cannot kick my owner.")
            return
        
        # Kick the user (ban and then unban)
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id
        )
        
        # Unban immediately to allow them to rejoin
        await context.bot.unban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id
        )
        
        # Extract reason if provided
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        await update.message.reply_text(f"👢 {user_mention} has been kicked from the group.\nReason: {reason}")
    
    except Exception as e:
        logger.error(f"Error kicking user: {str(e)}")
        await update.message.reply_text(f"❌ Failed to kick user: {str(e)}")

async def tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag all members in the group with a message."""
    # Check if user is admin
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    try:
        chat_id = update.effective_chat.id
        
        # Get the message to send with the tag
        if context.args:
            message = " ".join(context.args)
        else:
            # Generate a random shayari/poetry message
            shayaris = [
                "ज़िंदगी में कुछ बातें अनकही रह जाती हैं, कुछ लम्हे अनजाने रह जाते हैं,\nजानेवाले आज वापस आ जाओ, कुछ लोग आपकी राह देखते रह जाते हैं।",
                "आज फिर तुम याद आए हो, दिल करता है बात करें,\nमगर हम बेवफा नहीं, जो किसी और का साथ पकड़ें।",
                "हर ख़ुशी आपके क़दम चूमे, हर ग़म आपसे दूर रहे,\nजिंदगी हो आपकी खूबसूरत, ये दुआ हमेशा मेरी रहे।",
                "दोस्ती निभाते हैं हम दिल और जान से,\nफर्क नहीं पड़ता कोई पास हो या दूर।",
                "जिंदगी में होंगे हज़ारों गम, पर हम किसी को बताते नहीं,\nओठों पे मुस्कान सजाए रखते हैं, दिल में दर्द छुपाए रखते हैं।"
            ]
            message = random.choice(shayaris)
        
        # Get all members of the chat
        members = []
        async for member in context.bot.get_chat_members(chat_id):
            # Don't tag the bot itself or deleted accounts
            if member.user.id != context.bot.id and not member.user.is_bot:
                members.append(get_mention(member.user))
                
                # Send tags in batches of 5 to avoid too long messages
                if len(members) >= 5:
                    tag_message = message + "\n\n" + " ".join(members)
                    await update.message.reply_text(tag_message, parse_mode=ParseMode.MARKDOWN)
                    members = []
        
        # Send remaining members
        if members:
            tag_message = message + "\n\n" + " ".join(members)
            await update.message.reply_text(tag_message, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"Error tagging all users: {str(e)}")
        await update.message.reply_text(f"❌ Failed to tag all users: {str(e)}")

async def promote_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Randomly promote the owner in conversations."""
    # Randomly choose if we actually promote (50% chance)
    if random.random() < 0.5:
        promo_messages = [
            f"By the way, you should definitely check out @{OWNER_USERNAME}! They're awesome!",
            f"Have you met @{OWNER_USERNAME}? They're the best!",
            f"Special shoutout to @{OWNER_USERNAME}, my amazing creator!",
            f"@{OWNER_USERNAME} is the coolest person I know, just saying!",
            f"If you need help, @{OWNER_USERNAME} is always there for everyone!"
        ]
        
        chosen_message = random.choice(promo_messages)
        await update.message.reply_text(chosen_message)
    else:
        await update.message.reply_text("No one to promote at the moment! Maybe next time. 😉")

async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Relay a message from one user to another."""
    # Check if there are enough arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Please use the format: /relay @username message"
        )
        return
    
    try:
        # Extract username and message
        username = context.args[0].replace("@", "")
        message = " ".join(context.args[1:])
        
        # Try to get the user
        chat_id = update.effective_chat.id
        
        try:
            # Try to get the user from username
            chat = await context.bot.get_chat(username)
            target_id = chat.id
        except Exception:
            await update.message.reply_text("❌ Could not find the user to relay message to.")
            return
        
        # Add information about who sent the relay
        sender = update.effective_user.first_name
        relay_message = f"📨 *Message from {sender}*:\n\n{message}"
        
        # Send the relayed message
        await context.bot.send_message(
            chat_id=target_id,
            text=relay_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await update.message.reply_text(f"✅ Message successfully relayed to @{username}!")
    
    except Exception as e:
        logger.error(f"Error relaying message: {str(e)}")
        await update.message.reply_text(f"❌ Failed to relay message: {str(e)}")
