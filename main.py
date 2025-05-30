#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Telegram Bot
"""

import logging
import asyncio
import threading
import os
from bot import create_bot

# Import the Flask app for gunicorn when running in web mode
from app import app, start_bot, create_templates_directory, create_index_template

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Initialize any required directories and templates
create_templates_directory()
create_index_template()

if __name__ == '__main__':
    logger.info("Starting bot...")
    bot = create_bot()
    
    # Check if this is being run as a web server or standalone bot
    if os.environ.get('GUNICORN_RUNNING') == 'TRUE':
        # When running under gunicorn, we'll let the app.py handle starting the bot
        pass
    else:
        # Running as standalone bot
        try:
            asyncio.run(bot.run_polling())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
