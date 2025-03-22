import pygame
import sys
import os
import threading
import time
from chess_stockfish import ChessAI, DifficultyMenu
import random

pygame.init()

# ------------------ Global Constants ------------------
WIDTH, HEIGHT = 800, 600
SQUARE_SIZE = 60
BOARD_SIZE = SQUARE_SIZE * 8
MARGIN_X = (WIDTH - BOARD_SIZE) // 2
MARGIN_Y = (HEIGHT - BOARD_SIZE) // 2

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GREEN = (144, 238, 144)
DARK_GREEN = (0, 140, 0)
SELECTION = (255, 255, 0, 128)
CHECK_COLOR = (255, 0, 0, 128)
DARK_GRAY = (0, 35, 0)

# Material values for pieces
PIECE_VALUE = {
    "pawn": 1,
    "knight": 3,
    "bishop": 3,
    "rook": 5,
    "queen": 9,
    "king": 0  # The king has no material value in evaluation
}

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess")

def load_images():
    """
    Load chess piece images from the "img" directory.
    If a file is missing, create a fallback image.
    File names must follow: for white pieces (originally "b") use "w_king.png", etc.
    For black pieces (originally "n") use "b_king.png", etc.
    """
    if not os.path.exists("img"):
        os.makedirs("img")
    images = {}
    # Iterate over final color labels: white: "w", black: "b"
    for color in ["w", "b"]:
        for piece in ["king", "queen", "bishop", "knight", "rook", "pawn"]:
            key = f"{color}_{piece}"
            path = os.path.join("img", f"{color}_{piece}.png")
            surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            # Mapping: white pieces (originally "b") and black pieces (originally "n")
            if color == "w":
                circle_color = WHITE
                text_color = BLACK
            else:
                circle_color = BLACK
                text_color = WHITE
            radius = SQUARE_SIZE // 3
            pygame.draw.circle(surface, circle_color, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), radius)
            font = pygame.font.SysFont(None, 20)
            text = font.render(piece[:3].upper(), True, text_color)
            rect_text = text.get_rect(center=(SQUARE_SIZE // 2, SQUARE_SIZE // 2))
            surface.blit(text, rect_text)
            try:
                if os.path.exists(path):
                    image = pygame.image.load(path)
                    images[key] = image
                else:
                    images[key] = surface
            except Exception as e:
                images[key] = surface
    return images

# ------------------ Piece Classes ------------------
# All identifiers are now in English.
# Conversion of colors: original "b" (blancas) → "w" (white) and "n" (negras) → "b" (black)
class Piece:
    def __init__(self, piece_type, color, x, y):
        self.type = piece_type  # e.g., "pawn", "knight", etc.
        self.color = color      # "w" for white, "b" for black
        self.x = x
        self.y = y
        self.moved = False

    def __str__(self):
        return f"{self.color}_{self.type}"

    def move(self, x, y):
        """Update the piece's position and mark it as moved."""
        self.x = x
        self.y = y
        self.moved = True

    def valid_moves(self, board):
        return []

    def possible_moves(self, board):
        return []

class Pawn(Piece):
    def __init__(self, color, x, y):
        super().__init__("pawn", color, x, y)

    def possible_moves(self, board):
        moves = []
        # White ("w") moves upward (direction -1), black ("b") moves downward (+1)
        direction = -1 if self.color == "w" else 1
        is_board_obj = hasattr(board, 'board')
        board_matrix = board.board if is_board_obj else board
        if 0 <= self.y + direction < 8:
            if board_matrix[self.y + direction][self.x] is None:
                moves.append((self.x, self.y + direction))
                if not self.moved and 0 <= self.y + 2 * direction < 8:
                    if board_matrix[self.y + 2 * direction][self.x] is None:
                        moves.append((self.x, self.y + 2 * direction))
        for dx in [-1, 1]:
            nx = self.x + dx
            ny = self.y + direction
            if 0 <= nx < 8 and 0 <= ny < 8:
                target = board_matrix[ny][nx]
                if target is not None and target.color != self.color:
                    moves.append((nx, ny))
        if is_board_obj and board.last_pawn_moved is not None:
            last_x, last_y = board.last_pawn_moved
            # Original: white pawn on fifth row (originally "b" → now "w") at row 3; black pawn on fourth ("n" → now "b") at row 4.
            white_pawn_on_fifth = (self.color == "w" and self.y == 3)
            black_pawn_on_fourth = (self.color == "b" and self.y == 4)
            if white_pawn_on_fifth or black_pawn_on_fourth:
                same_level = ((white_pawn_on_fifth and last_y == 3) or (black_pawn_on_fourth and last_y == 4))
                if same_level and abs(self.x - last_x) == 1:
                    target_piece = board_matrix[last_y][last_x]
                    if target_piece and target_piece.type == "pawn" and target_piece.color != self.color:
                        capture_move = (last_x, self.y + direction)
                        moves.append(capture_move)
        return moves

    def valid_moves(self, board):
        board_matrix = board.board if hasattr(board, 'board') else board
        moves = self.possible_moves(board)
        filtered_moves = [move for move in moves if not leaves_king_in_check(board_matrix, self, move)]
        return filtered_moves

class Rook(Piece):
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

    def valid_moves(self, board):
        moves = self.possible_moves(board)
        return [move for move in moves if not leaves_king_in_check(board, self, move)]

class Knight(Piece):
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

    def valid_moves(self, board):
        moves = self.possible_moves(board)
        return [move for move in moves if not leaves_king_in_check(board, self, move)]

class Bishop(Piece):
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

    def valid_moves(self, board):
        moves = self.possible_moves(board)
        return [move for move in moves if not leaves_king_in_check(board, self, move)]

class Queen(Piece):
    def __init__(self, color, x, y):
        super().__init__("queen", color, x, y)

    def possible_moves(self, board):
        moves = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0),
                      (1, 1), (1, -1), (-1, -1), (-1, 1)]
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

    def valid_moves(self, board):
        moves = self.possible_moves(board)
        return [move for move in moves if not leaves_king_in_check(board, self, move)]

class King(Piece):
    def __init__(self, color, x, y):
        super().__init__("king", color, x, y)

    def possible_moves(self, board, check_castling=True):
        moves = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0),
                      (1, 1), (1, -1), (-1, -1), (-1, 1)]
        for dx, dy in directions:
            nx = self.x + dx
            ny = self.y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                target = board[ny][nx]
                if target is None or target.color != self.color:
                    moves.append((nx, ny))
        if check_castling and not self.moved:
            if not is_in_check_simple(board, self.color):
                if self._can_castle_kingside(board):
                    moves.append((self.x + 2, self.y))
                if self._can_castle_queenside(board):
                    moves.append((self.x - 2, self.y))
        return moves

    def _can_castle_kingside(self, board):
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
        moves = self.possible_moves(board)
        return [move for move in moves if not leaves_king_in_check(board, self, move)]

# ------------------ Board Utility Functions ------------------
def is_square_threatened(board, x, y, own_color):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece.color != own_color:
                if piece.type == "king":
                    dx = abs(col - x)
                    dy = abs(row - y)
                    if dx <= 1 and dy <= 1:
                        return True
                else:
                    moves = piece.possible_moves(board)
                    if (x, y) in moves:
                        return True
    return False

def leaves_king_in_check(current_board, piece, move):
    temp_board = [[current_board[y][x] for x in range(8)] for y in range(8)]
    x_dest, y_dest = move
    captured_piece = temp_board[y_dest][x_dest]
    en_passant_capture = False
    captured_pawn_pos = None
    if piece.type == "pawn" and abs(piece.x - x_dest) == 1 and temp_board[y_dest][x_dest] is None:
        white_pawn_on_fifth = (piece.color == "w" and piece.y == 3)
        black_pawn_on_fourth = (piece.color == "b" and piece.y == 4)
        if (white_pawn_on_fifth and y_dest == 2) or (black_pawn_on_fourth and y_dest == 5):
            if hasattr(current_board, 'last_pawn_moved') and current_board.last_pawn_moved is not None:
                last_x, last_y = current_board.last_pawn_moved
                if x_dest == last_x and ((white_pawn_on_fifth and last_y == 3) or (black_pawn_on_fourth and last_y == 4)):
                    en_passant_capture = True
                    captured_pawn_pos = (last_x, last_y)
    temp_board[piece.y][piece.x] = None
    temp_board[y_dest][x_dest] = piece
    if en_passant_capture and captured_pawn_pos:
        x_cap, y_cap = captured_pawn_pos
        temp_board[y_cap][x_cap] = None
    king_x, king_y = None, None
    for y in range(8):
        for x in range(8):
            p = temp_board[y][x]
            if p and p.type == "king" and p.color == piece.color:
                king_x, king_y = x, y
                break
        if king_x is not None:
            break
    if piece.type == "king":
        king_x, king_y = x_dest, y_dest
    in_check = is_in_check(temp_board, piece.color, (king_x, king_y))
    return in_check

def is_in_check_simple(board, king_color):
    king_x, king_y = None, None
    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece and piece.type == "king" and piece.color == king_color:
                king_x, king_y = x, y
                break
        if king_x is not None:
            break
    pawn_dirs = [(-1, -1), (1, -1)] if king_color == "w" else [(-1, 1), (1, 1)]
    for dx, dy in pawn_dirs:
        nx, ny = king_x + dx, king_y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            piece = board[ny][nx]
            if piece and piece.type == "pawn" and piece.color != king_color:
                return True
    knight_jumps = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
    for dx, dy in knight_jumps:
        nx, ny = king_x + dx, king_y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            piece = board[ny][nx]
            if piece and piece.type == "knight" and piece.color != king_color:
                return True
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = king_x + dx, king_y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                piece = board[ny][nx]
                if piece and piece.type == "king" and piece.color != king_color:
                    return True
    straight_dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    for dx, dy in straight_dirs:
        for i in range(1, 8):
            nx, ny = king_x + i * dx, king_y + i * dy
            if not (0 <= nx < 8 and 0 <= ny < 8):
                break
            piece = board[ny][nx]
            if piece:
                if piece.color != king_color and (piece.type == "rook" or piece.type == "queen"):
                    return True
                break
    diagonal_dirs = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
    for dx, dy in diagonal_dirs:
        for i in range(1, 8):
            nx, ny = king_x + i * dx, king_y + i * dy
            if not (0 <= nx < 8 and 0 <= ny < 8):
                break
            piece = board[ny][nx]
            if piece:
                if piece.color != king_color and (piece.type == "bishop" or piece.type == "queen"):
                    return True
                break
    return False

def is_in_check(board, king_color, king_position=None):
    if king_position is None:
        for y in range(8):
            for x in range(8):
                piece = board[y][x]
                if piece and piece.type == "king" and piece.color == king_color:
                    king_position = (x, y)
                    break
            if king_position is not None:
                break
    king_x, king_y = king_position
    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece and piece.color != king_color:
                if piece.type == "king":
                    dx = abs(x - king_x)
                    dy = abs(y - king_y)
                    if dx <= 1 and dy <= 1:
                        return True
                if piece.type == "king":
                    moves = piece.possible_moves(board, check_castling=False)
                else:
                    moves = piece.possible_moves(board)
                if (king_x, king_y) in moves:
                    return True
    return False

def is_checkmate(board, color):
    if not is_in_check(board, color):
        return False
    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece and piece.color == color:
                if piece.valid_moves(board):
                    return False
    return True

def is_stalemate(board, color):
    if is_in_check(board, color):
        return False
    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece and piece.color == color:
                if piece.valid_moves(board):
                    return False
    return True

def insufficient_material(board):
    pieces = []
    for row in board:
        for piece in row:
            if piece:
                pieces.append(piece)
    non_king = [p for p in pieces if p.type != "king"]
    if len(non_king) == 0:
        return True
    if len(non_king) == 1 and non_king[0].type in ["bishop", "knight"]:
        return True
    return False

def get_board_signature(board, turn):
    rows = []
    for y in range(8):
        row = []
        for x in range(8):
            p = board[y][x]
            row.append(f"{p.color[0]}{p.type[0]}" if p else ".")
        rows.append("".join(row))
    return "|".join(rows) + f"_{turn}"

def ease_movement(t):
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

# ------------------ Board Class ------------------
class Board:
    def __init__(self, ai_mode=False):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        # White moves first; now white is "w" (converted from original "b")
        self.turn = "w"
        self.initialize_board()
        self.selected_piece = None
        self.valid_moves = []
        self.history = []
        self.checkmate = False
        self.winner = None
        self.promotion_pending = False
        self.pawn_to_promote = None
        self.repeated_positions = {}
        initial_signature = get_board_signature(self.board, self.turn)
        self.repeated_positions[initial_signature] = 1
        self.last_pawn_moved = None
        self.board_rotated = False
        self.ai_mode = ai_mode

        # Animation attributes
        self.animating = False
        self.animating_piece = None
        self.start_pos = None
        self.end_pos = None
        self.animation_time = 0
        self.animation_duration = 15

        # For en passant and castling animations
        self.extra_animating_piece = None
        self.extra_start_pos = None
        self.extra_end_pos = None
        self.rotating = False
        self.rotation_time = 0
        self.rotation_duration = 20
        self.rotation_initial = False
        self.rotation_final = True

        self.white_material = 0
        self.white_captured_pieces = []
        self.black_captured_pieces = []

    def initialize_board(self):
        # White pieces (originally "b" become white "w")
        self.board[7][0] = Rook("w", 0, 7)
        self.board[7][1] = Knight("w", 1, 7)
        self.board[7][2] = Bishop("w", 2, 7)
        self.board[7][3] = Queen("w", 3, 7)
        self.board[7][4] = King("w", 4, 7)
        self.board[7][5] = Bishop("w", 5, 7)
        self.board[7][6] = Knight("w", 6, 7)
        self.board[7][7] = Rook("w", 7, 7)
        for i in range(8):
            self.board[6][i] = Pawn("w", i, 6)
        # Black pieces (originally "n" become black "b")
        self.board[0][0] = Rook("b", 0, 0)
        self.board[0][1] = Knight("b", 1, 0)
        self.board[0][2] = Bishop("b", 2, 0)
        self.board[0][3] = Queen("b", 3, 0)
        self.board[0][4] = King("b", 4, 0)
        self.board[0][5] = Bishop("b", 5, 0)
        self.board[0][6] = Knight("b", 6, 0)
        self.board[0][7] = Rook("b", 7, 0)
        for i in range(8):
            self.board[1][i] = Pawn("b", i, 1)

    def select_piece(self, x, y):
        if self.checkmate or self.promotion_pending:
            return False
        piece = self.board[y][x]
        if piece is not None and piece.color == self.turn:
            self.selected_piece = piece
            self.valid_moves = piece.valid_moves(self.board)
            if piece.type == "pawn" and self.last_pawn_moved is not None:
                last_x, last_y = self.last_pawn_moved
                # White pawn on fifth row: row 3; Black pawn on fourth row: row 4
                white_pawn_on_fifth = (piece.color == "w" and piece.y == 3)
                black_pawn_on_fourth = (piece.color == "b" and piece.y == 4)
                if white_pawn_on_fifth or black_pawn_on_fourth:
                    same_level = ((white_pawn_on_fifth and last_y == 3) or (black_pawn_on_fourth and last_y == 4))
                    if same_level and abs(piece.x - last_x) == 1:
                        pawn_piece = self.board[last_y][last_x]
                        if pawn_piece and pawn_piece.type == "pawn" and pawn_piece.color != piece.color:
                            direction = -1 if piece.color == "w" else 1
                            en_passant_move = (last_x, piece.y + direction)
                            if not leaves_king_in_check(self.board, piece, en_passant_move):
                                if en_passant_move not in self.valid_moves:
                                    self.valid_moves.append(en_passant_move)
            return True
        return False

    def update_animation(self):
        if not self.animating:
            return
        self.animation_time += 1
        if self.animation_time >= self.animation_duration:
            self._complete_move()

    def _complete_move(self):
        data = self._datos_movimiento
        piece = data['piece']
        start_x, start_y = data['desde_x'], data['desde_y']
        x, y = data['x'], data['y']
        castling = data['es_enroque']
        moved_rook = data['torre_movida']
        rook_from = data['torre_desde']
        rook_to = data['torre_hasta']
        en_passant = data['es_captura_al_paso']
        pawn_capture_pos = data['pos_peon_capturado']
        last_pawn_temp = data['ultimo_peon_temp']
        current_color = data['color_actual']
        captured_piece = self.board[y][x]
        if captured_piece:
            if piece.color == "w":
                self.white_captured_pieces.append(captured_piece.type)
                self.white_material += PIECE_VALUE[captured_piece.type]
            else:
                self.black_captured_pieces.append(captured_piece.type)
                self.white_material -= PIECE_VALUE[captured_piece.type]
        self.board[start_y][start_x] = None
        self.board[y][x] = piece
        piece.move(x, y)
        if castling:
            rook_x_orig, rook_y_orig = rook_from
            rook_x_new, rook_y_new = rook_to
            self.board[rook_y_orig][rook_x_orig] = None
            self.board[rook_y_new][rook_x_new] = moved_rook
            moved_rook.move(rook_x_new, rook_y_new)
        if en_passant:
            last_x, last_y = pawn_capture_pos
            captured_pawn = self.board[last_y][last_x]
            if piece.color == "w":
                self.white_captured_pieces.append("pawn")
                self.white_material += PIECE_VALUE["pawn"]
            else:
                self.black_captured_pieces.append("pawn")
                self.white_material -= PIECE_VALUE["pawn"]
            self.board[last_y][last_x] = None
        if piece.type == "pawn" and (y == 0 or y == 7):
            self.promotion_pending = True
            self.pawn_to_promote = piece
            self.selected_piece = None
            self.valid_moves = []
            self.last_pawn_moved = last_pawn_temp
            self.animating = False
            return
        self.turn = "b" if self.turn == "w" else "w"
        if not self.ai_mode:
            current_state = self.board_rotated
            self.rotating = True
            self.rotation_time = 0
            self.rotation_initial = current_state
            self.rotation_final = not current_state
        if self.last_pawn_moved is not None:
            last_x, last_y = self.last_pawn_moved
            last_pawn_piece = self.board[last_y][last_x]
            if last_pawn_piece and last_pawn_piece.color == current_color:
                self.last_pawn_moved = None
        if last_pawn_temp is not None:
            self.last_pawn_moved = last_pawn_temp
        signature = get_board_signature(self.board, self.turn)
        self.repeated_positions[signature] = self.repeated_positions.get(signature, 0) + 1
        if self.history:
            self.history[-1]['signature'] = signature
        if is_checkmate(self.board, self.turn):
            self.checkmate = True
            self.winner = "w" if self.turn == "b" else "b"
            Game.state = "final"
        elif self.repeated_positions[signature] >= 3:
            self.checkmate = True
            self.winner = "draw"
            Game.state = "final"
        elif is_stalemate(self.board, self.turn):
            self.checkmate = True
            self.winner = "draw"
            Game.state = "final"
        elif insufficient_material(self.board):
            self.checkmate = True
            self.winner = "draw"
            Game.state = "final"
        self.selected_piece = None
        self.valid_moves = []
        self.animating = False
        self.animating_piece = None
        self.extra_animating_piece = None

    def move_piece(self, x, y):
        if self.checkmate or self.promotion_pending or self.animating:
            return False
        if self.selected_piece and (x, y) in self.valid_moves:
            piece = self.selected_piece
            start_x, start_y = piece.x, piece.y
            current_color = self.turn
            direction = -1 if piece.color == "w" else 1
            en_passant = False
            pawn_captured = None
            last_pawn_temp = None
            castling = False
            moved_rook = None
            rook_from = None
            rook_to = None
            if piece.type == "king" and abs(x - start_x) == 2:
                castling = True
                if x > start_x:  # Kingside castling
                    rook_x = 7
                    rook_new_x = x - 1
                else:  # Queenside castling
                    rook_x = 0
                    rook_new_x = x + 1
                rook = self.board[start_y][rook_x]
                rook_from = (rook_x, start_y)
                rook_to = (rook_new_x, start_y)
                moved_rook = rook
            if piece.type == "pawn" and abs(x - start_x) == 1 and self.board[y][x] is None:
                if self.last_pawn_moved is not None:
                    last_x, last_y = self.last_pawn_moved
                    white_pawn_on_fifth = (piece.color == "w" and start_y == 3)
                    black_pawn_on_fourth = (piece.color == "b" and start_y == 4)
                    if (white_pawn_on_fifth or black_pawn_on_fourth) and x == last_x:
                        same_level = ((white_pawn_on_fifth and last_y == 3) or (black_pawn_on_fourth and last_y == 4))
                        if same_level:
                            pawn_piece = self.board[last_y][last_x]
                            if pawn_piece and pawn_piece.type == "pawn" and pawn_piece.color != piece.color:
                                en_passant = True
                                pawn_captured = pawn_piece
            history_entry = {
                'piece': piece,
                'from': (start_x, start_y),
                'to': (x, y),
                'capture': self.board[y][x],
                'moved': piece.moved
            }
            if castling:
                history_entry['castling'] = True
                history_entry['rook'] = moved_rook
                history_entry['rook_from'] = rook_from
                history_entry['rook_to'] = rook_to
            if en_passant:
                history_entry['en_passant'] = True
                history_entry['pawn_captured'] = pawn_captured
                history_entry['pawn_capture_pos'] = self.last_pawn_moved
            self.history.append(history_entry)
            self.animating = True
            self.animating_piece = piece
            self.start_pos = (start_x, start_y)
            self.end_pos = (x, y)
            self.animation_time = 0
            if castling:
                self.extra_animating_piece = moved_rook
                self.extra_start_pos = rook_from
                self.extra_end_pos = rook_to
            else:
                self.extra_animating_piece = None
                self.extra_start_pos = None
                self.extra_end_pos = None
            if piece.type == "pawn" and abs(start_y - y) == 2:
                last_pawn_temp = (x, y)
            self._datos_movimiento = {
                'piece': piece,
                'desde_x': start_x,
                'desde_y': start_y,
                'x': x,
                'y': y,
                'es_enroque': castling,
                'torre_movida': moved_rook,
                'torre_desde': rook_from,
                'torre_hasta': rook_to,
                'es_captura_al_paso': en_passant,
                'pos_peon_capturado': self.last_pawn_moved if en_passant else None,
                'ultimo_peon_temp': last_pawn_temp,
                'color_actual': current_color
            }
            return True
        return False

    def update_rotation(self):
        if not self.rotating:
            return
        self.rotation_time += 1
        if self.rotation_time >= self.rotation_duration:
            self.board_rotated = self.rotation_final
            self.rotating = False

    def promote_pawn(self, piece_type):
        if not self.promotion_pending or not self.pawn_to_promote:
            return False
        x, y = self.pawn_to_promote.x, self.pawn_to_promote.y
        color = self.pawn_to_promote.color
        value_diff = PIECE_VALUE[piece_type] - PIECE_VALUE["pawn"]
        if color == "w":
            self.white_material += value_diff
        else:
            self.white_material -= value_diff
        if piece_type == "queen":
            new_piece = Queen(color, x, y)
        elif piece_type == "rook":
            new_piece = Rook(color, x, y)
        elif piece_type == "bishop":
            new_piece = Bishop(color, x, y)
        elif piece_type == "knight":
            new_piece = Knight(color, x, y)
        else:
            return False
        self.board[y][x] = new_piece
        if self.history:
            last_move = self.history[-1]
            last_move['promotion'] = {
                'original_type': "pawn",
                'new_type': piece_type
            }
        self.promotion_pending = False
        self.pawn_to_promote = None
        self.turn = "b" if self.turn == "w" else "w"
        if not self.ai_mode:
            current_state = self.board_rotated
            self.rotating = True
            self.rotation_time = 0
            self.rotation_initial = current_state
            self.rotation_final = not current_state
        if is_checkmate(self.board, self.turn):
            self.checkmate = True
            self.winner = "b" if self.turn == "w" else "w"
            Game.state = "final"
        return True

    def undo_move(self):
        if self.history:
            last_move = self.history.pop()
            piece = last_move['piece']
            start_x, start_y = last_move['from']
            end_x, end_y = last_move['to']
            capture = last_move['capture']
            prev_moved = last_move['moved']
            if capture:
                if piece.color == "w":
                    if capture.type in self.white_captured_pieces:
                        self.white_captured_pieces.remove(capture.type)
                    self.white_material -= PIECE_VALUE[capture.type]
                else:
                    if capture.type in self.black_captured_pieces:
                        self.black_captured_pieces.remove(capture.type)
                    self.white_material += PIECE_VALUE[capture.type]
            if 'promotion' in last_move:
                new_type = last_move['promotion']['new_type']
                value_diff = PIECE_VALUE[new_type] - PIECE_VALUE["pawn"]
                if piece.color == "w":
                    self.white_material -= value_diff
                else:
                    self.white_material += value_diff
                piece = Pawn(piece.color, start_x, start_y)
                piece.moved = prev_moved
            self.board[start_y][start_x] = piece
            self.board[end_y][end_x] = capture
            piece.x, piece.y = start_x, start_y
            piece.moved = prev_moved
            if 'castling' in last_move and last_move['castling']:
                rook = last_move['rook']
                rook_from_x, rook_from_y = last_move['rook_from']
                rook_to_x, rook_to_y = last_move['rook_to']
                self.board[rook_to_y][rook_to_x] = None
                self.board[rook_from_y][rook_from_x] = rook
                rook.x, rook.y = rook_from_x, rook_from_y
                rook.moved = False
            if 'en_passant' in last_move and last_move['en_passant']:
                captured_pawn = last_move['pawn_captured']
                x_cap, y_cap = last_move['pawn_capture_pos']
                if piece.color == "w":
                    if "pawn" in self.white_captured_pieces:
                        self.white_captured_pieces.remove("pawn")
                    self.white_material -= PIECE_VALUE["pawn"]
                else:
                    if "pawn" in self.black_captured_pieces:
                        self.black_captured_pieces.remove("pawn")
                    self.white_material += PIECE_VALUE["pawn"]
                self.board[y_cap][x_cap] = captured_pawn
            self.turn = "b" if self.turn == "w" else "w"
            if not self.ai_mode:
                self.board_rotated = not self.board_rotated
            signature = last_move.get('signature')
            if signature and signature in self.repeated_positions:
                self.repeated_positions[signature] -= 1
                if self.repeated_positions[signature] <= 0:
                    del self.repeated_positions[signature]
            if self.checkmate:
                self.checkmate = False
                self.winner = None
                if Game.state == "final":
                    Game.state = "playing"
            if self.promotion_pending:
                self.promotion_pending = False
                self.pawn_to_promote = None
            self.selected_piece = None
            self.valid_moves = []
            if self.history:
                prev_move = self.history[-1]
                prev_piece = prev_move['piece']
                start_x_prev, start_y_prev = prev_move['from']
                end_x_prev, end_y_prev = prev_move['to']
                if prev_piece.type == "pawn" and abs(start_y_prev - end_y_prev) == 2:
                    self.last_pawn_moved = (end_x_prev, end_y_prev)
                else:
                    self.last_pawn_moved = None
            else:
                self.last_pawn_moved = None

    def is_in_check(self, color):
        return is_in_check(self.board, color)

# ------------------ Promotion Menu ------------------
class PromotionMenu:
    def __init__(self, color):
        self.color = color
        self.options = ["queen", "rook", "bishop", "knight"]
        self.selection = 0
        self.option_rects = []

    def draw(self, surface, images):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192))
        surface.blit(overlay, (0, 0))
        title_font = pygame.font.SysFont(None, 48)
        title = title_font.render("Select a piece for promotion", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        surface.blit(title, title_rect)
        self.option_rects = []
        spacing = 120
        start_x = WIDTH // 2 - (spacing * (len(self.options) - 1)) // 2
        for i, option in enumerate(self.options):
            pos_x = start_x + i * spacing
            pos_y = HEIGHT // 2
            if i == self.selection:
                button_rect = pygame.Rect(pos_x - 45, pos_y - 45, 90, 90)
                pygame.draw.rect(surface, LIGHT_GREEN, button_rect)
                pygame.draw.rect(surface, WHITE, button_rect, 2)
            else:
                button_rect = pygame.Rect(pos_x - 40, pos_y - 40, 80, 80)
                pygame.draw.rect(surface, (170, 170, 170), button_rect)
                pygame.draw.rect(surface, GRAY, button_rect, 2)
            self.option_rects.append(button_rect)
            key = f"{self.color}_{option}"
            if key in images:
                img = images[key]
                img_rect = img.get_rect(center=(pos_x, pos_y))
                surface.blit(img, img_rect)
            name_font = pygame.font.SysFont(None, 24)
            name = name_font.render(option.capitalize(), True, WHITE)
            name_rect = name.get_rect(center=(pos_x, pos_y + 60))
            surface.blit(name, name_rect)
        instr_font = pygame.font.SysFont(None, 28)
        instr = instr_font.render("Use left/right arrows, Enter or click to select", True, WHITE)
        instr_rect = instr.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        surface.blit(instr, instr_rect)

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selection = (self.selection - 1) % len(self.options)
            elif event.key == pygame.K_RIGHT:
                self.selection = (self.selection + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.options[self.selection]
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selection = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    return self.options[i]
        return None

# ------------------ Main Menu ------------------
class Menu:
    def __init__(self):
        self.options = ["2 Player Game", "Play vs AI", "Exit"]
        self.selection = 0
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)
        self.option_rects = []

    def draw(self, surface):
        surface.fill(GRAY)
        title = self.title_font.render("CHESS", True, BLACK)
        title_rect = title.get_rect(center=(WIDTH // 2, 100))
        surface.blit(title, title_rect)
        self.option_rects = []
        extra_gap = 40
        for i, option in enumerate(self.options):
            pos_y = 250 + i * 70 + (extra_gap if option == "Exit" else 0)
            color = LIGHT_GREEN if i == self.selection else WHITE
            text = self.font.render(option, True, BLACK)
            rect = text.get_rect(center=(WIDTH // 2, pos_y))
            rect_button = rect.inflate(40, 20)
            pygame.draw.rect(surface, color, rect_button)
            pygame.draw.rect(surface, BLACK, rect_button, 2)
            surface.blit(text, rect)
            self.option_rects.append(rect_button)

    def handle_events(self, event):
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

# ------------------ Side Menu ------------------
class SideMenu:
    def __init__(self):
        self.options = ["White", "Black", "Random", "Back"]
        self.selection = 0
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)
        self.option_rects = []

    def draw(self, surface, width, height):
        surface.fill((200, 200, 200))
        title = self.title_font.render("CHOOSE YOUR SIDE", True, (0, 0, 0))
        title_rect = title.get_rect(center=(width // 2, 100))
        surface.blit(title, title_rect)
        self.option_rects = []
        for i, option in enumerate(self.options):
            color = (144, 238, 144) if i == self.selection else (255, 255, 255)
            text = self.font.render(option, True, (0, 0, 0))
            pos_y = 250 + i * 70 + (40 if option == "Back" else 0)
            rect = text.get_rect(center=(width // 2, pos_y))
            rect_button = rect.inflate(40, 20)
            pygame.draw.rect(surface, color, rect_button)
            pygame.draw.rect(surface, (0, 0, 0), rect_button, 2)
            surface.blit(text, rect)
            self.option_rects.append(rect_button)

    def handle_events(self, event):
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
                    return self.selection
        return None

# ------------------ Main Game Class ------------------
class Game:
    state = "menu"

    def __init__(self):
        self.menu = Menu()
        self.promotion_menu = None
        self.difficulty_menu = DifficultyMenu()
        self.side_menu = SideMenu()
        self.board = None
        self.images = load_images()
        self.message = ""
        self.message_time = 0
        self.ai_mode = False
        self.ai = None
        self.ai_thinking = False
        self.ai_level = "medium"
        self.has_moved = False
        self.play_as_black = False  # If True, player plays as black

    def start_game(self, ai_mode=False, ai_level="medium", play_as_black=False):
        self.board = Board(ai_mode=ai_mode)
        self.board.board_rotated = play_as_black  # Rotate board if playing as black
        self.message = ""
        self.message_time = 0
        self.ai_mode = ai_mode
        self.ai_level = ai_level
        self.has_moved = False
        self.play_as_black = play_as_black
        if ai_mode:
            self.ai = ChessAI(level=ai_level)
            # If the player chooses black, the AI (white) should move first.
            if play_as_black:
                self.ai_thinking = True
                self.show_message("AI thinking...", 0)
                threading.Thread(target=self.ai_turn).start()
        Game.state = "playing"

    def return_to_menu(self):
        self.message = ""
        self.message_time = 0
        Game.state = "menu"

    def show_message(self, message, duration=2000):
        self.message = message
        self.message_time = pygame.time.get_ticks() + duration if duration > 0 else 0

    def update_messages(self):
        if self.message and self.message_time > 0 and pygame.time.get_ticks() > self.message_time:
            self.message = ""

    def draw_board(self, surface):
        surface.fill(GRAY)
        border_thickness = 4
        border_rect = pygame.Rect(
            MARGIN_X - border_thickness,
            MARGIN_Y - border_thickness,
            BOARD_SIZE + border_thickness * 2,
            BOARD_SIZE + border_thickness * 2
        )
        pygame.draw.rect(surface, DARK_GRAY, border_rect, border_thickness)
        for row in range(8):
            for col in range(8):
                if self.board.rotating:
                    t = self.board.rotation_time / self.board.rotation_duration
                    t = ease_movement(t)
                    if t < 0.5:
                        if self.board.rotation_initial:
                            adjusted_row = 7 - row
                            adjusted_col = 7 - col
                        else:
                            adjusted_row = row
                            adjusted_col = col
                    else:
                        if self.board.rotation_final:
                            adjusted_row = 7 - row
                            adjusted_col = 7 - col
                        else:
                            adjusted_row = row
                            adjusted_col = col
                else:
                    if self.board.board_rotated:
                        adjusted_row = 7 - row
                        adjusted_col = 7 - col
                    else:
                        adjusted_row = row
                        adjusted_col = col
                x = MARGIN_X + col * SQUARE_SIZE
                y = MARGIN_Y + row * SQUARE_SIZE
                square_color = WHITE if (row + col) % 2 == 0 else DARK_GREEN
                pygame.draw.rect(surface, square_color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
                piece = self.board.board[adjusted_row][adjusted_col]
                if piece and (not self.board.animating or
                              (piece != self.board.animating_piece and
                               (self.board.extra_animating_piece is None or piece != self.board.extra_animating_piece))):
                    key = f"{piece.color}_{piece.type}"
                    if key in self.images:
                        image = self.images[key]
                        img_rect = image.get_rect()
                        img_x = x + (SQUARE_SIZE - img_rect.width) // 2
                        img_y = y + (SQUARE_SIZE - img_rect.height) // 2
                        surface.blit(image, (img_x, img_y))
                        if piece.type == "king" and self.board.is_in_check(piece.color) and not self.board.checkmate:
                            overlay_check = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                            overlay_check.fill(CHECK_COLOR)
                            surface.blit(overlay_check, (x, y))
        coord_font = pygame.font.SysFont(None, 24)
        current_orientation = self.board.board_rotated
        if self.board.rotating:
            t = self.board.rotation_time / self.board.rotation_duration
            t = ease_movement(t)
            if t >= 0.5:
                current_orientation = self.board.rotation_final
        for i in range(8):
            letter = chr(97 + (7 - i)) if current_orientation else chr(97 + i)
            letter_text = coord_font.render(letter, True, BLACK)
            x_letter = MARGIN_X + i * SQUARE_SIZE + SQUARE_SIZE // 2 - letter_text.get_width() // 2
            y_letter = MARGIN_Y + BOARD_SIZE + 10
            surface.blit(letter_text, (x_letter, y_letter))
        for i in range(8):
            number = str(i + 1) if current_orientation else str(8 - i)
            number_text = coord_font.render(number, True, BLACK)
            x_number = MARGIN_X - number_text.get_width() - 10
            y_number = MARGIN_Y + i * SQUARE_SIZE + SQUARE_SIZE // 2 - number_text.get_height() // 2
            surface.blit(number_text, (x_number, y_number))
        if self.board.animating:
            t = self.board.animation_time / self.board.animation_duration
            t = ease_movement(t)
            from_x, from_y = self.board.start_pos
            to_x, to_y = self.board.end_pos
            if self.board.board_rotated:
                screen_from_x = MARGIN_X + (7 - from_x) * SQUARE_SIZE
                screen_from_y = MARGIN_Y + (7 - from_y) * SQUARE_SIZE
                screen_to_x = MARGIN_X + (7 - to_x) * SQUARE_SIZE
                screen_to_y = MARGIN_Y + (7 - to_y) * SQUARE_SIZE
            else:
                screen_from_x = MARGIN_X + from_x * SQUARE_SIZE
                screen_from_y = MARGIN_Y + from_y * SQUARE_SIZE
                screen_to_x = MARGIN_X + to_x * SQUARE_SIZE
                screen_to_y = MARGIN_Y + to_y * SQUARE_SIZE
            current_x = screen_from_x + (screen_to_x - screen_from_x) * t
            current_y = screen_from_y + (screen_to_y - screen_from_y) * t
            key = f"{self.board.animating_piece.color}_{self.board.animating_piece.type}"
            if key in self.images:
                image = self.images[key]
                img_rect = image.get_rect()
                img_x = current_x + (SQUARE_SIZE - img_rect.width) // 2
                img_y = current_y + (SQUARE_SIZE - img_rect.height) // 2
                surface.blit(image, (img_x, img_y))
            if self.board.extra_animating_piece:
                from_x, from_y = self.board.extra_start_pos
                to_x, to_y = self.board.extra_end_pos
                if self.board.board_rotated:
                    screen_from_x = MARGIN_X + (7 - from_x) * SQUARE_SIZE
                    screen_from_y = MARGIN_Y + (7 - from_y) * SQUARE_SIZE
                    screen_to_x = MARGIN_X + (7 - to_x) * SQUARE_SIZE
                    screen_to_y = MARGIN_Y + (7 - to_y) * SQUARE_SIZE
                else:
                    screen_from_x = MARGIN_X + from_x * SQUARE_SIZE
                    screen_from_y = MARGIN_Y + from_y * SQUARE_SIZE
                    screen_to_x = MARGIN_X + to_x * SQUARE_SIZE
                    screen_to_y = MARGIN_Y + to_y * SQUARE_SIZE
                current_x = screen_from_x + (screen_to_x - screen_from_x) * t
                current_y = screen_from_y + (screen_to_y - screen_from_y) * t
                key = f"{self.board.extra_animating_piece.color}_{self.board.extra_animating_piece.type}"
                if key in self.images:
                    image = self.images[key]
                    img_rect = image.get_rect()
                    img_x = current_x + (SQUARE_SIZE - img_rect.width) // 2
                    img_y = current_y + (SQUARE_SIZE - img_rect.height) // 2
                    surface.blit(image, (img_x, img_y))
        if self.board.rotating:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            t = self.board.rotation_time / self.board.rotation_duration
            t = ease_movement(t)
            opacity = int(255 * (1 - abs(2 * t - 1)))
            overlay.fill((0, 0, 0, opacity))
            surface.blit(overlay, (0, 0))
        if self.board.selected_piece and not self.board.checkmate and not self.board.promotion_pending and not self.board.animating and not self.board.rotating:
            if self.board.board_rotated:
                x_sel = MARGIN_X + (7 - self.board.selected_piece.x) * SQUARE_SIZE
                y_sel = MARGIN_Y + (7 - self.board.selected_piece.y) * SQUARE_SIZE
            else:
                x_sel = MARGIN_X + self.board.selected_piece.x * SQUARE_SIZE
                y_sel = MARGIN_Y + self.board.selected_piece.y * SQUARE_SIZE
            overlay_sel = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            overlay_sel.fill(SELECTION)
            surface.blit(overlay_sel, (x_sel, y_sel))
            for mx, my in self.board.valid_moves:
                if self.board.board_rotated:
                    x_mov = MARGIN_X + (7 - mx) * SQUARE_SIZE
                    y_mov = MARGIN_Y + (7 - my) * SQUARE_SIZE
                else:
                    x_mov = MARGIN_X + mx * SQUARE_SIZE
                    y_mov = MARGIN_Y + my * SQUARE_SIZE
                overlay_mov = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                overlay_mov.fill(SELECTION)
                surface.blit(overlay_mov, (x_mov, y_mov))
        info_font = pygame.font.SysFont(None, 36)
        turn_text = info_font.render(f"Turn: {'White' if self.board.turn == 'w' else 'Black'}", True, BLACK)
        surface.blit(turn_text, (20, 20))
        if self.message:
            msg_font = pygame.font.SysFont(None, 36)
            msg_text = msg_font.render(self.message, True, BLACK)
            msg_rect = msg_text.get_rect(topright=(WIDTH - 20, 20))
            surface.blit(msg_text, msg_rect)
        if self.board.checkmate:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            surface.blit(overlay, (0, 0))
            large_font = pygame.font.SysFont(None, 72)
            if self.board.winner == "draw":
                final_text = large_font.render("DRAW", True, WHITE)
                detail_text = large_font.render("", True, WHITE)
            else:
                winner = "White" if self.board.winner == "w" else "Black"
                final_text = large_font.render("CHECKMATE", True, WHITE)
                detail_text = large_font.render(f"{winner} wins", True, WHITE)
            final_rect = final_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            detail_rect = detail_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            surface.blit(final_text, final_rect)
            surface.blit(detail_text, detail_rect)
            instr_font = pygame.font.SysFont(None, 36)
            instr_text = instr_font.render("Press ESC to return to menu", True, WHITE)
            instr_rect = instr_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90))
            surface.blit(instr_text, instr_rect)
        self.draw_captured_material(surface)
        button_font = pygame.font.SysFont(None, 24)
        undo_text = button_font.render("Undo [Z]", True, BLACK)
        undo_rect = undo_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
        pygame.draw.rect(surface, WHITE, undo_rect.inflate(20, 10))
        pygame.draw.rect(surface, BLACK, undo_rect.inflate(20, 10), 2)
        surface.blit(undo_text, undo_rect)
        menu_text = button_font.render("Menu [ESC]", True, BLACK)
        menu_rect = menu_text.get_rect(bottomleft=(20, HEIGHT - 20))
        pygame.draw.rect(surface, WHITE, menu_rect.inflate(20, 10))
        pygame.draw.rect(surface, BLACK, menu_rect.inflate(20, 10), 2)
        surface.blit(menu_text, menu_rect)

    def handle_events(self, event):
        if Game.state == "menu":
            action = self.menu.handle_events(event)
            if action == 0:  # 2 Player Game
                self.start_game(ai_mode=False)
            elif action == 1:  # Play vs AI
                Game.state = "menu_side"
            elif action == 2:  # Exit
                return False
        elif Game.state == "menu_side":
            action = self.side_menu.handle_events(event)
            if action == 0:  # White
                self.play_as_black = False
                Game.state = "menu_difficulty"
            elif action == 1:  # Black
                self.play_as_black = True
                Game.state = "menu_difficulty"
            elif action == 2:  # Random
                self.play_as_black = random.choice([True, False])
                Game.state = "menu_difficulty"
            elif action == 3:  # Back
                Game.state = "menu"
        elif Game.state == "menu_difficulty":
            action = self.difficulty_menu.handle_events(event)
            if action == 0:  # Easy
                self.start_game(ai_mode=True, ai_level="easy", play_as_black=self.play_as_black)
            elif action == 1:  # Medium
                self.start_game(ai_mode=True, ai_level="medium", play_as_black=self.play_as_black)
            elif action == 2:  # Hard
                self.start_game(ai_mode=True, ai_level="hard", play_as_black=self.play_as_black)
            elif action == 3:  # Back
                Game.state = "menu_side"
        elif Game.state == "coronation":
            if self.promotion_menu:
                chosen_piece = self.promotion_menu.handle_events(event)
                if chosen_piece:
                    if self.board.promote_pawn(chosen_piece):
                        Game.state = "playing"
                        if self.board.checkmate:
                            self.show_message("CHECKMATE! Game over", 0)
                            Game.state = "final"
                    self.promotion_menu = None
        elif Game.state == "final":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.return_to_menu()
        elif Game.state == "playing":
            # Determine player and AI colors based on conversion:
            # If playing as black, player's pieces are "b" (black) and AI's are "w" (white), and vice versa.
            player_color = "b" if self.play_as_black else "w"
            ai_color = "w" if self.play_as_black else "b"
            # (Removed the condition that prevented selecting opponent pieces so capturing is allowed.)
            if self.board.animating or self.board.rotating or (self.ai_mode and self.ai_thinking):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.return_to_menu()
                return True
            if self.board.promotion_pending and not self.promotion_menu:
                self.promotion_menu = PromotionMenu(self.board.pawn_to_promote.color)
                Game.state = "coronation"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.board.checkmate and not self.board.promotion_pending:
                x, y = event.pos
                if MARGIN_X <= x < MARGIN_X + BOARD_SIZE and MARGIN_Y <= y < MARGIN_Y + SQUARE_SIZE * 8:
                    col = (x - MARGIN_X) // SQUARE_SIZE
                    row = (y - MARGIN_Y) // SQUARE_SIZE
                    if self.board.board_rotated:
                        adjusted_col = 7 - col
                        adjusted_row = 7 - row
                    else:
                        adjusted_col = col
                        adjusted_row = row
                    piece = self.board.board[adjusted_row][adjusted_col]
                    # Removed the check that prevented moving opponent (AI) pieces.
                    if self.board.selected_piece:
                        if self.board.move_piece(adjusted_col, adjusted_row):
                            self.has_moved = True
                            if self.board.promotion_pending:
                                self.promotion_menu = PromotionMenu(self.board.pawn_to_promote.color)
                                Game.state = "coronation"
                            elif self.board.checkmate:
                                if self.board.winner == "draw":
                                    self.show_message("DRAW", 0)
                                else:
                                    winner_color = "White" if self.board.winner == "w" else "Black"
                                    self.show_message(f"CHECKMATE! {winner_color} wins", 0)
                                Game.state = "final"
                        elif self.board.select_piece(adjusted_col, adjusted_row):
                            pass
                        else:
                            self.board.selected_piece = None
                            self.board.valid_moves = []
                    else:
                        self.board.select_piece(adjusted_col, adjusted_row)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.return_to_menu()
                elif event.key == pygame.K_z and not self.board.checkmate and not self.board.promotion_pending:
                    if self.ai_mode:
                        if self.board.turn == player_color and not self.has_moved:
                            if len(self.board.history) >= 2:
                                self.board.undo_move()
                                self.board.undo_move()
                                self.show_message("Moves undone", 2000)
                            else:
                                self.show_message("No moves to undo", 2000)
                        else:
                            self.show_message("You can only undo before moving", 2000)
                    else:
                        if self.board.history:
                            self.board.undo_move()
                            self.show_message("Move undone", 2000)
                        else:
                            self.show_message("No moves to undo", 2000)
        if Game.state == "playing" and self.ai_mode:
            ai_color = "w" if self.play_as_black else "b"
            if (self.board.turn == ai_color and not self.board.checkmate and
                not self.board.promotion_pending and not self.ai_thinking and
                not self.board.animating and not self.board.rotating):
                self.ai_thinking = True
                self.show_message("AI thinking...", 0)
                threading.Thread(target=self.ai_turn).start()
        player_color = "b" if self.play_as_black else "w"
        if self.ai_mode and self.board.turn == player_color and not self.ai_thinking:
            self.has_moved = False
        return True

    def ai_turn(self):
        try:
            move = self.ai.get_move(self.board.board, self.board.turn, self.board.last_pawn_moved)
            if not self.ai_thinking:
                return
            if move:
                (start_x, start_y), (end_x, end_y), promotion = move
                self.board.select_piece(start_x, start_y)
                self.board.move_piece(end_x, end_y)
                if self.board.promotion_pending and promotion:
                    self.board.promote_pawn(promotion)
        except Exception as e:
            self.show_message("Error: Could not obtain move from Stockfish", 5000)
            print(f"Error in ai_turn: {e}")
        self.ai_thinking = False
        if self.message == "AI thinking...":
            self.message = ""

    def draw_captured_material(self, surface):
        icon_size = 30
        gap = 0
        initial_vertical_position = MARGIN_Y + BOARD_SIZE // 2
        horizontal_margin = 20
        font = pygame.font.SysFont(None, 24)
        title_font = pygame.font.SysFont(None, 24)
        small_font = pygame.font.SysFont(None, 20)
        white_advantage = self.board.white_material if self.board.white_material > 0 else 0
        black_advantage = abs(self.board.white_material) if self.board.white_material < 0 else 0
        # Left side: White Advantage (captured black pieces)
        x_left = MARGIN_X - icon_size - horizontal_margin
        y_left = initial_vertical_position
        title_text = title_font.render("White Advantage", True, BLACK)
        offset_left = 100
        title_pos_left = (x_left - offset_left, y_left)
        surface.blit(title_text, title_pos_left)
        pygame.draw.line(surface, BLACK,
                         (title_pos_left[0], title_pos_left[1] + title_text.get_height()),
                         (title_pos_left[0] + title_text.get_width(), title_pos_left[1] + title_text.get_height()),
                         2)
        y_left += title_text.get_height() + gap + 15
        left_shift = 130
        left_table_x = MARGIN_X - horizontal_margin - left_shift
        white_captures = self.board.white_captured_pieces
        white_groups = {}
        for piece in white_captures:
            white_groups.setdefault(piece, 0)
            white_groups[piece] += 1
        priority_order = ["pawn", "knight", "bishop", "rook", "queen"]
        current_y_left = y_left
        for p_type in priority_order:
            if p_type in white_groups:
                count = white_groups[p_type]
                if p_type == "pawn":
                    num_rows = (count - 1) // 4 + 1
                    for row in range(num_rows):
                        start_index = row * 4
                        end_index = min(start_index + 4, count)
                        num_in_row = end_index - start_index
                        x_current = left_table_x
                        for i in range(num_in_row):
                            key = "b_pawn"  # Captured black pawn (original "n_pawn" → now "b_pawn")
                            if key in self.images:
                                img = self.images[key]
                                img_scaled = pygame.transform.smoothscale(img, (icon_size, icon_size))
                                surface.blit(img_scaled, (x_current, current_y_left))
                            x_current += icon_size + gap
                        current_y_left += icon_size + gap
                else:
                    num_in_row = count
                    x_current = left_table_x
                    for i in range(num_in_row):
                        key = f"b_{p_type}"
                        if key in self.images:
                            img = self.images[key]
                            img_scaled = pygame.transform.smoothscale(img, (icon_size, icon_size))
                            surface.blit(img_scaled, (x_current, current_y_left))
                        x_current += icon_size + gap
                    current_y_left += icon_size + gap
        if white_advantage != 0:
            adv_text = small_font.render(f"+{white_advantage}", True, BLACK)
            surface.blit(adv_text, (left_table_x, current_y_left + gap + 5))
        # Right side: Black Advantage (captured white pieces)
        extra_offset_right = 50
        x_right = MARGIN_X + BOARD_SIZE + horizontal_margin + extra_offset_right
        y_right = initial_vertical_position
        offset_n = 60
        title_text = title_font.render("Black Advantage", True, BLACK)
        title_pos_right = (x_right - offset_n, y_right)
        surface.blit(title_text, title_pos_right)
        pygame.draw.line(surface, BLACK,
                         (title_pos_right[0], title_pos_right[1] + title_text.get_height()),
                         (title_pos_right[0] + title_text.get_width(), title_pos_right[1] + title_text.get_height()),
                         2)
        y_right += title_text.get_height() + gap + 15
        right_table_x = x_right + 70
        black_captures = self.board.black_captured_pieces
        black_groups = {}
        for piece in black_captures:
            black_groups.setdefault(piece, 0)
            black_groups[piece] += 1
        current_y_right = y_right
        for p_type in priority_order:
            if p_type in black_groups:
                count = black_groups[p_type]
                if p_type == "pawn":
                    num_rows = (count - 1) // 4 + 1
                    for row in range(num_rows):
                        start_index = row * 4
                        end_index = min(start_index + 4, count)
                        num_in_row = end_index - start_index
                        x_current = right_table_x - icon_size
                        for i in range(num_in_row):
                            key = "w_pawn"  # Captured white pawn (original "b_pawn" → now "w_pawn")
                            if key in self.images:
                                img = self.images[key]
                                img_scaled = pygame.transform.smoothscale(img, (icon_size, icon_size))
                                surface.blit(img_scaled, (x_current, current_y_right))
                            x_current -= (icon_size + gap)
                        current_y_right += icon_size + gap
                else:
                    num_in_row = count
                    x_current = right_table_x - icon_size
                    for i in range(num_in_row):
                        key = f"w_{p_type}"
                        if key in self.images:
                            img = self.images[key]
                            img_scaled = pygame.transform.smoothscale(img, (icon_size, icon_size))
                            surface.blit(img_scaled, (x_current, current_y_right))
                        x_current -= (icon_size + gap)
                    current_y_right += icon_size + gap
        if black_advantage != 0:
            adv_text = small_font.render(f"+{black_advantage}", True, BLACK)
            text_width = adv_text.get_width()
            surface.blit(adv_text, (right_table_x - text_width, current_y_right + gap + 5))

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    if not self.handle_events(event):
                        running = False

            # NUEVA COMPROBACIÓN: Verificar turno de la IA sin depender de eventos
            if Game.state == "playing" and self.ai_mode:
                # Según nuestra conversión: si el jugador juega como black,
                # entonces el jugador usa "b" y la IA usa "w", y viceversa.
                ai_color = "w" if self.play_as_black else "b"
                if (self.board.turn == ai_color and not self.board.checkmate and
                        not self.board.promotion_pending and not self.ai_thinking and
                        not self.board.animating and not self.board.rotating):
                    self.ai_thinking = True
                    self.show_message("AI thinking...", 0)
                    threading.Thread(target=self.ai_turn).start()

            # Actualizar animaciones, mensajes, y redibujar pantalla
            if Game.state == "playing" and self.board:
                if hasattr(self.board, 'animating') and self.board.animating:
                    self.board.update_animation()
                if hasattr(self.board, 'rotating') and self.board.rotating:
                    self.board.update_rotation()
            self.update_messages()
            if Game.state == "menu":
                self.menu.draw(window)
            elif Game.state == "menu_side":
                self.side_menu.draw(window, WIDTH, HEIGHT)
            elif Game.state == "menu_difficulty":
                self.difficulty_menu.draw(window, WIDTH, HEIGHT)
            elif Game.state == "playing":
                self.draw_board(window)
            elif Game.state == "final":
                self.draw_board(window)
            elif Game.state == "coronation":
                self.draw_board(window)
                if self.promotion_menu:
                    self.promotion_menu.draw(window, self.images)
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
