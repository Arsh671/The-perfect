#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Truth or Dare game implementation for the Telegram Bot
"""

import logging
import random
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Truth questions
TRUTH_QUESTIONS = {
    "normal": [
        "What's the most embarrassing song you secretly like?",
        "What's the silliest thing you've done in front of a mirror?",
        "What's your most used emoji?",
        "What was the last lie you told?",
        "What's the weirdest dream you've ever had?",
        "What's something you've done that you hope your parents never find out about?",
        "What's your most bizarre nickname?",
        "What's the most childish thing you still do?",
        "What's a weird food combination that you enjoy?",
        "What's the strangest talent you have?",
        "If you could trade lives with someone for a day, who would it be?",
        "What's the most embarrassing thing in your search history?",
        "What's your guilty pleasure?",
        "If you had to eat one meal every day for the rest of your life, what would it be?",
        "What's something that everyone else loves, but you secretly hate?",
        "What's the most embarrassing thing that happened to you at school/work?",
        "What's your most awkward moment with a stranger?",
        "If you could only keep 5 apps on your phone, which would they be?",
        "What's the worst advice you've ever given?",
        "If you could become invisible for a day, what would you do?"
    ],
    "spicy": [
        "What's your most embarrassing dating story?",
        "What's the most rebellious thing you've ever done?",
        "What's a secret you've never told anyone in this chat?",
        "What's the biggest mistake you've made that turned out to be a blessing?",
        "If you had to date someone in this chat, who would it be?",
        "What's the weirdest place you've fallen asleep?",
        "What's something you did that you still feel guilty about?",
        "If you could read minds for a day, whose mind would you read?",
        "What's the worst lie you've ever told to get out of trouble?",
        "What's your most embarrassing fashion phase?",
        "What's one thing you'd change about your appearance if you could?",
        "What's a self-improvement you've been procrastinating on?",
        "What's the most desperate thing you've done when you were attracted to someone?",
        "What's a secret talent no one knows about?",
        "What's one thing you pretend to understand but actually don't?",
        "What's the weirdest thing you've done alone?",
        "What's something you've done that you think no one else in this chat has done?",
        "What's the most spontaneous thing you've ever done?",
        "If you had to be someone else in this chat for a week, who would you be?",
        "What's the worst rumor you've ever spread or believed?"
    ]
}

# Dare challenges
DARE_CHALLENGES = {
    "normal": [
        "Send a screenshot of your most recent emoji usage.",
        "Text a friend with only emojis and share their confused response.",
        "Post a childhood photo of yourself.",
        "Call someone in your contacts and sing happy birthday to them, even if it's not their birthday.",
        "Send the last five photos in your camera roll.",
        "Do your best impression of a celebrity.",
        "Text the 10th person in your contact list and say 'I know what you did'.",
        "Share an embarrassing story that happened to you.",
        "Speak in an accent for the next three messages.",
        "Send a message to a friend asking for a weird favor with no explanation.",
        "Change your profile picture to whatever the group chooses for 24 hours.",
        "Tell a joke so bad it makes everyone groan.",
        "Send a voice message singing your favorite song.",
        "Write a short poem about someone in the chat.",
        "Message three people 'I need to tell you something important' and ignore their response for an hour.",
        "Tell us your best pickup line.",
        "Share your screen time report for today.",
        "Type with your eyes closed for the next five minutes.",
        "Do 10 jumping jacks right now.",
        "Make up a short story about the last thing you ate."
    ],
    "spicy": [
        "Tell us your most awkward dating experience.",
        "Message someone you haven't talked to in at least 6 months and start a conversation.",
        "Post your most recent selfie that you've taken but haven't posted anywhere.",
        "Let someone in the chat post a status for you on one of your social media accounts.",
        "Imitate another person in this chat until someone guesses who it is.",
        "Reveal your crush's first name.",
        "Share an unpopular opinion you have.",
        "Send a voice message telling a true story that no one would believe.",
        "Send your most embarrassing saved meme.",
        "Tell us about a time you completely embarrassed yourself in front of someone you found attractive.",
        "Post a screenshot of the last three people you texted and what the conversation was about.",
        "Send the oldest selfie on your phone.",
        "For the next 10 minutes, you can only communicate using GIFs.",
        "Call a restaurant and ask if they deliver to the moon.",
        "Text your crush/partner asking them a random question.",
        "Write a short roast about each person in this chat.",
        "Send a message to a family member asking for strange life advice.",
        "Put your phone on speaker and play your most recent playlist for 30 seconds.",
        "Text someone random 'I know your secret' and share their response.",
        "Send a voice message of you doing your best evil laugh."
    ]
}

def get_truth_question(category: str = "normal") -> str:
    """
    Get a random truth question
    
    Args:
        category: Question category (normal or spicy)
        
    Returns:
        Random truth question
    """
    if category not in TRUTH_QUESTIONS:
        category = "normal"
    
    return random.choice(TRUTH_QUESTIONS[category])

def get_dare_challenge(category: str = "normal") -> str:
    """
    Get a random dare challenge
    
    Args:
        category: Challenge category (normal or spicy)
        
    Returns:
        Random dare challenge
    """
    if category not in DARE_CHALLENGES:
        category = "normal"
    
    return random.choice(DARE_CHALLENGES[category])

def add_truth_question(question: str, category: str = "normal") -> bool:
    """
    Add a new truth question
    
    Args:
        question: New question to add
        category: Question category
        
    Returns:
        True if added successfully, False otherwise
    """
    if category not in TRUTH_QUESTIONS:
        return False
    
    # Check if question already exists
    if question in TRUTH_QUESTIONS[category]:
        return False
    
    TRUTH_QUESTIONS[category].append(question)
    return True

def add_dare_challenge(challenge: str, category: str = "normal") -> bool:
    """
    Add a new dare challenge
    
    Args:
        challenge: New challenge to add
        category: Challenge category
        
    Returns:
        True if added successfully, False otherwise
    """
    if category not in DARE_CHALLENGES:
        return False
    
    # Check if challenge already exists
    if challenge in DARE_CHALLENGES[category]:
        return False
    
    DARE_CHALLENGES[category].append(challenge)
    return True
