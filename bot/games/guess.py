#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Guess (number/word) game implementation for the Telegram Bot
"""

import logging
import random
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# List of words for the word guessing game
WORDS = [
    "apple", "banana", "orange", "strawberry", "pineapple",
    "python", "javascript", "kotlin", "swift", "java",
    "keyboard", "mouse", "monitor", "laptop", "computer",
    "guitar", "piano", "drums", "violin", "flute",
    "elephant", "tiger", "lion", "giraffe", "zebra",
    "country", "city", "village", "town", "state",
    "ocean", "river", "lake", "mountain", "desert",
    "pizza", "burger", "pasta", "sandwich", "salad",
    "movie", "series", "show", "theatre", "cinema",
    "football", "cricket", "tennis", "basketball", "hockey"
]

def start_number_guess(min_val: int = 1, max_val: int = 100, max_attempts: int = 7) -> Dict[str, Any]:
    """
    Start a new number guessing game
    
    Args:
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)
        max_attempts: Maximum number of attempts allowed
        
    Returns:
        Game data dictionary
    """
    number = random.randint(min_val, max_val)
    
    return {
        "number": number,
        "attempts": 0,
        "max_attempts": max_attempts,
        "range_min": min_val,
        "range_max": max_val
    }

def make_number_guess(game: Dict[str, Any], guess: int) -> Dict[str, str]:
    """
    Process a number guess
    
    Args:
        game: Game data dictionary
        guess: Player's guessed number
        
    Returns:
        Result dictionary with status and message
    """
    if guess == game["number"]:
        # Correct guess
        game["attempts"] += 1
        return {
            "status": "correct",
            "message": f"Correct! The number was {guess}. You got it in {game['attempts']} attempts!"
        }
    elif guess > game["number"]:
        # Too high
        game["attempts"] += 1
        return {
            "status": "wrong_too_high",
            "message": "Too high! Try a lower number."
        }
    else:
        # Too low
        game["attempts"] += 1
        return {
            "status": "wrong_too_low",
            "message": "Too low! Try a higher number."
        }

def start_word_guess(max_attempts: int = 6) -> Dict[str, Any]:
    """
    Start a new word guessing game
    
    Args:
        max_attempts: Maximum number of attempts allowed
        
    Returns:
        Game data dictionary
    """
    # Pick a random word
    word = random.choice(WORDS).upper()
    
    # Create display with hidden letters
    display = "_" * len(word)
    
    return {
        "word": word,
        "display": display,
        "attempts": 0,
        "max_attempts": max_attempts,
        "guessed_letters": set()
    }

def make_word_guess(game: Dict[str, Any], letter: str) -> Dict[str, str]:
    """
    Process a letter guess in the word guessing game
    
    Args:
        game: Game data dictionary
        letter: Player's guessed letter
        
    Returns:
        Result dictionary with status and message
    """
    letter = letter.upper()
    
    # Check if letter was already guessed
    if letter in game["guessed_letters"]:
        return {
            "status": "already_guessed",
            "message": f"You already guessed '{letter}'."
        }
    
    # Add to guessed letters
    game["guessed_letters"].add(letter)
    
    # Check if letter is in the word
    if letter in game["word"]:
        # Update the display
        new_display = ""
        for i, char in enumerate(game["word"]):
            if char == letter or game["display"][i] != "_":
                new_display += char
            else:
                new_display += "_"
        
        game["display"] = new_display
        
        # Check if the word is complete
        if "_" not in game["display"]:
            return {
                "status": "win",
                "message": f"Congratulations! You guessed the word: {game['word']}"
            }
        
        return {
            "status": "correct",
            "message": f"Good guess! '{letter}' is in the word."
        }
    else:
        # Wrong guess
        game["attempts"] += 1
        
        # Check if out of attempts
        if game["attempts"] >= game["max_attempts"]:
            return {
                "status": "lose",
                "message": f"Game over! The word was: {game['word']}"
            }
        
        return {
            "status": "wrong",
            "message": f"Sorry, '{letter}' is not in the word."
        }

def get_random_word(difficulty: str = "medium") -> str:
    """
    Get a random word based on difficulty
    
    Args:
        difficulty: Difficulty level (easy, medium, hard)
        
    Returns:
        Random word
    """
    # For now, we're using the same word list regardless of difficulty
    # This could be enhanced with different word lists by difficulty
    return random.choice(WORDS)

def add_word_to_list(word: str) -> bool:
    """
    Add a new word to the word list
    
    Args:
        word: Word to add
        
    Returns:
        True if added successfully, False otherwise
    """
    word = word.lower().strip()
    
    # Validate word (letters only, reasonable length)
    if not word.isalpha() or len(word) < 3 or len(word) > 15:
        return False
    
    # Check if word already exists
    if word in WORDS:
        return False
    
    WORDS.append(word)
    return True
