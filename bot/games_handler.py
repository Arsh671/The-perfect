#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Games handler for the Telegram Bot
"""

import logging
import random
from typing import Dict, List, Any, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.database import log_game_result
from bot.games.tictactoe import (create_tictactoe_board, check_tictactoe_winner, 
                                make_tictactoe_move)
from bot.games.truth_or_dare import get_truth_question, get_dare_challenge
from bot.games.guess import start_number_guess, make_number_guess, start_word_guess, make_word_guess

logger = logging.getLogger(__name__)

# Store active games
active_games: Dict[str, Dict[str, Any]] = {}

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /game command - show available games"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Create keyboard with game options
    keyboard = [
        [
            InlineKeyboardButton("🎮 Tic-Tac-Toe", callback_data="ttt_new")
        ],
        [
            InlineKeyboardButton("🎯 Truth or Dare", callback_data="tod_choice")
        ],
        [
            InlineKeyboardButton("🔢 Guess the Number", callback_data="guess_number_new")
        ],
        [
            InlineKeyboardButton("🔤 Guess the Word", callback_data="guess_word_new")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=f"Hi {user.first_name}! Choose a game to play:",
        reply_markup=reply_markup
    )

async def guess_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /guess command - show guessing game options"""
    if update.effective_chat is None or update.effective_user is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Create keyboard with guess game options
    keyboard = [
        [
            InlineKeyboardButton("🔢 Guess the Number", callback_data="guess_number_new")
        ],
        [
            InlineKeyboardButton("🔤 Guess the Word", callback_data="guess_word_new")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat.id,
        text=f"Hi {user.first_name}! Choose a guessing game to play:",
        reply_markup=reply_markup
    )

async def tictactoe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Tic-Tac-Toe game callbacks"""
    if update.effective_chat is None or update.effective_user is None or update.callback_query is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    callback_data = query.data
    
    # Acknowledge the callback
    await query.answer()
    
    # New game
    if callback_data == "ttt_new":
        # Create a new game
        game_id = f"ttt_{chat.id}_{user.id}"
        board = create_tictactoe_board()
        
        active_games[game_id] = {
            "board": board,
            "player": "X",  # User is X, bot is O
            "user_id": user.id
        }
        
        # Create keyboard from board
        keyboard = []
        for i in range(3):
            row = []
            for j in range(3):
                cell = board[i][j]
                button_text = "·" if cell == " " else cell
                row.append(InlineKeyboardButton(button_text, callback_data=f"ttt_move_{i}_{j}"))
            keyboard.append(row)
        
        # Add quit button
        keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="ttt_quit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🎮 *Tic-Tac-Toe*\n\n{user.first_name} (X) vs Bot (O)\n\nYour turn! Select a position:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Quit game
    elif callback_data == "ttt_quit":
        game_id = f"ttt_{chat.id}_{user.id}"
        if game_id in active_games:
            del active_games[game_id]
        
        await query.edit_message_text(
            text="Game ended. Thanks for playing! Use /game to start a new game."
        )
    
    # Move
    elif callback_data.startswith("ttt_move_"):
        game_id = f"ttt_{chat.id}_{user.id}"
        
        # Check if game exists and belongs to this user
        if game_id not in active_games or active_games[game_id]["user_id"] != user.id:
            await query.edit_message_text(
                text="This game has ended or doesn't belong to you. Use /game to start a new game."
            )
            return
        
        game = active_games[game_id]
        
        # Parse move coordinates
        _, _, row, col = callback_data.split("_")
        row, col = int(row), int(col)
        
        # Check if cell is empty
        if game["board"][row][col] != " ":
            await query.answer("That cell is already taken! Choose another one.")
            return
        
        # Make player's move
        game["board"][row][col] = "X"
        
        # Check for winner or draw
        winner = check_tictactoe_winner(game["board"])
        
        if winner or all(" " not in row for row in game["board"]):
            # Game ended
            result = ""
            if winner == "X":
                result = f"🎉 {user.first_name} won! 🎉"
                log_game_result(user.id, "tictactoe", "win")
            elif winner == "O":
                result = "😅 Bot won! Better luck next time."
                log_game_result(user.id, "tictactoe", "loss")
            else:
                result = "🤝 It's a draw!"
                log_game_result(user.id, "tictactoe", "draw")
            
            # Create final keyboard
            keyboard = []
            for i in range(3):
                row = []
                for j in range(3):
                    cell = game["board"][i][j]
                    button_text = "·" if cell == " " else cell
                    row.append(InlineKeyboardButton(button_text, callback_data=f"ttt_none"))
                keyboard.append(row)
            
            # Add new game button
            keyboard.append([InlineKeyboardButton("🔄 New Game", callback_data="ttt_new")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"🎮 *Tic-Tac-Toe*\n\n{result}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Remove game from active games
            del active_games[game_id]
            return
        
        # Bot's turn
        bot_row, bot_col = make_tictactoe_move(game["board"])
        game["board"][bot_row][bot_col] = "O"
        
        # Check for winner or draw again
        winner = check_tictactoe_winner(game["board"])
        
        # Create updated keyboard
        keyboard = []
        for i in range(3):
            row = []
            for j in range(3):
                cell = game["board"][i][j]
                button_text = "·" if cell == " " else cell
                row.append(InlineKeyboardButton(button_text, callback_data=f"ttt_move_{i}_{j}"))
            keyboard.append(row)
        
        # Add quit button
        keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="ttt_quit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if winner or all(" " not in row for row in game["board"]):
            # Game ended after bot's move
            result = ""
            if winner == "X":
                result = f"🎉 {user.first_name} won! 🎉"
                log_game_result(user.id, "tictactoe", "win")
            elif winner == "O":
                result = "😅 Bot won! Better luck next time."
                log_game_result(user.id, "tictactoe", "loss")
            else:
                result = "🤝 It's a draw!"
                log_game_result(user.id, "tictactoe", "draw")
            
            # Create final keyboard
            keyboard = []
            for i in range(3):
                row = []
                for j in range(3):
                    cell = game["board"][i][j]
                    button_text = "·" if cell == " " else cell
                    row.append(InlineKeyboardButton(button_text, callback_data=f"ttt_none"))
                keyboard.append(row)
            
            # Add new game button
            keyboard.append([InlineKeyboardButton("🔄 New Game", callback_data="ttt_new")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"🎮 *Tic-Tac-Toe*\n\n{result}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Remove game from active games
            del active_games[game_id]
        else:
            # Game continues
            await query.edit_message_text(
                text=f"🎮 *Tic-Tac-Toe*\n\n{user.first_name} (X) vs Bot (O)\n\nYour turn! Select a position:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

async def truth_or_dare_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Truth or Dare game callbacks"""
    if update.effective_chat is None or update.effective_user is None or update.callback_query is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    callback_data = query.data
    
    # Acknowledge the callback
    await query.answer()
    
    # Handle different states
    if callback_data == "tod_choice":
        # Show truth or dare options
        keyboard = [
            [
                InlineKeyboardButton("🤔 Truth", callback_data="tod_truth_normal"),
                InlineKeyboardButton("🔥 Spicy Truth", callback_data="tod_truth_spicy")
            ],
            [
                InlineKeyboardButton("😎 Dare", callback_data="tod_dare_normal"),
                InlineKeyboardButton("🔥 Spicy Dare", callback_data="tod_dare_spicy")
            ],
            [
                InlineKeyboardButton("🔙 Back to Games", callback_data="tod_back")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🎯 *Truth or Dare*\n\nHi {user.first_name}! Choose an option:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "tod_back" or callback_data == "guess_back":
        # Go back to games menu
        await game_command(update, context)
    
    elif callback_data.startswith("tod_truth_"):
        # Get truth question
        category = callback_data.split("_")[2]
        question = get_truth_question(category)
        
        # Create keyboard for next question
        keyboard = [
            [
                InlineKeyboardButton("🔄 Another Truth", callback_data=callback_data)
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="tod_choice")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🤔 *Truth Question*\n\n{question}",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log game result
        log_game_result(user.id, "truth_or_dare", f"truth_{category}")
    
    elif callback_data.startswith("tod_dare_"):
        # Get dare challenge
        category = callback_data.split("_")[2]
        challenge = get_dare_challenge(category)
        
        # Create keyboard for next challenge
        keyboard = [
            [
                InlineKeyboardButton("🔄 Another Dare", callback_data=callback_data)
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="tod_choice")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"😎 *Dare Challenge*\n\n{challenge}",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log game result
        log_game_result(user.id, "truth_or_dare", f"dare_{category}")

async def guess_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Guess (number/word) game callbacks"""
    if update.effective_chat is None or update.effective_user is None or update.callback_query is None:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    callback_data = query.data
    
    # Acknowledge the callback
    await query.answer()
    
    # Number guessing game
    if callback_data == "guess_number_new":
        # Start new number guessing game
        game_id = f"guess_number_{chat.id}_{user.id}"
        game_data = start_number_guess()
        
        active_games[game_id] = {
            "number": game_data["number"],
            "attempts": game_data["attempts"],
            "max_attempts": game_data["max_attempts"],
            "range_min": game_data["range_min"],
            "range_max": game_data["range_max"],
            "user_id": user.id
        }
        
        # Create reply keyboard
        keyboard = []
        
        # Add number buttons
        range_size = game_data["range_max"] - game_data["range_min"] + 1
        if range_size <= 10:
            # Show all numbers if range is small
            row = []
            for num in range(game_data["range_min"], game_data["range_max"] + 1):
                row.append(InlineKeyboardButton(str(num), callback_data=f"guess_number_{num}"))
                if len(row) == 5:  # 5 buttons per row
                    keyboard.append(row)
                    row = []
            if row:  # Add remaining buttons
                keyboard.append(row)
        else:
            # Show ranges if range is large
            step = range_size // 5
            for i in range(5):
                start = game_data["range_min"] + i * step
                end = game_data["range_min"] + (i + 1) * step - 1
                if i == 4:  # Last range
                    end = game_data["range_max"]
                keyboard.append([InlineKeyboardButton(f"{start}-{end}", callback_data=f"guess_number_range_{start}_{end}")])
        
        # Add quit button
        keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="guess_number_quit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🔢 *Guess the Number*\n\nI'm thinking of a number between {game_data['range_min']} and {game_data['range_max']}.\n\n"
                 f"You have {game_data['max_attempts']} attempts remaining. Take a guess!",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data.startswith("guess_number_range_"):
        # Handle range selection
        game_id = f"guess_number_{chat.id}_{user.id}"
        
        # Check if game exists and belongs to this user
        if game_id not in active_games or active_games[game_id]["user_id"] != user.id:
            await query.edit_message_text(
                text="This game has ended or doesn't belong to you. Use /game to start a new game."
            )
            return
        
        game = active_games[game_id]
        
        # Parse range
        _, _, range_min, range_max = callback_data.split("_")
        range_min, range_max = int(range_min), int(range_max)
        
        # Create keyboard with individual numbers in the selected range
        keyboard = []
        row = []
        for num in range(range_min, range_max + 1):
            row.append(InlineKeyboardButton(str(num), callback_data=f"guess_number_{num}"))
            if len(row) == 5:  # 5 buttons per row
                keyboard.append(row)
                row = []
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        # Add back and quit buttons
        keyboard.append([
            InlineKeyboardButton("🔙 Back", callback_data="guess_number_back"),
            InlineKeyboardButton("🚫 Quit", callback_data="guess_number_quit")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🔢 *Guess the Number*\n\nI'm thinking of a number between {game['range_min']} and {game['range_max']}.\n\n"
                 f"You have {game['max_attempts'] - game['attempts']} attempts remaining. Select a number:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "guess_number_back":
        # Go back to main number guess view
        game_id = f"guess_number_{chat.id}_{user.id}"
        
        # Check if game exists and belongs to this user
        if game_id not in active_games or active_games[game_id]["user_id"] != user.id:
            await query.edit_message_text(
                text="This game has ended or doesn't belong to you. Use /game to start a new game."
            )
            return
        
        game = active_games[game_id]
        
        # Create reply keyboard
        keyboard = []
        
        # Add range buttons
        range_size = game["range_max"] - game["range_min"] + 1
        step = range_size // 5
        for i in range(5):
            start = game["range_min"] + i * step
            end = game["range_min"] + (i + 1) * step - 1
            if i == 4:  # Last range
                end = game["range_max"]
            keyboard.append([InlineKeyboardButton(f"{start}-{end}", callback_data=f"guess_number_range_{start}_{end}")])
        
        # Add quit button
        keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="guess_number_quit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🔢 *Guess the Number*\n\nI'm thinking of a number between {game['range_min']} and {game['range_max']}.\n\n"
                 f"You have {game['max_attempts'] - game['attempts']} attempts remaining. Select a range:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "guess_number_quit":
        # Quit number guessing game
        game_id = f"guess_number_{chat.id}_{user.id}"
        
        if game_id in active_games:
            game = active_games[game_id]
            
            # Log game result
            log_game_result(user.id, "guess_number", "quit")
            
            await query.edit_message_text(
                text=f"Game ended. The number was {game['number']}. Use /game to start a new game."
            )
            
            # Remove game from active games
            del active_games[game_id]
        else:
            await query.edit_message_text(
                text="Game already ended. Use /game to start a new game."
            )
    
    elif callback_data.startswith("guess_number_"):
        # Handle number guess
        game_id = f"guess_number_{chat.id}_{user.id}"
        
        # Check if game exists and belongs to this user
        if game_id not in active_games or active_games[game_id]["user_id"] != user.id:
            await query.edit_message_text(
                text="This game has ended or doesn't belong to you. Use /game to start a new game."
            )
            return
        
        game = active_games[game_id]
        
        # Parse guessed number
        guessed_number = int(callback_data.split("_")[2])
        
        # Process guess
        result = make_number_guess(game, guessed_number)
        
        if result["status"] == "correct":
            # Game won
            keyboard = [
                [InlineKeyboardButton("🔄 Play Again", callback_data="guess_number_new")],
                [InlineKeyboardButton("🔙 Back to Games", callback_data="guess_back")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"🎉 *Correct!* 🎉\n\nYou guessed the number {game['number']} in {game['attempts']} attempts!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Log game result
            log_game_result(user.id, "guess_number", "win")
            
            # Remove game from active games
            del active_games[game_id]
        
        elif result["status"] == "wrong_too_high":
            # Wrong guess (too high)
            game["attempts"] += 1
            
            if game["attempts"] >= game["max_attempts"]:
                # Game over, out of attempts
                keyboard = [
                    [InlineKeyboardButton("🔄 Play Again", callback_data="guess_number_new")],
                    [InlineKeyboardButton("🔙 Back to Games", callback_data="guess_back")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=f"Game over! You're out of attempts.\n\nThe number was {game['number']}.",
                    reply_markup=reply_markup
                )
                
                # Log game result
                log_game_result(user.id, "guess_number", "loss")
                
                # Remove game from active games
                del active_games[game_id]
            else:
                # Update range and continue
                game["range_max"] = guessed_number - 1
                
                # Create updated keyboard
                keyboard = []
                
                # Add range buttons
                range_size = game["range_max"] - game["range_min"] + 1
                
                if range_size <= 10:
                    # Show all numbers if range is small
                    row = []
                    for num in range(game["range_min"], game["range_max"] + 1):
                        row.append(InlineKeyboardButton(str(num), callback_data=f"guess_number_{num}"))
                        if len(row) == 5:  # 5 buttons per row
                            keyboard.append(row)
                            row = []
                    if row:  # Add remaining buttons
                        keyboard.append(row)
                else:
                    # Show ranges if range is large
                    step = range_size // 5
                    for i in range(5):
                        start = game["range_min"] + i * step
                        end = game["range_min"] + (i + 1) * step - 1
                        if i == 4:  # Last range
                            end = game["range_max"]
                        keyboard.append([InlineKeyboardButton(f"{start}-{end}", callback_data=f"guess_number_range_{start}_{end}")])
                
                # Add quit button
                keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="guess_number_quit")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=f"🔢 *Guess the Number*\n\nToo high! The number is lower than {guessed_number}.\n\n"
                         f"You have {game['max_attempts'] - game['attempts']} attempts remaining.",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        elif result["status"] == "wrong_too_low":
            # Wrong guess (too low)
            game["attempts"] += 1
            
            if game["attempts"] >= game["max_attempts"]:
                # Game over, out of attempts
                keyboard = [
                    [InlineKeyboardButton("🔄 Play Again", callback_data="guess_number_new")],
                    [InlineKeyboardButton("🔙 Back to Games", callback_data="guess_back")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=f"Game over! You're out of attempts.\n\nThe number was {game['number']}.",
                    reply_markup=reply_markup
                )
                
                # Log game result
                log_game_result(user.id, "guess_number", "loss")
                
                # Remove game from active games
                del active_games[game_id]
            else:
                # Update range and continue
                game["range_min"] = guessed_number + 1
                
                # Create updated keyboard
                keyboard = []
                
                # Add range buttons
                range_size = game["range_max"] - game["range_min"] + 1
                
                if range_size <= 10:
                    # Show all numbers if range is small
                    row = []
                    for num in range(game["range_min"], game["range_max"] + 1):
                        row.append(InlineKeyboardButton(str(num), callback_data=f"guess_number_{num}"))
                        if len(row) == 5:  # 5 buttons per row
                            keyboard.append(row)
                            row = []
                    if row:  # Add remaining buttons
                        keyboard.append(row)
                else:
                    # Show ranges if range is large
                    step = range_size // 5
                    for i in range(5):
                        start = game["range_min"] + i * step
                        end = game["range_min"] + (i + 1) * step - 1
                        if i == 4:  # Last range
                            end = game["range_max"]
                        keyboard.append([InlineKeyboardButton(f"{start}-{end}", callback_data=f"guess_number_range_{start}_{end}")])
                
                # Add quit button
                keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="guess_number_quit")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    text=f"🔢 *Guess the Number*\n\nToo low! The number is higher than {guessed_number}.\n\n"
                         f"You have {game['max_attempts'] - game['attempts']} attempts remaining.",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
    
    # Word guessing game
    elif callback_data == "guess_word_new":
        # Start new word guessing game
        game_id = f"guess_word_{chat.id}_{user.id}"
        game_data = start_word_guess()
        
        active_games[game_id] = {
            "word": game_data["word"],
            "display": game_data["display"],
            "attempts": game_data["attempts"],
            "max_attempts": game_data["max_attempts"],
            "guessed_letters": game_data["guessed_letters"],
            "user_id": user.id
        }
        
        # Create keyboard with letter buttons
        keyboard = []
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        # First row (A-M)
        row1 = []
        for letter in alphabet[:13]:
            row1.append(InlineKeyboardButton(letter, callback_data=f"guess_word_{letter}"))
        keyboard.append(row1)
        
        # Second row (N-Z)
        row2 = []
        for letter in alphabet[13:]:
            row2.append(InlineKeyboardButton(letter, callback_data=f"guess_word_{letter}"))
        keyboard.append(row2)
        
        # Add quit button
        keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="guess_word_quit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🔤 *Guess the Word*\n\nWord: {game_data['display']}\n\n"
                 f"You have {game_data['max_attempts']} attempts remaining. Choose a letter!",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_data == "guess_word_quit":
        # Quit word guessing game
        game_id = f"guess_word_{chat.id}_{user.id}"
        
        if game_id in active_games:
            game = active_games[game_id]
            
            # Log game result
            log_game_result(user.id, "guess_word", "quit")
            
            await query.edit_message_text(
                text=f"Game ended. The word was '{game['word']}'. Use /game to start a new game."
            )
            
            # Remove game from active games
            del active_games[game_id]
        else:
            await query.edit_message_text(
                text="Game already ended. Use /game to start a new game."
            )
    
    elif callback_data.startswith("guess_word_"):
        # Handle letter guess
        game_id = f"guess_word_{chat.id}_{user.id}"
        
        # Check if game exists and belongs to this user
        if game_id not in active_games or active_games[game_id]["user_id"] != user.id:
            await query.edit_message_text(
                text="This game has ended or doesn't belong to you. Use /game to start a new game."
            )
            return
        
        game = active_games[game_id]
        
        # Parse guessed letter
        guessed_letter = callback_data.split("_")[2]
        
        # Process guess
        result = make_word_guess(game, guessed_letter)
        
        # Create updated keyboard
        keyboard = []
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        # First row (A-M)
        row1 = []
        for letter in alphabet[:13]:
            # Disable already guessed letters
            if letter in game["guessed_letters"]:
                row1.append(InlineKeyboardButton(f"[{letter}]", callback_data=f"guess_word_none"))
            else:
                row1.append(InlineKeyboardButton(letter, callback_data=f"guess_word_{letter}"))
        keyboard.append(row1)
        
        # Second row (N-Z)
        row2 = []
        for letter in alphabet[13:]:
            # Disable already guessed letters
            if letter in game["guessed_letters"]:
                row2.append(InlineKeyboardButton(f"[{letter}]", callback_data=f"guess_word_none"))
            else:
                row2.append(InlineKeyboardButton(letter, callback_data=f"guess_word_{letter}"))
        keyboard.append(row2)
        
        # Add quit button
        keyboard.append([InlineKeyboardButton("🚫 Quit Game", callback_data="guess_word_quit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if result["status"] == "win":
            # Game won
            keyboard = [
                [InlineKeyboardButton("🔄 Play Again", callback_data="guess_word_new")],
                [InlineKeyboardButton("🔙 Back to Games", callback_data="guess_back")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"🎉 *You Won!* 🎉\n\nYou guessed the word: {game['word']}\n\n"
                     f"Attempts used: {game['attempts']}/{game['max_attempts']}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Log game result
            log_game_result(user.id, "guess_word", "win")
            
            # Remove game from active games
            del active_games[game_id]
        
        elif result["status"] == "lose":
            # Game lost
            keyboard = [
                [InlineKeyboardButton("🔄 Play Again", callback_data="guess_word_new")],
                [InlineKeyboardButton("🔙 Back to Games", callback_data="guess_back")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"Game over! You're out of attempts.\n\nThe word was: {game['word']}",
                reply_markup=reply_markup
            )
            
            # Log game result
            log_game_result(user.id, "guess_word", "loss")
            
            # Remove game from active games
            del active_games[game_id]
        
        elif result["status"] == "correct":
            # Correct letter guess
            await query.edit_message_text(
                text=f"🔤 *Guess the Word*\n\nGood guess! '{guessed_letter}' is in the word.\n\n"
                     f"Word: {game['display']}\n\n"
                     f"You have {game['max_attempts'] - game['attempts']} attempts remaining.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif result["status"] == "wrong":
            # Wrong letter guess
            await query.edit_message_text(
                text=f"🔤 *Guess the Word*\n\nSorry, '{guessed_letter}' is not in the word.\n\n"
                     f"Word: {game['display']}\n\n"
                     f"You have {game['max_attempts'] - game['attempts']} attempts remaining.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif result["status"] == "already_guessed":
            # Already guessed letter
            await query.edit_message_text(
                text=f"🔤 *Guess the Word*\n\nYou already guessed '{guessed_letter}'.\n\n"
                     f"Word: {game['display']}\n\n"
                     f"You have {game['max_attempts'] - game['attempts']} attempts remaining.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif callback_data == "guess_back":
        # Go back to games menu
        await game_command(update, context)
