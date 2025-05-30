import os
import tempfile
import logging
import hashlib
from gtts import gTTS
from langdetect import detect

from config import Config

logger = logging.getLogger(__name__)

async def generate_voice_message(text):
    """Generate a voice message from text using gTTS"""
    try:
        # Detect language
        try:
            language = detect(text)
            # If language is not supported, fall back to English
            supported_langs = ['en', 'hi', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'pt', 'ru', 'zh-cn']
            if language not in supported_langs:
                language = Config.TTS_LANGUAGE
        except:
            language = Config.TTS_LANGUAGE
        
        # Create a hash of the text for the filename
        text_hash = hashlib.md5(text.encode()).hexdigest()
        temp_file = os.path.join(tempfile.gettempdir(), f"voice_{text_hash}.mp3")
        
        # Check if we already have this file generated
        if os.path.exists(temp_file):
            return temp_file
        
        # If text is too long, trim it to a reasonable length
        if len(text) > 500:
            text = text[:497] + "..."
        
        # Generate speech
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(temp_file)
        
        return temp_file
    
    except Exception as e:
        logger.error(f"Error generating voice message: {e}")
        
        # Fallback to a simple message in English
        fallback_text = "I'm sorry, I couldn't generate a voice message at the moment."
        temp_file = os.path.join(tempfile.gettempdir(), "voice_fallback.mp3")
        
        # Generate fallback speech
        tts = gTTS(text=fallback_text, lang='en', slow=False)
        tts.save(temp_file)
        
        return temp_file
