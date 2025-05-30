import logging
import random
import asyncio
import json
import httpx
from bot.config import GROQ_API_KEYS, DEFAULT_AI_MODEL, SYSTEM_PROMPT
from bot.modules.cache import get_cached_response, cache_response

logger = logging.getLogger(__name__)

# Track API key usage to implement rotation
api_key_usage = {key: 0 for key in GROQ_API_KEYS}
key_locks = {key: asyncio.Lock() for key in GROQ_API_KEYS}
global_lock = asyncio.Lock()

async def get_ai_response(prompt, history=None, language="en"):
    """Get an AI response using Groq API."""
    # Check cache first
    cache_key = f"{prompt}_{language}_{json.dumps(history) if history else 'no_history'}"
    cached = get_cached_response(cache_key)
    if cached:
        logger.info("Using cached response")
        return cached
    
    # Initialize history if None
    if history is None:
        history = []
    
    # Prepare the full prompt based on language
    if language != "en":
        system_prompt = SYSTEM_PROMPT + f"\n\nRespond in {language} language."
    else:
        system_prompt = SYSTEM_PROMPT
    
    # Attempt to get response with API key rotation
    async with global_lock:
        # Get the least used API key
        api_key = min(api_key_usage.items(), key=lambda x: x[1])[0]
        api_key_usage[api_key] += 1
    
    # Acquire lock for this specific key
    async with key_locks[api_key]:
        try:
            return await _make_groq_request(api_key, system_prompt, prompt, history, cache_key)
        except Exception as e:
            logger.error(f"Error with API key {api_key}: {str(e)}")
            
            # Try again with a different API key
            backoff = 1
            for _ in range(len(GROQ_API_KEYS) - 1):  # Try all other keys
                # Get another key
                async with global_lock:
                    # Get the least used API key that's not the current one
                    other_keys = [k for k in api_key_usage.keys() if k != api_key]
                    if not other_keys:
                        break
                    api_key = min([(k, api_key_usage[k]) for k in other_keys], key=lambda x: x[1])[0]
                    api_key_usage[api_key] += 1
                
                # Wait before retry (exponential backoff)
                await asyncio.sleep(backoff)
                backoff *= 2
                
                # Try with new key
                async with key_locks[api_key]:
                    try:
                        return await _make_groq_request(api_key, system_prompt, prompt, history, cache_key)
                    except Exception as retry_e:
                        logger.error(f"Error with retry API key {api_key}: {str(retry_e)}")
                        continue
            
            # If all keys failed, return a fallback response
            logger.error("All API keys failed, using fallback response")
            return get_fallback_response()

async def _make_groq_request(api_key, system_prompt, prompt, history, cache_key):
    """Make a request to the Groq API."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    # Prepare the messages
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add history if provided
    if history:
        messages.extend(history)
    else:
        messages.append({"role": "user", "content": prompt})
    
    # Prepare the headers and data
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": DEFAULT_AI_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800,
        "top_p": 1,
        "stream": False
    }
    
    # Make the request
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            raise Exception(f"API error: {response.status_code}")
        
        # Parse the response
        response_data = response.json()
        
        try:
            ai_response = response_data["choices"][0]["message"]["content"]
            
            # Cache the response
            cache_response(cache_key, ai_response)
            
            return ai_response
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing API response: {str(e)}")
            logger.error(f"Response data: {response_data}")
            raise Exception("Error parsing API response")

def get_fallback_response():
    """Generate a fallback response when the API is unavailable."""
    fallback_responses = [
        "I'm having trouble connecting to my brain right now. Could you try again in a moment?",
        "Oops! I seem to be experiencing a temporary glitch. Please try again shortly.",
        "My thinking cap is a bit glitchy at the moment. Let's chat again in a minute!",
        "I'm currently having a moment of digital reflection. Would you mind trying again soon?",
        "It looks like my neural networks need a quick reboot. Please try again in a bit!"
    ]
    
    return random.choice(fallback_responses)
