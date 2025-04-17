"""
Game state management for tracking game progress, player information, and AI settings.
"""
from models.constants import (
    GAME_STATE_MENU, GAME_STATE_MENU_SIDE, GAME_STATE_MENU_DIFFICULTY,
    GAME_STATE_PLAYING, GAME_STATE_CORONATION, GAME_STATE_FINAL,
    COLOR_WHITE, COLOR_BLACK
)
import random


class GameState:
    """
    Manages the overall state of the game, including menus, players, and game progress.
    """

    def __init__(self):
        # Current game state (menu, playing, etc.)
        self.state = GAME_STATE_MENU

        # Game configuration
        self.ai_mode = False
        self.ai_level = "medium"
        self.play_as_black = False

        # Game progress tracking
        self.has_moved = False
        self.message = ""
        self.message_time = 0

        # AI status
        self.ai_thinking = False

    def start_game(self, ai_mode=False, ai_level="medium", play_as_black=False):
        """
        Initialize a new game with the specified settings.

        Args:
            ai_mode (bool): Whether AI opponent is enabled.
            ai_level (str): AI difficulty level ("easy", "medium", "hard").
            play_as_black (bool): Whether human player controls black pieces.
        """
        self.ai_mode = ai_mode
        self.ai_level = ai_level
        self.play_as_black = play_as_black
        self.has_moved = False
        self.message = ""
        self.message_time = 0
        self.state = GAME_STATE_PLAYING

    def choose_random_side(self):
        """
        Randomly selects whether the player will play as black or white.
        """
        self.play_as_black = random.choice([True, False])
        return self.play_as_black

    def show_message(self, message, duration=2000):
        """
        Display a temporary message for the specified duration.

        Args:
            message (str): The message to display.
            duration (int): Duration in milliseconds. If 0, shows indefinitely.
        """
        import pygame

        self.message = message
        self.message_time = pygame.time.get_ticks() + duration if duration > 0 else 0

    def update_message(self):
        """
        Check if the current message should be removed based on its duration.
        """
        import pygame

        if self.message and self.message_time > 0 and pygame.time.get_ticks() > self.message_time:
            self.message = ""

    def return_to_menu(self):
        """
        Reset game state and return to the main menu.
        """
        self.message = ""
        self.message_time = 0
        self.state = GAME_STATE_MENU