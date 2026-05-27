"""
main.py — Window creation and entry point.

Run with:  python main.py
"""

import sys
import os
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import GameController

WINDOW_W = 700
WINDOW_H = 700
TITLE    = "Maze Runner: Deception"


def main() -> None:
    root = tk.Tk()
    root.title(TITLE)
    root.resizable(False, False)
    root.configure(bg="#000000")

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{WINDOW_W}x{WINDOW_H}+{(sw-WINDOW_W)//2}+{(sh-WINDOW_H)//2}")

    canvas = tk.Canvas(
        root,
        width=WINDOW_W,
        height=WINDOW_H,
        bg="#000000",
        highlightthickness=0,
    )
    canvas.pack(fill="both", expand=True)

    root.focus_force()
    canvas.focus_set()

    GameController(root, canvas)
    root.mainloop()


if __name__ == "__main__":
    main()
