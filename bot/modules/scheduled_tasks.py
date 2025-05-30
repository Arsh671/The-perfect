import logging
import asyncio
import random
from datetime import datetime, time
from telegram.ext import Application, ContextTypes
from bot.modules.ai_service import get_ai_response
from bot.modules.db import get_all_users, get_all_groups
from bot.config import ENABLE_PROACTIVE_MESSAGES, OWNER_ID

logger = logging.getLogger(__name__)

def register_scheduled_tasks(application: Application):
    """Register all scheduled tasks."""
    if ENABLE_PROACTIVE_MESSAGES:
        # Schedule proactive messages every hour
        application.job_queue.run_repeating(send_proactive_messages, interval=3600, first=10)
    
    # Schedule daily stats report for owner
    application.job_queue.run_daily(
        send_daily_stats,
        time=time(hour=0, minute=0, second=0),  # Midnight
        chat_id=OWNER_ID
    )

async def send_proactive_messages(context: ContextTypes.DEFAULT_TYPE):
    """Send proactive messages to random users."""
    try:
        # Get all users
        users = await get_all_users()
        
        if not users:
            logger.info("No users to send proactive messages to")
            return
        
        # Select a random subset of users (max 10% or 5 users, whichever is smaller)
        max_users = min(5, max(1, int(len(users) * 0.1)))
        selected_users = random.sample(users, min(max_users, len(users)))
        
        # Current hour
        current_hour = datetime.now().hour
        
        for user in selected_users:
            user_id = user['user_id']
            first_name = user['first_name'] or "there"
            
            # Skip the owner to avoid annoying them
            if user_id == OWNER_ID:
                continue
            
            # Generate a contextual greeting based on time of day
            greeting = get_time_greeting(current_hour)
            
            # Create a prompt for the AI
            prompt = f"Generate a short, friendly message to {first_name} as a proactive check-in. Time context: {greeting}. Keep it brief, casual, and engaging. Ask an open-ended but simple question to encourage response."
            
            try:
                # Get AI response
                message = await get_ai_response(prompt, [], "en")
                
                # Send the message
                await context.bot.send_message(chat_id=user_id, text=message)
                logger.info(f"Sent proactive message to user {user_id}")
                
                # Wait a bit between messages to avoid rate limits
                await asyncio.sleep(2)
            
            except Exception as e:
                logger.error(f"Error sending proactive message to user {user_id}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in proactive messaging task: {str(e)}")

async def send_daily_stats(context: ContextTypes.DEFAULT_TYPE):
    """Send daily statistics to the owner."""
    try:
        from bot.modules.db import get_user_count, get_group_count, get_banned_users
        
        # Get stats
        user_count = await get_user_count()
        group_count = await get_group_count()
        banned_count = len(await get_banned_users())
        
        # Calculate new users and groups in the last 24 hours
        # (This would require storing the previous counts, which we don't do here)
        
        # Create stats message
        stats_message = (
            "📊 *Daily Bot Statistics* 📊\n\n"
            f"👤 Total Users: {user_count}\n"
            f"👥 Total Groups: {group_count}\n"
            f"🚫 Banned Users: {banned_count}\n\n"
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Send the stats to the owner
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=stats_message,
            parse_mode='Markdown'
        )
        
        logger.info("Sent daily stats to the owner")
    
    except Exception as e:
        logger.error(f"Error in daily stats task: {str(e)}")

def get_time_greeting(hour):
    """Get a greeting based on the time of day."""
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 22:
        return "Good evening"
    else:
        return "Hello"
