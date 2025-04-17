"""
Main game controller that coordinates the game state, board, and user interactions.
"""
import threading
import pygame
import random
from models.game_state import GameState
from models.board import Board
from controllers.ai_controller import AIController
from views.menu_view import MenuView, SideMenuView, DifficultyMenuView
from views.board_view import BoardView
from models.constants import (
    GAME_STATE_MENU, GAME_STATE_MENU_SIDE, GAME_STATE_MENU_DIFFICULTY,
    GAME_STATE_PLAYING, GAME_STATE_CORONATION, GAME_STATE_FINAL,
    COLOR_WHITE, COLOR_BLACK
)
from utils.helpers import load_images
from models.constants import SQUARE_SIZE


class GameController:
    """
    Main controller for the chess game. Manages the flow of the game,
    state transitions, and coordination between the model and views.
    """

    # Class variable for game state to allow easy global access
    state = GAME_STATE_MENU

    def __init__(self):
        """Initialize the game controller with all necessary components."""
        # Initialize pygame first
        pygame.init()

        self.game_state = GameState()
        self.board = None
        self.ai = None
        self.images = load_images(SQUARE_SIZE)

        # Initialize views
        self.menu_view = MenuView()
        self.side_menu_view = SideMenuView()
        self.difficulty_menu_view = DifficultyMenuView()
        self.board_view = None
        self.promotion_menu = None

    def start_game(self, ai_mode=False, ai_level="medium", play_as_black=False):
        """
        Start a new game with the specified settings.

        Args:
            ai_mode (bool): Whether AI opponent is enabled
            ai_level (str): AI difficulty level ("easy", "medium", "hard")
            play_as_black (bool): Whether human player controls black pieces
        """
        # Initialize the board
        self.board = Board(ai_mode=ai_mode)
        self.board.board_rotated = play_as_black

        # Update game state
        self.game_state.start_game(ai_mode, ai_level, play_as_black)
        GameController.state = GAME_STATE_PLAYING

        # Initialize the board view
        self.board_view = BoardView(self.board, self.images)

        # Initialize AI if needed
        if ai_mode:
            self.ai = AIController(level=ai_level)
            # If player is black, AI (white) makes the first move
            if play_as_black:
                self.game_state.ai_thinking = True
                self.game_state.show_message("AI thinking...", 0)
                threading.Thread(target=self.ai_turn).start()

    def return_to_menu(self):
        """Reset game state and return to the main menu."""
        self.game_state.return_to_menu()
        GameController.state = GAME_STATE_MENU

    def update(self):
        """Update game state, animations, and AI."""
        if GameController.state == GAME_STATE_PLAYING and self.board:
            # Update board animations
            if self.board.animating:
                self.board.update_animation()

            if self.board.rotating:
                self.board.update_rotation()

            # Check for game ending conditions
            if self.board.checkmate and GameController.state != GAME_STATE_FINAL:
                GameController.state = GAME_STATE_FINAL

            # Check for pawn promotion
            if self.board.promotion_pending and not self.promotion_menu:
                from views.promotion_menu import PromotionMenuView
                self.promotion_menu = PromotionMenuView(self.board.pawn_to_promote.color)
                GameController.state = GAME_STATE_CORONATION

            # AI turn check
            if self.game_state.ai_mode:
                ai_color = COLOR_WHITE if self.game_state.play_as_black else COLOR_BLACK
                if (self.board.turn == ai_color and not self.board.checkmate and
                        not self.board.promotion_pending and not self.game_state.ai_thinking and
                        not self.board.animating and not self.board.rotating):
                    self.game_state.ai_thinking = True
                    self.game_state.show_message("AI thinking...", 0)
                    threading.Thread(target=self.ai_turn).start()

        # Update message timer
        self.game_state.update_message()

    def ai_turn(self):
        """Calculate and execute an AI move."""
        try:
            move = self.ai.get_move(self.board.board, self.board.turn, self.board.last_pawn_moved)
            if not self.game_state.ai_thinking:
                return

            if move:
                (start_x, start_y), (end_x, end_y), promotion = move
                self.board.select_piece(start_x, start_y)
                self.board.move_piece(end_x, end_y)

                if self.board.promotion_pending and promotion:
                    self.board.promote_pawn(promotion)
        except Exception as e:
            self.game_state.show_message("Error: Could not obtain move from Stockfish", 5000)
            print(f"Error in ai_turn: {e}")

        self.game_state.ai_thinking = False
        if self.game_state.message == "AI thinking...":
            self.game_state.message = ""

    def handle_event(self, event):
        """
        Process user input events based on the current game state.

        Args:
            event (pygame.event.Event): Pygame event to process

        Returns:
            bool: False if the game should exit, True otherwise
        """
        if event.type == pygame.QUIT:
            return False

        if GameController.state == GAME_STATE_MENU:
            action = self.menu_view.handle_events(event)
            if action == 0:  # 2 Player Game
                self.start_game(ai_mode=False)
            elif action == 1:  # Play vs AI
                GameController.state = GAME_STATE_MENU_SIDE
            elif action == 2:  # Exit
                return False

        elif GameController.state == GAME_STATE_MENU_SIDE:
            action = self.side_menu_view.handle_events(event)
            if action == 0:  # White
                self.game_state.play_as_black = False
                GameController.state = GAME_STATE_MENU_DIFFICULTY
            elif action == 1:  # Black
                self.game_state.play_as_black = True
                GameController.state = GAME_STATE_MENU_DIFFICULTY
            elif action == 2:  # Random
                self.game_state.choose_random_side()
                GameController.state = GAME_STATE_MENU_DIFFICULTY
            elif action == 3:  # Back
                GameController.state = GAME_STATE_MENU

        elif GameController.state == GAME_STATE_MENU_DIFFICULTY:
            action = self.difficulty_menu_view.handle_events(event)
            if action == 0:  # Easy
                self.start_game(ai_mode=True, ai_level="easy", play_as_black=self.game_state.play_as_black)
            elif action == 1:  # Medium
                self.start_game(ai_mode=True, ai_level="medium", play_as_black=self.game_state.play_as_black)
            elif action == 2:  # Hard
                self.start_game(ai_mode=True, ai_level="hard", play_as_black=self.game_state.play_as_black)
            elif action == 3:  # Back
                GameController.state = GAME_STATE_MENU_SIDE

        elif GameController.state == GAME_STATE_CORONATION:
            if self.promotion_menu:
                chosen_piece = self.promotion_menu.handle_events(event)
                if chosen_piece:
                    if self.board.promote_pawn(chosen_piece):
                        GameController.state = GAME_STATE_PLAYING
                        if self.board.checkmate:
                            self.game_state.show_message("CHECKMATE! Game over", 0)
                            GameController.state = GAME_STATE_FINAL
                    self.promotion_menu = None

        elif GameController.state == GAME_STATE_FINAL:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.return_to_menu()

        elif GameController.state == GAME_STATE_PLAYING:
            player_color = COLOR_BLACK if self.game_state.play_as_black else COLOR_WHITE
            ai_color = COLOR_WHITE if self.game_state.play_as_black else COLOR_BLACK

            # Skip input during animations or AI thinking
            if self.board.animating or self.board.rotating or (self.game_state.ai_mode and self.game_state.ai_thinking):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.return_to_menu()
                return True

            # Handle clicks on the board
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.board.checkmate and not self.board.promotion_pending:
                self._handle_board_click(event.pos)

            # Handle keyboard inputs
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.return_to_menu()
                elif event.key == pygame.K_z and not self.board.checkmate and not self.board.promotion_pending:
                    self._handle_undo()

        return True

    def _handle_board_click(self, pos):
        """Handle mouse clicks on the chess board."""
        from models.constants import MARGIN_X, MARGIN_Y, BOARD_SIZE, SQUARE_SIZE

        x, y = pos
        if (MARGIN_X <= x < MARGIN_X + BOARD_SIZE and
                MARGIN_Y <= y < MARGIN_Y + BOARD_SIZE):
            col = (x - MARGIN_X) // SQUARE_SIZE
            row = (y - MARGIN_Y) // SQUARE_SIZE

            if self.board.board_rotated:
                adjusted_col = 7 - col
                adjusted_row = 7 - row
            else:
                adjusted_col = col
                adjusted_row = row

            piece = self.board.board[adjusted_row][adjusted_col]

            if self.board.selected_piece:
                if self.board.move_piece(adjusted_col, adjusted_row):
                    self.game_state.has_moved = True
                    if self.board.promotion_pending:
                        from views.promotion_menu import PromotionMenuView
                        self.promotion_menu = PromotionMenuView(self.board.pawn_to_promote.color)
                        GameController.state = GAME_STATE_CORONATION
                    elif self.board.checkmate:
                        if self.board.winner == "draw":
                            self.game_state.show_message("DRAW", 0)
                        else:
                            winner_color = "White" if self.board.winner == COLOR_WHITE else "Black"
                            self.game_state.show_message(f"CHECKMATE! {winner_color} wins", 0)
                        GameController.state = GAME_STATE_FINAL
                elif self.board.select_piece(adjusted_col, adjusted_row):
                    pass
                else:
                    self.board.selected_piece = None
                    self.board.valid_moves = []
            else:
                self.board.select_piece(adjusted_col, adjusted_row)

    def _handle_undo(self):
        """Handle undo move action."""
        if self.game_state.ai_mode:
            # In AI mode, allow undoing your most recent move and the AI's response
            player_color = COLOR_BLACK if self.game_state.play_as_black else COLOR_WHITE

            if self.board.turn == player_color:
                # If it's player's turn again, they can undo both their move and AI's response
                if len(self.board.history) >= 2:
                    self.board.undo_move()  # Undo AI's move
                    self.board.undo_move()  # Undo player's move
                    self.game_state.show_message("Moves undone", 2000)
                    self.game_state.has_moved = False
                else:
                    self.game_state.show_message("No moves to undo", 2000)
            else:
                # If it's AI's turn (player just moved), only undo the player's move
                if self.board.history:
                    self.board.undo_move()  # Undo player's move
                    self.game_state.show_message("Move undone", 2000)
                    self.game_state.has_moved = False
                else:
                    self.game_state.show_message("No moves to undo", 2000)
        else:
            # In 2-player mode, always allow undo
            if self.board.history:
                self.board.undo_move()
                self.game_state.show_message("Move undone", 2000)
            else:
                self.game_state.show_message("No moves to undo", 2000)

    def draw(self, window):
        """
        Draw the current game state to the window.

        Args:
            window (pygame.Surface): The window surface to draw on
        """
        if GameController.state == GAME_STATE_MENU:
            self.menu_view.draw(window)

        elif GameController.state == GAME_STATE_MENU_SIDE:
            self.side_menu_view.draw(window)

        elif GameController.state == GAME_STATE_MENU_DIFFICULTY:
            self.difficulty_menu_view.draw(window)

        elif GameController.state in [GAME_STATE_PLAYING, GAME_STATE_FINAL]:
            if self.board_view:
                self.board_view.draw(window, self.game_state.message)

        elif GameController.state == GAME_STATE_CORONATION:
            if self.board_view:
                self.board_view.draw(window, self.game_state.message)
                if self.promotion_menu:
                    self.promotion_menu.draw(window, self.images)

    def run(self):
        """Run the main game loop."""
        pygame.init()
        from models.constants import WIDTH, HEIGHT

        window = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess")

        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False

            self.update()
            self.draw(window)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()