import logging
import random
from config import Config

logger = logging.getLogger(__name__)

class APIKeyManager:
    """
    Manages API keys for the Groq API, with rotation and tracking of usage.
    """
    
    # Class variables to store API key information
    _api_keys = []
    _current_key_index = 0
    _key_usage_counts = {}
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize the API key manager with keys from config"""
        if cls._initialized:
            return
        
        cls._api_keys = Config.GROQ_API_KEYS
        
        if not cls._api_keys:
            logger.error("No API keys provided in configuration")
            raise ValueError("No API keys provided")
        
        # Initialize usage counts
        cls._key_usage_counts = {i: 0 for i in range(len(cls._api_keys))}
        
        # Randomize starting key
        cls._current_key_index = random.randint(0, len(cls._api_keys) - 1)
        
        cls._initialized = True
        logger.info(f"API Key Manager initialized with {len(cls._api_keys)} keys")
    
    @classmethod
    def get_current_key(cls):
        """Return the current API key"""
        if not cls._initialized:
            cls.initialize()
        
        return cls._api_keys[cls._current_key_index]
    
    @classmethod
    def rotate_key(cls):
        """Rotate to the next API key"""
        if not cls._initialized:
            cls.initialize()
        
        cls._current_key_index = (cls._current_key_index + 1) % len(cls._api_keys)
        logger.info(f"Rotated to API key #{cls._current_key_index + 1}")
        
        return cls._api_keys[cls._current_key_index]
    
    @classmethod
    def increment_usage(cls):
        """Increment the usage count for the current key"""
        if not cls._initialized:
            cls.initialize()
        
        cls._key_usage_counts[cls._current_key_index] += 1
        
        # Automatic rotation after reaching usage threshold (100 uses)
        if cls._key_usage_counts[cls._current_key_index] >= 100:
            logger.info(f"Key #{cls._current_key_index + 1} reached usage threshold, rotating")
            cls.rotate_key()
    
    @classmethod
    def get_key_info(cls, index):
        """Get information about a specific API key"""
        if not cls._initialized:
            cls.initialize()
        
        if index < 0 or index >= len(cls._api_keys):
            raise ValueError(f"Invalid key index: {index}")
        
        return {
            "index": index,
            "key": cls._api_keys[index],
            "usage": cls._key_usage_counts.get(index, 0)
        }
    
    @classmethod
    def get_current_key_info(cls):
        """Get information about the current API key"""
        if not cls._initialized:
            cls.initialize()
        
        return cls.get_key_info(cls._current_key_index)
    
    @classmethod
    def get_all_keys_info(cls):
        """Get information about all API keys"""
        if not cls._initialized:
            cls.initialize()
        
        return [cls.get_key_info(i) for i in range(len(cls._api_keys))]
