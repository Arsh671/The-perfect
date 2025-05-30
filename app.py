import os
import threading
import time
from datetime import datetime
import logging
import sys
import subprocess

from flask import Flask, render_template, jsonify

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Global variables to track bot status
bot_running = False
bot_started_at = None
bot_thread = None


@app.route('/')
def index():
    """Render the home page."""
    context = {
        'status': 'Running' if bot_running else 'Stopped',
        'started_at': bot_started_at.strftime('%Y-%m-%d %H:%M:%S UTC') if bot_started_at else 'N/A',
        'uptime': get_uptime() if bot_running else 'N/A',
    }
    return render_template('index.html', **context)


@app.route('/api/status')
def api_status():
    """Return the bot status as JSON."""
    return jsonify({
        'status': 'Running' if bot_running else 'Stopped',
        'started_at': bot_started_at.strftime('%Y-%m-%d %H:%M:%S UTC') if bot_started_at else None,
        'uptime': get_uptime() if bot_running else None,
    })


def get_uptime():
    """Calculate uptime if the bot is running."""
    if not bot_started_at:
        return 'N/A'
    
    delta = datetime.utcnow() - bot_started_at
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def start_bot():
    """Start the Telegram bot in a separate thread."""
    global bot_running, bot_started_at, bot_thread
    
    # Check if there's already a bot process running
    try:
        output = subprocess.check_output(["pgrep", "-f", "python main.py"]).decode().strip()
        if output:
            bot_running = True
            pid = int(output.split()[0])
            # Get process start time
            proc_info = subprocess.check_output(["ps", "-o", "lstart=", "-p", str(pid)]).decode().strip()
            proc_time = datetime.strptime(proc_info, "%a %b %d %H:%M:%S %Y")
            bot_started_at = proc_time
            logging.info(f"Found existing bot process (PID: {pid})")
            return
    except (subprocess.CalledProcessError, ValueError, IndexError):
        # No existing process, start a new one
        pass
    
    def _run_bot():
        try:
            subprocess.run(["python", "main.py"], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Bot process exited with error: {e}")
            global bot_running
            bot_running = False
    
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=_run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    bot_running = True
    bot_started_at = datetime.utcnow()
    logging.info("Bot started in background thread")


def create_templates_directory():
    """Create the templates directory if it doesn't exist."""
    os.makedirs('templates', exist_ok=True)


def create_index_template():
    """Create the index.html template."""
    html_content = """<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bestie AI - Telegram Bot Status</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <meta http-equiv="refresh" content="30">
    <style>
        body {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .status-badge {
            font-size: 1.2rem;
            padding: 0.5rem 1rem;
        }
        .info-card {
            max-width: 500px;
            margin: 0 auto;
        }
        .footer {
            margin-top: auto;
            padding: 1rem 0;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container main-content py-5">
        <div class="text-center mb-5">
            <h1 class="display-4">Bestie AI</h1>
            <p class="lead">Telegram Bot Status Dashboard</p>
        </div>
        
        <div class="card info-card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">Bot Status</h5>
                <span class="badge {% if status == 'Running' %}bg-success{% else %}bg-danger{% endif %} status-badge">
                    {{ status }}
                </span>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Started At:</strong></p>
                        <p>{{ started_at }}</p>
                    </div>
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Uptime:</strong></p>
                        <p>{{ uptime }}</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-5">
            <p>This page auto-refreshes every 30 seconds</p>
        </div>
    </div>
    
    <footer class="footer bg-dark">
        <div class="container">
            <p class="text-muted mb-0">
                © 2025 Bestie AI - <a href="https://t.me/+5e44PSnDdFNlMGM1" target="_blank">Support Group</a> | 
                <a href="https://t.me/promotionandsupport" target="_blank">Support Channel</a>
            </p>
        </div>
    </footer>
</body>
</html>
"""
    
    with open('templates/index.html', 'w') as f:
        f.write(html_content)


if __name__ == '__main__':
    # Create necessary directories and files
    create_templates_directory()
    create_index_template()
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the bot in a separate thread
    start_bot()
    
    # Get port from environment variable (for Heroku/Railway compatibility)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port)