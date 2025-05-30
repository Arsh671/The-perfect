import logging
import sqlite3
import asyncio
import time
from datetime import datetime
from pathlib import Path
from bot.config import DB_PATH, OWNER_ID

logger = logging.getLogger(__name__)

# SQLite connection pool
class ConnectionPool:
    def __init__(self, db_path, max_connections=10):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = []
        self.lock = asyncio.Lock()
    
    async def get_connection(self):
        async with self.lock:
            if self.connections:
                return self.connections.pop()
            else:
                # Create a new connection
                connection = sqlite3.connect(self.db_path)
                connection.row_factory = sqlite3.Row
                return connection
    
    async def release_connection(self, connection):
        async with self.lock:
            if len(self.connections) < self.max_connections:
                self.connections.append(connection)
            else:
                connection.close()

# Initialize the connection pool
pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = ConnectionPool(DB_PATH)
    return pool

async def execute_query(query, params=(), fetch_all=False, fetch_one=False, commit=False):
    """Execute a database query and return the results."""
    pool = await get_pool()
    conn = await pool.get_connection()
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if commit:
            conn.commit()
        
        if fetch_all:
            return cursor.fetchall()
        elif fetch_one:
            return cursor.fetchone()
        else:
            return cursor.lastrowid
    
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise
    
    finally:
        await pool.release_connection(conn)

def initialize_database():
    """Initialize the database and create necessary tables."""
    # Create the database directory if it doesn't exist
    db_dir = Path(DB_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_interaction TEXT
    )
    ''')
    
    # Create groups table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        chat_id INTEGER PRIMARY KEY,
        title TEXT,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_interaction TEXT
    )
    ''')
    
    # Create banned users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        banned_at TEXT DEFAULT CURRENT_TIMESTAMP,
        banned_by INTEGER
    )
    ''')
    
    # Create message logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS message_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        chat_id INTEGER,
        message_text TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # Create a config table for bot-wide settings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    # Insert default owner if not exists
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
        (OWNER_ID, 'fakesoul15', 'Owner', '')
    )
    
    # Commit and close
    conn.commit()
    conn.close()
    
    logger.info("Database initialized")

async def add_or_update_user(user_id, username, first_name, last_name):
    """Add a new user or update an existing user in the database."""
    # Check if user is banned
    if await is_user_banned(user_id):
        return False
    
    # Update last interaction time
    current_time = datetime.now().isoformat()
    
    # Check if user exists
    user = await get_user(user_id)
    
    if user:
        # Update existing user
        await execute_query(
            'UPDATE users SET username = ?, first_name = ?, last_name = ?, last_interaction = ? WHERE user_id = ?',
            (username, first_name, last_name, current_time, user_id),
            commit=True
        )
    else:
        # Add new user
        await execute_query(
            'INSERT INTO users (user_id, username, first_name, last_name, last_interaction) VALUES (?, ?, ?, ?, ?)',
            (user_id, username, first_name, last_name, current_time),
            commit=True
        )
    
    return True

async def add_or_update_group(chat_id, title):
    """Add a new group or update an existing group in the database."""
    # Update last interaction time
    current_time = datetime.now().isoformat()
    
    # Check if group exists
    group = await get_group(chat_id)
    
    if group:
        # Update existing group
        await execute_query(
            'UPDATE groups SET title = ?, last_interaction = ? WHERE chat_id = ?',
            (title, current_time, chat_id),
            commit=True
        )
    else:
        # Add new group
        await execute_query(
            'INSERT INTO groups (chat_id, title, last_interaction) VALUES (?, ?, ?)',
            (chat_id, title, current_time),
            commit=True
        )
    
    return True

async def log_message(user_id, chat_id, message_text):
    """Log a message to the database."""
    await execute_query(
        'INSERT INTO message_logs (user_id, chat_id, message_text) VALUES (?, ?, ?)',
        (user_id, chat_id, message_text),
        commit=True
    )

async def get_user(user_id):
    """Get a user by ID."""
    return await execute_query(
        'SELECT * FROM users WHERE user_id = ?',
        (user_id,),
        fetch_one=True
    )

async def get_group(chat_id):
    """Get a group by ID."""
    return await execute_query(
        'SELECT * FROM groups WHERE chat_id = ?',
        (chat_id,),
        fetch_one=True
    )

async def get_all_users():
    """Get all users."""
    return await execute_query(
        'SELECT * FROM users',
        fetch_all=True
    )

async def get_all_groups():
    """Get all groups."""
    return await execute_query(
        'SELECT * FROM groups',
        fetch_all=True
    )

async def get_user_count():
    """Get the count of users."""
    result = await execute_query(
        'SELECT COUNT(*) as count FROM users',
        fetch_one=True
    )
    return result['count'] if result else 0

async def get_group_count():
    """Get the count of groups."""
    result = await execute_query(
        'SELECT COUNT(*) as count FROM groups',
        fetch_one=True
    )
    return result['count'] if result else 0

async def ban_user(user_id, reason, banned_by=OWNER_ID):
    """Ban a user globally."""
    await execute_query(
        'INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by) VALUES (?, ?, ?)',
        (user_id, reason, banned_by),
        commit=True
    )

async def unban_user(user_id):
    """Unban a user globally."""
    await execute_query(
        'DELETE FROM banned_users WHERE user_id = ?',
        (user_id,),
        commit=True
    )

async def is_user_banned(user_id):
    """Check if a user is banned."""
    result = await execute_query(
        'SELECT * FROM banned_users WHERE user_id = ?',
        (user_id,),
        fetch_one=True
    )
    return result is not None

async def get_banned_users():
    """Get all banned users."""
    return await execute_query(
        'SELECT * FROM banned_users',
        fetch_all=True
    )

async def get_config_value(key, default=None):
    """Get a config value."""
    result = await execute_query(
        'SELECT value FROM config WHERE key = ?',
        (key,),
        fetch_one=True
    )
    return result['value'] if result else default

async def set_config_value(key, value):
    """Set a config value."""
    await execute_query(
        'INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)',
        (key, value),
        commit=True
    )
