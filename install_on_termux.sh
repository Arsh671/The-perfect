#!/bin/bash

# Bestie AI Telegram Bot - Termux Installation Script
# This script will help you install and configure the bot on Termux

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Bestie AI Telegram Bot - Termux Installation ===${NC}"
echo ""

# Step 1: Update Termux packages
echo -e "${BLUE}Step 1: Updating Termux packages...${NC}"
pkg update -y && pkg upgrade -y
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to update Termux packages. Please try again later.${NC}"
    exit 1
fi
echo -e "${GREEN}Termux packages updated successfully!${NC}"
echo ""

# Step 2: Install required packages
echo -e "${BLUE}Step 2: Installing required packages...${NC}"
pkg install -y python git
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install required packages. Please try again later.${NC}"
    exit 1
fi
echo -e "${GREEN}Required packages installed successfully!${NC}"
echo ""

# Step 3: Create Python virtual environment
echo -e "${BLUE}Step 3: Creating Python virtual environment...${NC}"
python -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Virtual environment creation failed. Continuing without it...${NC}"
else
    echo -e "${GREEN}Virtual environment created successfully!${NC}"
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
fi
echo ""

# Step 4: Install Python dependencies
echo -e "${BLUE}Step 4: Installing Python dependencies...${NC}"
pip install python-telegram-bot[job-queue] httpx gtts langdetect
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install Python dependencies. Please try again later.${NC}"
    exit 1
fi
echo -e "${GREEN}Python dependencies installed successfully!${NC}"
echo ""

# Step 5: Prompt for Bot Token
echo -e "${BLUE}Step 5: Configuration${NC}"
echo -e "${YELLOW}Please enter your Telegram Bot Token (from @BotFather):${NC}"
read bot_token

# Step 6: Prompt for Groq API Keys
echo -e "${YELLOW}Please enter your Groq API Keys (up to 5, one per line):${NC}"
echo -e "${YELLOW}When done, press Enter on a blank line to continue.${NC}"
api_keys=()
while true; do
    read api_key
    if [ -z "$api_key" ]; then
        break
    fi
    api_keys+=("$api_key")
done

# Step 7: Prompt for Owner ID
echo -e "${YELLOW}Please enter your Telegram User ID (for bot owner access):${NC}"
read owner_id

# Step 8: Prompt for Owner Username
echo -e "${YELLOW}Please enter your Telegram Username (without @):${NC}"
read owner_username

# Step 9: Update configuration file
echo -e "${BLUE}Step 9: Updating configuration file...${NC}"
if [ -f "bot/config.py" ]; then
    # Backup original config
    cp bot/config.py bot/config.py.bak
    
    # Update Bot Token
    sed -i "s/BOT_TOKEN = \".*\"/BOT_TOKEN = \"$bot_token\"/" bot/config.py
    
    # Update Owner ID
    sed -i "s/OWNER_ID = [0-9]*/OWNER_ID = $owner_id/" bot/config.py
    
    # Update Owner Username
    sed -i "s/OWNER_USERNAME = \".*\"/OWNER_USERNAME = \"$owner_username\"/" bot/config.py
    
    # Update API Keys
    api_keys_str="GROQ_API_KEYS = [\n"
    for key in "${api_keys[@]}"; do
        api_keys_str+="    \"$key\",\n"
    done
    api_keys_str+="]\n"
    
    # Use awk to replace the API keys section
    awk -v keys="$api_keys_str" '
    /GROQ_API_KEYS = \[/,/\]/ {
        if (!printed) {
            print keys;
            printed=1;
        }
        if (/\]/) {
            printed=0;
            next;
        }
        next;
    }
    { print }
    ' bot/config.py > bot/config.py.new
    
    mv bot/config.py.new bot/config.py
    
    echo -e "${GREEN}Configuration file updated successfully!${NC}"
else
    echo -e "${RED}Configuration file not found. Please check your installation.${NC}"
    exit 1
fi
echo ""

# Step 10: Make scripts executable
echo -e "${BLUE}Step 10: Making scripts executable...${NC}"
chmod +x run_bot.sh
echo -e "${GREEN}Scripts are now executable!${NC}"
echo ""

# Step 11: Install complete
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo -e "${YELLOW}To start the bot, run:${NC}"
echo -e "${BLUE}./run_bot.sh start${NC}"
echo ""
echo -e "${YELLOW}To check the bot status, run:${NC}"
echo -e "${BLUE}./run_bot.sh status${NC}"
echo ""
echo -e "${YELLOW}To view the logs, run:${NC}"
echo -e "${BLUE}./run_bot.sh logs${NC}"
echo ""
echo -e "${GREEN}Thank you for installing Bestie AI Telegram Bot!${NC}"
echo -e "${GREEN}Support Group: https://t.me/+5e44PSnDdFNlMGM1${NC}"
echo -e "${GREEN}Support Channel: https://t.me/promotionandsupport${NC}"
echo -e "${GREEN}Contact: @fakesoul15${NC}"