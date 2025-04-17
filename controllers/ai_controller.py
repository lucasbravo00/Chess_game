"""
AI controller module for handling Stockfish chess engine integration.
"""
import os
import threading
import chess
import chess.engine
from models.constants import COLOR_WHITE, COLOR_BLACK


class AIController:
    """
    Manages chess AI using the Stockfish engine, handles move calculation based on difficulty level.
    """

    def __init__(self, level="medium"):
        """
        Initialize the AI controller with the specified difficulty level.

        Args:
            level (str): Difficulty level - "easy", "medium", or "hard"
        """
        self.level = level
        self.thinking = False
        self.last_thought = None
        self.last_error = None

        # Configuration for various AI difficulty levels
        self.configuration = {
            "easy": {
                "depth": 2,
                "max_time": 0.1,
                "skill_level": 0,  # Lower skill level for easy difficulty
                "use_best_move": 0.25,  # 25% chance to use the best move
                "elo": 1350
            },
            "medium": {
                "depth": 5,
                "max_time": 0.5,
                "skill_level": 10,  # Moderate skill level for medium difficulty
                "use_best_move": 0.60,  # 60% chance to use the best move
                "elo": 2000
            },
            "hard": {
                "depth": 10,
                "max_time": 1.0,
                "skill_level": 20,  # Maximum skill level for hard difficulty
                "use_best_move": 1.0,  # Always use the best move
                "elo": None  # No ELO limit for hard
            }
        }

        # Path to Stockfish executable - adjust for your system
        self.stockfish_path = self._get_stockfish_path()

    def _get_stockfish_path(self):
        """
        Determine the Stockfish executable path based on the operating system.

        Returns:
            str: Path to the Stockfish executable
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        stockfish_dir = os.path.join(base_dir, "stockfish")

        if os.name == 'nt':  # Windows
            return os.path.join(stockfish_dir, "stockfish-windows-x86-64-avx2.exe")
        elif os.name == 'posix':  # Linux/Mac
            if os.uname().sysname == 'Darwin':  # Mac
                return os.path.join(stockfish_dir, "stockfish-macos-x86-64")
            else:  # Linux
                return os.path.join(stockfish_dir, "stockfish-linux-x86-64")
        else:
            # Default to Windows path if can't determine OS
            return os.path.join(stockfish_dir, "stockfish-windows-x86-64-avx2.exe")

    def board_to_fen(self, board_matrix, turn, last_pawn_double_move=None):
        """
        Convert the board matrix into FEN notation for Stockfish.

        Args:
            board_matrix (list[list]): 8x8 matrix representing the chess board
            turn (str): Current player's turn ("w" or "b")
            last_pawn_double_move (tuple, optional): Coordinates of last pawn that moved two squares

        Returns:
            str: FEN string representation of the board
        """
        fen = ""
        # Process each row of the board matrix to build the FEN piece placement section
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
                    # Map the piece type to its FEN symbol
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
                    # Use uppercase for white pieces and lowercase for black pieces
                    if piece.color == COLOR_WHITE:
                        symbol = symbol.upper()
                    fen += symbol
            if empty_spaces > 0:
                fen += str(empty_spaces)
            if row < 7:
                fen += "/"

        # Append the active color
        fen += " " + turn
        # Append castling rights (using full rights for simplicity)
        fen += " KQkq"

        # Append en passant target square if applicable
        if last_pawn_double_move:
            x, y = last_pawn_double_move
            if (turn == COLOR_WHITE and y == 3) or (turn == COLOR_BLACK and y == 4):
                column_letter = chr(ord('a') + x)
                row_num = 6 if turn == COLOR_WHITE else 3
                fen += f" {column_letter}{row_num}"
            else:
                fen += " -"
        else:
            fen += " -"

        # Append halfmove clock and fullmove number (default values used)
        fen += " 0 1"
        return fen

    def get_move(self, board_matrix, turn, last_pawn_double_move=None):
        """
        Calculate the best move using Stockfish and return it.

        Args:
            board_matrix (list[list]): 8x8 matrix representing the chess board
            turn (str): Current player's turn ("w" or "b")
            last_pawn_double_move (tuple, optional): Coordinates for en passant target

        Returns:
            tuple: ((from_x, from_y), (to_x, to_y), promotion) where promotion is None if not applicable

        Raises:
            Exception: If Stockfish does not return a valid move
        """
        self.thinking = True
        try:
            # Convert the current board state to FEN notation
            fen = self.board_to_fen(board_matrix, turn, last_pawn_double_move)
            print(f"FEN sent to Stockfish: {fen}")

            config = self.configuration[self.level]
            print(f"Level: {self.level}, configuring parameters for level {self.level}")

            # Create a chess board object using the FEN string
            board = chess.Board(fen)

            # Start the Stockfish engine
            engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)

            # Configure the engine based on the selected difficulty level
            if config["elo"]:
                engine.configure({
                    "UCI_LimitStrength": True,
                    "UCI_Elo": config["elo"]
                })
            else:
                engine.configure({
                    "Skill Level": config["skill_level"]
                })

            limit = chess.engine.Limit(depth=config["depth"], time=config["max_time"])
            print(f"Engine options: {engine.options}")

            # Get the best move from Stockfish
            result = engine.play(board, limit)
            result_move = result.move
            print(f"Best move according to Stockfish: {result_move}")
            engine.quit()

            if result_move:
                # Extract source and target squares from the UCI move string
                from_uci = result_move.uci()[:2]
                to_uci = result_move.uci()[2:4]
                from_x = ord(from_uci[0]) - ord('a')
                from_y = 8 - int(from_uci[1])
                to_x = ord(to_uci[0]) - ord('a')
                to_y = 8 - int(to_uci[1])

                promotion = None
                # Check if the move involves pawn promotion
                if len(result_move.uci()) >= 5:
                    promotion_map = {
                        'q': 'queen',
                        'r': 'rook',
                        'b': 'bishop',
                        'n': 'knight'
                    }
                    promotion = promotion_map.get(result_move.uci()[4], 'queen')

                # Store move details for debugging purposes
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