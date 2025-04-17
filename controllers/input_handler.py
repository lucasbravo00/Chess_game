"""
Input handler for the chess game.
"""
import pygame
from models.constants import (
    MARGIN_X, MARGIN_Y, SQUARE_SIZE, BOARD_SIZE,
    GAME_STATE_MENU, GAME_STATE_PLAYING, GAME_STATE_CORONATION, GAME_STATE_FINAL,
    COLOR_WHITE, COLOR_BLACK
)


class InputHandler:
    """
    Handles user input for the chess game, translating events to game actions.
    """

    @staticmethod
    def get_board_coords_from_mouse(x, y, board_rotated=False):
        """
        Convert mouse coordinates to board coordinates.

        Args:
            x (int): Mouse x-coordinate
            y (int): Mouse y-coordinate
            board_rotated (bool): Whether the board is rotated

        Returns:
            tuple or None: (col, row) board coordinates or None if outside the board
        """
        if not (MARGIN_X <= x < MARGIN_X + BOARD_SIZE and MARGIN_Y <= y < MARGIN_Y + BOARD_SIZE):
            return None

        col = (x - MARGIN_X) // SQUARE_SIZE
        row = (y - MARGIN_Y) // SQUARE_SIZE

        if board_rotated:
            col, row = 7 - col, 7 - row

        return col, row

    @staticmethod
    def handle_board_click(board, x, y):
        """
        Handle a click on the board.

        Args:
            board: The chess board model
            x (int): Click x-coordinate
            y (int): Click y-coordinate

        Returns:
            dict: Results of the click action
        """
        result = {
            'action': None,
            'promotion_pending': False,
            'checkmate': False,
            'winner': None
        }

        board_coords = InputHandler.get_board_coords_from_mouse(x, y, board.board_rotated)
        if not board_coords:
            return result

        col, row = board_coords
        piece = board.board[row][col]

        if board.selected_piece:
            if board.move_piece(col, row):
                result['action'] = 'moved'
                result['promotion_pending'] = board.promotion_pending
                result['checkmate'] = board.checkmate
                result['winner'] = board.winner
            elif board.select_piece(col, row):
                result['action'] = 'selected'
            else:
                board.selected_piece = None
                board.valid_moves = []
                result['action'] = 'deselected'
        else:
            if board.select_piece(col, row):
                result['action'] = 'selected'

        return result

    @staticmethod
    def is_click_on_button(x, y, button_rect):
        """
        Check if a click is on a specific button.

        Args:
            x (int): Click x-coordinate
            y (int): Click y-coordinate
            button_rect (pygame.Rect): Button rectangle

        Returns:
            bool: True if the click is on the button, False otherwise
        """
        return button_rect.collidepoint(x, y)

    @staticmethod
    def is_ai_turn(game_state, board):
        """
        Determine if it's the AI's turn to play.

        Args:
            game_state: Current game state
            board: The chess board model

        Returns:
            bool: True if it's the AI's turn, False otherwise
        """
        if not game_state.ai_mode:
            return False

        ai_color = COLOR_WHITE if game_state.play_as_black else COLOR_BLACK
        return board.turn == ai_color