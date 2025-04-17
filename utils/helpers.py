"""
Utility functions for chess logic and animations.
"""
from models.constants import COLOR_WHITE, COLOR_BLACK

def is_square_threatened(board, x, y, own_color):
    """
    Return True if the given square (x, y) is attacked by an opponent of 'own_color'.
    This checks potential moves of all opposing pieces.
    """
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece.color != own_color:
                # King adjacency check
                if piece.type == "king":
                    dx = abs(col - x)
                    dy = abs(row - y)
                    if dx <= 1 and dy <= 1:
                        return True
                else:
                    # For other pieces, consult possible_moves
                    moves = piece.possible_moves(board)
                    if (x, y) in moves:
                        return True
    return False

def leaves_king_in_check(current_board, piece, move):
    """
    Simulate the piece's move on a temporary board and check if it leaves
    the moving player's king in check.
    """
    temp_board = [[current_board[y][x] for x in range(8)] for y in range(8)]
    x_dest, y_dest = move

    captured_piece = temp_board[y_dest][x_dest]
    en_passant_capture = False
    captured_pawn_pos = None

    # Check for en passant
    if piece.type == "pawn" and abs(piece.x - x_dest) == 1 and temp_board[y_dest][x_dest] is None:
        white_pawn_on_fifth = (piece.color == COLOR_WHITE and piece.y == 3)
        black_pawn_on_fourth = (piece.color == COLOR_BLACK and piece.y == 4)
        if (white_pawn_on_fifth and y_dest == 2) or (black_pawn_on_fourth and y_dest == 5):
            if hasattr(current_board, 'last_pawn_moved') and current_board.last_pawn_moved is not None:
                last_x, last_y = current_board.last_pawn_moved
                if x_dest == last_x and (
                    (white_pawn_on_fifth and last_y == 3) or
                    (black_pawn_on_fourth and last_y == 4)
                ):
                    en_passant_capture = True
                    captured_pawn_pos = (last_x, last_y)

    temp_board[piece.y][piece.x] = None
    temp_board[y_dest][x_dest] = piece

    if en_passant_capture and captured_pawn_pos:
        x_cap, y_cap = captured_pawn_pos
        temp_board[y_cap][x_cap] = None

    king_x, king_y = None, None
    for r in range(8):
        for c in range(8):
            p = temp_board[r][c]
            if p and p.type == "king" and p.color == piece.color:
                king_x, king_y = c, r
                break
        if king_x is not None:
            break

    # If the piece is the king, update king's location
    if piece.type == "king":
        king_x, king_y = x_dest, y_dest

    in_check = is_in_check(temp_board, piece.color, (king_x, king_y))
    return in_check

def is_in_check_simple(board, king_color):
    """
    A simpler check method used to see if the king of 'king_color' is in check
    without temporarily moving pieces. This is used, for instance, before castling.
    """
    king_x, king_y = None, None
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece.type == "king" and piece.color == king_color:
                king_x, king_y = col, row
                break
        if king_x is not None:
            break

    # Check pawns
    pawn_dirs = [(-1, -1), (1, -1)] if king_color == COLOR_WHITE else [(-1, 1), (1, 1)]
    for dx, dy in pawn_dirs:
        nx, ny = king_x + dx, king_y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            piece = board[ny][nx]
            if piece and piece.type == "pawn" and piece.color != king_color:
                return True

    # Check knights
    knight_jumps = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
    for dx, dy in knight_jumps:
        nx, ny = king_x + dx, king_y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            piece = board[ny][nx]
            if piece and piece.type == "knight" and piece.color != king_color:
                return True

    # Check kings around
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = king_x + dx, king_y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                piece = board[ny][nx]
                if piece and piece.type == "king" and piece.color != king_color:
                    return True

    # Check rooks/queens (straight lines)
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

    # Check bishops/queens (diagonals)
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
    """
    Check if the king of 'king_color' is in check. Optionally specify (king_x, king_y)
    to skip searching for the king on the board.
    """
    if king_position is None:
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.type == "king" and piece.color == king_color:
                    king_position = (col, row)
                    break
            if king_position is not None:
                break

    king_x, king_y = king_position
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and piece.color != king_color:
                if piece.type == "king":
                    dx = abs(col - king_x)
                    dy = abs(row - king_y)
                    if dx <= 1 and dy <= 1:
                        return True

                if piece.type == "king":
                    # Avoid recursion by not checking castling when testing checks
                    moves = piece.possible_moves(board, check_castling=False)
                else:
                    moves = piece.possible_moves(board)
                if (king_x, king_y) in moves:
                    return True
    return False

def is_checkmate(board, color):
    """
    Check if the player of 'color' is in checkmate: the king is in check and no valid move can remove that check.
    """
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
    """
    Check if there's a stalemate for 'color': the king is not in check, but that player has no legal move.
    """
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
    """
    Check for one form of draw: insufficient material to checkmate.
    e.g. only kings left, or king + bishop vs king, king + knight vs king, etc.
    """
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
    """
    Create a string signature to detect repeated positions (for threefold repetition rule).
    Combines piece arrangement and current player's turn.
    """
    rows = []
    for y in range(8):
        row = []
        for x in range(8):
            p = board[y][x]
            row.append(f"{p.color[0]}{p.type[0]}" if p else ".")
        rows.append("".join(row))
    return "|".join(rows) + f"_{turn}"

def ease_movement(t):
    """
    A function for smooth piece animation (easing).
    """
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def load_images(square_size):
    """
    Load chess piece images from a folder named 'img'. If a file doesn't exist,
    create a placeholder with a colored circle and an abbreviation for the piece.
    The filenames must be <color>_<piece>.png (e.g. 'w_queen.png' for white queen).
    Returns a dictionary mapping keys like 'w_queen' to a pygame.Surface.
    """
    import pygame
    import os
    from models.constants import WHITE, BLACK

    if not os.path.exists("img"):
        os.makedirs("img")

    images = {}
    for color in ["w", "b"]:
        for piece in ["king", "queen", "bishop", "knight", "rook", "pawn"]:
            key = f"{color}_{piece}"
            path = os.path.join("img", f"{key}.png")
            placeholder = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
            circle_color = WHITE if color == "w" else BLACK
            text_color = BLACK if color == "w" else WHITE
            pygame.draw.circle(placeholder, circle_color, (square_size // 2, square_size // 2), square_size // 3)
            font = pygame.font.SysFont(None, 20)
            label = font.render(piece[:3].upper(), True, text_color)
            placeholder.blit(label, label.get_rect(center=(square_size // 2, square_size // 2)))

            try:
                if os.path.exists(path):
                    images[key] = pygame.image.load(path)
                else:
                    images[key] = placeholder
            except Exception:
                images[key] = placeholder

    return images