"""
main.py — Application bootstrap, window creation, and entry point.

Run with:  python main.py
"""

import tkinter as tk
import sys
import os

# Ensure the package directory is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import GameController

WINDOW_W = 700
WINDOW_H = 700
WINDOW_TITLE = "Maze Runner: Deception"


def main() -> None:
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.resizable(False, False)
    root.configure(bg="#000000")

    # Center window on screen
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x  = (sw - WINDOW_W) // 2
    y  = (sh - WINDOW_H) // 2
    root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

    canvas = tk.Canvas(
        root,
        width=WINDOW_W,
        height=WINDOW_H,
        bg="#000000",
        highlightthickness=0,
    )
    canvas.pack(fill="both", expand=True)

    # Focus so keyboard input works immediately
    root.focus_force()
    canvas.focus_set()

    # Boot the game
    GameController(root, canvas)

    root.mainloop()


if __name__ == "__main__":
    main()
