"""
Menu views for the chess game.
"""
import pygame
from models.constants import WIDTH, HEIGHT, BLACK, WHITE, LIGHT_GREEN, GRAY


class MenuView:
    """
    Main menu screen with game mode options.
    """

    def __init__(self):
        """Initialize the main menu view."""
        self.options = ["2 Player Game", "Play vs AI", "Exit"]
        self.selection = 0
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)
        self.option_rects = []

    def draw(self, surface):
        """
        Draw the main menu on the given surface.

        Args:
            surface (pygame.Surface): Surface to draw on
        """
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
        """
        Process input events for menu navigation.

        Args:
            event (pygame.event.Event): Event to process

        Returns:
            int or None: Selected option index if confirmed, None otherwise
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


class SideMenuView:
    """
    Menu for choosing which side (white/black) to play as against the AI.
    """

    def __init__(self):
        """Initialize the side selection menu view."""
        self.options = ["White", "Black", "Random", "Back"]
        self.selection = 0
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)
        self.option_rects = []

    def draw(self, surface):
        """
        Draw the side selection menu on the given surface.

        Args:
            surface (pygame.Surface): Surface to draw on
        """
        surface.fill(GRAY)
        title = self.title_font.render("CHOOSE YOUR SIDE", True, BLACK)
        title_rect = title.get_rect(center=(WIDTH // 2, 100))
        surface.blit(title, title_rect)

        self.option_rects = []
        for i, option in enumerate(self.options):
            color = LIGHT_GREEN if i == self.selection else WHITE
            text = self.font.render(option, True, BLACK)
            pos_y = 250 + i * 70 + (40 if option == "Back" else 0)
            rect = text.get_rect(center=(WIDTH // 2, pos_y))
            rect_button = rect.inflate(40, 20)
            pygame.draw.rect(surface, color, rect_button)
            pygame.draw.rect(surface, BLACK, rect_button, 2)
            surface.blit(text, rect)
            self.option_rects.append(rect_button)

    def handle_events(self, event):
        """
        Process input events for menu navigation.

        Args:
            event (pygame.event.Event): Event to process

        Returns:
            int or None: Selected option index if confirmed, None otherwise
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


class DifficultyMenuView:
    """
    Menu for selecting AI difficulty level.
    """

    def __init__(self):
        """Initialize the difficulty selection menu view."""
        self.options = ["Easy", "Medium", "Hard", "Back"]
        self.selection = 0
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)
        self.option_rects = []

    def draw(self, surface):
        """
        Draw the difficulty selection menu on the given surface.

        Args:
            surface (pygame.Surface): Surface to draw on
        """
        surface.fill(GRAY)
        title = self.title_font.render("SELECT DIFFICULTY", True, BLACK)
        title_rect = title.get_rect(center=(WIDTH // 2, 100))
        surface.blit(title, title_rect)

        self.option_rects = []
        for i, option in enumerate(self.options):
            color = LIGHT_GREEN if i == self.selection else WHITE
            text = self.font.render(option, True, BLACK)
            pos_y = 250 + i * 70 + (40 if option == "Back" else 0)
            rect = text.get_rect(center=(WIDTH // 2, pos_y))
            rect_button = rect.inflate(40, 20)
            pygame.draw.rect(surface, color, rect_button)
            pygame.draw.rect(surface, BLACK, rect_button, 2)
            surface.blit(text, rect)
            self.option_rects.append(rect_button)

    def handle_events(self, event):
        """
        Process input events for menu navigation.

        Args:
            event (pygame.event.Event): Event to process

        Returns:
            int or None: Selected option index if confirmed, None otherwise
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