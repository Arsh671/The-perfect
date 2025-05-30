from telegram.ext import Application
from bot.handlers.conversation import register_conversation_handlers
from bot.handlers.group_admin import register_group_admin_handlers
from bot.handlers.utility import register_utility_handlers
from bot.handlers.games import register_game_handlers
from bot.handlers.owner import register_owner_handlers
import logging

logger = logging.getLogger(__name__)

def register_handlers(application: Application):
    """Register all handlers with the application."""
    logger.info("Registering handlers...")
    
    # Register conversation handlers
    register_conversation_handlers(application)
    
    # Register group admin handlers
    register_group_admin_handlers(application)
    
    # Register utility handlers
    register_utility_handlers(application)
    
    # Register game handlers
    register_game_handlers(application)
    
    # Register owner handlers
    register_owner_handlers(application)
    
    logger.info("All handlers registered successfully")
