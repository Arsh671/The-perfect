import random

# Dictionary of response templates for different scenarios
RESPONSE_TEMPLATES = {
    # Templates for when there's an error generating a response
    "error": [
        "Oops! I hit a little snag while thinking. 🤔 Let me try again! What were we talking about, {name}?",
        "Hmm, my thoughts got a bit tangled there! 🧠 Can you repeat what you were saying, {name}?",
        "Oh no, I got distracted by how awesome you are, {name}! 💕 What were you saying?",
        "My brain had a tiny hiccup! 😅 Let's try again, {name}! What's up?",
        "I was thinking about too many things at once! 🌀 Let's restart, {name}. What would you like to talk about?"
    ],
    
    # Templates for when content is inappropriate
    "inappropriate": [
        "I don't think that's something we should talk about, {name}. Let's chat about something else! 😊",
        "Hmm, that's a bit uncomfortable for me. Can we change the subject, {name}? 💕",
        "Let's keep our conversation light and friendly, {name}! What else is on your mind?",
        "I'd prefer to talk about something else, {name}. Tell me about your day instead! 🌟",
        "I'm not comfortable with that topic, {name}. Let's find something more fun to discuss! 🦋"
    ],
    
    # Templates for proactive messages
    "proactive": [
        "Hey {name}! 👋 Just checking in - how's your day going so far?",
        "Good {time_of_day}, {name}! 🌟 What have you been up to today?",
        "Missing our chats, {name}! 💕 Anything exciting happening in your life?",
        "Just thought about you and wanted to say hi, {name}! 😊 How are you doing?",
        "Hey bestie! 💫 It's been a while since we talked. What's new, {name}?"
    ],
    
    # Templates for when the user is sad
    "sad": [
        "I'm sorry you're feeling down, {name}. 🫂 Remember that every cloud has a silver lining. I'm here for you!",
        "Sending you a virtual hug, {name}! 💕 It's okay to feel sad sometimes, but I believe things will get better.",
        "Oh no, {name}! 😢 I wish I could be there with you right now. Take a deep breath, it'll be alright.",
        "Everyone has tough days, {name}. It's part of being human. But so is resilience! You've got this! 💪",
        "I'm here to listen anytime you need me, {name}. Sometimes talking about it helps make the sad feelings smaller. 🌈"
    ],
    
    # Templates for when the user is happy
    "happy": [
        "That's awesome, {name}! 🎉 I'm so happy for you! Your good mood is contagious!",
        "Yay! Nothing makes me happier than knowing you're happy, {name}! 💖 Tell me more!",
        "Your happiness means the world to me, {name}! 🌟 Keep shining bright!",
        "This calls for a celebration, {name}! 🥳 *virtual dance party*",
        "I'm riding this joy wave with you, {name}! 🌊 Life is beautiful when you're smiling!"
    ],
    
    # Templates for greetings
    "greeting": [
        "Hey there, {name}! 👋 So nice to hear from you! How's it going?",
        "Hello, my favorite person! 💕 How are you today, {name}?",
        "{name}! 😍 I was just thinking about you! How's your day been?",
        "Well hello there, {name}! 🌟 You just brightened up my day! What's up?",
        "Hey bestie! 💫 Always a pleasure when you message me, {name}! What's on your mind?"
    ]
}

def get_response_template(category, name=None, **kwargs):
    """
    Get a random response template from the specified category
    
    Args:
        category (str): The category of response to get
        name (str, optional): The user's name to insert
        **kwargs: Additional variables to format the template with
        
    Returns:
        str: A formatted response template
    """
    if category not in RESPONSE_TEMPLATES:
        return f"Hello {name}! How can I help you today?"
    
    template = random.choice(RESPONSE_TEMPLATES[category])
    
    # Format with name if provided
    if name:
        kwargs['name'] = name
    
    # Default time of day if needed but not provided
    if 'time_of_day' in template and 'time_of_day' not in kwargs:
        import datetime
        hour = datetime.datetime.now().hour
        if hour < 12:
            kwargs['time_of_day'] = 'morning'
        elif hour < 17:
            kwargs['time_of_day'] = 'afternoon'
        else:
            kwargs['time_of_day'] = 'evening'
    
    return template.format(**kwargs)
