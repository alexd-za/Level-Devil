"""
game.py — Main game loop, collision, rendering orchestration, input processing.
"""

from __future__ import annotations
import tkinter as tk
import time
from typing import Optional, Callable

from entities import Player, Wall, Exit, FakeExit, TriggerTile, MovingExit, TILE_SIZE
from levels import (
    Level, LevelConfig, make_level,
    LEVEL_INTROS, LEVEL_DEATHS, LEVEL_COMPLETIONS, INTRO_TEXT,
)
from ui import UIManager, CANVAS_W, CANVAS_H, BG


FRAME_MS   = 16          # ~60 fps
TOTAL_LEVELS = 5

# score constants
SCORE_BASE       = 5000
SCORE_TIME_BONUS = 100   # per second under 60s
SCORE_DEATH_PEN  = 200   # per death

# shake params
SHAKE_FRAMES   = 8
SHAKE_STRENGTH = 5


class GameState:
    MENU          = "menu"
    LEVEL_INTRO   = "level_intro"
    PLAYING       = "playing"
    DEAD          = "dead"
    LEVEL_DONE    = "level_done"
    ENDING        = "ending"


class GameController:
    """Orchestrates the whole game from boot to ending."""

    def __init__(self, root: tk.Tk, canvas: tk.Canvas):
        self.root   = root
        self.canvas = canvas
        self.ui     = UIManager(canvas)

        # timing
        self._last_time: float = time.perf_counter()
        self._tick_id: Optional[str] = None

        # input state
        self._keys: set[str] = set()
        self._bind_keys()

        # overall progression
        self.state        = GameState.MENU
        self.current_level_num = 1
        self.total_score  = 0
        self.total_deaths = 0

        # level runtime
        self.level:   Optional[Level]  = None
        self.player:  Optional[Player] = None
        self._level_timer   = 0.0
        self._intro_timer   = 3.0
        self._death_timer   = 0.0
        self._done_timer    = 0.0
        self._ending_tick   = 0

        # blink
        self._blink_timer = 0.0
        self._blink_state = True

        # camera shake
        self._shake_remaining = 0
        self._shake_offset    = (0, 0)

        # pending score for level
        self._level_score = 0

        # menu state
        self._menu_blink = True

        self._start_loop()

    # ------------------------------------------------------------------
    # Key bindings
    # ------------------------------------------------------------------

    def _bind_keys(self) -> None:
        self.root.bind("<KeyPress>",   self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)

    def _on_key_press(self, event: tk.Event) -> None:
        k = event.keysym.lower()
        self._keys.add(k)
        self._handle_action_key(k)

    def _on_key_release(self, event: tk.Event) -> None:
        self._keys.discard(event.keysym.lower())

    def _handle_action_key(self, k: str) -> None:
        if self.state == GameState.MENU:
            if k in ("return", "enter", "space"):
                self._begin_level(1)

        elif self.state == GameState.LEVEL_INTRO:
            if k in ("return", "enter", "space"):
                self._intro_timer = 0.0

        elif self.state == GameState.PLAYING:
            if k == "r":
                self._restart_current_level()
            elif k == "escape":
                self._go_to_menu()

        elif self.state == GameState.DEAD:
            if k == "r":
                self._restart_current_level()
            elif k == "escape":
                self._go_to_menu()

        elif self.state == GameState.LEVEL_DONE:
            if k in ("return", "enter") and self._done_timer > 1.5:
                self._advance_level()

        elif self.state == GameState.ENDING:
            if k in ("return", "enter"):
                self._go_to_menu()

    # ------------------------------------------------------------------
    # Loop
    # ------------------------------------------------------------------

    def _start_loop(self) -> None:
        self._last_time = time.perf_counter()
        self._tick()

    def _tick(self) -> None:
        now = time.perf_counter()
        dt  = min(now - self._last_time, 0.05)   # cap dt at 50ms
        self._last_time = now

        self._update(dt)
        self._render()

        self._tick_id = self.root.after(FRAME_MS, self._tick)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self, dt: float) -> None:
        self._blink_timer += dt
        if self._blink_timer > 0.5:
            self._blink_timer = 0.0
            self._blink_state = not self._blink_state

        if self.state == GameState.MENU:
            pass

        elif self.state == GameState.LEVEL_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0:
                self._start_playing()

        elif self.state == GameState.PLAYING:
            self._update_playing(dt)

        elif self.state == GameState.DEAD:
            self._death_timer += dt

        elif self.state == GameState.LEVEL_DONE:
            self._done_timer += dt

        elif self.state == GameState.ENDING:
            self._ending_tick += 1

        # shake decay
        if self._shake_remaining > 0:
            self._shake_remaining -= 1
            import random
            s = SHAKE_STRENGTH
            self._shake_offset = (
                random.randint(-s, s),
                random.randint(-s, s),
            )
        else:
            self._shake_offset = (0, 0)

    def _update_playing(self, dt: float) -> None:
        if not self.player or not self.level:
            return

        self._level_timer += dt
        self.player.tick_effects(dt)

        # input
        dx, dy = self._get_input()
        xm, ym = self.player.get_input_multiplier()
        dx *= xm
        dy *= ym

        self.player.update(dx, dy, dt, self.level.walls)

        # level tick
        event = self.level.update(dt, self.player)

        if event == "killed":
            self._trigger_death()
        elif event == "level_complete":
            self._trigger_level_complete()
        elif event == "invert_applied":
            self._shake(4)

    def _get_input(self) -> tuple[float, float]:
        k = self._keys
        dx = 0.0
        dy = 0.0
        if "a" in k or "left" in k:
            dx -= 1.0
        if "d" in k or "right" in k:
            dx += 1.0
        if "w" in k or "up" in k:
            dy -= 1.0
        if "s" in k or "down" in k:
            dy += 1.0

        # normalize diagonal
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        return dx, dy

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _begin_level(self, num: int) -> None:
        self.current_level_num = num
        self._intro_timer = 3.0
        self.state = GameState.LEVEL_INTRO

    def _start_playing(self) -> None:
        lv, start = make_level(self.current_level_num)
        self.level = lv
        self.player = Player(*start)
        self._level_timer = 0.0
        self.state = GameState.PLAYING

    def _restart_current_level(self) -> None:
        if self.player:
            self.total_deaths += 1
        self._start_playing()

    def _trigger_death(self) -> None:
        if self.player:
            self.player.die()
            self.total_deaths += 1
        self._death_timer = 0.0
        self._shake(SHAKE_FRAMES)
        self.state = GameState.DEAD

    def _trigger_level_complete(self) -> None:
        self._level_score = self._calc_score()
        self.total_score += self._level_score
        self._done_timer = 0.0
        self.state = GameState.LEVEL_DONE

    def _advance_level(self) -> None:
        nxt = self.current_level_num + 1
        if nxt > TOTAL_LEVELS:
            self.state = GameState.ENDING
            self._ending_tick = 0
        else:
            self._begin_level(nxt)

    def _go_to_menu(self) -> None:
        self.total_score = 0
        self.total_deaths = 0
        self.current_level_num = 1
        self.level  = None
        self.player = None
        self.state  = GameState.MENU

    def _calc_score(self) -> int:
        deaths = self.player.deaths if self.player else 0
        base = SCORE_BASE * self.current_level_num
        time_bonus = max(0, int((60 - self._level_timer) * SCORE_TIME_BONUS))
        death_pen  = deaths * SCORE_DEATH_PEN
        return max(0, base + time_bonus - death_pen)

    def _shake(self, frames: int) -> None:
        self._shake_remaining = frames

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _render(self) -> None:
        self.canvas.delete("all")
        ox, oy = self._shake_offset

        if self.state == GameState.MENU:
            self.ui.draw_main_menu(self._blink_state)

        elif self.state == GameState.LEVEL_INTRO:
            lines = LEVEL_INTROS.get(self.current_level_num, [])
            self.ui.draw_level_intro(lines, max(0.0, self._intro_timer))

        elif self.state == GameState.PLAYING:
            self._render_maze(ox, oy)
            self._render_player(ox, oy)
            # HUD
            effect_msg = ""
            if self.player and self.player.has_effect("invert_controls"):
                rem = self.player.effects.get("invert_controls", 0.0)
                effect_msg = f"CONTROLS INVERTED  [{rem:.1f}s]"
            deaths = self.player.deaths if self.player else 0
            self.ui.draw_hud(
                self.current_level_num,
                self._level_timer,
                self.total_score,
                deaths,
                effect_msg,
            )

        elif self.state == GameState.DEAD:
            self._render_maze(ox, oy)
            lines = LEVEL_DEATHS.get(self.current_level_num, ["You died."])
            self.ui.draw_death_overlay(lines, min(1.0, self._death_timer / 0.4))

        elif self.state == GameState.LEVEL_DONE:
            self._render_maze(0, 0)
            lines = LEVEL_COMPLETIONS.get(self.current_level_num, ["Level complete."])
            # last level → ending, not level_done
            self.ui.draw_level_complete(lines, self._level_score)

        elif self.state == GameState.ENDING:
            lines = LEVEL_COMPLETIONS.get(5, [])
            self.ui.draw_ending(lines, self._ending_tick)

    # ------------------------------------------------------------------
    # Maze rendering
    # ------------------------------------------------------------------

    def _calc_offset(self) -> tuple[int, int]:
        """Center the maze on the 700x700 canvas."""
        if not self.level:
            return 0, 0
        maze_w = self.level.cols * TILE_SIZE
        maze_h = self.level.rows * TILE_SIZE
        return (CANVAS_W - maze_w) // 2, (CANVAS_H - maze_h) // 2

    def _render_maze(self, shake_x: int = 0, shake_y: int = 0) -> None:
        if not self.level:
            return
        ox, oy = self._calc_offset()
        ox += shake_x
        oy += shake_y

        # background
        self.canvas.create_rectangle(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")

        for entity in self.level.get_all_renderable():
            ex = entity.gx * TILE_SIZE + ox
            ey = entity.gy * TILE_SIZE + oy
            ew = TILE_SIZE
            eh = TILE_SIZE

            if isinstance(entity, Wall):
                self.canvas.create_rectangle(
                    ex, ey, ex + ew, ey + eh,
                    fill="#dddddd", outline="#888888", width=1,
                )
            elif isinstance(entity, FakeExit):
                self._draw_exit_tile(ex, ey, ew, "#00cc44", fake=True)
            elif isinstance(entity, (Exit, MovingExit)):
                pulse_alpha = self._pulse_color(entity)
                self._draw_exit_tile(ex, ey, ew, pulse_alpha, fake=False)
            elif isinstance(entity, TriggerTile):
                self.canvas.create_rectangle(
                    ex + 2, ey + 2, ex + ew - 2, ey + eh - 2,
                    fill="#220022", outline="",
                )

    def _draw_exit_tile(self, ex: float, ey: float, ew: int,
                        color: str, fake: bool) -> None:
        self.canvas.create_rectangle(
            ex, ey, ex + ew, ey + ew,
            fill=color, outline="#ffffff" if not fake else color, width=2,
        )
        label = "EXIT" if not fake else "EXIT"
        self.canvas.create_text(
            ex + ew // 2, ey + ew // 2, text=label,
            font=("Courier", 7, "bold"), fill="#000000",
        )

    def _pulse_color(self, entity) -> str:
        """Returns a pulsing green shade for exit tiles."""
        import math
        t = time.perf_counter()
        v = int(180 + 75 * math.sin(t * 4))
        v = max(0, min(255, v))
        return f"#{0:02x}{v:02x}{70:02x}"

    def _render_player(self, shake_x: int = 0, shake_y: int = 0) -> None:
        if not self.player or not self.player.alive:
            return
        ox, oy = self._calc_offset()
        ox += shake_x
        oy += shake_y

        px = self.player.gx * TILE_SIZE + 3 + ox
        py = self.player.gy * TILE_SIZE + 3 + oy
        ps = self.player.SIZE

        color = self.player.color
        if self.player.has_effect("invert_controls"):
            import math
            t = time.perf_counter()
            v = int(180 + 75 * math.sin(t * 8))
            color = f"#{v:02x}{0:02x}{v:02x}"

        self.canvas.create_rectangle(
            px, py, px + ps, py + ps,
            fill=color, outline="#ff8888", width=1,
        )
        # directional dot
        cx, cy = px + ps // 2, py + ps // 2
        r = 3
        fdx, fdy = {
            "right": (6, 0), "left": (-6, 0),
            "down":  (0, 6), "up":   (0, -6),
        }.get(self.player.facing, (0, 0))
        self.canvas.create_oval(
            cx + fdx - r, cy + fdy - r,
            cx + fdx + r, cy + fdy + r,
            fill="#ffffff", outline="",
        )
