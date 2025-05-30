import random

# List of welcome messages with a placeholder for the user's name
WELCOME_MESSAGES = [
    "Hey {name}! 👋 Welcome to the group! We're so happy to have you here. I'm Bestie, your AI assistant. Feel free to tag me if you need anything! 💕",
    
    "Welcome to the party, {name}! 🎉 Great to see you here! If you need any help, just tag me or ask the group - we're all friendly here!",
    
    "Look who just joined! Welcome, {name}! 🌟 Make yourself at home and don't be shy to start a conversation!",
    
    "Yay! {name} is here! 🥳 The group just got even better! Looking forward to chatting with you!",
    
    "{name} has entered the chat! 💃 Hello and welcome! Hope you have a wonderful time with us!",
    
    "A warm welcome to {name}! 🤗 So glad you found us! Feel free to introduce yourself when you're ready!",
    
    "Welcome aboard, {name}! 🚢 We're excited to have you join our community! I'm Bestie, your friendly AI companion here!",
    
    "Hey everyone, give a warm welcome to {name}! 👋 New friend alert! Hope you enjoy your time here!",
    
    "Welcome to the family, {name}! 💖 We're a friendly bunch, so don't hesitate to join the conversations!",
    
    "Awesome! {name} just joined us! 🌈 Welcome! Can't wait to get to know you better!"
]

def get_random_welcome_message(name):
    """
    Get a random welcome message with the user's name inserted
    
    Args:
        name (str): The name to insert into the welcome message
        
    Returns:
        str: A personalized welcome message
    """
    message = random.choice(WELCOME_MESSAGES)
    return message.format(name=name)
