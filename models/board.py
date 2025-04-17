"""
Board model representing the chess board state, move validation, and game mechanics.
"""
from models.piece import Pawn, Rook, Knight, Bishop, Queen, King
from models.constants import PIECE_VALUE, COLOR_WHITE, COLOR_BLACK, ANIMATION_DURATION, ROTATION_DURATION
from utils.helpers import is_in_check, is_checkmate, is_stalemate, get_board_signature, insufficient_material, \
    ease_movement


class Board:
    """
    The Board class manages piece placement, turn logic, move validation, check/checkmate,
    threefold repetition, castling, en passant, pawn promotion, animations, etc.
    """

    def __init__(self, ai_mode=False):
        self.board = [[None for _ in range(8)] for _ in range(8)]

        # White moves first: "w"
        self.turn = COLOR_WHITE
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

        # Animation controls
        self.animating = False
        self.animating_piece = None
        self.start_pos = None
        self.end_pos = None
        self.animation_time = 0
        self.animation_duration = ANIMATION_DURATION

        # For castling or en passant animations
        self.extra_animating_piece = None
        self.extra_start_pos = None
        self.extra_end_pos = None

        self.rotating = False
        self.rotation_time = 0
        self.rotation_duration = ROTATION_DURATION
        self.rotation_initial = False
        self.rotation_final = True

        # Material tracking: White "score" is +, black "score" is -
        self.white_material = 0
        self.white_captured_pieces = []
        self.black_captured_pieces = []

        # Storage for move data that will be applied after animation completes
        self._move_data = None

    def initialize_board(self):
        """
        Set up initial positions for both sides: rooks, knights, bishops, queen, king, pawns.
        White pieces are denoted 'w', black pieces 'b'.
        """
        # White pieces (bottom row in standard orientation)
        self.board[7][0] = Rook(COLOR_WHITE, 0, 7)
        self.board[7][1] = Knight(COLOR_WHITE, 1, 7)
        self.board[7][2] = Bishop(COLOR_WHITE, 2, 7)
        self.board[7][3] = Queen(COLOR_WHITE, 3, 7)
        self.board[7][4] = King(COLOR_WHITE, 4, 7)
        self.board[7][5] = Bishop(COLOR_WHITE, 5, 7)
        self.board[7][6] = Knight(COLOR_WHITE, 6, 7)
        self.board[7][7] = Rook(COLOR_WHITE, 7, 7)
        for i in range(8):
            self.board[6][i] = Pawn(COLOR_WHITE, i, 6)

        # Black pieces (top row in standard orientation)
        self.board[0][0] = Rook(COLOR_BLACK, 0, 0)
        self.board[0][1] = Knight(COLOR_BLACK, 1, 0)
        self.board[0][2] = Bishop(COLOR_BLACK, 2, 0)
        self.board[0][3] = Queen(COLOR_BLACK, 3, 0)
        self.board[0][4] = King(COLOR_BLACK, 4, 0)
        self.board[0][5] = Bishop(COLOR_BLACK, 5, 0)
        self.board[0][6] = Knight(COLOR_BLACK, 6, 0)
        self.board[0][7] = Rook(COLOR_BLACK, 7, 0)
        for i in range(8):
            self.board[1][i] = Pawn(COLOR_BLACK, i, 1)

    def select_piece(self, x, y):
        """
        Select a piece at (x, y) if it matches the current player's turn.
        Store it and calculate its valid moves.
        """
        if self.checkmate or self.promotion_pending:
            return False

        piece = self.board[y][x]
        if piece is not None and piece.color == self.turn:
            self.selected_piece = piece
            self.valid_moves = piece.valid_moves(self.board)

            # Check en passant possibility
            if piece.type == "pawn" and self.last_pawn_moved is not None:
                last_x, last_y = self.last_pawn_moved

                white_pawn_on_fifth = (piece.color == COLOR_WHITE and piece.y == 3)
                black_pawn_on_fourth = (piece.color == COLOR_BLACK and piece.y == 4)
                if white_pawn_on_fifth or black_pawn_on_fourth:
                    same_level = ((white_pawn_on_fifth and last_y == 3) or (black_pawn_on_fourth and last_y == 4))
                    if same_level and abs(piece.x - last_x) == 1:
                        pawn_piece = self.board[last_y][last_x]
                        if pawn_piece and pawn_piece.type == "pawn" and pawn_piece.color != piece.color:
                            direction = -1 if piece.color == COLOR_WHITE else 1
                            en_passant_move = (last_x, piece.y + direction)
                            from utils.helpers import leaves_king_in_check
                            if not leaves_king_in_check(self.board, piece, en_passant_move):
                                if en_passant_move not in self.valid_moves:
                                    self.valid_moves.append(en_passant_move)
            return True
        return False

    def update_animation(self):
        """
        Advance animation by incrementing time. If finished, finalize the move.
        """
        if not self.animating:
            return
        self.animation_time += 1
        if self.animation_time >= self.animation_duration:
            self._complete_move()

    def _complete_move(self):
        """
        After the animation completes, carry out the move on the board, handle captures,
        switch turns, check for checkmate/stalemate/draw, etc.
        """
        data = self._move_data
        piece = data['piece']
        start_x, start_y = data['from_x'], data['from_y']
        x, y = data['to_x'], data['to_y']
        castling = data['is_castling']
        moved_rook = data['moved_rook']
        rook_from = data['rook_from']
        rook_to = data['rook_to']
        en_passant = data['is_en_passant']
        pawn_capture_pos = data['pawn_capture_pos']
        last_pawn_temp = data['last_pawn_temp']
        current_color = data['current_color']

        captured_piece = self.board[y][x]
        if captured_piece:
            # Update captured piece data
            if piece.color == COLOR_WHITE:
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
            if piece.color == COLOR_WHITE:
                self.white_captured_pieces.append("pawn")
                self.white_material += PIECE_VALUE["pawn"]
            else:
                self.black_captured_pieces.append("pawn")
                self.white_material -= PIECE_VALUE["pawn"]
            self.board[last_y][last_x] = None

        # Pawn promotion check
        if piece.type == "pawn" and (y == 0 or y == 7):
            self.promotion_pending = True
            self.pawn_to_promote = piece
            self.selected_piece = None
            self.valid_moves = []
            self.last_pawn_moved = last_pawn_temp
            self.animating = False
            return

        # Switch turns
        self.turn = COLOR_BLACK if self.turn == COLOR_WHITE else COLOR_WHITE

        # If not AI mode, rotate board after each move
        if not self.ai_mode:
            self.rotating = True
            self.rotation_time = 0
            self.rotation_initial = self.board_rotated
            self.rotation_final = not self.board_rotated

        # Clear last_pawn_moved if it was the same color
        if self.last_pawn_moved is not None:
            last_x, last_y = self.last_pawn_moved
            last_pawn_piece = self.board[last_y][last_x]
            if last_pawn_piece and last_pawn_piece.color == current_color:
                self.last_pawn_moved = None

        if last_pawn_temp is not None:
            self.last_pawn_moved = last_pawn_temp

        # Threefold repetition signature
        signature = get_board_signature(self.board, self.turn)
        self.repeated_positions[signature] = self.repeated_positions.get(signature, 0) + 1
        if self.history:
            self.history[-1]['signature'] = signature

        # Check for game-ending conditions
        if is_checkmate(self.board, self.turn):
            self.checkmate = True
            self.winner = COLOR_WHITE if self.turn == COLOR_BLACK else COLOR_BLACK
            # Game state will be updated by the controller
        elif self.repeated_positions[signature] >= 3:
            self.checkmate = True
            self.winner = "draw"
            # Game state will be updated by the controller
        elif is_stalemate(self.board, self.turn):
            self.checkmate = True
            self.winner = "draw"
            # Game state will be updated by the controller
        elif insufficient_material(self.board):
            self.checkmate = True
            self.winner = "draw"
            # Game state will be updated by the controller

        self.selected_piece = None
        self.valid_moves = []
        self.animating = False
        self.animating_piece = None
        self.extra_animating_piece = None

    def move_piece(self, x, y):
        """
        Attempt to move the currently selected piece to (x, y).
        If valid, start the animation. En passant, castling, and capture are handled here.
        """
        if self.checkmate or self.promotion_pending or self.animating:
            return False

        if self.selected_piece and (x, y) in self.valid_moves:
            piece = self.selected_piece
            start_x, start_y = piece.x, piece.y
            current_color = self.turn
            direction = -1 if piece.color == COLOR_WHITE else 1
            en_passant = False
            pawn_captured = None
            last_pawn_temp = None
            castling = False
            moved_rook = None
            rook_from = None
            rook_to = None

            # Castling check
            if piece.type == "king" and abs(x - start_x) == 2:
                castling = True
                if x > start_x:  # Kingside
                    rook_x = 7
                    rook_new_x = x - 1
                else:  # Queenside
                    rook_x = 0
                    rook_new_x = x + 1
                rook = self.board[start_y][rook_x]
                rook_from = (rook_x, start_y)
                rook_to = (rook_new_x, start_y)
                moved_rook = rook

            # En passant check
            if piece.type == "pawn" and abs(x - start_x) == 1 and self.board[y][x] is None:
                if self.last_pawn_moved is not None:
                    last_x, last_y = self.last_pawn_moved
                    white_pawn_on_fifth = (piece.color == COLOR_WHITE and start_y == 3)
                    black_pawn_on_fourth = (piece.color == COLOR_BLACK and start_y == 4)
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

            # Track last double-step pawn move
            if piece.type == "pawn" and abs(start_y - y) == 2:
                last_pawn_temp = (x, y)

            self._move_data = {
                'piece': piece,
                'from_x': start_x,
                'from_y': start_y,
                'to_x': x,
                'to_y': y,
                'is_castling': castling,
                'moved_rook': moved_rook,
                'rook_from': rook_from,
                'rook_to': rook_to,
                'is_en_passant': en_passant,
                'pawn_capture_pos': self.last_pawn_moved if en_passant else None,
                'last_pawn_temp': last_pawn_temp,
                'current_color': current_color
            }

            return True
        return False

    def update_rotation(self):
        """
        Handle the board-rotation animation after each move (if ai_mode is disabled).
        """
        if not self.rotating:
            return
        self.rotation_time += 1

        if self.rotation_time == self.rotation_duration // 2:
            self.board_rotated = self.rotation_final

        if self.rotation_time >= self.rotation_duration:
            self.rotating = False

    def promote_pawn(self, piece_type):
        """
        Promote a pawn that reached the last rank to the chosen piece type
        (queen, rook, bishop, or knight).
        Adjust material scoring accordingly.
        """
        if not self.promotion_pending or not self.pawn_to_promote:
            return False

        x, y = self.pawn_to_promote.x, self.pawn_to_promote.y
        color = self.pawn_to_promote.color
        value_diff = PIECE_VALUE[piece_type] - PIECE_VALUE["pawn"]
        if color == COLOR_WHITE:
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

        self.turn = COLOR_BLACK if self.turn == COLOR_WHITE else COLOR_WHITE

        if not self.ai_mode:
            self.rotating = True
            self.rotation_time = 0
            self.rotation_initial = self.board_rotated
            self.rotation_final = not self.board_rotated

        if is_checkmate(self.board, self.turn):
            self.checkmate = True
            self.winner = COLOR_BLACK if self.turn == COLOR_WHITE else COLOR_WHITE

        return True

    def undo_move(self):
        """
        Undo the last move. Restore board position, captured pieces, and any promotion or castling.
        """
        if self.history:
            last_move = self.history.pop()
            piece = last_move['piece']
            start_x, start_y = last_move['from']
            end_x, end_y = last_move['to']
            capture = last_move['capture']
            prev_moved = last_move['moved']

            if capture:
                # Update material if we revert a capture
                if piece.color == COLOR_WHITE:
                    if capture.type in self.white_captured_pieces:
                        self.white_captured_pieces.remove(capture.type)
                    self.white_material -= PIECE_VALUE[capture.type]
                else:
                    if capture.type in self.black_captured_pieces:
                        self.black_captured_pieces.remove(capture.type)
                    self.white_material += PIECE_VALUE[capture.type]

            if 'promotion' in last_move:
                # Revert pawn promotion
                new_type = last_move['promotion']['new_type']
                value_diff = PIECE_VALUE[new_type] - PIECE_VALUE["pawn"]
                if piece.color == COLOR_WHITE:
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
                if piece.color == COLOR_WHITE:
                    if "pawn" in self.white_captured_pieces:
                        self.white_captured_pieces.remove("pawn")
                    self.white_material -= PIECE_VALUE["pawn"]
                else:
                    if "pawn" in self.black_captured_pieces:
                        self.black_captured_pieces.remove("pawn")
                    self.white_material += PIECE_VALUE["pawn"]
                self.board[y_cap][x_cap] = captured_pawn

            self.turn = COLOR_BLACK if self.turn == COLOR_WHITE else COLOR_WHITE
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

            return True
        return False

    def is_in_check(self, color):
        """
        Utility method to quickly see if 'color' is in check, delegating to is_in_check function.
        """
        return is_in_check(self.board, color)