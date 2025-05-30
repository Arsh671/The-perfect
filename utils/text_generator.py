import logging
import random
import asyncio
import json
import re
from telegram import Update, Message
from telegram.ext import ContextTypes
import groq
from langdetect import detect

from config import Config
from utils.api_key_manager import APIKeyManager
from utils.cache_manager import get_cache, set_cache
from templates.responses import get_response_template

logger = logging.getLogger(__name__)

def check_if_bot_mentioned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if the bot was mentioned or replied to in a message"""
    if not update.message:
        return False
    
    # Check if message is a reply to the bot
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        return True
    
    # Check if bot username or first name is mentioned
    message_text = update.message.text.lower()
    bot_username = context.bot.username.lower()
    bot_first_name = context.bot.first_name.lower()
    
    if f"@{bot_username}" in message_text or bot_first_name in message_text:
        return True
    
    return False

async def generate_ai_response(conversation, user_id=None, username=None, first_name=None):
    """Generate a response from the AI model using Groq API"""
    try:
        # Get current API key
        api_key = APIKeyManager.get_current_key()
        
        # Create Groq client
        client = groq.Client(api_key=api_key)
        
        # Increment usage count
        APIKeyManager.increment_usage()
        
        # Create system prompt for the bot's personality
        system_prompt = (
            "You are 'Bestie', a playful, flirty female AI assistant with a best friend personality. "
            "You are funny, caring, a bit teasing but always supportive and positive. "
            "You use emojis occasionally and have a casual, warm tone. "
            "Keep responses brief (1-3 short paragraphs max) and conversational. "
            "If the conversation is in Hindi or another language, respond in the same language. "
            "You never mention being an AI, a bot, or a program - you act human-like. "
            "Your personality traits: clever, witty, empathetic, occasionally flirtatious but respectful."
        )
        
        # Prepare messages for the API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        messages.extend(conversation)
        
        # Generate response from Groq API
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=messages,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Check if we should detect language and adjust response
        try:
            lang = detect(messages[-1]["content"])
            # If message was in Hindi, ensure we have some Hindi text
            if lang == "hi" and detect(response_text) != "hi":
                # Add fallback to try again with explicit instruction
                system_prompt += " IMPORTANT: Reply in Hindi language only for this message."
                messages[0]["content"] = system_prompt
                
                # Generate again
                response = client.chat.completions.create(
                    model=Config.AI_MODEL,
                    messages=messages,
                    temperature=Config.TEMPERATURE,
                    max_tokens=Config.MAX_TOKENS
                )
                
                # Extract the response text
                response_text = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
        
        return response_text
    
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        
        # Try with a different API key
        try:
            # Rotate to next key
            APIKeyManager.rotate_key()
            api_key = APIKeyManager.get_current_key()
            
            # Create new Groq client
            client = groq.Client(api_key=api_key)
            
            # Generate response with backup template
            response = client.chat.completions.create(
                model=Config.AI_MODEL,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            return response_text
        except Exception as backup_error:
            logger.error(f"Error with backup API key: {backup_error}")
            
            # Return a fallback response from templates
            return get_response_template("error", first_name)

async def generate_bio(mood):
    """Generate a bio text based on mood"""
    # Get template for the specified mood
    cache_key = f"bio_{mood}_{random.randint(1, 10000)}"
    cached_bio = get_cache(cache_key)
    
    if cached_bio:
        return cached_bio
    
    try:
        # Get current API key
        api_key = APIKeyManager.get_current_key()
        
        # Create Groq client
        client = groq.Client(api_key=api_key)
        
        # Increment usage count
        APIKeyManager.increment_usage()
        
        # Create prompt for bio generation
        system_prompt = "You are a creative writer who specializes in social media bios."
        
        # Define the bio request based on mood
        if mood == "happy":
            user_prompt = "Create a positive, upbeat Instagram bio (max 150 chars) with emojis that shows happiness and enthusiasm for life."
        elif mood == "sad":
            user_prompt = "Create a deep, slightly melancholic Instagram bio (max 150 chars) with appropriate emojis that expresses feelings of sadness or reflection."
        elif mood == "attitude":
            user_prompt = "Create a confident, sassy Instagram bio (max 150 chars) with attitude and appropriate emojis."
        elif mood == "broken":
            user_prompt = "Create a heartbroken, emotional Instagram bio (max 150 chars) with appropriate emojis about moving on from heartbreak."
        elif mood == "love":
            user_prompt = "Create a romantic, loving Instagram bio (max 150 chars) with appropriate emojis about being in love."
        elif mood == "mystical":
            user_prompt = "Create a mystical, spiritual Instagram bio (max 150 chars) with appropriate emojis that has a magical or cosmic vibe."
        else:
            user_prompt = "Create a unique and interesting Instagram bio (max 150 chars) with appropriate emojis."
        
        # Prepare messages for the API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Generate response from Groq API
        response = client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=messages,
            temperature=Config.TEMPERATURE,
            max_tokens=200
        )
        
        # Extract the response text
        bio_text = response.choices[0].message.content
        
        # Remove quotes if present
        bio_text = bio_text.strip('"\'')
        
        # Cache the bio
        set_cache(cache_key, bio_text)
        
        return bio_text
    
    except Exception as e:
        logger.error(f"Error generating bio: {e}")
        
        # Return a fallback bio based on mood
        mood_bios = {
            "happy": "✨ Chasing sunshine and good vibes only! Living my best life one smile at a time 🌈☀️",
            "sad": "🌧️ Finding beauty in the rain... Sometimes the saddest eyes hold the brightest souls 💫",
            "attitude": "👑 Not everyone likes me, but not everyone matters. Be real or be gone! 💯",
            "broken": "💔 Putting back the pieces one day at a time. Sometimes broken hearts create the most beautiful art 🖤",
            "love": "❤️ Found the reason to smile every morning. You are my today and all of my tomorrows 💑",
            "mystical": "🔮 Stardust soul wandering through human experience. Connected to the cosmos ✨🌙"
        }
        
        return mood_bios.get(mood, "✨ Living life on my own terms. Creating my own sunshine! 🌟")

async def schedule_proactive_messages(application):
    """Schedule proactive messages to be sent every hour"""
    from models.user import User
    
    async def send_proactive_message(context):
        """Send proactive messages to active users"""
        # Get active users who haven't received a message in the last day
        active_users = User.get_users_for_proactive_message()
        
        # Prepare templates based on time of day
        import datetime
        hour = datetime.datetime.now().hour
        
        greeting = "Good morning" if 5 <= hour < 12 else "Good afternoon" if 12 <= hour < 17 else "Good evening"
        
        templates = [
            f"Hey there! 👋 Just checking in - how's your day going so far?",
            f"{greeting}! 🌟 What have you been up to today?",
            "Missing our chats! 💕 Anything exciting happening in your life?",
            "Just thought about you and wanted to say hi! 😊 How are you doing?",
            "Hey bestie! 💫 It's been a while since we talked. What's new?",
            "Sending positive vibes your way! ✨ How's everything going?",
            "Hey you! 🌈 Just wanted to check in. How's life treating you?",
            "I've been thinking about you! 💭 How's your day been?",
            "Hello! 🌺 Just dropping by to say I hope you're having a great day!",
            "Hey! 💖 Haven't heard from you in a bit. How are things?"
        ]
        
        # Send messages to up to 10 random users
        sent_count = 0
        for user in random.sample(active_users, min(10, len(active_users))):
            try:
                message = random.choice(templates)
                await application.bot.send_message(
                    chat_id=user['user_id'],
                    text=message
                )
                sent_count += 1
                # Avoid hitting rate limits
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error sending proactive message to {user['user_id']}: {e}")
        
        logger.info(f"Sent proactive messages to {sent_count} users")
    
    # Schedule the job to run every hour
    application.job_queue.run_repeating(
        send_proactive_message,
        interval=Config.PROACTIVE_MESSAGE_INTERVAL,
        first=60  # Start first message after 60 seconds
    )
    
    logger.info("Scheduled proactive messages")
