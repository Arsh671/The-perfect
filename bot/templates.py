#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Template messages for various bot functions
"""

import random
from typing import List, Dict, Any

# Welcome messages for groups
WELCOME_TEMPLATES = [
    "👋 Welcome {mentions} to *{group_name}*! I hope you have a fantastic time here! If you need any help, just tag me! 💕",
    "Hey there {mentions}! Welcome to *{group_name}*! So excited to have you join us! 🎉✨",
    "Look who just arrived! {mentions} has joined *{group_name}*! Welcome and enjoy your stay! 💖",
    "A warm welcome to {mentions}! Thanks for joining *{group_name}*! Feel free to introduce yourself! 😊",
    "Yay! {mentions} is here! Welcome to *{group_name}*! We're happy to have you! 🥳",
    "Hey {mentions}! Welcome aboard *{group_name}*! I hope you brought snacks to share! 😋",
    "Welcome {mentions}! *{group_name}* just got more awesome with you here! 🌟",
    "Woohoo! {mentions} has joined the party at *{group_name}*! Great to have you here! 💃🕺",
    "Hello {mentions}! Welcome to our cozy corner of Telegram - *{group_name}*! 🏡",
    "New friend alert! {mentions} has joined *{group_name}*! We're so glad you're here! ❤️"
]

# Leave messages for groups
LEAVE_TEMPLATES = [
    "😢 {user} has left *{group_name}*. We'll miss you!",
    "Goodbye {user}! *{group_name}* won't be the same without you! 👋",
    "Oh no! {user} just left *{group_name}*. Come back soon! 😢",
    "{user} has departed from *{group_name}*. Wishing you all the best! ✨",
    "We'll miss you {user}! Hope to see you back in *{group_name}* someday! 💖",
    "Farewell {user}! Thanks for being part of *{group_name}*! 🙏",
    "{user} has left the building! *{group_name}* will remember you! 🌟",
    "Goodbye {user}! Remember, you're always welcome back to *{group_name}*! 🏠",
    "Safe travels {user}! *{group_name}* was better with you here! 🚀",
    "{user} has wandered off from *{group_name}*. The adventure continues elsewhere! 🗺️"
]

# Shayri/poetry for mass tagging
SHAYRI_TEMPLATES = [
    "दिल से दिल तक, एक पैगाम हमारा, आओ मिलकर बातें करें, यह अवसर है प्यारा। ✨",
    "तुम्हारी याद में हम खो गए हैं, आओ अब वापस लौट आओ, हम इंतज़ार कर रहे हैं। 💭",
    "ज़िन्दगी के इस सफर में, मिलना था तो मिल गए, अब साथ चलेंगे हम, मंज़िल अभी दूर है। 🚶‍♂️",
    "हर पल खूबसूरत है जब तुम साथ हो, हर लम्हा यादगार है जब तुम पास हो। ❤️",
    "कुछ लोग दिल में बसते हैं, कुछ लोग दिल को छूते हैं, जो दिल में बस जाते हैं, वो कभी भूलाए नहीं जाते। 💗",
    "Stars in the sky, dreams in our hearts, let's come together and never part. ✨",
    "Life is short, the world is wide, let's make some memories side by side. 🌏",
    "In this chat of friends so true, I'm sending all my love to you. 💌",
    "Words connect us, hearts direct us, in this group we're all precious. 👥",
    "Time flies, memories stay, in this group we laugh every day. 😄"
]

# Owner promotion templates
OWNER_PROMOTION_TEMPLATES = [
    "Hey everyone! Have you checked out @{username}'s profile? They're amazing! 🌟",
    "Just a reminder that @{username} is the awesome person who created this bot! Show them some love! ❤️",
    "If you're enjoying this bot, don't forget to thank @{username}! They work hard to keep it running! 🙏",
    "Quick shoutout to @{username} for making this bot possible! They're pretty cool! 😎",
    "Psst... Did you know @{username} is the genius behind this bot? Go say hi! 👋",
    "This message was brought to you by @{username} - the mastermind behind this bot! 🧠",
    "Special thanks to @{username} for creating me! They deserve all the credit! 🏆",
    "Without @{username}, I wouldn't exist! They're my creator and they're awesome! ✨",
    "Ever wondered who made this bot? It's the incredible @{username}! 🚀",
    "Fun fact: @{username} is the person who built this bot from scratch! Impressive, right? 💯"
]

# Proactive messages for periodic sending
PROACTIVE_TEMPLATES = [
    "Hey {name}! Just checking in to see how you're doing today! 😊",
    "Hi {name}! Miss chatting with you! What's new? 💕",
    "Hey there {name}! Just dropping by to say hello! How's everything? 👋",
    "{name}! Long time no chat! How have you been? 🤗",
    "Hey {name}! Just wanted to see how your day is going! 🌈",
    "Knock knock, {name}! Just thought I'd check in on you! 😄",
    "Hi {name}! I was just thinking about you and wanted to say hi! 💭",
    "Hey {name}! Anything exciting happening in your world? 🌟",
    "Just popping in to say hi, {name}! Hope you're having a great day! ☀️",
    "Hey {name}! What's the highlight of your day so far? 🎯"
]

# Stylish name templates
STYLISH_NAME_TEMPLATES = [
    "꧁༺ {name} ༻꧂",
    "★彡 {name} 彡★",
    "✰{name}✰",
    "『 {name} 』",
    "₊˚✧{name}✧˚₊",
    "⚡ {name} ⚡",
    "♡ {name} ♡",
    "✿ {name} ✿",
    "↫ {name} ↬",
    "⊰ {name} ⊱",
    "⧼ {name} ⧽",
    "〖 {name} 〗",
    "❅ {name} ❅",
    "⊹ {name} ⊹",
    "{name} ♔",
    "ꕥ {name} ꕥ",
    "⋆｡°✩ {name} ✩°｡⋆",
    "▄︻┻═┳一 {name}",
    "◤ {name} ◢",
    "╰☆☆ {name} ☆☆╮",
    "✧*。{name} 。*✧",
    "꒰ {name} ꒱",
    "{name} with emoji ❤️",
    "{name} with emoji 💋",
    "{name} with emoji 💫"
]

# Bio templates by mood
BIO_TEMPLATES = {
    "sad": [
        "In the rain of emotions, finding my own rainbow. 🌧️",
        "Some days are just heavy, and that's okay. 💭",
        "Finding beauty in the broken pieces. 💔",
        "Silent battles, loud recovery. 🌑→🌕",
        "It's okay not to be okay sometimes. 🖤",
        "Pages of my story include both tears and triumphs. 📖",
        "Finding strength in my vulnerability. 🕊️",
        "Healing is not linear, but I'm trying every day. 📈📉",
        "Beautiful things often come from the darkest times. 🌹",
        "Wearing my scars like constellations. ✨"
    ],
    "angry": [
        "Don't test my patience, I'm running low. ⏱️",
        "I'm not angry, I'm passionate about my boundaries. 🔥",
        "Sometimes the nice person gets tired. 😤",
        "Unapologetically expressing my emotions. 💢",
        "Warning: May contain explosive emotions. 💣",
        "If attitude had a face, it would be mine today. 👑",
        "I'm allergic to nonsense. 🙄",
        "My patience level is equivalent to a toddler without a nap. 🧨",
        "Too much fire to handle. 🔥",
        "Not in the mood. Try again later. ⚠️"
    ],
    "attitude": [
        "Born to stand out, not fit in. 💯",
        "Too glam to give a damn. ✨",
        "My vibe is on a frequency you can't access. 📶",
        "I'm not trying to be different. I just am. 💅",
        "I'm the exception, not the rule. 📏",
        "Life's too short for bad vibes. 🚫",
        "I decide my vibe. 👑",
        "Perfectly imperfect. 💫",
        "I bring the attitude to the party. 🎭",
        "Eyes forward, hustle strong. 👊",
        "Watch me shine like the star I am. ⭐",
        "My attitude is my identity and my signature. 📝",
        "Living life on my own terms. 📋"
    ],
    "happy": [
        "Collecting moments, not things. ✨",
        "Sunshine mixed with a little hurricane. 🌪️☀️",
        "Spreading positivity like confetti. 🎊",
        "Life is beautiful with the right mindset. 🌈",
        "Finding joy in the little things. 🌸",
        "Professional smile carrier. 😁",
        "Living my best life, one day at a time. 🌟",
        "Happiness is an inside job. 💫",
        "Choose happiness and watch life bloom. 🌻",
        "Radiating good vibes only. ✌️"
    ],
    "love": [
        "Heart full of love and dreams. ❤️",
        "Loving freely, living fully. 💗",
        "In love with life and all its possibilities. 💕",
        "Love is my religion. 🕊️",
        "Wearing my heart on my sleeve. 💌",
        "Love deeply, forgive quickly. 💖",
        "Finding magic in love's simplicity. ✨",
        "My heart has a story to tell. 📖❤️",
        "Love is the answer, no matter the question. 💞",
        "Capturing love in every moment. 📸💕"
    ]
}

def get_random_welcome_message() -> str:
    """Get a random welcome message template"""
    return random.choice(WELCOME_TEMPLATES)

def get_random_leave_message() -> str:
    """Get a random leave message template"""
    return random.choice(LEAVE_TEMPLATES)

def get_random_shayri() -> str:
    """Get a random shayri/poem for mass tagging"""
    return random.choice(SHAYRI_TEMPLATES)

def get_random_promotion_message() -> str:
    """Get a random owner promotion message"""
    return random.choice(OWNER_PROMOTION_TEMPLATES)

def get_random_proactive_message() -> str:
    """Get a random proactive message template"""
    return random.choice(PROACTIVE_TEMPLATES)

def get_stylish_name_templates() -> List[str]:
    """Get all stylish name templates"""
    return STYLISH_NAME_TEMPLATES

def get_bio_templates(mood: str = "attitude") -> List[str]:
    """Get bio templates for a specific mood"""
    if mood in BIO_TEMPLATES:
        return BIO_TEMPLATES[mood]
    else:
        # Default to attitude if mood not found
        return BIO_TEMPLATES["attitude"]
