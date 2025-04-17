"""
Chess pieces and their movement logic.
"""
from models.constants import COLOR_WHITE, COLOR_BLACK


class Piece:
    """
    Base class for all chess pieces. Holds basic attributes:
    piece type, color, board coordinates, and a flag to indicate if moved (relevant for castling/pawn moves).
    """

    def __init__(self, piece_type, color, x, y):
        self.type = piece_type  # e.g., "pawn", "knight", etc.
        self.color = color  # "w" (white) or "b" (black)
        self.x = x
        self.y = y
        self.moved = False

    def __str__(self):
        return f"{self.color}_{self.type}"

    def move(self, x, y):
        """
        Update the piece's position and mark it as moved.
        """
        self.x = x
        self.y = y
        self.moved = True

    def valid_moves(self, board):
        """
        Return a list of valid moves. By default, delegates to possible_moves
        then filters out any moves that would leave the king in check.
        """
        from utils.helpers import leaves_king_in_check

        board_matrix = board.board if hasattr(board, 'board') else board
        moves = self.possible_moves(board_matrix)
        return [move for move in moves if not leaves_king_in_check(board_matrix, self, move)]

    def possible_moves(self, board):
        """
        Return all possible moves ignoring checks. Override in subclasses.
        """
        return []


class Pawn(Piece):
    """
    Pawns move differently based on their color:
    - White pawns move up (y - 1).
    - Black pawns move down (y + 1).
    They can move forward one square if it's empty, or two squares from their starting position if both squares are empty.
    They capture diagonally. En passant is also handled.
    """

    def __init__(self, color, x, y):
        super().__init__("pawn", color, x, y)

    def possible_moves(self, board):
        moves = []
        is_board_obj = hasattr(board, 'board')
        board_matrix = board.board if is_board_obj else board

        direction = -1 if self.color == COLOR_WHITE else 1
        # Forward one square
        if 0 <= self.y + direction < 8:
            if board_matrix[self.y + direction][self.x] is None:
                moves.append((self.x, self.y + direction))
                # Forward two squares (only if not moved yet)
                if not self.moved and 0 <= self.y + 2 * direction < 8:
                    if board_matrix[self.y + 2 * direction][self.x] is None:
                        moves.append((self.x, self.y + 2 * direction))

        # Diagonal captures
        for dx in [-1, 1]:
            nx = self.x + dx
            ny = self.y + direction
            if 0 <= nx < 8 and 0 <= ny < 8:
                target = board_matrix[ny][nx]
                if target is not None and target.color != self.color:
                    moves.append((nx, ny))

        # En passant
        if is_board_obj and board.last_pawn_moved is not None:
            last_x, last_y = board.last_pawn_moved

            white_pawn_on_fifth = (self.color == COLOR_WHITE and self.y == 3)
            black_pawn_on_fourth = (self.color == COLOR_BLACK and self.y == 4)

            if white_pawn_on_fifth or black_pawn_on_fourth:
                same_level = ((white_pawn_on_fifth and last_y == 3) or (black_pawn_on_fourth and last_y == 4))
                if same_level and abs(self.x - last_x) == 1:
                    target_piece = board_matrix[last_y][last_x]
                    if target_piece and target_piece.type == "pawn" and target_piece.color != self.color:
                        capture_move = (last_x, self.y + direction)
                        moves.append(capture_move)

        return moves


class Rook(Piece):
    """
    Rooks move in straight lines (horizontal and vertical).
    They may continue moving until blocked by another piece or the board edge.
    """

    def __init__(self, color, x, y):
        super().__init__("rook", color, x, y)

    def possible_moves(self, board):
        moves = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for dx, dy in directions:
            for i in range(1, 8):
                nx = self.x + i * dx
                ny = self.y + i * dy
                if not (0 <= nx < 8 and 0 <= ny < 8):
                    break
                target = board[ny][nx]
                if target is None:
                    moves.append((nx, ny))
                else:
                    if target.color != self.color:
                        moves.append((nx, ny))
                    break
        return moves


class Knight(Piece):
    """
    Knights move in an 'L' shape: 2 squares in one direction and 1 square perpendicular.
    Knights can jump over other pieces.
    """

    def __init__(self, color, x, y):
        super().__init__("knight", color, x, y)

    def possible_moves(self, board):
        moves = []
        jumps = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
        for dx, dy in jumps:
            nx = self.x + dx
            ny = self.y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                target = board[ny][nx]
                if target is None or target.color != self.color:
                    moves.append((nx, ny))
        return moves


class Bishop(Piece):
    """
    Bishops move diagonally in any direction until blocked or reaching the board edge.
    """

    def __init__(self, color, x, y):
        super().__init__("bishop", color, x, y)

    def possible_moves(self, board):
        moves = []
        directions = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
        for dx, dy in directions:
            for i in range(1, 8):
                nx = self.x + i * dx
                ny = self.y + i * dy
                if not (0 <= nx < 8 and 0 <= ny < 8):
                    break
                target = board[ny][nx]
                if target is None:
                    moves.append((nx, ny))
                else:
                    if target.color != self.color:
                        moves.append((nx, ny))
                    break
        return moves


class Queen(Piece):
    """
    Queens combine the movements of rooks and bishops:
    they can move any number of squares along rank, file, or diagonal until blocked.
    """

    def __init__(self, color, x, y):
        super().__init__("queen", color, x, y)

    def possible_moves(self, board):
        moves = []
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),  # Rook-like (vertical/horizontal)
            (1, 1), (1, -1), (-1, -1), (-1, 1)  # Bishop-like (diagonals)
        ]
        for dx, dy in directions:
            for i in range(1, 8):
                nx = self.x + i * dx
                ny = self.y + i * dy
                if not (0 <= nx < 8 and 0 <= ny < 8):
                    break
                target = board[ny][nx]
                if target is None:
                    moves.append((nx, ny))
                else:
                    if target.color != self.color:
                        moves.append((nx, ny))
                    break
        return moves


class King(Piece):
    """
    The King can move one square in any direction. Castling is also handled here:
    - The king cannot castle through check or when it has moved.
    - The rook involved must not have moved, and squares between must be empty and not under attack.
    """

    def __init__(self, color, x, y):
        super().__init__("king", color, x, y)

    def possible_moves(self, board, check_castling=True):
        from utils.helpers import is_square_threatened, is_in_check_simple

        moves = []
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),
            (1, 1), (1, -1), (-1, -1), (-1, 1)
        ]
        for dx, dy in directions:
            nx = self.x + dx
            ny = self.y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                target = board[ny][nx]
                if target is None or target.color != self.color:
                    moves.append((nx, ny))

        # Castling check
        if check_castling and not self.moved:
            if not is_in_check_simple(board, self.color):
                # Kingside castling
                if self._can_castle_kingside(board):
                    moves.append((self.x + 2, self.y))
                # Queenside castling
                if self._can_castle_queenside(board):
                    moves.append((self.x - 2, self.y))
        return moves

    def _can_castle_kingside(self, board):
        from utils.helpers import is_square_threatened

        rook_x = 7
        rook = board[self.y][rook_x]
        if not rook or rook.type != "rook" or rook.color != self.color or rook.moved:
            return False
        for x in range(self.x + 1, rook_x):
            if board[self.y][x] is not None:
                return False
        for x in range(self.x + 1, self.x + 3):
            if is_square_threatened(board, x, self.y, self.color):
                return False
        return True

    def _can_castle_queenside(self, board):
        from utils.helpers import is_square_threatened

        rook_x = 0
        rook = board[self.y][rook_x]
        if not rook or rook.type != "rook" or rook.color != self.color or rook.moved:
            return False
        for x in range(rook_x + 1, self.x):
            if board[self.y][x] is not None:
                return False
        for x in range(self.x - 1, self.x - 3, -1):
            if is_square_threatened(board, x, self.y, self.color):
                return False
        return True

    def valid_moves(self, board):
        """
        Override the valid_moves method to pass check_castling=True,
        ensuring we handle castle logic in this final check.
        """
        from utils.helpers import leaves_king_in_check

        moves = self.possible_moves(board, check_castling=True)
        return [move for move in moves if not leaves_king_in_check(board, self, move)]