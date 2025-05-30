import logging
import json
from database import execute_query, execute_insert

logger = logging.getLogger(__name__)

class Conversation:
    """
    Model for interacting with conversation data in the database
    """
    
    @staticmethod
    def store(user_id, message, response):
        """Store a conversation exchange in the database"""
        try:
            execute_insert(
                """
                INSERT INTO conversations (user_id, message, response)
                VALUES (?, ?, ?)
                """,
                (user_id, message, response)
            )
            logger.debug(f"Stored conversation for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing conversation for user {user_id}: {e}")
            return False
    
    @staticmethod
    def get_recent_for_user(user_id, limit=10):
        """Get recent conversations for a user"""
        try:
            return execute_query(
                """
                SELECT * FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
        except Exception as e:
            logger.error(f"Error getting recent conversations for user {user_id}: {e}")
            return []
    
    @staticmethod
    def get_by_id(conversation_id):
        """Get a conversation by ID"""
        try:
            result = execute_query(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None
    
    @staticmethod
    def count_all():
        """Count all conversations"""
        try:
            result = execute_query("SELECT COUNT(*) as count FROM conversations")
            if result:
                return result[0]['count']
            return 0
        except Exception as e:
            logger.error(f"Error counting conversations: {e}")
            return 0
    
    @staticmethod
    def count_for_user(user_id):
        """Count conversations for a specific user"""
        try:
            result = execute_query(
                "SELECT COUNT(*) as count FROM conversations WHERE user_id = ?",
                (user_id,)
            )
            if result:
                return result[0]['count']
            return 0
        except Exception as e:
            logger.error(f"Error counting conversations for user {user_id}: {e}")
            return 0
    
    @staticmethod
    def delete_for_user(user_id):
        """Delete all conversations for a user"""
        try:
            execute_query(
                "DELETE FROM conversations WHERE user_id = ?",
                (user_id,)
            )
            logger.info(f"Deleted all conversations for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting conversations for user {user_id}: {e}")
            return False
    
    @staticmethod
    def get_context_for_user(user_id, limit=5):
        """Get conversation context for a user in a format suitable for AI"""
        try:
            conversations = execute_query(
                """
                SELECT message, response FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            
            # Format for AI context (most recent first)
            context = []
            for conv in reversed(conversations):
                context.append({"role": "user", "content": conv['message']})
                context.append({"role": "assistant", "content": conv['response']})
            
            return context
        except Exception as e:
            logger.error(f"Error getting context for user {user_id}: {e}")
            return []
    
    @staticmethod
    def search(query, limit=10):
        """Search conversations for a specific query"""
        try:
            return execute_query(
                """
                SELECT * FROM conversations
                WHERE message LIKE ? OR response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", limit)
            )
        except Exception as e:
            logger.error(f"Error searching conversations for '{query}': {e}")
            return []
