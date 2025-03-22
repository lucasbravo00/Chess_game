import pygame
import random
import time
import chess
import chess.engine
import os


class ChessAI:
    def __init__(self, level="medium"):
        """
        Initialize the Chess AI with a specified difficulty level.

        Args:
            level (str): Difficulty level. Options are "easy", "medium", or "hard".
        """
        self.level = level  # AI difficulty level
        self.thinking = False  # Flag to indicate if the AI is currently calculating a move
        self.animation_frame = 0  # Counter used for animation effects (e.g., thinking indicator)
        self.last_thought = None  # Stores details of the last calculated move (for debugging)
        self.last_error = None  # Stores the last error encountered during move calculation

        # Path to the Stockfish engine executable. Adjust this path as needed.
        self.stockfish_path = os.path.join(os.path.dirname(__file__), "stockfish", "stockfish-windows-x86-64-avx2.exe")

        # AI configuration settings based on the difficulty level.
        self.configuration = {
            "easy": {
                "depth": 2,
                "max_time": 0.1,
                "skill_level": 0,  # Lower skill level for easy difficulty
                "use_best_move": 0.25  # 25% chance to use the best move
            },
            "medium": {
                "depth": 5,
                "max_time": 0.5,
                "skill_level": 10,  # Moderate skill level for medium difficulty
                "use_best_move": 0.60  # 60% chance to use the best move
            },
            "hard": {
                "depth": 10,
                "max_time": 1.0,
                "skill_level": 20,  # Maximum skill level for hard difficulty
                "use_best_move": 1.0  # Always use the best move
            }
        }

    def board_to_fen(self, board_matrix, turn, last_pawn_double_move=None):
        """
        Convert the board matrix into FEN notation for Stockfish.

        Args:
            board_matrix (list[list]): 8x8 matrix representing the chess board.
            turn (str): The player to move next. "w" for white or "b" for black.
            last_pawn_double_move (tuple, optional): Coordinates (x, y) of the last pawn that moved two squares.

        Returns:
            str: The FEN string representing the current board state.

        Note:
            Piece types are expected to be in English (e.g., "pawn", "knight", "bishop", "rook", "queen", "king").
            The FEN notation follows the standard: uppercase for white pieces, lowercase for black pieces.
        """
        fen = ""
        # Process each row of the board matrix to build the FEN piece placement section.
        for row in range(8):
            empty_spaces = 0
            for col in range(8):
                piece = board_matrix[row][col]
                if piece is None:
                    empty_spaces += 1
                else:
                    if empty_spaces > 0:
                        fen += str(empty_spaces)
                        empty_spaces = 0
                    symbol = ""
                    # Map the piece type to its FEN symbol.
                    if piece.type == "pawn":
                        symbol = "p"
                    elif piece.type == "knight":
                        symbol = "n"
                    elif piece.type == "bishop":
                        symbol = "b"
                    elif piece.type == "rook":
                        symbol = "r"
                    elif piece.type == "queen":
                        symbol = "q"
                    elif piece.type == "king":
                        symbol = "k"
                    # Use uppercase for white pieces and lowercase for black pieces.
                    if piece.color == "w":
                        symbol = symbol.upper()
                    else:
                        symbol = symbol.lower()
                    fen += symbol
            if empty_spaces > 0:
                fen += str(empty_spaces)
            if row < 7:
                fen += "/"

        # Append the active color.
        fen += " " + turn
        # Append castling rights (using full rights for simplicity).
        fen += " KQkq"

        # Append en passant target square if applicable.
        if last_pawn_double_move:
            x, y = last_pawn_double_move
            if (turn == "w" and y == 3) or (turn == "b" and y == 4):
                column_letter = chr(ord('a') + x)
                row_num = 6 if turn == "w" else 3
                fen += f" {column_letter}{row_num}"
            else:
                fen += " -"
        else:
            fen += " -"

        # Append halfmove clock and fullmove number (default values used).
        fen += " 0 1"
        return fen

    def get_move(self, board_matrix, turn, last_pawn_double_move=None):
        """
        Calculate the best move using Stockfish and return it.

        Args:
            board_matrix (list[list]): 8x8 matrix representing the chess board.
            turn (str): The player to move. "w" for white or "b" for black.
            last_pawn_double_move (tuple, optional): Coordinates (x, y) for en passant target if applicable.

        Returns:
            tuple: A tuple containing ((from_x, from_y), (to_x, to_y), promotion)
                   where promotion is None if not applicable.

        Raises:
            Exception: If Stockfish does not return a valid move.
        """
        self.thinking = True
        self.animation_frame = 0
        try:
            # Convert the current board state to FEN notation.
            fen = self.board_to_fen(board_matrix, turn, last_pawn_double_move)
            print(f"FEN sent to Stockfish: {fen}")

            config = self.configuration[self.level]
            print(f"Level: {self.level}, configuring parameters for level {self.level}")

            # Create a chess board object using the FEN string.
            board = chess.Board(fen)

            # Start the Stockfish engine.
            engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)

            # Configure the engine based on the selected difficulty level.
            if self.level == "easy":
                engine.configure({
                    "UCI_LimitStrength": True,
                    "UCI_Elo": 1350
                })
                limit = chess.engine.Limit(depth=2, time=0.1)
                print("Configured as player ELO 1500")
            elif self.level == "medium":
                engine.configure({
                    "UCI_LimitStrength": True,
                    "UCI_Elo": 2000
                })
                limit = chess.engine.Limit(depth=5, time=0.5)
                print("Configured as player ELO 2000")
            else:
                engine.configure({
                    "Skill Level": 20
                })
                limit = chess.engine.Limit(depth=10, time=1.0)
                print("Configured with maximum strength (Skill Level 20)")

            print(f"Engine options: {engine.options}")

            # Get the best move from Stockfish.
            result = engine.play(board, limit)
            result_move = result.move
            print(f"Best move according to Stockfish: {result_move}")
            engine.quit()

            if result_move:
                # Extract source and target squares from the UCI move string.
                from_uci = result_move.uci()[:2]
                to_uci = result_move.uci()[2:4]
                from_x = ord(from_uci[0]) - ord('a')
                from_y = 8 - int(from_uci[1])
                to_x = ord(to_uci[0]) - ord('a')
                to_y = 8 - int(to_uci[1])

                promotion = None
                # Check if the move involves pawn promotion.
                if len(result_move.uci()) >= 5:
                    promotion_map = {
                        'q': 'queen',
                        'r': 'rook',
                        'b': 'bishop',
                        'n': 'knight'
                    }
                    promotion = promotion_map.get(result_move.uci()[4], 'queen')

                # Store move details for debugging purposes.
                self.last_thought = {
                    "eval": 0,
                    "depth": config["depth"],
                    "move": result_move.uci()
                }
                print(f"Translated move: from ({from_x}, {from_y}) to ({to_x}, {to_y})")
                self.thinking = False
                return ((from_x, from_y), (to_x, to_y), promotion)

            raise Exception("Stockfish did not return a valid move")

        except Exception as e:
            print(f"Error with Stockfish: {e}")
            import traceback
            traceback.print_exc()
            self.last_error = f"Stockfish error: {str(e)}"
            self.thinking = False
            raise

    def draw_indicator(self, window, x, y):
        """
        Draw a visual indicator (e.g., a spinning arc) on the provided window
        to show that the AI is processing its move.

        Args:
            window (pygame.Surface): The surface to draw the indicator on.
            x (int): X-coordinate for the center of the indicator.
            y (int): Y-coordinate for the center of the indicator.
        """
        if not self.thinking:
            return
        radius = 15
        thickness = 4
        # Increment the animation frame to create a spinning effect.
        self.animation_frame = (self.animation_frame + 1) % 360
        start_angle = 0
        end_angle = self.animation_frame
        rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        pygame.draw.arc(window, (255, 0, 0), rect, start_angle * 0.01745, end_angle * 0.01745, thickness)


class DifficultyMenu:
    def __init__(self):
        """
        Initialize the difficulty selection menu.
        """
        self.options = ["Easy", "Medium", "Hard", "Back"]  # Menu options in English
        self.selection = 0  # Index of the currently selected option
        self.font = pygame.font.SysFont(None, 48)  # Font for menu options
        self.title_font = pygame.font.SysFont(None, 72)  # Font for the menu title
        self.option_rects = []  # Rectangles representing clickable areas for each option

    def draw(self, window, width, height):
        """
        Draw the difficulty menu on the given window.

        Args:
            window (pygame.Surface): The surface to draw the menu on.
            width (int): The width of the window.
            height (int): The height of the window.
        """
        window.fill((200, 200, 200))
        title = self.title_font.render("SELECT DIFFICULTY", True, (0, 0, 0))
        title_rect = title.get_rect(center=(width // 2, 100))
        window.blit(title, title_rect)

        self.option_rects = []
        # Draw each menu option with its respective background and border.
        for i, option in enumerate(self.options):
            color = (144, 238, 144) if i == self.selection else (255, 255, 255)
            text = self.font.render(option, True, (0, 0, 0))
            pos_y = 250 + i * 70 + 40 if option == "Back" else 250 + i * 70
            rect = text.get_rect(center=(width // 2, pos_y))
            button_rect = rect.inflate(40, 20)
            pygame.draw.rect(window, color, button_rect)
            pygame.draw.rect(window, (0, 0, 0), button_rect, 2)
            window.blit(text, rect)
            self.option_rects.append(button_rect)

    def handle_events(self, event):
        """
        Process input events for menu navigation.

        Args:
            event (pygame.event.Event): A Pygame event.

        Returns:
            int or None: The index of the selected option if confirmed, otherwise None.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selection = (self.selection - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selection = (self.selection + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.selection
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selection = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    return i
        return None
