#!/bin/bash

# Telegram Bot Launcher Script
# For use in Termux, Heroku, Railway or similar environments

# Directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if the bot is running
is_bot_running() {
    pgrep -f "python main.py" > /dev/null
    return $?
}

# Function to start the bot
start_bot() {
    echo -e "${YELLOW}Starting Telegram bot...${NC}"
    
    # Check if already running
    if is_bot_running; then
        echo -e "${RED}Bot is already running!${NC}"
        return 1
    fi
    
    # Run the bot in the background
    nohup python main.py > bot.log 2>&1 &
    
    # Wait a moment to check if it started
    sleep 2
    
    # Verify it's running
    if is_bot_running; then
        echo -e "${GREEN}Bot started successfully!${NC}"
        echo -e "${BLUE}Logs are being written to bot.log${NC}"
        return 0
    else
        echo -e "${RED}Failed to start bot. Check bot.log for errors.${NC}"
        return 1
    fi
}

# Function to stop the bot
stop_bot() {
    echo -e "${YELLOW}Stopping Telegram bot...${NC}"
    
    # Check if it's running
    if ! is_bot_running; then
        echo -e "${RED}Bot is not running!${NC}"
        return 1
    fi
    
    # Kill the process
    pkill -f "python main.py"
    
    # Wait a moment to check if it stopped
    sleep 2
    
    # Verify it stopped
    if ! is_bot_running; then
        echo -e "${GREEN}Bot stopped successfully!${NC}"
        return 0
    else
        echo -e "${RED}Failed to stop bot. You may need to kill it manually.${NC}"
        return 1
    fi
}

# Function to check status
status_bot() {
    if is_bot_running; then
        echo -e "${GREEN}Bot is running!${NC}"
        
        # Get PID and uptime
        PID=$(pgrep -f "python main.py")
        if [ -n "$PID" ]; then
            START_TIME=$(ps -o lstart= -p "$PID")
            echo -e "${BLUE}Process ID: ${NC}$PID"
            echo -e "${BLUE}Started at: ${NC}$START_TIME"
        fi
    else
        echo -e "${RED}Bot is not running!${NC}"
    fi
}

# Function to view logs
view_logs() {
    if [ -f "bot.log" ]; then
        echo -e "${YELLOW}Last 20 lines of bot.log:${NC}"
        tail -n 20 bot.log
    else
        echo -e "${RED}No log file found!${NC}"
    fi
}

# Process command line argument
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        stop_bot
        sleep 2
        start_bot
        ;;
    status)
        status_bot
        ;;
    logs)
        view_logs
        ;;
    *)
        echo -e "${YELLOW}Bestie AI Telegram Bot Manager${NC}"
        echo -e "${BLUE}Usage:${NC}"
        echo -e "  $0 ${GREEN}start${NC}   - Start the bot"
        echo -e "  $0 ${GREEN}stop${NC}    - Stop the bot"
        echo -e "  $0 ${GREEN}restart${NC} - Restart the bot"
        echo -e "  $0 ${GREEN}status${NC}  - Check bot status"
        echo -e "  $0 ${GREEN}logs${NC}    - View recent logs"
        ;;
esac

exit 0