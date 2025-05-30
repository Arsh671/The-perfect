#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database operations for the Telegram Bot
"""

import sqlite3
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from contextlib import contextmanager

from bot.config import DATABASE_PATH

logger = logging.getLogger(__name__)

# SQL statements for creating tables
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    is_banned INTEGER DEFAULT 0,
    ban_reason TEXT,
    join_date INTEGER,
    last_interaction INTEGER,
    language_code TEXT,
    message_count INTEGER DEFAULT 0,
    is_admin INTEGER DEFAULT 0
)
"""

CREATE_GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS groups (
    group_id INTEGER PRIMARY KEY,
    title TEXT,
    join_date INTEGER,
    last_interaction INTEGER,
    message_count INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0,
    ban_reason TEXT
)
"""

CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    group_id INTEGER,
    message_text TEXT,
    response_text TEXT,
    timestamp INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (group_id) REFERENCES groups (group_id)
)
"""

CREATE_STATS_TABLE = """
CREATE TABLE IF NOT EXISTS stats (
    date TEXT PRIMARY KEY,
    total_messages INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    total_groups INTEGER DEFAULT 0,
    total_commands INTEGER DEFAULT 0,
    ai_calls INTEGER DEFAULT 0,
    voice_messages INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    stickers_sent INTEGER DEFAULT 0,
    stickers_received INTEGER DEFAULT 0
)
"""

CREATE_GAME_STATS_TABLE = """
CREATE TABLE IF NOT EXISTS game_stats (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    game_type TEXT,
    result TEXT,
    timestamp INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
"""

CREATE_STICKERS_TABLE = """
CREATE TABLE IF NOT EXISTS stickers (
    sticker_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    set_name TEXT,
    emoji TEXT,
    category TEXT,
    is_animated INTEGER DEFAULT 0,
    is_video INTEGER DEFAULT 0,
    is_approved INTEGER DEFAULT 0,
    added_by INTEGER,
    added_date INTEGER,
    times_used INTEGER DEFAULT 0,
    FOREIGN KEY (added_by) REFERENCES users (user_id)
)
"""

CREATE_STICKER_CATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS sticker_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
)
"""

CREATE_USER_MOOD_TABLE = """
CREATE TABLE IF NOT EXISTS user_mood (
    user_id INTEGER PRIMARY KEY,
    mood TEXT NOT NULL,
    last_updated INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

CREATE_TAUGHT_FACTS_TABLE = """
CREATE TABLE IF NOT EXISTS taught_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE NOT NULL,
    fact TEXT NOT NULL,
    created_at INTEGER NOT NULL
)
"""

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def update_stats_table_schema():
    """Update stats table schema to include new columns"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if stickers_sent column exists
            cursor.execute("PRAGMA table_info(stats)")
            columns = cursor.fetchall()
            column_names = [col["name"] for col in columns]
            
            # Add stickers_sent and stickers_received columns if they don't exist
            if "stickers_sent" not in column_names:
                cursor.execute("ALTER TABLE stats ADD COLUMN stickers_sent INTEGER DEFAULT 0")
                logger.info("Added stickers_sent column to stats table")
                
            if "stickers_received" not in column_names:
                cursor.execute("ALTER TABLE stats ADD COLUMN stickers_received INTEGER DEFAULT 0")
                logger.info("Added stickers_received column to stats table")
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        logger.error(f"Error updating stats schema: {e}")
        return False

def init_db():
    """Initialize the database and create tables if they don't exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_USERS_TABLE)
            cursor.execute(CREATE_GROUPS_TABLE)
            cursor.execute(CREATE_MESSAGES_TABLE)
            cursor.execute(CREATE_STATS_TABLE)
            cursor.execute(CREATE_GAME_STATS_TABLE)
            cursor.execute(CREATE_SETTINGS_TABLE)
            cursor.execute(CREATE_STICKERS_TABLE)
            cursor.execute(CREATE_STICKER_CATEGORIES_TABLE)
            cursor.execute(CREATE_USER_MOOD_TABLE)
            cursor.execute(CREATE_TAUGHT_FACTS_TABLE)
            
            # Insert default sticker categories if they don't exist
            default_categories = [
                ("funny", "Humorous stickers"),
                ("cute", "Cute and adorable stickers"),
                ("love", "Romantic and love-themed stickers"),
                ("happy", "Happy and joyful stickers"),
                ("sad", "Sad and emotional stickers"),
                ("angry", "Angry or upset stickers"),
                ("surprise", "Surprised or shocked stickers"),
                ("greeting", "Hello, goodbye and greeting stickers"),
                ("reaction", "Reaction stickers"),
                ("animal", "Animal stickers"),
                ("flirty", "Flirty and romantic stickers")
            ]
            
            for category, description in default_categories:
                cursor.execute("""
                    INSERT OR IGNORE INTO sticker_categories (name, description)
                    VALUES (?, ?)
                """, (category, description))
            
            conn.commit()
            
            # Update any schema changes
            update_stats_table_schema()
            
            logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
        raise

def add_or_update_user(user_id: int, username: str = None, first_name: str = None, 
                       last_name: str = None, language_code: str = None) -> bool:
    """Add a new user or update an existing one"""
    current_time = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if user:
                # Update existing user
                cursor.execute("""
                    UPDATE users SET 
                    username = COALESCE(?, username),
                    first_name = COALESCE(?, first_name),
                    last_name = COALESCE(?, last_name),
                    language_code = COALESCE(?, language_code),
                    last_interaction = ?
                    WHERE user_id = ?
                """, (username, first_name, last_name, language_code, current_time, user_id))
            else:
                # Add new user
                cursor.execute("""
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, language_code, join_date, last_interaction)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, language_code, current_time, current_time))
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error adding/updating user: {e}")
        return False

def add_or_update_group(group_id: int, title: str = None) -> bool:
    """Add a new group or update an existing one"""
    current_time = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if group exists
            cursor.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
            group = cursor.fetchone()
            
            if group:
                # Update existing group
                cursor.execute("""
                    UPDATE groups SET 
                    title = COALESCE(?, title),
                    last_interaction = ?
                    WHERE group_id = ?
                """, (title, current_time, group_id))
            else:
                # Add new group
                cursor.execute("""
                    INSERT INTO groups 
                    (group_id, title, join_date, last_interaction)
                    VALUES (?, ?, ?, ?)
                """, (group_id, title, current_time, current_time))
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error adding/updating group: {e}")
        return False

def log_message(user_id: int, group_id: Optional[int], message_text: str, response_text: str) -> bool:
    """Log a message to the database"""
    current_time = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Add message
            cursor.execute("""
                INSERT INTO messages 
                (user_id, group_id, message_text, response_text, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, group_id, message_text, response_text, current_time))
            
            # Update message counts
            cursor.execute("UPDATE users SET message_count = message_count + 1, last_interaction = ? WHERE user_id = ?", 
                          (current_time, user_id))
            
            if group_id:
                cursor.execute("UPDATE groups SET message_count = message_count + 1, last_interaction = ? WHERE group_id = ?", 
                              (current_time, group_id))
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error logging message: {e}")
        return False

def update_daily_stats(messages: int = 0, users: int = 0, groups: int = 0, 
                      commands: int = 0, ai_calls: int = 0, voice_messages: int = 0, 
                      games_played: int = 0, stickers_sent: int = 0, stickers_received: int = 0) -> bool:
    """Update daily statistics"""
    current_date = time.strftime("%Y-%m-%d")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if today's stats exist
            cursor.execute("SELECT * FROM stats WHERE date = ?", (current_date,))
            stats = cursor.fetchone()
            
            if stats:
                # Update existing stats
                cursor.execute("""
                    UPDATE stats SET 
                    total_messages = total_messages + ?,
                    total_users = total_users + ?,
                    total_groups = total_groups + ?,
                    total_commands = total_commands + ?,
                    ai_calls = ai_calls + ?,
                    voice_messages = voice_messages + ?,
                    games_played = games_played + ?,
                    stickers_sent = stickers_sent + ?,
                    stickers_received = stickers_received + ?
                    WHERE date = ?
                """, (messages, users, groups, commands, ai_calls, voice_messages, games_played, 
                     stickers_sent, stickers_received, current_date))
            else:
                # Add new stats
                cursor.execute("""
                    INSERT INTO stats 
                    (date, total_messages, total_users, total_groups, total_commands, ai_calls, 
                     voice_messages, games_played, stickers_sent, stickers_received)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (current_date, messages, users, groups, commands, ai_calls, 
                     voice_messages, games_played, stickers_sent, stickers_received))
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error updating daily stats: {e}")
        return False

def ban_user(user_id: int, reason: str = None) -> bool:
    """Ban a user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?", 
                          (reason, user_id))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error banning user: {e}")
        return False

def unban_user(user_id: int) -> bool:
    """Unban a user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?", 
                          (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error unbanning user: {e}")
        return False

def ban_group(group_id: int, reason: str = None) -> bool:
    """Ban a group"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE groups SET is_banned = 1, ban_reason = ? WHERE group_id = ?", 
                          (reason, group_id))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error banning group: {e}")
        return False

def unban_group(group_id: int) -> bool:
    """Unban a group"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE groups SET is_banned = 0, ban_reason = NULL WHERE group_id = ?", 
                          (group_id,))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error unbanning group: {e}")
        return False

def is_user_banned(user_id: int) -> bool:
    """Check if a user is banned"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result and result["is_banned"] == 1
    except sqlite3.Error as e:
        logger.error(f"Error checking if user is banned: {e}")
        return False

def is_group_banned(group_id: int) -> bool:
    """Check if a group is banned"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_banned FROM groups WHERE group_id = ?", (group_id,))
            result = cursor.fetchone()
            return result and result["is_banned"] == 1
    except sqlite3.Error as e:
        logger.error(f"Error checking if group is banned: {e}")
        return False

def log_game_result(user_id: int, game_type: str, result: str) -> bool:
    """Log a game result"""
    current_time = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO game_stats 
                (user_id, game_type, result, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, game_type, result, current_time))
            conn.commit()
            
            # Update daily stats
            update_daily_stats(games_played=1)
            return True
    except sqlite3.Error as e:
        logger.error(f"Error logging game result: {e}")
        return False

def get_setting(key: str, default=None) -> Any:
    """Get a setting from the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            if result:
                # Try to parse as JSON, fall back to string if it fails
                try:
                    return json.loads(result["value"])
                except (json.JSONDecodeError, TypeError):
                    return result["value"]
            return default
    except sqlite3.Error as e:
        logger.error(f"Error getting setting: {e}")
        return default

def set_setting(key: str, value: Any) -> bool:
    """Set a setting in the database"""
    try:
        # Convert value to JSON string if it's not a string
        if not isinstance(value, str):
            value = json.dumps(value)
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?
            """, (key, value, value))
            conn.commit()
            return True
    except (sqlite3.Error, TypeError, json.JSONDecodeError) as e:
        logger.error(f"Error setting setting: {e}")
        return False

def get_user_stats() -> Dict[str, int]:
    """Get user statistics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as active FROM users WHERE last_interaction > ?", 
                          (int(time.time()) - 86400 * 7,))  # Active in last 7 days
            active = cursor.fetchone()["active"]
            
            cursor.execute("SELECT COUNT(*) as banned FROM users WHERE is_banned = 1")
            banned = cursor.fetchone()["banned"]
            
            return {
                "total": total,
                "active": active,
                "banned": banned
            }
    except sqlite3.Error as e:
        logger.error(f"Error getting user stats: {e}")
        return {"total": 0, "active": 0, "banned": 0}

def get_group_stats() -> Dict[str, int]:
    """Get group statistics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM groups")
            total = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as active FROM groups WHERE last_interaction > ?", 
                          (int(time.time()) - 86400 * 7,))  # Active in last 7 days
            active = cursor.fetchone()["active"]
            
            cursor.execute("SELECT COUNT(*) as banned FROM groups WHERE is_banned = 1")
            banned = cursor.fetchone()["banned"]
            
            return {
                "total": total,
                "active": active,
                "banned": banned
            }
    except sqlite3.Error as e:
        logger.error(f"Error getting group stats: {e}")
        return {"total": 0, "active": 0, "banned": 0}

def get_message_stats() -> Dict[str, int]:
    """Get message statistics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM messages")
            total = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) as today FROM messages WHERE timestamp > ?", 
                          (int(time.time()) - 86400,))  # Last 24 hours
            today = cursor.fetchone()["today"]
            
            cursor.execute("SELECT COUNT(*) as week FROM messages WHERE timestamp > ?", 
                          (int(time.time()) - 86400 * 7,))  # Last 7 days
            week = cursor.fetchone()["week"]
            
            return {
                "total": total,
                "today": today,
                "week": week
            }
    except sqlite3.Error as e:
        logger.error(f"Error getting message stats: {e}")
        return {"total": 0, "today": 0, "week": 0}

def get_active_users(limit: int = 100) -> List[Dict[str, Any]]:
    """Get most active users"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, first_name, last_name, message_count 
                FROM users 
                ORDER BY message_count DESC
                LIMIT ?
            """, (limit,))
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "message_count": row["message_count"]
                })
            
            return users
    except sqlite3.Error as e:
        logger.error(f"Error getting active users: {e}")
        return []

def get_active_groups(limit: int = 100) -> List[Dict[str, Any]]:
    """Get most active groups"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT group_id, title, message_count 
                FROM groups 
                ORDER BY message_count DESC
                LIMIT ?
            """, (limit,))
            
            groups = []
            for row in cursor.fetchall():
                groups.append({
                    "group_id": row["group_id"],
                    "title": row["title"],
                    "message_count": row["message_count"]
                })
            
            return groups
    except sqlite3.Error as e:
        logger.error(f"Error getting active groups: {e}")
        return []

def get_all_users() -> List[Dict[str, Any]]:
    """Get all users"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, first_name, last_name FROM users WHERE is_banned = 0")
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"]
                })
            
            return users
    except sqlite3.Error as e:
        logger.error(f"Error getting all users: {e}")
        return []

def get_all_groups() -> List[Dict[str, Any]]:
    """Get all groups"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT group_id, title FROM groups WHERE is_banned = 0")
            
            groups = []
            for row in cursor.fetchall():
                groups.append({
                    "group_id": row["group_id"],
                    "title": row["title"]
                })
            
            return groups
    except sqlite3.Error as e:
        logger.error(f"Error getting all groups: {e}")
        return []



# Sticker Management Functions
def save_sticker(sticker_id: str, file_id: str, set_name: str, emoji: str, 
                category: str, is_animated: bool, is_video: bool, added_by: int) -> bool:
    """Save a sticker to the database"""
    current_time = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if sticker exists
            cursor.execute("SELECT * FROM stickers WHERE sticker_id = ?", (sticker_id,))
            sticker = cursor.fetchone()
            
            if sticker:
                # Update existing sticker
                cursor.execute("""
                    UPDATE stickers SET 
                    file_id = ?,
                    set_name = ?,
                    emoji = ?,
                    category = ?,
                    is_animated = ?,
                    is_video = ?
                    WHERE sticker_id = ?
                """, (file_id, set_name if set_name else "", emoji if emoji else "", category, 
                      1 if is_animated else 0, 1 if is_video else 0, sticker_id))
            else:
                # Add new sticker
                cursor.execute("""
                    INSERT INTO stickers 
                    (sticker_id, file_id, set_name, emoji, category, 
                     is_animated, is_video, is_approved, added_by, added_date, times_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sticker_id, file_id, set_name if set_name else "", emoji if emoji else "", category, 
                      1 if is_animated else 0, 1 if is_video else 0, 
                      1, added_by, current_time, 0))
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error saving sticker: {e}")
        return False

def increment_sticker_usage(sticker_id: str) -> bool:
    """Increment the usage count for a sticker"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE stickers 
                SET times_used = times_used + 1
                WHERE sticker_id = ?
            """, (sticker_id,))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error incrementing sticker usage: {e}")
        return False

def get_random_sticker(category: str = None, limit: int = 1) -> List[Dict[str, Any]]:
    """Get random stickers optionally filtered by category"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if category:
                cursor.execute("""
                    SELECT * FROM stickers
                    WHERE category = ? AND is_approved = 1
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (category, limit))
            else:
                cursor.execute("""
                    SELECT * FROM stickers
                    WHERE is_approved = 1
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (limit,))
                
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Error getting random sticker: {e}")
        return []

def get_stickers_by_mood(mood: str, limit: int = 1) -> List[Dict[str, Any]]:
    """Get stickers based on user mood"""
    # Map mood to category
    mood_to_category = {
        "happy": ["happy", "funny", "celebration", "approval", "cool"],
        "sad": ["sad", "thinking", "annoyed"],
        "angry": ["angry", "disapproval", "annoyed"],
        "love": ["love", "flirty", "approval", "cute"],
        "excited": ["happy", "surprise", "celebration"],
        "bored": ["funny", "reaction", "thinking", "cool"],
        "curious": ["thinking", "surprise", "reaction"],
        "flirty": ["flirty", "love", "cool", "approval"],
        "surprised": ["surprise", "funny", "reaction"],
        "confused": ["thinking", "reaction", "funny"],
        "thank": ["thank", "approval", "love"],
        "greeting": ["greeting", "approval", "celebration"]
    }
    
    # Default to reaction category if mood not recognized
    categories = mood_to_category.get(mood.lower(), ["reaction", "other"])
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Use placeholders for the IN clause
            placeholders = ", ".join(["?"] * len(categories))
            query = f"""
                SELECT * FROM stickers
                WHERE category IN ({placeholders}) AND is_approved = 1
                ORDER BY RANDOM()
                LIMIT ?
            """
            
            cursor.execute(query, categories + [limit])
            result = [dict(row) for row in cursor.fetchall()]
            
            # If no stickers found for the mood, fall back to any sticker
            if not result:
                query = """
                    SELECT * FROM stickers
                    WHERE is_approved = 1
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                cursor.execute(query, [limit])
                result = [dict(row) for row in cursor.fetchall()]
                
            # Log that we're returning stickers
            logger.debug(f"Retrieved {len(result)} stickers for mood: {mood}")
            return result
            
    except sqlite3.Error as e:
        logger.error(f"Error getting stickers by mood: {e}")
        return []

def is_sticker_explicit(sticker_id: str, file_id: str, set_name: str = None) -> bool:
    """
    Check if a sticker is potentially explicit/adult content
    This is a basic implementation - in production, you'd use more sophisticated methods
    """
    # Blacklisted set names (partial matches)
    explicit_set_keywords = [
        "adult", "xxx", "nsfw", "porn", "sex", "nude", "naked", 
        "18+", "mature", "explicit", "hentai", "erotic"
    ]
    
    # Check set name for explicit keywords
    if set_name:
        set_name_lower = set_name.lower()
        for keyword in explicit_set_keywords:
            if keyword in set_name_lower:
                return True
    
    # Always approved sets (whitelist)
    safe_prefixes = ["official", "telegram", "disney", "emoji", "cute"]
    if set_name:
        set_name_lower = set_name.lower()
        for prefix in safe_prefixes:
            if prefix in set_name_lower:
                return False
    
    # Check if sticker was previously flagged
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_approved FROM stickers WHERE sticker_id = ?", (sticker_id,))
            result = cursor.fetchone()
            if result:
                return result["is_approved"] == 0
    except sqlite3.Error as e:
        logger.error(f"Error checking if sticker is explicit: {e}")
    
    # Default to not explicit
    return False

def update_user_mood(user_id: int, mood: str) -> bool:
    """Update or set a user's current mood"""
    current_time = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_mood (user_id, mood, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                mood = ?, last_updated = ?
            """, (user_id, mood, current_time, mood, current_time))
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error updating user mood: {e}")
        return False

def get_user_mood(user_id: int) -> Optional[str]:
    """Get a user's current mood"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mood FROM user_mood WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result["mood"] if result else None
    except sqlite3.Error as e:
        logger.error(f"Error getting user mood: {e}")
        return None
        
def add_taught_fact(keyword: str, fact: str) -> bool:
    """Add a new fact taught by the owner
    
    Args:
        keyword: Keyword to associate with the fact
        fact: The fact content
        
    Returns:
        True if successful, False otherwise
    """
    current_time = int(time.time())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if keyword exists
            cursor.execute("SELECT * FROM taught_facts WHERE keyword = ?", (keyword.lower(),))
            result = cursor.fetchone()
            
            if result:
                # Update existing fact
                cursor.execute("""
                    UPDATE taught_facts SET 
                    fact = ?,
                    created_at = ?
                    WHERE keyword = ?
                """, (fact, current_time, keyword.lower()))
            else:
                # Add new fact
                cursor.execute("""
                    INSERT INTO taught_facts 
                    (keyword, fact, created_at)
                    VALUES (?, ?, ?)
                """, (keyword.lower(), fact, current_time))
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Error adding taught fact: {e}")
        return False
        
def get_taught_fact(keyword: str) -> Optional[str]:
    """Get a fact previously taught by the owner
    
    Args:
        keyword: Keyword associated with the fact
        
    Returns:
        The fact if found, None otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fact FROM taught_facts WHERE keyword = ?", (keyword.lower(),))
            result = cursor.fetchone()
            return result["fact"] if result else None
    except sqlite3.Error as e:
        logger.error(f"Error getting taught fact: {e}")
        return None
        
def get_all_taught_facts() -> List[Dict[str, Any]]:
    """Get all facts taught by the owner
    
    Returns:
        List of facts with their keywords and creation timestamps
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT keyword, fact, created_at FROM taught_facts ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Error getting all taught facts: {e}")
        return []
        
def delete_taught_fact(keyword: str) -> bool:
    """Delete a fact taught by the owner
    
    Args:
        keyword: Keyword associated with the fact
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM taught_facts WHERE keyword = ?", (keyword.lower(),))
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error deleting taught fact: {e}")
        return False
