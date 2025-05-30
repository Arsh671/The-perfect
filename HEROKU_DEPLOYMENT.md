# Deploying Bestie AI Telegram Bot to Heroku

This guide will walk you through deploying the Bestie AI Telegram Bot to Heroku, a cloud platform as a service that enables you to run the bot in the cloud.

## Prerequisites

1. A Heroku account (sign up at [heroku.com](https://heroku.com) if you don't have one)
2. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed on your computer
3. [Git](https://git-scm.com/downloads) installed on your computer
4. Your Telegram Bot Token (from [@BotFather](https://t.me/botfather))
5. Your Groq API keys (5 recommended for key rotation)

## Step 1: Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/bestie-ai-bot.git
cd bestie-ai-bot
```

## Step 2: Create a Heroku App

Create a new Heroku app using the Heroku CLI:

```bash
heroku login
heroku create your-bot-name
```

Replace `your-bot-name` with a unique name for your Heroku app.

## Step 3: Configure Environment Variables

Set up the necessary environment variables for your bot:

```bash
# Set your bot token
heroku config:set BOT_TOKEN="your_telegram_bot_token"

# Set your Groq API keys (comma-separated)
heroku config:set GROQ_API_KEYS="key1,key2,key3,key4,key5"

# Set your owner ID and username
heroku config:set OWNER_ID="your_telegram_user_id"
heroku config:set OWNER_USERNAME="your_telegram_username"

# Optional: Set other configuration values
heroku config:set SUPPORT_GROUP="https://t.me/yoursupportgroup"
heroku config:set SUPPORT_CHANNEL="https://t.me/yoursupportchannel"
```

## Step 4: Deploy to Heroku

Push your code to Heroku:

```bash
git push heroku main
```

If your main branch is called `master` instead of `main`, use:

```bash
git push heroku master
```

## Step 5: Scale the Dynos

Heroku uses "dynos" which are like containerized processes. You need to enable both the web and worker processes:

```bash
# Enable the web process to serve the status dashboard
heroku ps:scale web=1

# Enable the worker process to run the bot
heroku ps:scale worker=1
```

## Step 6: Verify Deployment

Check the logs to make sure everything is running:

```bash
heroku logs --tail
```

Look for messages indicating that the bot has started successfully.

## Step 7: Access the Web Dashboard

You can access the web dashboard for your bot at:

```
https://your-bot-name.herokuapp.com/
```

This dashboard shows the bot's status, uptime, and other information.

## Common Issues and Troubleshooting

### Bot Not Starting

If the bot doesn't start, check the logs with:

```bash
heroku logs --tail
```

Common issues include:
- Invalid bot token
- Invalid Groq API keys
- Errors in the code

### Dyno Hours Limit

Free Heroku accounts have a limit of 550 dyno hours per month. Since you're running two dynos (web and worker), you'll use about 1,100 hours per month, which exceeds the free tier.

Solutions:
1. Add a credit card to your Heroku account to get 1,000 free dyno hours
2. Consider upgrading to a paid plan
3. Use an alternative hosting solution

### Bot Goes to Sleep

Heroku free tier dynos go to sleep after 30 minutes of inactivity. To keep the bot awake:

1. Add your app to a service like [UptimeRobot](https://uptimerobot.com/) to ping it every few minutes
2. Consider a paid Heroku plan to avoid sleeping dynos

## Advanced Configuration

### Custom Domain

To use a custom domain for your bot's dashboard:

```bash
heroku domains:add www.yourdomain.com
```

Follow the instructions provided by Heroku to configure your DNS settings.

### Database Persistence

By default, the bot uses SQLite which will be reset whenever Heroku rebuilds the dyno. For better persistence:

1. Add a PostgreSQL database:

```bash
heroku addons:create heroku-postgresql:hobby-dev
```

2. Update the bot's configuration to use the PostgreSQL URL:

```bash
heroku config:set USE_POSTGRES=true
```

## Maintenance

### Updating the Bot

To update the bot code:

1. Pull the latest changes from the repository
2. Push to Heroku:

```bash
git push heroku main
```

### Restarting the Bot

If you need to restart the bot:

```bash
heroku restart
```

### Viewing Logs

To view the most recent logs:

```bash
heroku logs
```

To continuously view logs:

```bash
heroku logs --tail
```

## Security Considerations

- Heroku environment variables are secure for storing your tokens and API keys
- Regularly rotate your Groq API keys for added security
- Consider setting up IP restrictions for your bot if available

## Additional Resources

- [Heroku Documentation](https://devcenter.heroku.com/)
- [Python Telegram Bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [Groq API Documentation](https://console.groq.com/docs)

For more help, join our support group: [https://t.me/+5e44PSnDdFNlMGM1](https://t.me/+5e44PSnDdFNlMGM1)