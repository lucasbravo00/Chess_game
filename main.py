"""
Main entry point for the chess game.
"""
from controllers.game_controller import GameController

def main():
    """
    Initialize and run the chess game.
    """
    game_controller = GameController()
    game_controller.run()

if __name__ == "__main__":
    main()