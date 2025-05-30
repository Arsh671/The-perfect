import logging
import random
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

from database import execute_query, execute_insert
from models.user import User

logger = logging.getLogger(__name__)

# Game states
GAME_STATES = {}

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available games"""
    games_text = (
        "🎮 *Available Games* 🎮\n\n"
        "Choose a game to play:\n\n"
        "🎯 *Tic-Tac-Toe* - Play the classic game!\n"
        "🎲 *Truth or Dare* - Fun questions and challenges!\n"
        "🔢 *Guess the Number* - Test your luck!\n"
    )
    
    # Create keyboard with game options
    keyboard = [
        [InlineKeyboardButton("🎯 Tic-Tac-Toe", callback_data="play_tictactoe")],
        [InlineKeyboardButton("🎲 Truth or Dare", callback_data="play_truthordare")],
        [InlineKeyboardButton("🔢 Guess the Number", callback_data="play_guess")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        games_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def game_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection"""
    query = update.callback_query
    await query.answer()
    
    game = query.data.replace("play_", "")
    
    if game == "tictactoe":
        await start_tictactoe(update, context)
    elif game == "truthordare":
        await start_truthordare(update, context)
    elif game == "guess":
        await start_guess_game(update, context)

# Tic-Tac-Toe Game
async def tictactoe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new Tic-Tac-Toe game"""
    await start_tictactoe(update, context)

async def start_tictactoe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize a new Tic-Tac-Toe game"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Initialize game board (3x3 grid with empty cells)
    board = [[" " for _ in range(3)] for _ in range(3)]
    
    # Store game state
    GAME_STATES[chat_id] = {
        "type": "tictactoe",
        "board": board,
        "current_player": "X",
        "player_x": user_id,
        "player_o": None,  # Bot will play as O
        "status": "waiting_for_move"
    }
    
    # Save game to database
    game_data = json.dumps(GAME_STATES[chat_id])
    execute_insert(
        "INSERT INTO games (game_type, chat_id, status, data) VALUES (?, ?, ?, ?)",
        ("tictactoe", chat_id, "active", game_data)
    )
    
    # Create keyboard for the game board
    keyboard = create_tictactoe_keyboard(board)
    
    await update.effective_message.reply_text(
        "🎮 *Tic-Tac-Toe* 🎮\n\n"
        "You are X, I am O.\n"
        "Click on a button to make your move!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def create_tictactoe_keyboard(board):
    """Create keyboard for Tic-Tac-Toe board"""
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = board[i][j]
            # Display X, O, or empty cell
            text = cell if cell != " " else " "
            row.append(InlineKeyboardButton(text, callback_data=f"ttt_{i}_{j}"))
        keyboard.append(row)
    
    # Add a button to quit the game
    keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="ttt_quit")])
    
    return keyboard

async def tictactoe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Tic-Tac-Toe game moves"""
    query = update.callback_query
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if game exists for this chat
    if chat_id not in GAME_STATES or GAME_STATES[chat_id]["type"] != "tictactoe":
        await query.answer("No active Tic-Tac-Toe game found.")
        await query.edit_message_text("This game has expired. Start a new one with /tictactoe")
        return
    
    # Get game state
    game = GAME_STATES[chat_id]
    
    # Handle quit button
    if query.data == "ttt_quit":
        await query.answer("Game cancelled")
        await query.edit_message_text("Tic-Tac-Toe game was cancelled.")
        del GAME_STATES[chat_id]
        
        # Update game in database
        execute_query(
            "UPDATE games SET status = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
            ("cancelled", chat_id, "tictactoe", "active")
        )
        return
    
    # Check if it's the user's turn
    if game["current_player"] == "X" and user_id != game["player_x"]:
        await query.answer("This is not your game!")
        return
    
    # Parse move coordinates
    _, row, col = query.data.split("_")
    row, col = int(row), int(col)
    
    # Check if the cell is empty
    if game["board"][row][col] != " ":
        await query.answer("This cell is already taken!")
        return
    
    # Make the move
    game["board"][row][col] = game["current_player"]
    
    # Check for win or draw
    winner = check_tictactoe_winner(game["board"])
    is_draw = all(game["board"][i][j] != " " for i in range(3) for j in range(3))
    
    # Update message with new board
    keyboard = create_tictactoe_keyboard(game["board"])
    
    if winner:
        # Game over - someone won
        if winner == "X":
            result_text = "🎉 You won! Congratulations! 🏆"
        else:
            result_text = "I won this time! Better luck next game! 😉"
        
        await query.edit_message_text(
            f"🎮 *Tic-Tac-Toe* 🎮\n\n{result_text}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Clean up game state
        game["status"] = "finished"
        execute_query(
            "UPDATE games SET status = ?, data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
            ("finished", json.dumps(game), chat_id, "tictactoe", "active")
        )
        del GAME_STATES[chat_id]
    elif is_draw:
        # Game over - draw
        await query.edit_message_text(
            "🎮 *Tic-Tac-Toe* 🎮\n\n"
            "It's a draw! Good game! 👏",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Clean up game state
        game["status"] = "finished"
        execute_query(
            "UPDATE games SET status = ?, data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
            ("finished", json.dumps(game), chat_id, "tictactoe", "active")
        )
        del GAME_STATES[chat_id]
    else:
        # Game continues - switch player
        game["current_player"] = "O" if game["current_player"] == "X" else "X"
        
        # Update game in database
        execute_query(
            "UPDATE games SET data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
            (json.dumps(game), chat_id, "tictactoe", "active")
        )
        
        await query.edit_message_text(
            "🎮 *Tic-Tac-Toe* 🎮\n\n"
            f"Your move!" if game["current_player"] == "X" else "My turn! Thinking...",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # If it's the bot's turn, make a move
        if game["current_player"] == "O":
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(1)  # Simulate thinking
            
            # Make bot move
            row, col = get_bot_tictactoe_move(game["board"])
            game["board"][row][col] = "O"
            
            # Check for win or draw again
            winner = check_tictactoe_winner(game["board"])
            is_draw = all(game["board"][i][j] != " " for i in range(3) for j in range(3))
            
            # Update message with new board
            keyboard = create_tictactoe_keyboard(game["board"])
            
            if winner:
                # Game over - bot won
                await query.edit_message_text(
                    "🎮 *Tic-Tac-Toe* 🎮\n\n"
                    "I won this time! Better luck next game! 😉",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                # Clean up game state
                game["status"] = "finished"
                execute_query(
                    "UPDATE games SET status = ?, data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
                    ("finished", json.dumps(game), chat_id, "tictactoe", "active")
                )
                del GAME_STATES[chat_id]
            elif is_draw:
                # Game over - draw
                await query.edit_message_text(
                    "🎮 *Tic-Tac-Toe* 🎮\n\n"
                    "It's a draw! Good game! 👏",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                # Clean up game state
                game["status"] = "finished"
                execute_query(
                    "UPDATE games SET status = ?, data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
                    ("finished", json.dumps(game), chat_id, "tictactoe", "active")
                )
                del GAME_STATES[chat_id]
            else:
                # Game continues - player's turn
                game["current_player"] = "X"
                
                # Update game in database
                execute_query(
                    "UPDATE games SET data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
                    (json.dumps(game), chat_id, "tictactoe", "active")
                )
                
                await query.edit_message_text(
                    "🎮 *Tic-Tac-Toe* 🎮\n\n"
                    "I made my move. Your turn now!",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

def check_tictactoe_winner(board):
    """Check if there's a winner in Tic-Tac-Toe"""
    # Check rows
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != " ":
            return board[i][0]
    
    # Check columns
    for i in range(3):
        if board[0][i] == board[1][i] == board[2][i] != " ":
            return board[0][i]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    
    return None

def get_bot_tictactoe_move(board):
    """Get the bot's move in Tic-Tac-Toe with simple AI"""
    # Look for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == " ":
                board[i][j] = "O"
                if check_tictactoe_winner(board) == "O":
                    board[i][j] = " "  # Reset the cell
                    return i, j
                board[i][j] = " "  # Reset the cell
    
    # Look for blocking move
    for i in range(3):
        for j in range(3):
            if board[i][j] == " ":
                board[i][j] = "X"
                if check_tictactoe_winner(board) == "X":
                    board[i][j] = " "  # Reset the cell
                    return i, j
                board[i][j] = " "  # Reset the cell
    
    # Take center if available
    if board[1][1] == " ":
        return 1, 1
    
    # Take a corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)
    for i, j in corners:
        if board[i][j] == " ":
            return i, j
    
    # Take any available cell
    available_moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] == " "]
    return random.choice(available_moves) if available_moves else (0, 0)

# Truth or Dare Game
async def truthordare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new Truth or Dare game"""
    await start_truthordare(update, context)

async def start_truthordare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize a new Truth or Dare game"""
    # Create keyboard for Truth or Dare options
    keyboard = [
        [
            InlineKeyboardButton("🔍 Truth", callback_data="td_truth"),
            InlineKeyboardButton("🔥 Dare", callback_data="td_dare")
        ],
        [InlineKeyboardButton("🚫 End Game", callback_data="td_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "🎮 *Truth or Dare* 🎮\n\n"
        "Choose Truth or Dare!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

# Truth and Dare questions/challenges
TRUTH_QUESTIONS = [
    "What's the most embarrassing thing you've ever done?",
    "What's your biggest fear?",
    "What's the craziest dream you've ever had?",
    "What's your biggest pet peeve?",
    "What's the weirdest food combination you enjoy?",
    "What's a secret talent you have?",
    "What's the last lie you told?",
    "What's your most awkward date experience?",
    "What's your guilty pleasure?",
    "If you could swap lives with anyone for a day, who would it be?",
    "What's the most childish thing you still do?",
    "What's your biggest regret?",
    "What's the most trouble you've ever been in?",
    "What's the strangest thing you've done when alone?",
    "What's your most embarrassing childhood memory?",
    "What's the weirdest thing you've ever googled?",
    "What's a silly thing that makes you anxious?",
    "Have you ever had a crush on someone in this chat?",
    "What's the worst gift you've ever received?",
    "What's something you've never told anyone?"
]

DARE_CHALLENGES = [
    "Send a screenshot of your recent emoji usage",
    "Send a selfie with a funny face",
    "Text a random contact asking how their pet dinosaur is doing",
    "Share the last photo you took",
    "Write a short poem about someone in this chat",
    "Change your profile picture to what I send you for 24 hours",
    "Send a voice message singing your favorite song",
    "Text your crush/partner something sweet",
    "Share your screen time report",
    "Use only emojis for your next 5 messages",
    "Tell a joke that will make everyone laugh",
    "Send a screenshot of your most recent search history",
    "Set your status to 'I love potatoes' for 24 hours",
    "Tell a funny story from your childhood",
    "Do 10 push-ups (honor system!)",
    "Send a message to a friend saying 'I know what you did'",
    "Speak in an accent for your next 3 voice messages",
    "Share your favorite meme",
    "Send a message to a group chat with only the word 'quack'",
    "Write a silly haiku about the person who gave you this dare"
]

async def truthordare_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Truth or Dare game choices"""
    query = update.callback_query
    await query.answer()
    
    choice = query.data.replace("td_", "")
    
    if choice == "truth":
        # Give a random truth question
        question = random.choice(TRUTH_QUESTIONS)
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 Another Truth", callback_data="td_truth"),
                InlineKeyboardButton("🔥 Try a Dare", callback_data="td_dare")
            ],
            [InlineKeyboardButton("🚫 End Game", callback_data="td_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔍 *Truth* 🔍\n\n"
            f"{question}\n\n"
            "Answer truthfully! 😊",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    elif choice == "dare":
        # Give a random dare challenge
        challenge = random.choice(DARE_CHALLENGES)
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 Try a Truth", callback_data="td_truth"),
                InlineKeyboardButton("🔥 Another Dare", callback_data="td_dare")
            ],
            [InlineKeyboardButton("🚫 End Game", callback_data="td_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔥 *Dare* 🔥\n\n"
            f"{challenge}\n\n"
            "Do you accept? 😏",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    elif choice == "end":
        # End the game
        await query.edit_message_text(
            "Thanks for playing Truth or Dare! 👋\n"
            "Start a new game anytime with /truthordare"
        )

# Guess the Number Game
async def guess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new Guess the Number game"""
    await start_guess_game(update, context)

async def start_guess_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialize a new Guess the Number game"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Generate a random number between 1 and 100
    secret_number = random.randint(1, 100)
    
    # Store game state
    GAME_STATES[chat_id] = {
        "type": "guess",
        "secret_number": secret_number,
        "attempts": 0,
        "max_attempts": 10,
        "player": user_id,
        "status": "active"
    }
    
    # Save game to database
    game_data = json.dumps(GAME_STATES[chat_id])
    execute_insert(
        "INSERT INTO games (game_type, chat_id, status, data) VALUES (?, ?, ?, ?)",
        ("guess", chat_id, "active", game_data)
    )
    
    # Create keyboard with number ranges
    keyboard = [
        [
            InlineKeyboardButton("1-20", callback_data="guess_1-20"),
            InlineKeyboardButton("21-40", callback_data="guess_21-40"),
            InlineKeyboardButton("41-60", callback_data="guess_41-60")
        ],
        [
            InlineKeyboardButton("61-80", callback_data="guess_61-80"),
            InlineKeyboardButton("81-100", callback_data="guess_81-100")
        ],
        [InlineKeyboardButton("🚫 Quit Game", callback_data="guess_quit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        "🎮 *Guess the Number* 🎮\n\n"
        "I'm thinking of a number between 1 and 100.\n"
        "Can you guess it within 10 attempts?\n\n"
        "Choose a range or type a number:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def guess_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Guess the Number game callbacks"""
    query = update.callback_query
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if game exists for this chat
    if chat_id not in GAME_STATES or GAME_STATES[chat_id]["type"] != "guess":
        await query.answer("No active Guess the Number game found.")
        await query.edit_message_text("This game has expired. Start a new one with /guess")
        return
    
    # Get game state
    game = GAME_STATES[chat_id]
    
    # Check if it's the player's game
    if user_id != game["player"]:
        await query.answer("This is not your game!")
        return
    
    # Handle quit button
    if query.data == "guess_quit":
        await query.answer("Game cancelled")
        await query.edit_message_text(
            f"Game over! The number was {game['secret_number']}.\n"
            "Start a new game with /guess"
        )
        
        # Clean up game state
        game["status"] = "cancelled"
        execute_query(
            "UPDATE games SET status = ?, data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
            ("cancelled", json.dumps(game), chat_id, "guess", "active")
        )
        del GAME_STATES[chat_id]
        return
    
    # Handle range selection
    if query.data.startswith("guess_"):
        await query.answer()
        
        range_str = query.data.replace("guess_", "")
        start, end = map(int, range_str.split("-"))
        
        # Create keyboard with individual numbers in the selected range
        keyboard = []
        row = []
        for i in range(start, end + 1):
            row.append(InlineKeyboardButton(str(i), callback_data=f"guess_num_{i}"))
            if len(row) == 5:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        # Add back and quit buttons
        keyboard.append([
            InlineKeyboardButton("⬅️ Back", callback_data="guess_back"),
            InlineKeyboardButton("🚫 Quit", callback_data="guess_quit")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎮 *Guess the Number* 🎮\n\n"
            f"Selected range: {start}-{end}\n"
            f"Attempts: {game['attempts']}/{game['max_attempts']}\n\n"
            f"Choose a number:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        return
    
    # Handle back button
    if query.data == "guess_back":
        await query.answer()
        
        # Return to main range selection
        keyboard = [
            [
                InlineKeyboardButton("1-20", callback_data="guess_1-20"),
                InlineKeyboardButton("21-40", callback_data="guess_21-40"),
                InlineKeyboardButton("41-60", callback_data="guess_41-60")
            ],
            [
                InlineKeyboardButton("61-80", callback_data="guess_61-80"),
                InlineKeyboardButton("81-100", callback_data="guess_81-100")
            ],
            [InlineKeyboardButton("🚫 Quit Game", callback_data="guess_quit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎮 *Guess the Number* 🎮\n\n"
            f"I'm thinking of a number between 1 and 100.\n"
            f"Attempts: {game['attempts']}/{game['max_attempts']}\n\n"
            f"Choose a range:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        return
    
    # Handle number guess
    if query.data.startswith("guess_num_"):
        guess = int(query.data.replace("guess_num_", ""))
        
        # Increment attempts
        game["attempts"] += 1
        
        secret_number = game["secret_number"]
        attempts = game["attempts"]
        max_attempts = game["max_attempts"]
        
        # Check the guess
        if guess == secret_number:
            # Correct guess
            await query.answer("Correct! 🎉")
            
            await query.edit_message_text(
                f"🎮 *Guess the Number* 🎮\n\n"
                f"🎉 *Congratulations!* 🎉\n"
                f"You guessed the correct number: {secret_number}\n"
                f"It took you {attempts} attempts.\n\n"
                f"Start a new game with /guess",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Clean up game state
            game["status"] = "won"
            execute_query(
                "UPDATE games SET status = ?, data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
                ("won", json.dumps(game), chat_id, "guess", "active")
            )
            del GAME_STATES[chat_id]
        elif attempts >= max_attempts:
            # Out of attempts
            await query.answer("Game over!")
            
            await query.edit_message_text(
                f"🎮 *Guess the Number* 🎮\n\n"
                f"Game over! You've used all {max_attempts} attempts.\n"
                f"The number was {secret_number}.\n\n"
                f"Start a new game with /guess",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Clean up game state
            game["status"] = "lost"
            execute_query(
                "UPDATE games SET status = ?, data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
                ("lost", json.dumps(game), chat_id, "guess", "active")
            )
            del GAME_STATES[chat_id]
        else:
            # Wrong guess
            hint = "higher" if guess < secret_number else "lower"
            
            # Update game in database
            execute_query(
                "UPDATE games SET data = ? WHERE chat_id = ? AND game_type = ? AND status = ?",
                (json.dumps(game), chat_id, "guess", "active")
            )
            
            await query.answer(f"Wrong! Try {hint}.")
            
            # Create keyboard with ranges
            keyboard = [
                [
                    InlineKeyboardButton("1-20", callback_data="guess_1-20"),
                    InlineKeyboardButton("21-40", callback_data="guess_21-40"),
                    InlineKeyboardButton("41-60", callback_data="guess_41-60")
                ],
                [
                    InlineKeyboardButton("61-80", callback_data="guess_61-80"),
                    InlineKeyboardButton("81-100", callback_data="guess_81-100")
                ],
                [InlineKeyboardButton("🚫 Quit Game", callback_data="guess_quit")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🎮 *Guess the Number* 🎮\n\n"
                f"Your guess: {guess}\n"
                f"Hint: The number is {hint}.\n"
                f"Attempts: {attempts}/{max_attempts}\n\n"
                f"Choose a range:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

def register_game_handlers(application):
    """Register all game-related handlers"""
    # Import asyncio for the tic-tac-toe bot move delay
    global asyncio
    import asyncio
    
    # Game commands
    application.add_handler(CommandHandler("games", games_command))
    application.add_handler(CommandHandler("tictactoe", tictactoe_command))
    application.add_handler(CommandHandler("truthordare", truthordare_command))
    application.add_handler(CommandHandler("guess", guess_command))
    
    # Game callbacks
    application.add_handler(CallbackQueryHandler(game_selection_callback, pattern=r'^play_'))
    application.add_handler(CallbackQueryHandler(tictactoe_callback, pattern=r'^ttt_'))
    application.add_handler(CallbackQueryHandler(truthordare_callback, pattern=r'^td_'))
    application.add_handler(CallbackQueryHandler(guess_callback, pattern=r'^guess_'))
