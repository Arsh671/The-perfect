import logging
import time
from database import execute_query, execute_insert

logger = logging.getLogger(__name__)

class User:
    """
    Model for interacting with user data in the database
    """
    
    @staticmethod
    def create_or_update(user_id, username=None, first_name=None):
        """Create a new user or update an existing one"""
        try:
            # Check if user exists
            user = User.get(user_id)
            
            if user:
                # Update existing user
                execute_query(
                    """
                    UPDATE users SET 
                        username = CASE WHEN ? IS NOT NULL THEN ? ELSE username END,
                        first_name = CASE WHEN ? IS NOT NULL THEN ? ELSE first_name END,
                        last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (username, username, first_name, first_name, user_id)
                )
                logger.info(f"Updated user: {user_id}")
            else:
                # Insert new user
                execute_insert(
                    """
                    INSERT INTO users (user_id, username, first_name)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, username, first_name)
                )
                logger.info(f"Created new user: {user_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating/updating user {user_id}: {e}")
            return False
    
    @staticmethod
    def get(user_id):
        """Get a user by ID"""
        try:
            result = execute_query(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    @staticmethod
    def update_last_active(user_id):
        """Update a user's last active timestamp"""
        try:
            execute_query(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Error updating last active for user {user_id}: {e}")
            return False
    
    @staticmethod
    def increment_chat_count(user_id):
        """Increment a user's chat count"""
        try:
            execute_query(
                "UPDATE users SET chat_count = chat_count + 1 WHERE user_id = ?",
                (user_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Error incrementing chat count for user {user_id}: {e}")
            return False
    
    @staticmethod
    def ban(user_id, banned_by, reason=None):
        """Ban a user"""
        try:
            # Update user's ban status
            execute_query(
                "UPDATE users SET is_banned = 1 WHERE user_id = ?",
                (user_id,)
            )
            
            # Add to banned_users table
            execute_insert(
                """
                INSERT INTO banned_users (user_id, reason, banned_by)
                VALUES (?, ?, ?)
                """,
                (user_id, reason, banned_by)
            )
            
            logger.info(f"User {user_id} banned by {banned_by}")
            return True
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
            return False
    
    @staticmethod
    def unban(user_id):
        """Unban a user"""
        try:
            # Update user's ban status
            execute_query(
                "UPDATE users SET is_banned = 0 WHERE user_id = ?",
                (user_id,)
            )
            
            # Remove from banned_users table
            execute_query(
                "DELETE FROM banned_users WHERE user_id = ?",
                (user_id,)
            )
            
            logger.info(f"User {user_id} unbanned")
            return True
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
            return False
    
    @staticmethod
    def is_banned(user_id):
        """Check if a user is banned"""
        try:
            result = execute_query(
                "SELECT is_banned FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if result and result[0]['is_banned'] == 1:
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking if user {user_id} is banned: {e}")
            return False
    
    @staticmethod
    def count_all():
        """Count all users"""
        try:
            result = execute_query("SELECT COUNT(*) as count FROM users")
            if result:
                return result[0]['count']
            return 0
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
    
    @staticmethod
    def count_banned():
        """Count banned users"""
        try:
            result = execute_query("SELECT COUNT(*) as count FROM users WHERE is_banned = 1")
            if result:
                return result[0]['count']
            return 0
        except Exception as e:
            logger.error(f"Error counting banned users: {e}")
            return 0
    
    @staticmethod
    def get_all_active():
        """Get all active (non-banned) users"""
        try:
            return execute_query(
                "SELECT * FROM users WHERE is_banned = 0"
            )
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    @staticmethod
    def get_top_users(limit=5):
        """Get top users by chat count"""
        try:
            return execute_query(
                "SELECT * FROM users ORDER BY chat_count DESC LIMIT ?",
                (limit,)
            )
        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            return []
    
    @staticmethod
    def get_users_for_proactive_message(hours=24):
        """Get users who haven't received a message in the specified hours"""
        try:
            # Calculate timestamp for comparison
            timestamp = int(time.time() - (hours * 3600))
            
            return execute_query(
                """
                SELECT * FROM users 
                WHERE is_banned = 0 
                AND datetime(last_active) <= datetime(?, 'unixepoch')
                """,
                (timestamp,)
            )
        except Exception as e:
            logger.error(f"Error getting users for proactive message: {e}")
            return []
