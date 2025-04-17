"""
Chess board visualization component.
"""
import pygame
from models.constants import (
    WIDTH, HEIGHT, MARGIN_X, MARGIN_Y, SQUARE_SIZE, BOARD_SIZE,
    WHITE, BLACK, GRAY, DARK_GREEN, DARK_GRAY, SELECTION, CHECK_COLOR
)
from utils.helpers import ease_movement


class BoardView:
    """
    Handles the rendering of the chess board, pieces, and game UI elements.
    """

    def __init__(self, board, images):
        """
        Initialize the board view.

        Args:
            board (Board): The chess board model
            images (dict): Dictionary of piece images
        """
        self.board = board
        self.images = images

    def draw(self, surface, message=""):
        """
        Draw the chess board and all related elements.

        Args:
            surface (pygame.Surface): The surface to draw on
            message (str): Optional message to display
        """
        surface.fill(GRAY)

        # Draw board border
        border_thickness = 4
        border_rect = pygame.Rect(
            MARGIN_X - border_thickness,
            MARGIN_Y - border_thickness,
            BOARD_SIZE + border_thickness * 2,
            BOARD_SIZE + border_thickness * 2
        )
        pygame.draw.rect(surface, DARK_GRAY, border_rect, border_thickness)

        # Draw board squares
        self._draw_board_squares(surface)

        # Calculate rotation progress
        if self.board.rotating:
            t = self.board.rotation_time / self.board.rotation_duration
            # Shorter black phase - adjust these values to control duration
            black_phase = (t > 0.35 and t < 0.65)
        else:
            black_phase = False

        # Only draw pieces if not in the black phase of rotation
        if not black_phase:
            self._draw_pieces(surface)
            self._draw_animations(surface)
            self._draw_selected_highlights(surface)

        # Draw coordinate labels
        self._draw_coordinates(surface)

        # Draw game info and UI elements
        self._draw_game_info(surface, message)
        self._draw_material_difference(surface)
        self._draw_ui_buttons(surface)

        # Draw rotation overlay with adjusted opacity
        if self.board.rotating:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            t = self.board.rotation_time / self.board.rotation_duration

            # Adjusted opacity function for milder, shorter black period
            if t < 0.35:
                # Fade in phase: 0 to max_opacity
                progress = t / 0.35
                opacity = int(180 * progress)  # Max opacity reduced to 180 (from 255)
            elif t > 0.65:
                # Fade out phase: max_opacity to 0
                progress = (t - 0.65) / 0.35
                opacity = int(180 * (1 - progress))
            else:
                # Middle phase: stay at max_opacity
                opacity = 180  # Reduced from 255 for less darkness

            overlay.fill((0, 0, 0))
            overlay.set_alpha(opacity)
            surface.blit(overlay, (0, 0))

        # Draw checkmate/draw overlay if game is over
        if self.board.checkmate:
            self._draw_game_over_overlay(surface)

    def _draw_board_squares(self, surface):
        """Draw the chess board squares with proper colors."""
        for row in range(8):
            for col in range(8):
                # Handle rotation animation or final rotation state
                if self.board.rotating:
                    t = self.board.rotation_time / self.board.rotation_duration
                    t = ease_movement(t)
                    if t < 0.5:
                        if self.board.rotation_initial:
                            adjusted_row, adjusted_col = 7 - row, 7 - col
                        else:
                            adjusted_row, adjusted_col = row, col
                    else:
                        if self.board.rotation_final:
                            adjusted_row, adjusted_col = 7 - row, 7 - col
                        else:
                            adjusted_row, adjusted_col = row, col
                else:
                    if self.board.board_rotated:
                        adjusted_row, adjusted_col = 7 - row, 7 - col
                    else:
                        adjusted_row, adjusted_col = row, col

                x = MARGIN_X + col * SQUARE_SIZE
                y = MARGIN_Y + row * SQUARE_SIZE
                square_color = WHITE if (row + col) % 2 == 0 else DARK_GREEN
                pygame.draw.rect(surface, square_color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    def _draw_pieces(self, surface):
        """Draw all chess pieces on the board."""
        for row in range(8):
            for col in range(8):
                # Calculate adjusted position based on rotation
                if self.board.board_rotated:
                    adjusted_row, adjusted_col = 7 - row, 7 - col
                else:
                    adjusted_row, adjusted_col = row, col

                x = MARGIN_X + col * SQUARE_SIZE
                y = MARGIN_Y + row * SQUARE_SIZE
                piece = self.board.board[adjusted_row][adjusted_col]

                # Don't draw pieces that are being animated
                if piece and (not self.board.animating or
                              (piece != self.board.animating_piece and
                               (
                                       self.board.extra_animating_piece is None or piece != self.board.extra_animating_piece))):
                    key = f"{piece.color}_{piece.type}"
                    if key in self.images:
                        image = self.images[key]
                        img_rect = image.get_rect()
                        img_x = x + (SQUARE_SIZE - img_rect.width) // 2
                        img_y = y + (SQUARE_SIZE - img_rect.height) // 2
                        surface.blit(image, (img_x, img_y))

                        # Highlight king in check
                        if piece.type == "king" and self.board.is_in_check(piece.color) and not self.board.checkmate:
                            overlay_check = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                            overlay_check.fill(CHECK_COLOR)
                            surface.blit(overlay_check, (x, y))

    def _draw_animations(self, surface):
        """Draw piece movement animations."""
        if not self.board.animating:
            return

        t = self.board.animation_time / self.board.animation_duration
        t = ease_movement(t)
        from_x, from_y = self.board.start_pos
        to_x, to_y = self.board.end_pos

        # Calculate screen positions based on board rotation
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

        # Interpolate current position
        current_x = screen_from_x + (screen_to_x - screen_from_x) * t
        current_y = screen_from_y + (screen_to_y - screen_from_y) * t

        # Draw the moving piece
        key = f"{self.board.animating_piece.color}_{self.board.animating_piece.type}"
        if key in self.images:
            image = self.images[key]
            img_rect = image.get_rect()
            img_x = current_x + (SQUARE_SIZE - img_rect.width) // 2
            img_y = current_y + (SQUARE_SIZE - img_rect.height) // 2
            surface.blit(image, (img_x, img_y))

        # If castling, animate the rook too
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

        # Add rotation overlay effect
        if self.board.rotating:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            t = self.board.rotation_time / self.board.rotation_duration
            t = ease_movement(t)
            opacity = int(255 * (1 - abs(2 * t - 1)))
            overlay.fill((0, 0, 0, opacity))
            surface.blit(overlay, (0, 0))

    def _draw_selected_highlights(self, surface):
        """Highlight selected piece and its valid moves."""
        if (self.board.selected_piece and not self.board.checkmate and
                not self.board.promotion_pending and not self.board.animating and not self.board.rotating):
            # Highlight selected piece
            if self.board.board_rotated:
                x_sel = MARGIN_X + (7 - self.board.selected_piece.x) * SQUARE_SIZE
                y_sel = MARGIN_Y + (7 - self.board.selected_piece.y) * SQUARE_SIZE
            else:
                x_sel = MARGIN_X + self.board.selected_piece.x * SQUARE_SIZE
                y_sel = MARGIN_Y + self.board.selected_piece.y * SQUARE_SIZE

            overlay_sel = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            overlay_sel.fill(SELECTION)
            surface.blit(overlay_sel, (x_sel, y_sel))

            # Highlight valid moves
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

    def _draw_coordinates(self, surface):
        """Draw rank and file coordinate labels."""
        coord_font = pygame.font.SysFont(None, 24)
        current_orientation = self.board.board_rotated

        # Adjust orientation during rotation animation
        if self.board.rotating:
            t = self.board.rotation_time / self.board.rotation_duration
            t = ease_movement(t)
            if t >= 0.5:
                current_orientation = self.board.rotation_final

        # Draw file labels (a-h)
        for i in range(8):
            letter = chr(97 + (7 - i)) if current_orientation else chr(97 + i)
            letter_text = coord_font.render(letter, True, BLACK)
            x_letter = MARGIN_X + i * SQUARE_SIZE + SQUARE_SIZE // 2 - letter_text.get_width() // 2
            y_letter = MARGIN_Y + BOARD_SIZE + 10
            surface.blit(letter_text, (x_letter, y_letter))

        # Draw rank labels (1-8)
        for i in range(8):
            number = str(i + 1) if current_orientation else str(8 - i)
            number_text = coord_font.render(number, True, BLACK)
            x_number = MARGIN_X - number_text.get_width() - 10
            y_number = MARGIN_Y + i * SQUARE_SIZE + SQUARE_SIZE // 2 - number_text.get_height() // 2
            surface.blit(number_text, (x_number, y_number))

    def _draw_game_info(self, surface, message):
        """Draw turn indicator and message."""
        info_font = pygame.font.SysFont(None, 36)
        turn_text = info_font.render(f"Turn: {'White' if self.board.turn == 'w' else 'Black'}", True, BLACK)
        surface.blit(turn_text, (20, 20))

        # Display message if any
        if message:
            msg_font = pygame.font.SysFont(None, 36)
            msg_text = msg_font.render(message, True, BLACK)
            msg_rect = msg_text.get_rect(topright=(WIDTH - 20, 20))
            surface.blit(msg_text, msg_rect)

    def _draw_material_difference(self, surface):
        """Draw captured pieces and material advantage."""
        icon_size = 30
        gap = 0
        initial_vertical_position = MARGIN_Y + BOARD_SIZE // 2 + 60
        horizontal_margin = 20
        font = pygame.font.SysFont(None, 24)
        title_font = pygame.font.SysFont(None, 24)
        small_font = pygame.font.SysFont(None, 20)

        # Calculate material advantage
        white_advantage = self.board.white_material if self.board.white_material > 0 else 0
        black_advantage = abs(self.board.white_material) if self.board.white_material < 0 else 0

        # Left side: White advantage (captured black pieces)
        x_left = MARGIN_X - icon_size - horizontal_margin
        y_left = initial_vertical_position
        title_text = title_font.render("White Advantage", True, BLACK)
        offset_left = 130
        title_pos_left = (x_left - offset_left, y_left)
        surface.blit(title_text, title_pos_left)
        pygame.draw.line(
            surface, BLACK,
            (title_pos_left[0], title_pos_left[1] + title_text.get_height()),
            (title_pos_left[0] + title_text.get_width(), title_pos_left[1] + title_text.get_height()),
            2
        )
        y_left += title_text.get_height() + gap + 15
        left_shift = 130
        left_table_x = MARGIN_X - horizontal_margin - left_shift - 40

        # Count and group white's captured pieces
        white_captures = self.board.white_captured_pieces
        white_groups = {}
        for piece in white_captures:
            white_groups.setdefault(piece, 0)
            white_groups[piece] += 1

        # Draw white's captured pieces
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
                            key = f"b_{p_type}"
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

        # Show white's advantage score
        if white_advantage != 0:
            adv_text = small_font.render(f"+{white_advantage}", True, BLACK)
            surface.blit(adv_text, (left_table_x, current_y_left + gap + 5))

        # Right side: Black advantage (captured white pieces)
        extra_offset_right = 50
        x_right = MARGIN_X + BOARD_SIZE + horizontal_margin + extra_offset_right
        y_right = initial_vertical_position
        offset_n = 40
        title_text = title_font.render("Black Advantage", True, BLACK)
        title_pos_right = (x_right - offset_n, y_right)
        surface.blit(title_text, title_pos_right)
        pygame.draw.line(
            surface, BLACK,
            (title_pos_right[0], title_pos_right[1] + title_text.get_height()),
            (title_pos_right[0] + title_text.get_width(), title_pos_right[1] + title_text.get_height()),
            2
        )
        y_right += title_text.get_height() + gap + 15
        right_table_x = x_right + 100

        # Count and group black's captured pieces
        black_captures = self.board.black_captured_pieces
        black_groups = {}
        for piece in black_captures:
            black_groups.setdefault(piece, 0)
            black_groups[piece] += 1

        # Draw black's captured pieces
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
                            key = f"w_{p_type}"
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

        # Show black's advantage score
        if black_advantage != 0:
            adv_text = small_font.render(f"+{black_advantage}", True, BLACK)
            text_width = adv_text.get_width()
            surface.blit(adv_text, (right_table_x - text_width, current_y_right + gap + 5))

    def _draw_ui_buttons(self, surface):
        """Draw UI buttons like Undo and Menu."""
        button_font = pygame.font.SysFont(None, 24)

        # Undo button
        undo_text = button_font.render("Undo [Z]", True, BLACK)
        undo_rect = undo_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
        pygame.draw.rect(surface, WHITE, undo_rect.inflate(20, 10))
        pygame.draw.rect(surface, BLACK, undo_rect.inflate(20, 10), 2)
        surface.blit(undo_text, undo_rect)

        # Menu button
        menu_text = button_font.render("Menu [ESC]", True, BLACK)
        menu_rect = menu_text.get_rect(bottomleft=(20, HEIGHT - 20))
        pygame.draw.rect(surface, WHITE, menu_rect.inflate(20, 10))
        pygame.draw.rect(surface, BLACK, menu_rect.inflate(20, 10), 2)
        surface.blit(menu_text, menu_rect)

    def _draw_game_over_overlay(self, surface):
        """Draw game over screen with winner or draw information."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
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