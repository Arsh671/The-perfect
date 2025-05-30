#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tic-Tac-Toe game implementation for the Telegram Bot
"""

import logging
import random
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Type alias for board
Board = List[List[str]]

def create_tictactoe_board() -> Board:
    """
    Create a new empty Tic-Tac-Toe board
    
    Returns:
        3x3 empty board
    """
    return [[" " for _ in range(3)] for _ in range(3)]

def check_tictactoe_winner(board: Board) -> Optional[str]:
    """
    Check if there's a winner on the board
    
    Args:
        board: Current game board
        
    Returns:
        "X" if X won, "O" if O won, None if no winner
    """
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != " ":
            return row[0]
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != " ":
            return board[0][col]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != " ":
        return board[0][2]
    
    # No winner
    return None

def make_tictactoe_move(board: Board) -> Tuple[int, int]:
    """
    Make a move for the bot (O player) in Tic-Tac-Toe
    
    Args:
        board: Current game board
        
    Returns:
        Row and column indices of the bot's move
    """
    # Check if we can win in the next move
    for i in range(3):
        for j in range(3):
            if board[i][j] == " ":
                # Try this move
                board[i][j] = "O"
                if check_tictactoe_winner(board) == "O":
                    board[i][j] = " "  # Reset the move
                    return i, j
                board[i][j] = " "  # Reset the move
    
    # Check if we need to block the player from winning
    for i in range(3):
        for j in range(3):
            if board[i][j] == " ":
                # Try this move for the player
                board[i][j] = "X"
                if check_tictactoe_winner(board) == "X":
                    board[i][j] = " "  # Reset the move
                    return i, j
                board[i][j] = " "  # Reset the move
    
    # Check for center
    if board[1][1] == " ":
        return 1, 1
    
    # Check for corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)
    for i, j in corners:
        if board[i][j] == " ":
            return i, j
    
    # Check for edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    random.shuffle(edges)
    for i, j in edges:
        if board[i][j] == " ":
            return i, j
    
    # No valid moves (should never happen in a valid game)
    logger.error("No valid moves found for Tic-Tac-Toe bot")
    return 0, 0

def print_board(board: Board) -> str:
    """
    Create a string representation of the board
    
    Args:
        board: Game board
        
    Returns:
        String representation of the board
    """
    result = ""
    for i, row in enumerate(board):
        result += " | ".join(row) + "\n"
        if i < 2:
            result += "---------\n"
    return result

def is_board_full(board: Board) -> bool:
    """
    Check if the board is full (draw)
    
    Args:
        board: Game board
        
    Returns:
        True if board is full, False otherwise
    """
    for row in board:
        if " " in row:
            return False
    return True
