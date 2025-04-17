"""
Pawn promotion menu for the chess game.
"""
import pygame
from models.constants import WIDTH, HEIGHT, WHITE, GRAY, LIGHT_GREEN


class PromotionMenuView:
    """
    Menu to select which piece to promote a pawn into.
    """

    def __init__(self, color):
        """
        Initialize the promotion menu.

        Args:
            color (str): Color of the pawn to promote ("w" or "b")
        """
        self.color = color
        self.options = ["queen", "rook", "bishop", "knight"]
        self.selection = 0
        self.option_rects = []

    def draw(self, surface, images):
        """
        Draw the promotion menu on the given surface.

        Args:
            surface (pygame.Surface): Surface to draw on
            images (dict): Dictionary of piece images
        """
        # Darken the background
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192))  # Semi-transparent black
        surface.blit(overlay, (0, 0))

        # Draw title
        title_font = pygame.font.SysFont(None, 48)
        title = title_font.render("Select a piece for promotion", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        surface.blit(title, title_rect)

        # Draw piece options
        self.option_rects = []
        spacing = 120
        start_x = WIDTH // 2 - (spacing * (len(self.options) - 1)) // 2

        for i, option in enumerate(self.options):
            pos_x = start_x + i * spacing
            pos_y = HEIGHT // 2

            # Draw selection box (highlighted if selected)
            if i == self.selection:
                button_rect = pygame.Rect(pos_x - 45, pos_y - 45, 90, 90)
                pygame.draw.rect(surface, LIGHT_GREEN, button_rect)
                pygame.draw.rect(surface, WHITE, button_rect, 2)
            else:
                button_rect = pygame.Rect(pos_x - 40, pos_y - 40, 80, 80)
                pygame.draw.rect(surface, (170, 170, 170), button_rect)
                pygame.draw.rect(surface, GRAY, button_rect, 2)

            self.option_rects.append(button_rect)

            # Draw piece image
            key = f"{self.color}_{option}"
            if key in images:
                img = images[key]
                img_rect = img.get_rect(center=(pos_x, pos_y))
                surface.blit(img, img_rect)

            # Draw piece name
            name_font = pygame.font.SysFont(None, 24)
            name = name_font.render(option.capitalize(), True, WHITE)
            name_rect = name.get_rect(center=(pos_x, pos_y + 60))
            surface.blit(name, name_rect)

        # Draw instructions
        instr_font = pygame.font.SysFont(None, 28)
        instr = instr_font.render("Use left/right arrows, Enter or click to select", True, WHITE)
        instr_rect = instr.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        surface.blit(instr, instr_rect)

    def handle_events(self, event):
        """
        Process input events for promotion selection.

        Args:
            event (pygame.event.Event): Event to process

        Returns:
            str or None: Selected piece type if confirmed, None otherwise
        """
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