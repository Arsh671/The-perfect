import logging
from database import execute_query, execute_insert

logger = logging.getLogger(__name__)

class Group:
    """
    Model for interacting with group data in the database
    """
    
    @staticmethod
    def create_or_update(group_id, name=None):
        """Create a new group or update an existing one"""
        try:
            # Check if group exists
            group = Group.get(group_id)
            
            if group:
                # Update existing group
                execute_query(
                    """
                    UPDATE groups SET 
                        name = CASE WHEN ? IS NOT NULL THEN ? ELSE name END,
                        last_active = CURRENT_TIMESTAMP
                    WHERE group_id = ?
                    """,
                    (name, name, group_id)
                )
                logger.info(f"Updated group: {group_id}")
            else:
                # Insert new group
                execute_insert(
                    """
                    INSERT INTO groups (group_id, name)
                    VALUES (?, ?)
                    """,
                    (group_id, name)
                )
                logger.info(f"Created new group: {group_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating/updating group {group_id}: {e}")
            return False
    
    @staticmethod
    def get(group_id):
        """Get a group by ID"""
        try:
            result = execute_query(
                "SELECT * FROM groups WHERE group_id = ?",
                (group_id,)
            )
            
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting group {group_id}: {e}")
            return None
    
    @staticmethod
    def update_last_active(group_id):
        """Update a group's last active timestamp"""
        try:
            execute_query(
                "UPDATE groups SET last_active = CURRENT_TIMESTAMP WHERE group_id = ?",
                (group_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Error updating last active for group {group_id}: {e}")
            return False
    
    @staticmethod
    def increment_message_count(group_id):
        """Increment a group's message count"""
        try:
            execute_query(
                "UPDATE groups SET message_count = message_count + 1 WHERE group_id = ?",
                (group_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Error incrementing message count for group {group_id}: {e}")
            return False
    
    @staticmethod
    def ban(group_id, banned_by, reason=None):
        """Ban a group"""
        try:
            # Update group's ban status
            execute_query(
                "UPDATE groups SET is_banned = 1 WHERE group_id = ?",
                (group_id,)
            )
            
            # Add to banned_groups table
            execute_insert(
                """
                INSERT INTO banned_groups (group_id, reason, banned_by)
                VALUES (?, ?, ?)
                """,
                (group_id, reason, banned_by)
            )
            
            logger.info(f"Group {group_id} banned by {banned_by}")
            return True
        except Exception as e:
            logger.error(f"Error banning group {group_id}: {e}")
            return False
    
    @staticmethod
    def unban(group_id):
        """Unban a group"""
        try:
            # Update group's ban status
            execute_query(
                "UPDATE groups SET is_banned = 0 WHERE group_id = ?",
                (group_id,)
            )
            
            # Remove from banned_groups table
            execute_query(
                "DELETE FROM banned_groups WHERE group_id = ?",
                (group_id,)
            )
            
            logger.info(f"Group {group_id} unbanned")
            return True
        except Exception as e:
            logger.error(f"Error unbanning group {group_id}: {e}")
            return False
    
    @staticmethod
    def is_banned(group_id):
        """Check if a group is banned"""
        try:
            result = execute_query(
                "SELECT is_banned FROM groups WHERE group_id = ?",
                (group_id,)
            )
            
            if result and result[0]['is_banned'] == 1:
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking if group {group_id} is banned: {e}")
            return False
    
    @staticmethod
    def count_all():
        """Count all groups"""
        try:
            result = execute_query("SELECT COUNT(*) as count FROM groups")
            if result:
                return result[0]['count']
            return 0
        except Exception as e:
            logger.error(f"Error counting groups: {e}")
            return 0
    
    @staticmethod
    def count_banned():
        """Count banned groups"""
        try:
            result = execute_query("SELECT COUNT(*) as count FROM groups WHERE is_banned = 1")
            if result:
                return result[0]['count']
            return 0
        except Exception as e:
            logger.error(f"Error counting banned groups: {e}")
            return 0
    
    @staticmethod
    def get_all_active():
        """Get all active (non-banned) groups"""
        try:
            return execute_query(
                "SELECT * FROM groups WHERE is_banned = 0"
            )
        except Exception as e:
            logger.error(f"Error getting active groups: {e}")
            return []
    
    @staticmethod
    def get_top_groups(limit=5):
        """Get top groups by message count"""
        try:
            return execute_query(
                "SELECT * FROM groups ORDER BY message_count DESC LIMIT ?",
                (limit,)
            )
        except Exception as e:
            logger.error(f"Error getting top groups: {e}")
            return []
