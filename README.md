# Chess Game

This repository contains the complete source code for a Chess game developed in Python using Pygame and python-chess. The game supports both two-player mode and playing against an AI powered by Stockfish.

## Features
- **Two Player Mode:** Play chess with a friend on the same computer
- **Play vs AI:** Challenge an AI opponent that uses Stockfish for move evaluation
- **Promotions, Castling, and En Passant:** Full chess rules are implemented
- **Animated Moves:** Visual animations for moving pieces
- **Captured Material Display:** View the material advantage for each side

## Installation

### Prerequisites
- Python 3.x

### Steps
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/chess-game.git
   cd chess-game
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   The required packages are listed in `requirements.txt`. Install them with:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Stockfish:**
   Stockfish is used as the chess engine. You can either:
   - Use the version included in this repository
   - Download the latest Stockfish binary from [Stockfish Downloads](https://stockfishchess.org/download/)
   
   **Important:** The Stockfish engine folder must be placed in the same directory as the game code. The application expects to find the engine in this location for proper functionality.
   
   **Platform note:** The Stockfish binary included in stockfish/ is the Windows‑only build (stockfish-windows-x86-64-avx2.exe). If you’re running macOS or Linux, download the matching Stockfish release for your OS from https://stockfishchess.org/download/ and replace the executable in the stockfish/ folder. Then open chess_stockfish.py and update the self.stockfish_path line to point to the new filename (for example "stockfish/stockfish-linux-x86-64").

## Running the Game
Once all dependencies are installed and Stockfish is configured, run the game with:

```bash
python chess_game.py
```

## Licenses and Attribution

### Stockfish
- **License:** GNU General Public License v3.0 (GPL‑3.0)  
- **Notice:** This repository includes the Stockfish binary. Per GPL‑3.0 requirements, the full source code and license text are available at https://github.com/official-stockfish/Stockfish and in LICENSE‑STOCKFISH.txt.

### Lichess Pieces
- **License:** CC0 (public domain) — no restrictions.  
- **Attribution (optional):** Chess piece graphics courtesy of Lichess (https://lichess.org), released under CC0/public domain.

## Project Structure
- **chess_game.py:** The main entry point for the game.
- **chess_stockfish.py:** Contains the AI integration using Stockfish.
- **stockfish/:** Folder containing the Stockfish binary.
- **img/**: Folder containing chess piece images.
- **requirements.txt:** Lists required Python packages.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Contact
For any questions or issues, please open an issue on GitHub.

## License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

