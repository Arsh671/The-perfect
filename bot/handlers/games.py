import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from telegram.constants import ParseMode
from bot.config import ENABLE_GAMES

logger = logging.getLogger(__name__)

def register_game_handlers(application: Application):
    """Register all game-related handlers."""
    if not ENABLE_GAMES:
        return
    
    # Tic Tac Toe
    application.add_handler(CommandHandler("tictactoe", tictactoe_start))
    application.add_handler(CallbackQueryHandler(tictactoe_button, pattern="^ttt_"))
    
    # Truth or Dare
    application.add_handler(CommandHandler("truth", truth_command))
    application.add_handler(CommandHandler("dare", dare_command))
    
    # Guess the number
    application.add_handler(CommandHandler("guess", guess_start))
    application.add_handler(CallbackQueryHandler(guess_button, pattern="^guess_"))

# Tic Tac Toe game
async def tictactoe_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new Tic Tac Toe game."""
    # Initialize the board
    board = ["_"] * 9
    context.user_data["ttt_board"] = board
    context.user_data["ttt_player_turn"] = True  # True for player (X), False for bot (O)
    
    # Create the keyboard
    keyboard = build_ttt_keyboard(board)
    
    await update.message.reply_text(
        "🎮 *Tic Tac Toe* 🎮\n\n"
        "You are X, I am O. Your turn first!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def build_ttt_keyboard(board):
    """Build the inline keyboard for Tic Tac Toe."""
    keyboard = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            index = i + j
            if board[index] == "_":
                text = " "
            elif board[index] == "X":
                text = "❌"
            else:  # O
                text = "⭕"
            row.append(InlineKeyboardButton(text, callback_data=f"ttt_{index}"))
        keyboard.append(row)
    return keyboard

async def tictactoe_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses in Tic Tac Toe."""
    query = update.callback_query
    await query.answer()
    
    # Get the board from user_data
    board = context.user_data.get("ttt_board", ["_"] * 9)
    player_turn = context.user_data.get("ttt_player_turn", True)
    
    # Extract the cell index from callback data
    index = int(query.data.split("_")[1])
    
    # Check if the cell is already taken
    if board[index] != "_":
        return
    
    # Check if it's the player's turn
    if not player_turn:
        return
    
    # Update the board with player's move
    board[index] = "X"
    context.user_data["ttt_player_turn"] = False
    
    # Check if the player won
    if check_win(board, "X"):
        keyboard = build_ttt_keyboard(board)
        await query.edit_message_text(
            "🎮 *Tic Tac Toe* 🎮\n\n"
            "Congratulations! You won! 🏆",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check if the board is full (draw)
    if "_" not in board:
        keyboard = build_ttt_keyboard(board)
        await query.edit_message_text(
            "🎮 *Tic Tac Toe* 🎮\n\n"
            "It's a draw! 🤝",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Bot's turn
    # Simple AI: first try to win, then block player, then random move
    bot_index = get_best_move(board)
    board[bot_index] = "O"
    context.user_data["ttt_player_turn"] = True
    
    # Check if the bot won
    if check_win(board, "O"):
        keyboard = build_ttt_keyboard(board)
        await query.edit_message_text(
            "🎮 *Tic Tac Toe* 🎮\n\n"
            "I won this time! Better luck next time! 😊",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check if the board is full (draw)
    if "_" not in board:
        keyboard = build_ttt_keyboard(board)
        await query.edit_message_text(
            "🎮 *Tic Tac Toe* 🎮\n\n"
            "It's a draw! 🤝",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Continue the game
    keyboard = build_ttt_keyboard(board)
    await query.edit_message_text(
        "🎮 *Tic Tac Toe* 🎮\n\n"
        "Your turn!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def check_win(board, player):
    """Check if the player has won."""
    # Check rows
    for i in range(0, 9, 3):
        if board[i] == board[i+1] == board[i+2] == player:
            return True
    
    # Check columns
    for i in range(3):
        if board[i] == board[i+3] == board[i+6] == player:
            return True
    
    # Check diagonals
    if board[0] == board[4] == board[8] == player:
        return True
    if board[2] == board[4] == board[6] == player:
        return True
    
    return False

def get_best_move(board):
    """Get the best move for the bot."""
    # Check if bot can win
    for i in range(9):
        if board[i] == "_":
            # Try the move
            board[i] = "O"
            if check_win(board, "O"):
                board[i] = "_"  # Reset the board
                return i
            board[i] = "_"  # Reset the board
    
    # Check if player can win and block
    for i in range(9):
        if board[i] == "_":
            # Try the move
            board[i] = "X"
            if check_win(board, "X"):
                board[i] = "_"  # Reset the board
                return i
            board[i] = "_"  # Reset the board
    
    # Take center if available
    if board[4] == "_":
        return 4
    
    # Take corners if available
    corners = [0, 2, 6, 8]
    random.shuffle(corners)
    for corner in corners:
        if board[corner] == "_":
            return corner
    
    # Take any available cell
    available = [i for i, cell in enumerate(board) if cell == "_"]
    return random.choice(available) if available else 0

# Truth or Dare game
async def truth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random truth question."""
    truths = [
        "What's the most embarrassing thing you've ever done?",
        "What's your biggest fear?",
        "What's the craziest dream you've ever had?",
        "What's the most childish thing you still do?",
        "What's a secret you've never told anyone?",
        "What's the most embarrassing thing in your search history?",
        "What's the worst gift you've ever received?",
        "What's your guilty pleasure?",
        "If you could be invisible for a day, what would you do?",
        "What's the weirdest food combination you enjoy?",
        "What's your biggest pet peeve?",
        "What's your most embarrassing childhood memory?",
        "If you could switch lives with someone for a day, who would it be and why?",
        "What's the most rebellious thing you've ever done?",
        "What's something you're passionate about but people would be surprised to know?",
        "If you could go back in time and change one decision, what would it be?",
        "What's the most embarrassing thing your parents caught you doing?",
        "What's your biggest regret?",
        "If you had to eat one food for the rest of your life, what would it be?",
        "What's the strangest place you've ever fallen asleep?"
    ]
    
    # Select a random truth question
    truth = random.choice(truths)
    
    # Create keyboard with button to get another truth
    keyboard = [
        [InlineKeyboardButton("🔄 Another Truth", callback_data="guess_truth")],
        [InlineKeyboardButton("🎲 Try a Dare", callback_data="guess_dare")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔮 *Truth Question* 🔮\n\n"
        f"{truth}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def dare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random dare challenge."""
    dares = [
        "Send the last photo you took.",
        "Message someone you haven't talked to in at least 6 months.",
        "Type with your elbows for the next three messages.",
        "Send a voice message singing your favorite song.",
        "Change your profile picture to whatever the group chooses for 24 hours.",
        "Tell a joke that makes everyone laugh.",
        "Share the most embarrassing photo of yourself.",
        "Talk in an accent for the next 10 minutes.",
        "Call a friend and tell them a completely absurd story.",
        "Do 10 push-ups right now.",
        "Show the group your screen time report.",
        "Text your crush or someone you find attractive.",
        "Put as many clothes on as possible in 60 seconds.",
        "Send a message to a family member saying 'I know your secret'.",
        "Speak in rhymes for the next 5 minutes.",
        "Let someone else post a status on your social media.",
        "Say the alphabet backward in under 30 seconds.",
        "Show the last 5 people you texted and what the messages said.",
        "Draw a portrait of someone in the group and share it.",
        "Call a random number and sing Happy Birthday."
    ]
    
    # Select a random dare challenge
    dare = random.choice(dares)
    
    # Create keyboard with button to get another dare
    keyboard = [
        [InlineKeyboardButton("🔄 Another Dare", callback_data="guess_dare")],
        [InlineKeyboardButton("🔮 Try a Truth", callback_data="guess_truth")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎲 *Dare Challenge* 🎲\n\n"
        f"{dare}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

# Guess the number game
async def guess_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new Guess the Number game."""
    # Generate a random number between 1 and 100
    secret_number = random.randint(1, 100)
    context.user_data["guess_number"] = secret_number
    context.user_data["guess_attempts"] = 0
    
    # Create keyboard with number ranges
    keyboard = [
        [
            InlineKeyboardButton("1-25", callback_data="guess_1_25"),
            InlineKeyboardButton("26-50", callback_data="guess_26_50")
        ],
        [
            InlineKeyboardButton("51-75", callback_data="guess_51_75"),
            InlineKeyboardButton("76-100", callback_data="guess_76_100")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔢 *Guess the Number* 🔢\n\n"
        "I'm thinking of a number between 1 and 100. Can you guess it?\n"
        "Choose a range to narrow down your search:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def guess_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses in Guess the Number game."""
    query = update.callback_query
    await query.answer()
    
    # Check if it's Truth or Dare callback
    if query.data == "guess_truth":
        # Get a new truth question
        truths = [
            "What's the most embarrassing thing you've ever done?",
            "What's your biggest fear?",
            "What's the craziest dream you've ever had?",
            "What's the most childish thing you still do?",
            "What's a secret you've never told anyone?",
            "What's the most embarrassing thing in your search history?",
            "What's the worst gift you've ever received?",
            "What's your guilty pleasure?",
            "If you could be invisible for a day, what would you do?",
            "What's the weirdest food combination you enjoy?",
            "What's your biggest pet peeve?",
            "What's your most embarrassing childhood memory?",
            "If you could switch lives with someone for a day, who would it be and why?",
            "What's the most rebellious thing you've ever done?",
            "What's something you're passionate about but people would be surprised to know?",
            "If you could go back in time and change one decision, what would it be?",
            "What's the most embarrassing thing your parents caught you doing?",
            "What's your biggest regret?",
            "If you had to eat one food for the rest of your life, what would it be?",
            "What's the strangest place you've ever fallen asleep?"
        ]
        
        # Select a random truth question
        truth = random.choice(truths)
        
        # Create keyboard with button to get another truth
        keyboard = [
            [InlineKeyboardButton("🔄 Another Truth", callback_data="guess_truth")],
            [InlineKeyboardButton("🎲 Try a Dare", callback_data="guess_dare")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🔮 *Truth Question* 🔮\n\n"
            f"{truth}",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    elif query.data == "guess_dare":
        # Get a new dare challenge
        dares = [
            "Send the last photo you took.",
            "Message someone you haven't talked to in at least 6 months.",
            "Type with your elbows for the next three messages.",
            "Send a voice message singing your favorite song.",
            "Change your profile picture to whatever the group chooses for 24 hours.",
            "Tell a joke that makes everyone laugh.",
            "Share the most embarrassing photo of yourself.",
            "Talk in an accent for the next 10 minutes.",
            "Call a friend and tell them a completely absurd story.",
            "Do 10 push-ups right now.",
            "Show the group your screen time report.",
            "Text your crush or someone you find attractive.",
            "Put as many clothes on as possible in 60 seconds.",
            "Send a message to a family member saying 'I know your secret'.",
            "Speak in rhymes for the next 5 minutes.",
            "Let someone else post a status on your social media.",
            "Say the alphabet backward in under 30 seconds.",
            "Show the last 5 people you texted and what the messages said.",
            "Draw a portrait of someone in the group and share it.",
            "Call a random number and sing Happy Birthday."
        ]
        
        # Select a random dare challenge
        dare = random.choice(dares)
        
        # Create keyboard with button to get another dare
        keyboard = [
            [InlineKeyboardButton("🔄 Another Dare", callback_data="guess_dare")],
            [InlineKeyboardButton("🔮 Try a Truth", callback_data="guess_truth")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎲 *Dare Challenge* 🎲\n\n"
            f"{dare}",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # For Guess the Number game
    # Get the secret number and attempts
    secret_number = context.user_data.get("guess_number")
    attempts = context.user_data.get("guess_attempts", 0)
    
    if not secret_number:
        # Start a new game if no secret number exists
        await query.edit_message_text(
            "Let's start a new game! Use /guess to play Guess the Number."
        )
        return
    
    # Increment attempts
    attempts += 1
    context.user_data["guess_attempts"] = attempts
    
    # Extract the range from callback data
    if "_" in query.data:
        parts = query.data.split("_")
        if len(parts) >= 3:
            min_val = int(parts[1])
            max_val = int(parts[2])
            
            if min_val <= secret_number <= max_val:
                # The secret number is in this range
                if max_val - min_val <= 5:
                    # Range is small enough to list individual numbers
                    keyboard = []
                    row = []
                    for num in range(min_val, max_val + 1):
                        row.append(InlineKeyboardButton(str(num), callback_data=f"guess_num_{num}"))
                        if len(row) == 5:
                            keyboard.append(row)
                            row = []
                    if row:
                        keyboard.append(row)
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"🔢 *Guess the Number* 🔢\n\n"
                        f"Getting closer! The number is between {min_val} and {max_val}.\n"
                        f"Attempts: {attempts}",
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    # Split the range into smaller chunks
                    mid = (min_val + max_val) // 2
                    keyboard = [
                        [
                            InlineKeyboardButton(f"{min_val}-{mid}", callback_data=f"guess_{min_val}_{mid}"),
                            InlineKeyboardButton(f"{mid+1}-{max_val}", callback_data=f"guess_{mid+1}_{max_val}")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"🔢 *Guess the Number* 🔢\n\n"
                        f"Good! The number is between {min_val} and {max_val}.\n"
                        f"Attempts: {attempts}",
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                # The secret number is not in this range
                keyboard = [
                    [InlineKeyboardButton("Try Again", callback_data="guess_1_100")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🔢 *Guess the Number* 🔢\n\n"
                    f"The number is NOT between {min_val} and {max_val}.\n"
                    f"Attempts: {attempts}",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
        elif len(parts) >= 2 and parts[1] == "1" and parts[2] == "100":
            # Reset the game to the beginning
            keyboard = [
                [
                    InlineKeyboardButton("1-25", callback_data="guess_1_25"),
                    InlineKeyboardButton("26-50", callback_data="guess_26_50")
                ],
                [
                    InlineKeyboardButton("51-75", callback_data="guess_51_75"),
                    InlineKeyboardButton("76-100", callback_data="guess_76_100")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔢 *Guess the Number* 🔢\n\n"
                "I'm thinking of a number between 1 and 100. Can you guess it?\n"
                f"Attempts: {attempts}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    # Check if it's a direct number guess
    elif "num_" in query.data:
        guess = int(query.data.split("_")[2])
        
        if guess == secret_number:
            # Correct guess
            keyboard = [
                [InlineKeyboardButton("🎮 Play Again", callback_data="guess_play_again")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🎉 *Congratulations!* 🎉\n\n"
                f"You guessed the number {secret_number} correctly in {attempts} attempts!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Reset the game
            context.user_data.pop("guess_number", None)
            context.user_data.pop("guess_attempts", None)
        else:
            # Wrong guess
            hint = "higher" if secret_number > guess else "lower"
            
            # Determine the new range based on the hint
            min_val = guess + 1 if hint == "higher" else 1
            max_val = guess - 1 if hint == "lower" else 100
            
            keyboard = [
                [InlineKeyboardButton(f"{min_val}-{max_val}", callback_data=f"guess_{min_val}_{max_val}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🔢 *Guess the Number* 🔢\n\n"
                f"Not quite! The number is {hint} than {guess}.\n"
                f"Attempts: {attempts}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif query.data == "guess_play_again":
        # Start a new game
        secret_number = random.randint(1, 100)
        context.user_data["guess_number"] = secret_number
        context.user_data["guess_attempts"] = 0
        
        # Create keyboard with number ranges
        keyboard = [
            [
                InlineKeyboardButton("1-25", callback_data="guess_1_25"),
                InlineKeyboardButton("26-50", callback_data="guess_26_50")
            ],
            [
                InlineKeyboardButton("51-75", callback_data="guess_51_75"),
                InlineKeyboardButton("76-100", callback_data="guess_76_100")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔢 *Guess the Number* 🔢\n\n"
            "I'm thinking of a number between 1 and 100. Can you guess it?\n"
            "Choose a range to narrow down your search:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
