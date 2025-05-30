import logging
import os
import tempfile
from gtts import gTTS
from bot.config import ENABLE_VOICE

logger = logging.getLogger(__name__)

async def text_to_speech(text, language="en"):
    """Convert text to speech using gTTS."""
    if not ENABLE_VOICE:
        logger.info("Voice messages are disabled globally")
        return None
    
    try:
        # Map language code to gTTS language code
        lang_map = {
            "en": "en",
            "hi": "hi",
            "es": "es",
            "fr": "fr",
            "de": "de",
            "it": "it",
            "ja": "ja",
            "ko": "ko",
            "pt": "pt",
            "ru": "ru",
            "zh": "zh-CN"
        }
        
        # Default to English if language not supported
        gtts_lang = lang_map.get(language, "en")
        
        # Create a temporary file for the voice message
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.close()
        
        # Generate the speech
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(temp_file.name)
        
        # Open the file for reading
        voice_file = open(temp_file.name, "rb")
        
        return voice_file
    
    except Exception as e:
        logger.error(f"Error generating voice message: {str(e)}")
        # Clean up the temporary file if it exists
        if 'temp_file' in locals() and os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        return None
