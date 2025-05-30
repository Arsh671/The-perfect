# Bestie AI - Advanced Telegram Chatbot

A sophisticated multi-feature Telegram bot with flirty female AI personality, voice capabilities, group management tools, utility features, games, and admin panel.

## Features

- **Conversational AI**: Human-like conversations using Groq LLM API
- **Multi-language Support**: Responds in English, Hindi, and other languages
- **Voice Messages**: Text-to-speech capabilities for voice interactions
- **Group Management**: Admin commands for managing Telegram groups
- **Games**: Interactive games including Tic-Tac-Toe, Truth or Dare, and Guess games
- **Advanced Caching**: Optimized caching system to minimize API usage
- **Content Moderation**: Built-in content filtering for appropriate conversations
- **Owner Admin Tools**: Global broadcast, ban controls, and statistics

## Requirements

- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Groq API keys (5 recommended for key rotation)
- Internet connection

## How to Install

### On Termux (Android)

1. Install Termux from F-Droid (recommended) or Google Play Store
2. Open Termux and run the following commands:

```bash
# Update packages
pkg update && pkg upgrade

# Install required packages
pkg install python git

# Clone the repository
git clone https://github.com/yourusername/bestie-ai-bot.git
cd bestie-ai-bot

# Install Python dependencies
pip install -r requirements.txt

# Configure your bot (update config.py with your bot token and API keys)
nano bot/config.py

# Make launcher script executable
chmod +x run_bot.sh

# Start the bot
./run_bot.sh start
```

### On Heroku

See [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md) for detailed instructions.

### On Railway

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed instructions.

## Configuration

The main configuration is in `bot/config.py`. Important settings include:

- `BOT_TOKEN`: Your Telegram bot token
- `OWNER_ID`: Your Telegram user ID for admin access
- `GROQ_API_KEYS`: List of your Groq API keys for rotation
- `AI_MODELS`: The AI models to use (default and backup)
- `BOT_PERSONALITY`: Personality settings for the AI
- `FEATURES`: Enable/disable specific features

## Usage

### Launcher Script

The included `run_bot.sh` script makes it easy to manage the bot:

```bash
# Start the bot
./run_bot.sh start

# Stop the bot
./run_bot.sh stop

# Restart the bot
./run_bot.sh restart

# Check bot status
./run_bot.sh status

# View recent logs
./run_bot.sh logs
```

### Bot Commands

The bot supports the following commands:

- `/start` - Start the bot
- `/help` - Get help information
- `/voice [text]` - Convert text to voice message
- `/name` - Generate stylish name suggestions
- `/bio` - Generate profile bio suggestions
- `/game` - Play games
- `/stats` - View your statistics

### Group Admin Commands

- `/ban` - Ban a user from the group
- `/unban` - Unban a user from the group
- `/mute` - Mute a user in the group
- `/unmute` - Unmute a user in the group
- `/kick` - Kick a user from the group
- `/masstag` - Tag all users in a group with a message

### Owner Commands

- `/broadcast` - Send a message to all users/groups
- `/gban` - Globally ban a user
- `/logging` - Toggle message logging
- `/adminstats` - View detailed admin statistics

## Optimization for Long-term Use

This bot is designed for 100,000+ users over 10+ years with only 5 API keys through:

1. **Multi-level Caching**: Responses are cached to minimize API calls
2. **API Key Rotation**: Keys are rotated to avoid rate limits
3. **Selective Responses**: In groups, the bot only responds when mentioned
4. **Idle Mode**: During low-usage hours, proactive messages are disabled

## Troubleshooting

Common issues and solutions:

- **Bot not responding**: Check if the bot is running with `./run_bot.sh status`
- **API errors**: Verify your Groq API keys are valid
- **Database errors**: Check the database file permissions
- **Memory issues on Termux**: Close other apps and restart Termux

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Python Telegram Bot: https://github.com/python-telegram-bot/python-telegram-bot
- Groq AI: https://groq.com
- gTTS for voice conversion: https://gtts.readthedocs.io

## Contact

For support or questions, contact the owner through Telegram: @fakesoul15
Support Group: https://t.me/+5e44PSnDdFNlMGM1
Support Channel: https://t.me/promotionandsupport