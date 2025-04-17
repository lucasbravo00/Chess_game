"""
Global constants used throughout the chess game.
"""
import pygame

# Window settings
WIDTH, HEIGHT = 900, 700
SQUARE_SIZE = 60
BOARD_SIZE = SQUARE_SIZE * 8
MARGIN_X = (WIDTH - BOARD_SIZE) // 2
MARGIN_Y = (HEIGHT - BOARD_SIZE) // 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GREEN = (144, 238, 144)
DARK_GREEN = (0, 140, 0)
DARK_GRAY = (0, 35, 0)
SELECTION = (255, 255, 0, 128)  # Transparent yellow overlay
CHECK_COLOR = (255, 0, 0, 128)  # Transparent red overlay

# Material values for piece evaluation
PIECE_VALUE = {
    "pawn": 1,
    "knight": 3,
    "bishop": 3,
    "rook": 5,
    "queen": 9,
    "king": 0  # Not used for material advantage
}

# Game states
GAME_STATE_MENU = "menu"
GAME_STATE_MENU_SIDE = "menu_side"
GAME_STATE_MENU_DIFFICULTY = "menu_difficulty"
GAME_STATE_PLAYING = "playing"
GAME_STATE_CORONATION = "coronation"
GAME_STATE_FINAL = "final"

# Player colors
COLOR_WHITE = "w"
COLOR_BLACK = "b"

# Animation settings
ANIMATION_DURATION = 15
ROTATION_DURATION = 20