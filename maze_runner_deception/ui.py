"""
ui.py — HUD rendering, dialogue overlays, menus, and transition screens.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable


CANVAS_W = 700
CANVAS_H = 700

# Colors
BG       = "#000000"
FG_DIM   = "#444444"
FG_MID   = "#888888"
FG_MAIN  = "#cccccc"
FG_BRIGHT= "#ffffff"
ACCENT   = "#ff3333"
GREEN    = "#00ff88"
YELLOW   = "#ffcc00"


class UIManager:
    """All canvas-based UI overlays and screens."""

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self._overlay_ids: list[int] = []

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def clear_overlay(self) -> None:
        for cid in self._overlay_ids:
            try:
                self.canvas.delete(cid)
            except Exception:
                pass
        self._overlay_ids.clear()

    def _text(self, x: float, y: float, text: str, **kwargs) -> int:
        cid = self.canvas.create_text(x, y, text=text, **kwargs)
        self._overlay_ids.append(cid)
        return cid

    def _rect(self, x1, y1, x2, y2, **kwargs) -> int:
        cid = self.canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
        self._overlay_ids.append(cid)
        return cid

    # ------------------------------------------------------------------
    # Main Menu
    # ------------------------------------------------------------------

    def draw_main_menu(self, blink_state: bool) -> None:
        self.clear_overlay()
        c = self.canvas

        # full background
        self._rect(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")

        # title block
        self._text(CANVAS_W // 2, 200, "MAZE RUNNER",
                   font=("Courier", 44, "bold"), fill=FG_BRIGHT, anchor="center")
        self._text(CANVAS_W // 2, 250, "DECEPTION",
                   font=("Courier", 32, "bold"), fill=ACCENT, anchor="center")

        self._text(CANVAS_W // 2, 320,
                   "Subject 47, escape the facility. Or try.",
                   font=("Courier", 12), fill=FG_MID, anchor="center")

        # blinking prompt
        if blink_state:
            self._text(CANVAS_W // 2, 420, "[ PRESS  ENTER  TO  BEGIN ]",
                       font=("Courier", 14, "bold"), fill=YELLOW, anchor="center")

        # controls hint
        self._text(CANVAS_W // 2, 520,
                   "WASD / Arrow Keys  ·  R to restart  ·  ESC to menu",
                   font=("Courier", 10), fill=FG_DIM, anchor="center")

        self._text(CANVAS_W // 2, 680,
                   "The facility assumes no liability for psychological distress.",
                   font=("Courier", 9), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Level intro screen
    # ------------------------------------------------------------------

    def draw_level_intro(self, lines: list[str], countdown: float) -> None:
        self.clear_overlay()
        self._rect(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")

        # static noise border
        self._rect(20, 20, CANVAS_W - 20, CANVAS_H - 20,
                   outline=FG_DIM, fill="", width=1)

        cy = 260
        for i, line in enumerate(lines):
            if i == 0:
                color, size = ACCENT, 18
            elif line == "":
                cy += 14
                continue
            else:
                color, size = FG_MAIN, 13
            self._text(CANVAS_W // 2, cy, line,
                       font=("Courier", size, "bold" if i == 0 else "normal"),
                       fill=color, anchor="center")
            cy += size + 10

        bar = int((3.0 - countdown) / 3.0 * (CANVAS_W - 120))
        self._rect(60, CANVAS_H - 80, 60 + bar, CANVAS_H - 68,
                   fill=ACCENT, outline="")
        self._rect(60, CANVAS_H - 80, CANVAS_W - 60, CANVAS_H - 68,
                   fill="", outline=FG_DIM)
        self._text(CANVAS_W // 2, CANVAS_H - 50,
                   f"Commencing in {countdown:.1f}s  (press ENTER to skip)",
                   font=("Courier", 10), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # HUD (in-game overlay)
    # ------------------------------------------------------------------

    def draw_hud(self, level: int, elapsed: float, score: int,
                 deaths: int, effect_msg: str = "") -> None:
        self.clear_overlay()

        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        time_str = f"{mins:02d}:{secs:02d}"

        pad = 10
        self._text(pad, pad, f"LEVEL {level}",
                   font=("Courier", 11, "bold"), fill=ACCENT, anchor="nw")
        self._text(CANVAS_W // 2, pad, f"TIME  {time_str}",
                   font=("Courier", 11), fill=FG_MID, anchor="n")
        self._text(CANVAS_W - pad, pad, f"SCORE  {score:05d}",
                   font=("Courier", 11), fill=FG_MID, anchor="ne")
        self._text(CANVAS_W - pad, 28, f"DEATHS  {deaths}",
                   font=("Courier", 10), fill=FG_DIM, anchor="ne")

        if effect_msg:
            self._text(CANVAS_W // 2, CANVAS_H - 40, effect_msg,
                       font=("Courier", 11, "bold"), fill=YELLOW, anchor="center")

    # ------------------------------------------------------------------
    # Death overlay
    # ------------------------------------------------------------------

    def draw_death_overlay(self, lines: list[str], alpha_pct: float) -> None:
        """Semi-transparent death message.  alpha_pct: 0.0 → 1.0"""
        self.clear_overlay()
        # simulate dim overlay with a semi-transparent rect
        self._rect(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="",
                   stipple="gray50" if alpha_pct > 0.3 else "gray25")

        cy = 300
        for i, line in enumerate(lines):
            color = ACCENT if i == 0 else FG_MID
            size = 16 if i == 0 else 12
            self._text(CANVAS_W // 2, cy, line,
                       font=("Courier", size, "bold" if i == 0 else "normal"),
                       fill=color, anchor="center")
            cy += size + 12

        self._text(CANVAS_W // 2, cy + 20, "[ R  to retry ]",
                   font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Level complete
    # ------------------------------------------------------------------

    def draw_level_complete(self, lines: list[str], score_gained: int) -> None:
        self.clear_overlay()
        self._rect(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._rect(30, 30, CANVAS_W - 30, CANVAS_H - 30,
                   outline=GREEN, fill="", width=1)

        cy = 220
        for i, line in enumerate(lines):
            if line == "":
                cy += 14
                continue
            color = GREEN if i == 0 else FG_MAIN
            size = 18 if i == 0 else 13
            self._text(CANVAS_W // 2, cy, line,
                       font=("Courier", size, "bold" if i == 0 else "normal"),
                       fill=color, anchor="center")
            cy += size + 12

        self._text(CANVAS_W // 2, cy + 30, f"+ {score_gained}  pts",
                   font=("Courier", 14, "bold"), fill=YELLOW, anchor="center")

        self._text(CANVAS_W // 2, CANVAS_H - 60,
                   "[ ENTER to continue ]",
                   font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Final ending screen
    # ------------------------------------------------------------------

    def draw_ending(self, lines: list[str], tick: int) -> None:
        self.clear_overlay()
        self._rect(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")

        # flickering border
        col = ACCENT if tick % 6 < 3 else FG_DIM
        self._rect(15, 15, CANVAS_W - 15, CANVAS_H - 15,
                   outline=col, fill="", width=2)

        cy = 160
        for i, line in enumerate(lines):
            if line == "":
                cy += 18
                continue
            if i == 0:
                color, size = ACCENT, 20
            elif "BREACH" in line or "DETECTED" in line:
                color, size = ACCENT, 16
            elif "Thank you" in line or "cooperation" in line:
                color, size = YELLOW, 13
            else:
                color, size = FG_MID, 12
            self._text(CANVAS_W // 2, cy, line,
                       font=("Courier", size, "bold" if size >= 16 else "normal"),
                       fill=color, anchor="center")
            cy += size + 14

        self._text(CANVAS_W // 2, CANVAS_H - 60,
                   "[ ENTER for main menu ]",
                   font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Invert warning
    # ------------------------------------------------------------------

    def draw_invert_warning(self, remaining: float) -> None:
        """Flashing CONTROLS INVERTED banner — called each frame while active."""
        msg = f"CONTROLS INVERTED  [{remaining:.1f}s]"
        self._text(CANVAS_W // 2, CANVAS_H - 40, msg,
                   font=("Courier", 12, "bold"), fill=YELLOW, anchor="center")
