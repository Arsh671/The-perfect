import sqlite3
import os
from config import Config
import logging

logger = logging.getLogger(__name__)

def dict_factory(cursor, row):
    """Convert database row objects to dictionaries"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = dict_factory
    return conn

def init_db():
    """Initialize the database with required tables"""
    logger.info("Initializing database...")
    
    # SQL statements to create tables
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        is_banned INTEGER DEFAULT 0,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        chat_count INTEGER DEFAULT 0
    );
    """
    
    create_groups_table = """
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY,
        name TEXT,
        is_banned INTEGER DEFAULT 0,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        message_count INTEGER DEFAULT 0
    );
    """
    
    create_conversations_table = """
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        response TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
    """
    
    create_banned_users_table = """
    CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        banned_by INTEGER,
        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (banned_by) REFERENCES users (user_id)
    );
    """
    
    create_banned_groups_table = """
    CREATE TABLE IF NOT EXISTS banned_groups (
        group_id INTEGER PRIMARY KEY,
        reason TEXT,
        banned_by INTEGER,
        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES groups (group_id),
        FOREIGN KEY (banned_by) REFERENCES users (user_id)
    );
    """
    
    create_games_table = """
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_type TEXT,
        chat_id INTEGER,
        status TEXT,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(create_users_table)
        cursor.execute(create_groups_table)
        cursor.execute(create_conversations_table)
        cursor.execute(create_banned_users_table)
        cursor.execute(create_banned_groups_table)
        cursor.execute(create_games_table)
        conn.commit()
    
    logger.info("Database initialized successfully")

def execute_query(query, params=()):
    """Execute a query with parameters and return results"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall()

def execute_insert(query, params=()):
    """Execute an insert query and return the last row id"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
