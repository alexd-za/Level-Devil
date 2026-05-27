"""
ui.py — All canvas-based UI: menus, HUD, overlays, typewriter, help.
"""

from __future__ import annotations
import tkinter as tk
import math
from typing import Optional

CANVAS_W = 700
CANVAS_H = 700

# Palette
BG       = "#000000"
FG_DARK  = "#222222"
FG_DIM   = "#444444"
FG_MID   = "#888888"
FG_MAIN  = "#cccccc"
FG_BRIGHT= "#ffffff"
ACCENT   = "#ff3333"
GREEN    = "#00ff88"
YELLOW   = "#ffcc00"
CYAN     = "#00ffcc"
PURPLE   = "#cc00ff"


# ---------------------------------------------------------------------------
# Typewriter text component
# ---------------------------------------------------------------------------

class TypewriterText:
    """Animates lines of text as if being typed."""

    CHARS_PER_SEC = 42.0

    def __init__(self, lines: list[str]):
        self.lines    = lines
        self._elapsed = 0.0
        self._total   = sum(len(l) for l in lines if l)

    def reset(self, lines: list[str]) -> None:
        self.lines    = lines
        self._elapsed = 0.0
        self._total   = sum(len(l) for l in lines if l)

    def update(self, dt: float) -> None:
        self._elapsed += dt

    def skip(self) -> None:
        self._elapsed = self._total / self.CHARS_PER_SEC + 1.0

    @property
    def is_done(self) -> bool:
        return self._elapsed * self.CHARS_PER_SEC >= self._total

    def visible_lines(self) -> list[str]:
        remaining = int(self._elapsed * self.CHARS_PER_SEC)
        result    = []
        for line in self.lines:
            if not line:
                result.append("")
                continue
            if remaining <= 0:
                result.append("")
            elif remaining >= len(line):
                result.append(line)
                remaining -= len(line)
            else:
                result.append(line[:remaining])
                remaining = 0
        return result


# ---------------------------------------------------------------------------
# UIManager
# ---------------------------------------------------------------------------

class UIManager:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self._ids:  list[int] = []
        self._tw    = TypewriterText([])
        self._scanline_ids: list[int] = []

    def clear(self) -> None:
        for cid in self._ids:
            try: self.canvas.delete(cid)
            except Exception: pass
        self._ids.clear()

    def _t(self, x, y, text, **kw) -> int:
        cid = self.canvas.create_text(x, y, text=text, **kw)
        self._ids.append(cid)
        return cid

    def _r(self, x1, y1, x2, y2, **kw) -> int:
        cid = self.canvas.create_rectangle(x1, y1, x2, y2, **kw)
        self._ids.append(cid)
        return cid

    def _l(self, x1, y1, x2, y2, **kw) -> int:
        cid = self.canvas.create_line(x1, y1, x2, y2, **kw)
        self._ids.append(cid)
        return cid

    # ------------------------------------------------------------------
    # Scanline overlay — call once per frame AFTER maze render
    # ------------------------------------------------------------------
    def draw_scanlines(self) -> None:
        for y in range(0, CANVAS_H, 4):
            cid = self.canvas.create_line(
                0, y, CANVAS_W, y,
                fill="#000000", width=1, stipple="gray25",
            )
            self._ids.append(cid)

    # ------------------------------------------------------------------
    # Main menu
    # ------------------------------------------------------------------
    def draw_main_menu(self, blink: bool, tick: int) -> None:
        self.clear()

        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")

        # corner brackets
        bracket_col = FG_DIM
        for bx, by, dx, dy in [(30,30,1,1),(670,30,-1,1),(30,670,1,-1),(670,670,-1,-1)]:
            self._l(bx, by, bx+dx*24, by, fill=bracket_col, width=1)
            self._l(bx, by, bx, by+dy*24, fill=bracket_col, width=1)

        self._t(CANVAS_W//2, 175, "MAZE RUNNER",
                font=("Courier", 46, "bold"), fill=FG_BRIGHT, anchor="center")
        self._t(CANVAS_W//2, 228, "D  E  C  E  P  T  I  O  N",
                font=("Courier", 16), fill=ACCENT, anchor="center")

        # separator line
        self._l(120, 260, 580, 260, fill=FG_DIM, width=1)

        self._t(CANVAS_W//2, 300,
                "Subject 47, escape the facility.",
                font=("Courier", 13), fill=FG_MID, anchor="center")
        self._t(CANVAS_W//2, 322, "Or try.",
                font=("Courier", 13, "italic"), fill=FG_DIM, anchor="center")

        if blink:
            self._t(CANVAS_W//2, 410, "[ ENTER  TO  BEGIN ]",
                    font=("Courier", 14, "bold"), fill=YELLOW, anchor="center")
        else:
            self._t(CANVAS_W//2, 410, "[ ENTER  TO  BEGIN ]",
                    font=("Courier", 14, "bold"), fill=FG_DIM, anchor="center")

        self._t(CANVAS_W//2, 490, "H — help",
                font=("Courier", 10), fill=FG_DIM, anchor="center")

        self._t(CANVAS_W//2, 530,
                "WASD / Arrows  ·  R restart  ·  ESC menu",
                font=("Courier", 10), fill=FG_DIM, anchor="center")

        # version tag
        v_col = FG_DIM if tick % 120 < 100 else FG_MID
        self._t(CANVAS_W - 10, CANVAS_H - 14,
                "FACILITY OS  v4.7",
                font=("Courier", 9), fill=v_col, anchor="se")

        self._t(CANVAS_W//2, CANVAS_H - 14,
                "The facility assumes no liability for psychological distress.",
                font=("Courier", 9), fill=FG_DIM, anchor="s")

    # ------------------------------------------------------------------
    # Help screen
    # ------------------------------------------------------------------
    def draw_help(self) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._r(40, 40, CANVAS_W-40, CANVAS_H-40, fill="", outline=FG_DIM, width=1)

        self._t(CANVAS_W//2, 80, "FACILITY ORIENTATION GUIDE",
                font=("Courier", 16, "bold"), fill=ACCENT, anchor="center")
        self._t(CANVAS_W//2, 104,
                "The facility provides this guide as a courtesy.",
                font=("Courier", 10, "italic"), fill=FG_DIM, anchor="center")
        self._t(CANVAS_W//2, 118,
                "The facility accepts no responsibility for its accuracy.",
                font=("Courier", 10, "italic"), fill=FG_DIM, anchor="center")

        self._l(80, 138, CANVAS_W-80, 138, fill=FG_DIM, width=1)

        controls = [
            ("MOVEMENT",   "WASD  or  Arrow Keys"),
            ("RESTART",    "R"),
            ("MAIN MENU",  "ESC"),
            ("THIS GUIDE", "H  (from menu)"),
        ]
        cy = 165
        for label, key in controls:
            self._t(160, cy, label, font=("Courier", 11, "bold"), fill=FG_MID, anchor="w")
            self._t(420, cy, key,   font=("Courier", 11),         fill=FG_BRIGHT, anchor="w")
            cy += 28

        self._l(80, cy+5, CANVAS_W-80, cy+5, fill=FG_DIM, width=1)
        cy += 25

        self._t(CANVAS_W//2, cy, "OBJECTIVE",
                font=("Courier", 12, "bold"), fill=GREEN, anchor="center")
        cy += 26
        self._t(CANVAS_W//2, cy,
                "Reach the green exit tile to advance.",
                font=("Courier", 11), fill=FG_MAIN, anchor="center")
        cy += 22
        self._t(CANVAS_W//2, cy,
                "There are 5 levels. Each has one trap.",
                font=("Courier", 11), fill=FG_MAIN, anchor="center")
        cy += 22
        self._t(CANVAS_W//2, cy,
                "The facility guarantees the traps are clearly signposted.",
                font=("Courier", 11, "italic"), fill=FG_DIM, anchor="center")

        self._l(80, cy+20, CANVAS_W-80, cy+20, fill=FG_DIM, width=1)
        cy += 40

        self._t(CANVAS_W//2, cy, "SCORING",
                font=("Courier", 12, "bold"), fill=YELLOW, anchor="center")
        cy += 26
        self._t(CANVAS_W//2, cy,
                "Score = (5000 × level) + time bonus − (200 × deaths)",
                font=("Courier", 10), fill=FG_MID, anchor="center")
        cy += 20
        self._t(CANVAS_W//2, cy,
                "Dying is suboptimal.",
                font=("Courier", 10, "italic"), fill=FG_DIM, anchor="center")

        self._t(CANVAS_W//2, CANVAS_H - 55,
                "[ ESC to return ]",
                font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Level intro
    # ------------------------------------------------------------------
    def start_intro(self, lines: list[str]) -> None:
        self._tw.reset(lines)

    def update_typewriter(self, dt: float) -> None:
        self._tw.update(dt)

    def skip_typewriter(self) -> None:
        self._tw.skip()

    def draw_level_intro(self, countdown: float) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._r(25, 25, CANVAS_W-25, CANVAS_H-25, fill="", outline=FG_DIM, width=1)

        visible = self._tw.visible_lines()
        cy = 240
        for i, line in enumerate(visible):
            if not line and i != 0:
                cy += 14
                continue
            if i == 0:
                color, size = ACCENT, 17
            else:
                color, size = FG_MAIN, 12
            if line:
                self._t(CANVAS_W//2, cy, line,
                        font=("Courier", size, "bold" if i == 0 else "normal"),
                        fill=color, anchor="center")
            cy += size + 10

        # progress bar
        bar_w = CANVAS_W - 120
        prog  = max(0.0, (3.0 - countdown) / 3.0)
        self._r(60, CANVAS_H-75, 60 + bar_w, CANVAS_H-63, fill="", outline=FG_DIM)
        if prog > 0:
            self._r(60, CANVAS_H-75, 60 + int(bar_w*prog), CANVAS_H-63,
                    fill=ACCENT, outline="")
        self._t(CANVAS_W//2, CANVAS_H-48,
                f"Commencing in {max(0.0,countdown):.1f}s  ·  ENTER to skip",
                font=("Courier", 10), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # HUD  (drawn every game frame)
    # ------------------------------------------------------------------
    def draw_hud(self, level: int, elapsed: float, score: int,
                 deaths: int, effect_msg: str, hint: str,
                 invert_remaining: float) -> None:
        self.clear()

        m, s = divmod(int(elapsed), 60)
        time_str = f"{m:02d}:{s:02d}"

        # top bar background
        self._r(0, 0, CANVAS_W, 38, fill="#0a0a0a", outline=FG_DIM, width=1)

        self._t(12, 10, f"LVL {level}",
                font=("Courier", 11, "bold"), fill=ACCENT, anchor="nw")
        self._t(CANVAS_W//2, 10, time_str,
                font=("Courier", 11), fill=FG_MID, anchor="n")
        self._t(CANVAS_W-12, 10, f"{score:06d}",
                font=("Courier", 11), fill=FG_MID, anchor="ne")
        self._t(CANVAS_W-12, 24, f"✕{deaths}",
                font=("Courier", 9), fill=FG_DIM, anchor="ne")

        # invert countdown
        if invert_remaining > 0:
            pulse = "#ffcc00" if int(invert_remaining*4) % 2 == 0 else "#ff8800"
            self._t(CANVAS_W//2, CANVAS_H-44,
                    f"⚠ CONTROLS INVERTED  [{invert_remaining:.1f}s] ⚠",
                    font=("Courier", 12, "bold"), fill=pulse, anchor="center")

        # narrator hint
        if hint:
            self._t(CANVAS_W//2, CANVAS_H-18, hint,
                    font=("Courier", 9, "italic"), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Death overlay
    # ------------------------------------------------------------------
    def draw_death(self, lines: list[str], fade: float) -> None:
        """fade: 0→1 how opaque the overlay is."""
        self.clear()
        stipple = "" if fade > 0.7 else ("gray75" if fade > 0.4 else "gray50")
        self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="",
                stipple=stipple if stipple else "")

        cy = 290
        visible = self._tw.visible_lines()
        for i, line in enumerate(visible):
            if not line:
                cy += 12
                continue
            col  = ACCENT if i == 0 else FG_MID
            size = 16 if i == 0 else 11
            self._t(CANVAS_W//2, cy, line,
                    font=("Courier", size, "bold" if i == 0 else "normal"),
                    fill=col, anchor="center")
            cy += size + 12

        if self._tw.is_done:
            self._t(CANVAS_W//2, cy + 24, "[ R to retry  ·  ESC for menu ]",
                    font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Level complete
    # ------------------------------------------------------------------
    def draw_level_complete(self, score_gained: int) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._r(35, 35, CANVAS_W-35, CANVAS_H-35, fill="", outline=GREEN, width=1)

        visible = self._tw.visible_lines()
        cy = 210
        for i, line in enumerate(visible):
            if not line:
                cy += 16
                continue
            if "BREACH" in line or "DETECTED" in line or i == 0:
                color, size = GREEN if i == 0 else ACCENT, 18
            else:
                color, size = FG_MAIN, 12
            self._t(CANVAS_W//2, cy, line,
                    font=("Courier", size, "bold" if size >= 16 else "normal"),
                    fill=color, anchor="center")
            cy += size + 14

        if self._tw.is_done:
            self._t(CANVAS_W//2, cy+20, f"+ {score_gained:,} pts",
                    font=("Courier", 14, "bold"), fill=YELLOW, anchor="center")
            self._t(CANVAS_W//2, CANVAS_H-55, "[ ENTER to continue ]",
                    font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Ending screen
    # ------------------------------------------------------------------
    def draw_ending(self, tick: int) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")

        border_col = ACCENT if tick % 8 < 4 else FG_DIM
        self._r(18, 18, CANVAS_W-18, CANVAS_H-18, fill="", outline=border_col, width=2)
        self._r(22, 22, CANVAS_W-22, CANVAS_H-22, fill="", outline=FG_DIM, width=1)

        visible = self._tw.visible_lines()
        cy = 145
        for i, line in enumerate(visible):
            if not line:
                cy += 20
                continue
            if "BREACH" in line or "DETECTED" in line:
                col, size = ACCENT, 19
            elif i == 0:
                col, size = ACCENT, 16
            elif "Thank you" in line or "cooperation" in line:
                col, size = YELLOW, 13
            elif "miss" in line.lower() or "will not" in line.lower():
                col, size = FG_DIM, 11
            elif any(x in line for x in ["obedience","measured","anticipated"]):
                col, size = FG_MID, 11
            else:
                col, size = FG_MID, 12
            self._t(CANVAS_W//2, cy, line,
                    font=("Courier", size, "bold" if size >= 16 else "normal"),
                    fill=col, anchor="center")
            cy += size + 14

        if self._tw.is_done:
            self._t(CANVAS_W//2, CANVAS_H-55, "[ ENTER for main menu ]",
                    font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Fade overlay  (call after rendering game world)
    # ------------------------------------------------------------------
    def draw_fade(self, alpha: float) -> None:
        """alpha 0=transparent → 1=solid black"""
        if alpha <= 0.0:
            return
        if alpha > 0.85:
            self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="")
        elif alpha > 0.60:
            self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="",
                    stipple="gray75")
        elif alpha > 0.35:
            self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="",
                    stipple="gray50")
        else:
            self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="",
                    stipple="gray25")

    # ------------------------------------------------------------------
    # Cyan invert flash
    # ------------------------------------------------------------------
    def draw_invert_flash(self, intensity: float) -> None:
        """Brief cyan tint when controls invert. intensity 0-1."""
        if intensity <= 0: return
        sp = "gray25" if intensity < 0.5 else "gray50"
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=CYAN, outline="", stipple=sp)
