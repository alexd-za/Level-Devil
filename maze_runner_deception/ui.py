from __future__ import annotations
import tkinter as tk
import math
import random as _rng
from typing import Optional

_STAR_POSITIONS: list[tuple[int, int]] = []
_rng.seed(0xfa117)
for _i in range(70):
    _STAR_POSITIONS.append((_rng.randint(2, 698), _rng.randint(2, 698)))

CANVAS_W = 700
CANVAS_H = 700
HUD_H    = 42

BG       = "#000000"
FG_DARK  = "#1a1a1a"
FG_DIM   = "#666666"
FG_MID   = "#aaaaaa"
FG_MAIN  = "#dddddd"
FG_BRIGHT= "#ffffff"
ACCENT   = "#ff3333"
GREEN    = "#00ff88"
YELLOW   = "#ffcc00"
CYAN     = "#00ffcc"
PURPLE   = "#cc00ff"
ORANGE   = "#ff8800"


class TypewriterText:
    CHARS_PER_SEC = 44.0

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


class UIManager:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self._ids: list[int] = []
        self._tw   = TypewriterText([])

    def clear(self) -> None:
        for cid in self._ids:
            try:
                self.canvas.delete(cid)
            except Exception:
                pass
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

    def draw_scanlines(self) -> None:
        pass

    def _draw_stars(self, tick: int) -> None:
        for i, (sx, sy) in enumerate(_STAR_POSITIONS):
            phase = (tick + i * 7) % 120
            if phase < 100:
                col = "#1e1e2e"
            elif phase < 110:
                col = "#aaaacc"
            else:
                col = "#ffffff"
            self._r(sx, sy, sx + 1, sy + 1, fill=col, outline="")

    def draw_starfield_raw(self, canvas: tk.Canvas, tick: int) -> None:
        for i, (sx, sy) in enumerate(_STAR_POSITIONS):
            phase = (tick + i * 7) % 120
            if phase < 100:
                col = "#1e1e2e"
            elif phase < 110:
                col = "#aaaacc"
            else:
                col = "#ffffff"
            canvas.create_rectangle(sx, sy, sx + 1, sy + 1, fill=col, outline="")

    # ------------------------------------------------------------------
    # Main menu
    # ------------------------------------------------------------------

    def draw_main_menu(self, blink: bool, tick: int) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._draw_stars(tick)

        for bx, by, dx, dy in [(30,30,1,1),(670,30,-1,1),(30,670,1,-1),(670,670,-1,-1)]:
            self._l(bx, by, bx + dx * 26, by, fill=FG_DIM, width=1)
            self._l(bx, by, bx, by + dy * 26, fill=FG_DIM, width=1)

        self._t(CANVAS_W // 2, 158, "MAZE RUNNER",
                font=("Courier", 48, "bold"), fill=FG_BRIGHT, anchor="center")
        self._t(CANVAS_W // 2, 214, "D  E  C  E  P  T  I  O  N",
                font=("Courier", 16), fill=ACCENT, anchor="center")

        self._l(100, 248, 600, 248, fill=FG_DIM, width=1)

        self._t(CANVAS_W // 2, 280, "Subject 47 — Day 23",
                font=("Courier", 12), fill=FG_MID, anchor="center")
        self._t(CANVAS_W // 2, 300, "Your cooperation is appreciated.",
                font=("Courier", 12), fill=FG_MID, anchor="center")
        self._t(CANVAS_W // 2, 320, "Your escape attempts are also appreciated.",
                font=("Courier", 11, "italic"), fill=FG_DIM, anchor="center")
        self._t(CANVAS_W // 2, 338, "(They are very amusing.)",
                font=("Courier", 10, "italic"), fill=FG_DIM, anchor="center")

        enter_col = YELLOW if blink else FG_DIM
        self._t(CANVAS_W // 2, 408, "[ ENTER  TO  BEGIN ]",
                font=("Courier", 14, "bold"), fill=enter_col, anchor="center")

        self._l(100, 448, 600, 448, fill=FG_DIM, width=1)

        self._t(CANVAS_W // 2, 472,
                "WASD / Arrows — move   |   R — restart   |   ESC — menu",
                font=("Courier", 10), fill=FG_DIM, anchor="center")
        self._t(CANVAS_W // 2, 492, "H — help   |   L — leaderboard",
                font=("Courier", 10), fill=FG_DIM, anchor="center")

        v_col = FG_DIM if tick % 120 < 95 else FG_MID
        self._t(CANVAS_W - 10, CANVAS_H - 12, "FACILITY OS  v7.3",
                font=("Courier", 9), fill=v_col, anchor="se")
        self._t(CANVAS_W // 2, CANVAS_H - 12,
                "The facility assumes no liability for psychological distress.",
                font=("Courier", 9), fill=FG_DIM, anchor="s")

    # ------------------------------------------------------------------
    # Help screen
    # ------------------------------------------------------------------

    def draw_help(self) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._draw_stars(0)
        self._r(38, 38, CANVAS_W - 38, CANVAS_H - 38, fill="", outline=FG_DIM, width=1)

        self._t(CANVAS_W // 2, 68, "FACILITY ORIENTATION GUIDE",
                font=("Courier", 16, "bold"), fill=ACCENT, anchor="center")
        self._t(CANVAS_W // 2, 90,
                "The facility provides this guide as a courtesy.",
                font=("Courier", 10, "italic"), fill=FG_DIM, anchor="center")
        self._t(CANVAS_W // 2, 105,
                "The facility accepts no responsibility for its accuracy.",
                font=("Courier", 10, "italic"), fill=FG_DIM, anchor="center")

        self._l(80, 124, CANVAS_W - 80, 124, fill=FG_DIM, width=1)

        controls = [
            ("MOVEMENT",   "WASD  or  Arrow Keys"),
            ("RESTART",    "R  or  ENTER (death screen)"),
            ("MAIN MENU",  "ESC"),
            ("THIS GUIDE", "H  (from main menu)"),
        ]
        cy = 144
        for label, binding in controls:
            self._t(148, cy, label,   font=("Courier", 11, "bold"), fill=FG_MID,    anchor="w")
            self._t(388, cy, binding, font=("Courier", 11),          fill=FG_BRIGHT, anchor="w")
            cy += 28

        self._l(80, cy + 2, CANVAS_W - 80, cy + 2, fill=FG_DIM, width=1)
        cy += 22

        self._t(CANVAS_W // 2, cy, "OBJECTIVE",
                font=("Courier", 12, "bold"), fill=GREEN, anchor="center")
        cy += 26
        tips = [
            "Reach the green EXIT tile in each of 5 sectors.",
            "Each sector introduces one new deception.",
            "Glowing yellow icons are collectible documents.",
            "Walk into suspicious walls. Some are passable.",
            "",
            "The facility guarantees the rules are fair.",
            "(This guarantee is void.)",
        ]
        for tip in tips:
            if not tip:
                cy += 10
                continue
            col   = FG_DIM if tip.startswith("(") else FG_MAIN
            style = "italic" if tip.startswith("(") else "normal"
            self._t(CANVAS_W // 2, cy, tip,
                    font=("Courier", 10, style), fill=col, anchor="center")
            cy += 19

        self._l(80, cy + 2, CANVAS_W - 80, cy + 2, fill=FG_DIM, width=1)
        cy += 20

        self._t(CANVAS_W // 2, cy, "SCORING",
                font=("Courier", 12, "bold"), fill=YELLOW, anchor="center")
        cy += 24
        self._t(CANVAS_W // 2, cy,
                "Score = (6000 × sector) + time bonus − (250 × deaths)",
                font=("Courier", 10), fill=FG_MID, anchor="center")
        cy += 18
        self._t(CANVAS_W // 2, cy, "Dying is suboptimal.",
                font=("Courier", 10, "italic"), fill=FG_DIM, anchor="center")

        self._t(CANVAS_W // 2, CANVAS_H - 56, "[ ESC or H to return ]",
                font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Intro / death typewriter screen
    # ------------------------------------------------------------------

    def start_intro(self, lines: list[str]) -> None:
        self._tw.reset(lines)

    def update_typewriter(self, dt: float) -> None:
        self._tw.update(dt)

    def skip_typewriter(self) -> None:
        self._tw.skip()

    def draw_level_intro(self) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._draw_stars(0)
        self._r(24, 24, CANVAS_W - 24, CANVAS_H - 24, fill="", outline=FG_DIM, width=1)

        visible = self._tw.visible_lines()
        cy = 215
        for i, line in enumerate(visible):
            if not line:
                cy += 14
                continue
            if i == 0:
                col, size, style = ACCENT, 18, "bold"
            elif line.startswith("[ORACLE") or line.startswith("[FRAGMENT"):
                col, size, style = PURPLE, 10, "italic"
            elif line.startswith("("):
                col, size, style = FG_DIM, 10, "italic"
            else:
                col, size, style = FG_MAIN, 12, "normal"
            self._t(CANVAS_W // 2, cy, line,
                    font=("Courier", size, style), fill=col, anchor="center")
            cy += size + 11

        if self._tw.is_done:
            # Blinking "press ENTER" prompt
            import time as _time
            blink_on = int(_time.perf_counter() * 2) % 2 == 0
            prompt_col = YELLOW if blink_on else FG_DIM
            self._t(CANVAS_W // 2, CANVAS_H - 54,
                    "[ ENTER  TO  BEGIN ]",
                    font=("Courier", 13, "bold"), fill=prompt_col, anchor="center")
        else:
            self._t(CANVAS_W // 2, CANVAS_H - 54,
                    "[ ENTER to skip ]",
                    font=("Courier", 10), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def draw_hud(self, level: int, elapsed: float, score: int,
                 deaths: int, hint: str,
                 invert_remaining: float, dark_remaining: float,
                 speed_remaining: float, shield_remaining: float,
                 notes_found: int,
                 lab_msg: str = "", lab_timer: float = 0.0) -> None:
        self.clear()

        m, s = divmod(int(elapsed), 60)
        time_str = f"{m:02d}:{s:02d}"

        self._r(0, 0, CANVAS_W, HUD_H, fill="#060608", outline="")
        self._l(0, HUD_H - 1, CANVAS_W, HUD_H - 1, fill=FG_DIM, width=1)

        self._t(10, 8, f"SECTOR {level}",
                font=("Courier", 11, "bold"), fill=ACCENT, anchor="nw")
        import time as _t
        if elapsed > 120:
            t_col = ACCENT if int(_t.perf_counter() * 3) % 2 == 0 else "#660000"
        elif elapsed > 90:
            t_col = ORANGE
        elif elapsed > 60:
            t_col = YELLOW
        else:
            t_col = FG_MID
        self._t(CANVAS_W // 2, 8, time_str,
                font=("Courier", 11, "bold" if elapsed > 90 else "normal"), fill=t_col, anchor="n")
        self._t(CANVAS_W - 10, 8, f"{score:07d}",
                font=("Courier", 11), fill=FG_MID, anchor="ne")
        self._t(CANVAS_W - 10, 24, f"deaths: {deaths}",
                font=("Courier", 9), fill=FG_DIM, anchor="ne")

        if notes_found > 0:
            self._t(12, 26, f"docs: {notes_found}",
                    font=("Courier", 9), fill="#886600", anchor="nw")

        by = CANVAS_H - 18
        if hint:
            self._t(CANVAS_W // 2, by, hint,
                    font=("Courier", 9, "italic"), fill=FG_DIM, anchor="center")
            by -= 20

        if speed_remaining > 0:
            self._t(CANVAS_W // 2, by,
                    f"▶▶  SPEED BOOST  [{speed_remaining:.1f}s]",
                    font=("Courier", 11, "bold"), fill=CYAN, anchor="center")
            by -= 20

        if shield_remaining > 0:
            self._t(CANVAS_W // 2, by,
                    f"◆  SHIELD ACTIVE  [{shield_remaining:.1f}s]  ◆",
                    font=("Courier", 11, "bold"), fill="#aaff44", anchor="center")
            by -= 20

        if dark_remaining > 0:
            self._t(CANVAS_W // 2, by,
                    f"LIGHTS OUT  [{dark_remaining:.1f}s]",
                    font=("Courier", 11, "bold"), fill=PURPLE, anchor="center")
            by -= 20

        if invert_remaining > 0:
            import time as _t
            blink = int(_t.perf_counter() * 5) % 2 == 0
            pulse = YELLOW if blink else ORANGE
            self._r(60, by - 14, CANVAS_W - 60, by + 4,
                    fill="#1a0800", outline=ORANGE, width=1)
            self._t(CANVAS_W // 2, by - 5,
                    f"⚠  CONTROLS INVERTED  [{invert_remaining:.1f}s]  ⚠",
                    font=("Courier", 13, "bold"), fill=pulse, anchor="center")

        if lab_msg and lab_timer > 0:
            self.draw_lab_message(lab_msg, lab_timer)

    # ------------------------------------------------------------------
    # Death overlay
    # ------------------------------------------------------------------

    def draw_death(self, fade: float) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._draw_stars(0)
        stipple = "" if fade > 0.7 else ("gray75" if fade > 0.4 else "gray50")
        self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="",
                stipple=stipple if stipple else "")

        visible = self._tw.visible_lines()
        cy = 265
        for i, line in enumerate(visible):
            if not line:
                cy += 12
                continue
            if i == 0:
                col, size = ACCENT, 17
            elif any(w in line for w in ("SECURITY", "CONTACT", "ORACLE", "UNIT")):
                col, size = ORANGE, 11
            else:
                col, size = FG_MID, 11
            style = "bold" if i == 0 else "normal"
            self._t(CANVAS_W // 2, cy, line,
                    font=("Courier", size, style), fill=col, anchor="center")
            cy += size + 12

        if self._tw.is_done:
            self._t(CANVAS_W // 2, cy + 26,
                    "[ ENTER / R — retry   ·   ESC — main menu ]",
                    font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Level complete
    # ------------------------------------------------------------------

    def draw_level_complete(self, score_gained: int) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._draw_stars(0)
        self._r(32, 32, CANVAS_W - 32, CANVAS_H - 32, fill="", outline=GREEN, width=1)

        visible = self._tw.visible_lines()
        cy = 190
        for i, line in enumerate(visible):
            if not line:
                cy += 18
                continue
            if i == 0:
                col, size = GREEN, 19
            elif "BREACH" in line or "DETECTED" in line:
                col, size = ACCENT, 16
            elif line.startswith("("):
                col, size = FG_DIM, 10
            else:
                col, size = FG_MAIN, 12
            style = "bold" if size >= 16 else ("italic" if line.startswith("(") else "normal")
            self._t(CANVAS_W // 2, cy, line,
                    font=("Courier", size, style), fill=col, anchor="center")
            cy += size + 14

        if self._tw.is_done:
            self._t(CANVAS_W // 2, cy + 16, f"+ {score_gained:,} pts",
                    font=("Courier", 14, "bold"), fill=YELLOW, anchor="center")
            self._t(CANVAS_W // 2, CANVAS_H - 55, "[ ENTER to continue ]",
                    font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Ending screen
    # ------------------------------------------------------------------

    def draw_ending(self, tick: int) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._draw_stars(tick // 2)
        border_col = ACCENT if tick % 8 < 4 else FG_DIM
        self._r(16, 16, CANVAS_W - 16, CANVAS_H - 16,
                fill="", outline=border_col, width=2)
        self._r(20, 20, CANVAS_W - 20, CANVAS_H - 20,
                fill="", outline=FG_DIM, width=1)

        visible = self._tw.visible_lines()

        # Measure total height first so we can auto-scroll as text grows
        LINE_GAP = 6
        line_heights = []
        for i, line in enumerate(visible):
            if not line:
                line_heights.append(10)
                continue
            if "BREACH" in line or "DETECTED" in line:
                size = 14
            elif i == 0:
                size = 13
            elif "Group D" in line or "forever" in line:
                size = 11
            elif "See you" in line or "tomorrow" in line:
                size = 11
            elif line.startswith("(") and ")" in line:
                size = 9
            elif "chose" in line.lower() or "consent" in line.lower():
                size = 11
            else:
                size = 10
            line_heights.append(size + LINE_GAP)

        total_h = sum(line_heights)
        view_h  = CANVAS_H - 80  # reserve top/bottom border
        # scroll: as total_h exceeds view_h, shift upward
        scroll  = max(0, total_h - view_h)
        cy      = 36 - scroll

        for i, line in enumerate(visible):
            lh = line_heights[i]
            draw_y = cy + lh // 2
            if 24 <= draw_y <= CANVAS_H - 50:  # only draw if in viewport
                if not line:
                    pass
                else:
                    if "BREACH" in line or "DETECTED" in line:
                        col, size = ACCENT, 14
                    elif i == 0:
                        col, size = ACCENT, 13
                    elif "Group D" in line or "forever" in line:
                        col, size = PURPLE, 11
                    elif "See you" in line or "tomorrow" in line:
                        col, size = ORANGE, 11
                    elif line.startswith("(") and ")" in line:
                        col, size = FG_DIM, 9
                    elif "chose" in line.lower() or "consent" in line.lower():
                        col, size = YELLOW, 11
                    elif "not a lie" in line:
                        col, size = GREEN, 10
                    elif line.startswith("[LOADING]"):
                        col, size = FG_DIM, 10
                    else:
                        col, size = FG_MID, 10
                    style = "italic" if line.startswith("(") else ("bold" if size >= 13 else "normal")
                    self._t(CANVAS_W // 2, draw_y, line,
                            font=("Courier", size, style), fill=col, anchor="center")
            cy += lh

        if self._tw.is_done:
            self._t(CANVAS_W // 2, CANVAS_H - 34, "[ ENTER — main menu ]",
                    font=("Courier", 11), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Note popup
    # ------------------------------------------------------------------

    def draw_note_popup(self, lines: list[str], timer: float) -> None:
        alpha    = min(1.0, timer / 0.4) if timer > 5.6 else min(1.0, timer / 1.0)
        panel_h  = 20 + len(lines) * 15 + 10
        py       = CANVAS_H - panel_h - 52
        stipple  = "" if alpha > 0.85 else ("gray75" if alpha > 0.5 else "gray50")
        base_kw  = {"stipple": stipple} if stipple else {}

        self._r(42, py - 2, CANVAS_W - 42, py + panel_h + 2,
                fill="#000000", outline="", **base_kw)
        self._r(44, py, CANVAS_W - 44, py + panel_h,
                fill="#070705", outline=YELLOW, width=1, **base_kw)

        hdr_col = YELLOW if alpha > 0.6 else "#887700"
        self._t(CANVAS_W // 2, py + 10,
                "▶  CLASSIFIED DOCUMENT RETRIEVED  ◀",
                font=("Courier", 9, "bold"), fill=hdr_col, anchor="center")

        for i, line in enumerate(lines):
            col  = YELLOW if line.startswith("[") else (FG_DIM if line == "" else FG_MAIN)
            self._t(CANVAS_W // 2, py + 24 + i * 15, line,
                    font=("Courier", 9), fill=col, anchor="center")

    # ------------------------------------------------------------------
    # Lab message corner popup
    # ------------------------------------------------------------------

    def draw_lab_message(self, msg: str, timer: float) -> None:
        alpha = min(1.0, timer / 0.4) if timer > 4.6 else min(1.0, timer / 1.0)
        stipple = "" if alpha > 0.85 else ("gray75" if alpha > 0.5 else "gray50")
        base_kw = {"stipple": stipple} if stipple else {}

        pw = 320
        panel_h = 56
        px = 8
        py = CANVAS_H - HUD_H - panel_h - 62

        self._r(px, py, px + pw, py + panel_h,
                fill="#000000", outline="", **base_kw)
        self._r(px + 4, py, px + 7, py + panel_h,
                fill="#cc3300", outline="", **base_kw)
        self._r(px + 7, py, px + pw, py + panel_h,
                fill="#0c0400", outline="#441000", width=1, **base_kw)
        self._l(px + 7, py + 18, px + pw - 2, py + 18,
                fill="#331100", width=1)

        hdr_col = "#ff5500" if alpha > 0.7 else "#882200"
        self._t(px + 8 + (pw - 8) // 2, py + 9,
                "◀  FACILITY LOG  ▶",
                font=("Courier", 8, "bold"), fill=hdr_col, anchor="center")

        msg_col = "#ee6600" if alpha > 0.7 else "#774400"
        self._t(px + 14, py + 30,
                msg,
                font=("Courier", 8), fill=msg_col, anchor="nw",
                width=pw - 18)

    # ------------------------------------------------------------------
    # Leaderboard screen
    # ------------------------------------------------------------------

    def draw_leaderboard(self, scores: list) -> None:
        self.clear()
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self._draw_stars(0)
        self._r(32, 32, CANVAS_W - 32, CANVAS_H - 32, fill="", outline=YELLOW, width=1)

        self._t(CANVAS_W // 2, 62, "FACILITY RECORDS",
                font=("Courier", 20, "bold"), fill=YELLOW, anchor="center")
        self._t(CANVAS_W // 2, 88, "Top Subjects by Score",
                font=("Courier", 11, "italic"), fill=FG_DIM, anchor="center")

        self._l(80, 108, CANVAS_W - 80, 108, fill=FG_DIM, width=1)

        if not scores:
            self._t(CANVAS_W // 2, CANVAS_H // 2,
                    "No scores recorded yet.",
                    font=("Courier", 12, "italic"), fill=FG_MID, anchor="center")
            self._t(CANVAS_W // 2, CANVAS_H // 2 + 28,
                    "Complete the game to enter the leaderboard.",
                    font=("Courier", 10), fill=FG_DIM, anchor="center")
        else:
            headers = ("RANK", "NAME", "SCORE", "DEATHS")
            col_x   = (90, 200, 450, 590)
            cy = 126
            for i, hdr in enumerate(headers):
                self._t(col_x[i], cy, hdr,
                        font=("Courier", 10, "bold"), fill=FG_MID, anchor="nw")
            cy += 22
            self._l(80, cy, CANVAS_W - 80, cy, fill=FG_DIM, width=1)
            cy += 8

            medals = {0: YELLOW, 1: "#c0c0c0", 2: "#cd7f32"}
            for idx, entry in enumerate(scores):
                row_col = medals.get(idx, FG_MAIN)
                rank_str  = f"#{idx + 1}"
                name_str  = entry.get("name", "???")[:14]
                score_str = f"{entry.get('score', 0):,}"
                death_str = str(entry.get("deaths", 0))
                for col_i, text in enumerate(
                        (rank_str, name_str, score_str, death_str)):
                    self._t(col_x[col_i], cy, text,
                            font=("Courier", 11), fill=row_col, anchor="nw")
                cy += 24

        self._l(80, CANVAS_H - 70, CANVAS_W - 80, CANVAS_H - 70, fill=FG_DIM, width=1)
        self._t(CANVAS_W // 2, CANVAS_H - 50,
                "[ ESC / L / ENTER — back to menu ]",
                font=("Courier", 10), fill=FG_DIM, anchor="center")

    # ------------------------------------------------------------------
    # Overlays
    # ------------------------------------------------------------------

    def draw_pause(self) -> None:
        self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="", stipple="gray50")
        pw, ph = 340, 180
        px = (CANVAS_W - pw) // 2
        py = (CANVAS_H - ph) // 2
        self._r(px, py, px + pw, py + ph, fill="#050508", outline=FG_DIM, width=1)
        self._r(px + 2, py + 2, px + pw - 2, py + 4, fill=ACCENT, outline="")
        self._t(CANVAS_W // 2, py + 26, "PAUSED",
                font=("Courier", 22, "bold"), fill=FG_BRIGHT, anchor="center")
        self._l(px + 20, py + 50, px + pw - 20, py + 50, fill=FG_DIM, width=1)
        self._t(CANVAS_W // 2, py + 68, "P / ESC  — resume",
                font=("Courier", 11), fill=FG_MID, anchor="center")
        self._t(CANVAS_W // 2, py + 90, "R  — restart level",
                font=("Courier", 11), fill=FG_MID, anchor="center")
        self._t(CANVAS_W // 2, py + 112, "M  — main menu",
                font=("Courier", 11), fill=FG_MID, anchor="center")
        self._t(CANVAS_W // 2, py + 148,
                "The facility thanks you for your patience.",
                font=("Courier", 9, "italic"), fill=FG_DIM, anchor="center")

    def draw_admin_panel(self, level: int, noclip: bool, speed: bool) -> None:
        pw, ph = 260, 180
        px, py = CANVAS_W - pw - 8, HUD_H + 8
        self._r(px, py, px + pw, py + ph, fill="#000800", outline="#00cc44", width=1)
        self._r(px + 2, py + 2, px + pw - 2, py + 4, fill="#00cc44", outline="")
        self._t(px + pw // 2, py + 14, "▶  ADMIN MODE  ◀",
                font=("Courier", 9, "bold"), fill="#00ff44", anchor="center")
        self._l(px + 8, py + 24, px + pw - 8, py + 24, fill="#004400", width=1)
        lines = [
            (f"SECTOR  : {level}", "#00cc44"),
            (f"NOCLIP  : {'ON' if noclip else 'OFF'}  [N]", "#00ff44" if noclip else "#337733"),
            (f"SPEED   : {'ON' if speed else 'OFF'}  [B]", "#00ff44" if speed else "#337733"),
            ("KILL ENEMIES   [K]", "#cc4400"),
            ("GET ALL DOCS   [C]", "#ccaa00"),
            ("JUMP SECTOR  [1-5]", "#0088cc"),
        ]
        cy = py + 36
        for txt, col in lines:
            self._t(px + 12, cy, txt, font=("Courier", 9), fill=col, anchor="nw")
            cy += 20
        self._t(px + pw // 2, py + ph - 10,
                "` to close", font=("Courier", 8), fill="#224422", anchor="center")

    def draw_fade(self, alpha: float) -> None:
        if alpha <= 0.0:
            return
        if alpha > 0.85:
            self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="")
        elif alpha > 0.60:
            self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="", stipple="gray75")
        elif alpha > 0.35:
            self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="", stipple="gray50")
        else:
            self._r(0, 0, CANVAS_W, CANVAS_H, fill="#000000", outline="", stipple="gray25")

    def draw_invert_flash(self, intensity: float) -> None:
        if intensity <= 0:
            return
        sp = "gray25" if intensity < 0.5 else "gray50"
        self._r(0, 0, CANVAS_W, CANVAS_H, fill=CYAN, outline="", stipple=sp)

    def draw_powerup_flash(self, intensity: float) -> None:
        if intensity <= 0:
            return
        sp = "gray25" if intensity < 0.5 else "gray50"
        self._r(0, 0, CANVAS_W, CANVAS_H, fill="#00ffaa", outline="", stipple=sp)
