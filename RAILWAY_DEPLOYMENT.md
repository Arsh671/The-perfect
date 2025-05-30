# Deploying Bestie AI Telegram Bot to Railway

This guide will walk you through deploying the Bestie AI Telegram Bot to Railway, a modern cloud platform that makes deployment simple and efficient.

## Why Railway?

Railway offers several advantages over other platforms:
- Simple deployment process
- Free tier with generous resources
- No sleeping apps (unlike Heroku free tier)
- Easy environment variable management
- Automatic deployments from GitHub

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app) using GitHub)
2. Your Telegram Bot Token (from [@BotFather](https://t.me/botfather))
3. Your Groq API keys (5 recommended for key rotation)
4. GitHub account (to connect your repository)

## Step 1: Prepare Your Repository

If you haven't already, push your bot code to a GitHub repository:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/bestie-ai-bot.git
git push -u origin main
```

## Step 2: Create a New Project on Railway

1. Log in to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your GitHub repository
5. Railway will automatically detect the Procfile and start the deployment

## Step 3: Configure Environment Variables

1. Go to your project's "Variables" tab
2. Add the following environment variables:

```
BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEYS=key1,key2,key3,key4,key5
OWNER_ID=your_telegram_user_id
OWNER_USERNAME=your_telegram_username
SUPPORT_GROUP=https://t.me/yoursupportgroup
SUPPORT_CHANNEL=https://t.me/yoursupportchannel
```

## Step 4: Configure the Service

1. Go to your project's "Settings" tab
2. Under "Start Command", make sure it's set to use the Procfile
3. If needed, you can manually set:
   - For Web Service: `python app.py`
   - For Worker Service: `python main.py`

## Step 5: Verify Deployment

1. Go to the "Deployments" tab to check the deployment status
2. Check the logs to ensure the bot is running properly
3. If everything is working, you should see logs indicating successful startup

## Step 6: Access the Web Dashboard

1. Go to the "Settings" tab
2. Look for the "Domains" section
3. Railway should have automatically assigned a domain like `https://your-project-name.up.railway.app`
4. Visit this URL to see the bot status dashboard

## Step 7: Connect a Custom Domain (Optional)

1. In the "Settings" tab, find the "Domains" section
2. Click "Add Domain"
3. Enter your custom domain
4. Follow Railway's instructions to update your DNS settings

## Troubleshooting

### Bot Not Starting

If the bot doesn't start, check the logs for error messages. Common issues include:

- Invalid bot token
- Invalid Groq API keys
- Missing environment variables
- Errors in the code

### Database Persistence

Railway provides persistent storage by default, but you can add a dedicated database if needed:

1. Go to your project dashboard
2. Click "New"
3. Select "Database" then "PostgreSQL"
4. Once created, Railway will automatically add the database connection string to your environment variables

## Resource Management

Railway's free tier includes:

- $5 of free credits per month
- 512MB RAM per service
- 1GB of storage
- 100GB of outbound bandwidth

Monitor your usage in the Railway dashboard to avoid unexpected charges once free credits are used.

## Continuous Deployment

Railway automatically deploys when you push to your GitHub repository. To disable this:

1. Go to your project's "Settings" tab
2. Scroll to "Deployments"
3. Toggle off "Automatic Deployments"

## Monitoring and Scaling

### Monitoring

1. Use the "Metrics" tab to monitor your app's performance
2. Use the "Logs" tab to view real-time logs

### Scaling

If you need more resources:

1. Go to your project's "Settings" tab
2. Find the "Resources" section
3. Adjust the CPU and memory allocation as needed (note that this will affect billing)

## Security Considerations

- Railway securely stores your environment variables
- Consider rotating your API keys regularly
- Monitor your application for unusual activity

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Python Telegram Bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [Groq API Documentation](https://console.groq.com/docs)

For more help, join our support group: [https://t.me/+5e44PSnDdFNlMGM1](https://t.me/+5e44PSnDdFNlMGM1)