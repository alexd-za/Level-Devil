"""
game.py — Game loop, particles, transitions, collision, rendering.
"""

from __future__ import annotations
import tkinter as tk
import time
import math
import random
from typing import Optional, Callable
from dataclasses import dataclass, field

from entities import (
    Player, Wall, Exit, FakeExit, TriggerTile, MovingExit,
    TILE_SIZE, PLAYER_SIZE, PLAYER_GAP,
)
from levels import (
    Level, make_level,
    LEVEL_INTROS, LEVEL_COMPLETIONS, LEVEL_HINTS,
    INTRO_TEXT,
)
from ui import UIManager, CANVAS_W, CANVAS_H, BG

FRAME_MS     = 16          # ~62.5 fps
TOTAL_LEVELS = 5

SCORE_BASE       = 5000
SCORE_TIME_BONUS = 100
SCORE_DEATH_PEN  = 200

SHAKE_FRAMES   = 10
SHAKE_STRENGTH = 6


# ---------------------------------------------------------------------------
# Particle system
# ---------------------------------------------------------------------------

@dataclass
class Particle:
    x:        float
    y:        float
    vx:       float
    vy:       float
    life:     float
    max_life: float
    size:     float
    color:    str


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def burst(self, px: float, py: float, color: str = "#ff3333",
              count: int = 14) -> None:
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(50, 160)
            ml    = random.uniform(0.35, 0.65)
            self.particles.append(Particle(
                x=px, y=py,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=ml, max_life=ml,
                size=random.uniform(2.5, 5.5),
                color=color,
            ))

    def update(self, dt: float) -> None:
        for p in self.particles:
            p.x  += p.vx * dt
            p.y  += p.vy * dt
            p.vy += 220 * dt     # gravity
            p.vx *= 0.96         # drag
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0]

    def render(self, canvas: tk.Canvas) -> None:
        for p in self.particles:
            a = max(0.0, p.life / p.max_life)
            r = int(255 * a)
            try:
                col = f"#{r:02x}{0:02x}{0:02x}"
            except Exception:
                col = "#ff0000"
            s = p.size * a
            canvas.create_rectangle(
                p.x - s, p.y - s, p.x + s, p.y + s,
                fill=col, outline="",
            )


# ---------------------------------------------------------------------------
# Fade transition
# ---------------------------------------------------------------------------

class FadeTransition:
    SPEED = 3.5   # full cycle in 1/SPEED seconds per half

    def __init__(self):
        self.alpha     = 0.0
        self._dir      = 0       # 0=idle, 1=fade-out, -1=fade-in
        self._callback: Optional[Callable] = None
        self._called   = False

    @property
    def active(self) -> bool:
        return self._dir != 0

    def start(self, callback: Callable) -> None:
        self._dir      = 1
        self.alpha     = 0.0
        self._callback = callback
        self._called   = False

    def update(self, dt: float) -> None:
        if self._dir == 0:
            return
        self.alpha += self._dir * self.SPEED * dt
        if self._dir == 1 and self.alpha >= 1.0:
            self.alpha = 1.0
            if self._callback and not self._called:
                self._called = True
                self._callback()
            self._dir = -1
        elif self._dir == -1 and self.alpha <= 0.0:
            self.alpha = 0.0
            self._dir  = 0


# ---------------------------------------------------------------------------
# Game states
# ---------------------------------------------------------------------------

class GS:
    MENU        = "menu"
    HELP        = "help"
    INTRO       = "intro"
    PLAYING     = "playing"
    DEAD        = "dead"
    LEVEL_DONE  = "level_done"
    ENDING      = "ending"


# ---------------------------------------------------------------------------
# GameController
# ---------------------------------------------------------------------------

class GameController:
    def __init__(self, root: tk.Tk, canvas: tk.Canvas):
        self.root   = root
        self.canvas = canvas
        self.ui     = UIManager(canvas)
        self.particles = ParticleSystem()
        self.fade      = FadeTransition()

        self._keys: set[str] = set()
        self._bind_keys()

        # global counters
        self.total_score  = 0
        self.total_deaths = 0
        self.current_lvl  = 1

        # runtime
        self.state:  str            = GS.MENU
        self.level:  Optional[Level]  = None
        self.player: Optional[Player] = None

        self._level_timer   = 0.0
        self._intro_timer   = 3.0
        self._death_timer   = 0.0
        self._done_timer    = 0.0
        self._ending_tick   = 0
        self._level_score   = 0

        # narrator hint
        self._hint_text     = ""
        self._hint_shown    = False
        self._hint_timer    = 0.0

        # invert flash visual
        self._invert_flash  = 0.0   # countdown seconds

        # glitch flash (level 4 wall spawn)
        self._glitch_frames = 0

        # screen shake
        self._shake_rem  = 0
        self._shake_off  = (0, 0)

        # blink / tick
        self._blink_t    = 0.0
        self._blink      = True
        self._tick_count = 0

        self._last_t = time.perf_counter()
        self._loop()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _bind_keys(self) -> None:
        self.root.bind("<KeyPress>",   self._on_press)
        self.root.bind("<KeyRelease>", self._on_release)

    def _on_press(self, ev: tk.Event) -> None:
        k = ev.keysym.lower()
        self._keys.add(k)
        self._handle_action(k)

    def _on_release(self, ev: tk.Event) -> None:
        self._keys.discard(ev.keysym.lower())

    def _handle_action(self, k: str) -> None:
        if self.state == GS.MENU:
            if k in ("return", "enter"):
                self._do_fade(lambda: self._begin_level(1))
            elif k == "h":
                self.state = GS.HELP

        elif self.state == GS.HELP:
            if k in ("escape", "h"):
                self.state = GS.MENU

        elif self.state == GS.INTRO:
            if k in ("return", "enter"):
                self.ui.skip_typewriter()
                self._intro_timer = 0.0

        elif self.state == GS.PLAYING:
            if k == "r":
                self._do_fade(self._restart)
            elif k == "escape":
                self._do_fade(self._go_menu)

        elif self.state == GS.DEAD:
            if k == "r":
                self._do_fade(self._restart)
            elif k == "escape":
                self._do_fade(self._go_menu)

        elif self.state == GS.LEVEL_DONE:
            if k in ("return", "enter") and self._done_timer > 1.4:
                if self.ui._tw.is_done:
                    self._do_fade(self._advance)
                else:
                    self.ui.skip_typewriter()

        elif self.state == GS.ENDING:
            if k in ("return", "enter"):
                if self.ui._tw.is_done:
                    self._do_fade(self._go_menu)
                else:
                    self.ui.skip_typewriter()

    def _get_input(self) -> tuple[float, float]:
        k = self._keys
        dx = dy = 0.0
        if "a" in k or "left"  in k: dx -= 1.0
        if "d" in k or "right" in k: dx += 1.0
        if "w" in k or "up"    in k: dy -= 1.0
        if "s" in k or "down"  in k: dy += 1.0
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        return dx, dy

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        now = time.perf_counter()
        dt  = min(now - self._last_t, 0.05)
        self._last_t = now

        self._update(dt)
        self._render()

        self.root.after(FRAME_MS, self._loop)

    def _update(self, dt: float) -> None:
        self._tick_count += 1
        self._blink_t    += dt
        if self._blink_t > 0.5:
            self._blink_t = 0.0
            self._blink   = not self._blink

        self.particles.update(dt)
        self.fade.update(dt)

        if self._invert_flash > 0:
            self._invert_flash = max(0.0, self._invert_flash - dt)

        # shake decay
        if self._shake_rem > 0:
            self._shake_rem -= 1
            s = SHAKE_STRENGTH
            self._shake_off = (random.randint(-s, s), random.randint(-s, s))
        else:
            self._shake_off = (0, 0)

        if   self.state == GS.INTRO:       self._upd_intro(dt)
        elif self.state == GS.PLAYING:     self._upd_playing(dt)
        elif self.state == GS.DEAD:        self._upd_dead(dt)
        elif self.state == GS.LEVEL_DONE:  self._upd_done(dt)
        elif self.state == GS.ENDING:      self._ending_tick += 1

    def _upd_intro(self, dt: float) -> None:
        self.ui.update_typewriter(dt)
        self._intro_timer -= dt
        if self._intro_timer <= 0 and self.ui._tw.is_done:
            self._start_playing()
        elif self._intro_timer <= 0:
            # finished countdown — auto-skip remaining text
            self.ui.skip_typewriter()
            self._start_playing()

    def _upd_playing(self, dt: float) -> None:
        if not self.player or not self.level:
            return
        self._level_timer += dt
        self.player.tick_effects(dt)

        # narrator hint
        hint_cfg = LEVEL_HINTS.get(self.current_lvl)
        if hint_cfg and not self._hint_shown:
            self._hint_timer += dt
            if self._hint_timer >= hint_cfg[0]:
                self._hint_shown = True
                self._hint_text  = hint_cfg[1]

        dx, dy = self._get_input()
        xm, ym = self.player.get_input_multiplier()
        self.player.update(dx * xm, dy * ym, dt, self.level.walls)

        event = self.level.update(dt, self.player)
        if   event == "killed":        self._trigger_death()
        elif event == "level_complete": self._trigger_complete()
        elif event == "invert_applied":
            self._shake(4)
            self._invert_flash = 0.25

        if self.level._glitch_countdown > 0:
            self._shake(6)

    def _upd_dead(self, dt: float) -> None:
        self._death_timer += dt
        self.ui.update_typewriter(dt)
        if self.player:
            self.player._tick_death_flash(dt)

    def _upd_done(self, dt: float) -> None:
        self._done_timer += dt
        self.ui.update_typewriter(dt)

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _begin_level(self, num: int) -> None:
        self.current_lvl  = num
        self._intro_timer = 3.0
        self._hint_shown  = False
        self._hint_timer  = 0.0
        self._hint_text   = ""
        lines = LEVEL_INTROS.get(num, [f"LEVEL {num}"])
        self.ui.start_intro(lines)
        self.state = GS.INTRO

    def _start_playing(self) -> None:
        lv, start = make_level(self.current_lvl)
        self.level  = lv
        self.player = Player(*start)
        self._level_timer  = 0.0
        self._hint_shown   = False
        self._hint_timer   = 0.0
        self._hint_text    = ""
        self.state = GS.PLAYING

    def _restart(self) -> None:
        self._start_playing()

    def _trigger_death(self) -> None:
        if self.player:
            self.player.die()
            cx, cy = self.player.center
            ox, oy = self._maze_offset()
            self.particles.burst(cx + ox, cy + oy)
            self.total_deaths += 1
        self._death_timer = 0.0
        self._shake(SHAKE_FRAMES)
        lines = self.level.pick_death_message() if self.level else ["You died."]
        self.ui.start_intro(lines)   # reuse typewriter for death text
        self.state = GS.DEAD

    def _trigger_complete(self) -> None:
        self._level_score  = self._calc_score()
        self.total_score  += self._level_score
        self._done_timer   = 0.0
        lines = LEVEL_COMPLETIONS.get(self.current_lvl, ["Level complete."])
        self.ui.start_intro(lines)
        self.state = GS.LEVEL_DONE

    def _advance(self) -> None:
        nxt = self.current_lvl + 1
        if nxt > TOTAL_LEVELS:
            lines = LEVEL_COMPLETIONS.get(5, [])
            self.ui.start_intro(lines)
            self._ending_tick = 0
            self.state = GS.ENDING
        else:
            self._begin_level(nxt)

    def _go_menu(self) -> None:
        self.total_score  = 0
        self.total_deaths = 0
        self.current_lvl  = 1
        self.level  = None
        self.player = None
        self.state  = GS.MENU

    def _do_fade(self, callback: Callable) -> None:
        if not self.fade.active:
            self.fade.start(callback)

    def _calc_score(self) -> int:
        deaths    = self.player.deaths if self.player else 0
        base      = SCORE_BASE * self.current_lvl
        time_bon  = max(0, int((60 - self._level_timer) * SCORE_TIME_BONUS))
        death_pen = deaths * SCORE_DEATH_PEN
        return max(0, base + time_bon - death_pen)

    def _shake(self, frames: int) -> None:
        self._shake_rem = max(self._shake_rem, frames)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self) -> None:
        self.canvas.delete("all")
        ox, oy = self._shake_off

        if   self.state == GS.MENU:
            self.ui.draw_main_menu(self._blink, self._tick_count)

        elif self.state == GS.HELP:
            self.ui.draw_help()

        elif self.state == GS.INTRO:
            self.ui.draw_level_intro(max(0.0, self._intro_timer))

        elif self.state in (GS.PLAYING, GS.DEAD):
            self._draw_maze(ox, oy)
            if self.state == GS.PLAYING:
                self._draw_player(ox, oy)
            elif self.player:
                self._draw_player_dead(ox, oy)
            self.particles.render(self.canvas)
            self.ui.draw_scanlines()

            if self.state == GS.PLAYING:
                invert_rem = self.player.effects.get("invert_controls", 0.0) if self.player else 0.0
                self.ui.draw_hud(
                    self.current_lvl, self._level_timer, self.total_score,
                    self.player.deaths if self.player else 0,
                    "", self._hint_text if self._hint_shown else "",
                    invert_rem,
                )
                if self._invert_flash > 0:
                    self.ui.draw_invert_flash(self._invert_flash * 4)
            elif self.state == GS.DEAD:
                self.ui.draw_death([], self._death_timer)

        elif self.state == GS.LEVEL_DONE:
            self._draw_maze(0, 0)
            self.ui.draw_scanlines()
            self.ui.draw_level_complete(self._level_score)

        elif self.state == GS.ENDING:
            self.ui.draw_ending(self._ending_tick)

        # fade on top of everything
        if self.fade.active:
            self.ui.draw_fade(self.fade.alpha)

    # ------------------------------------------------------------------
    # Maze / player rendering
    # ------------------------------------------------------------------

    def _maze_offset(self) -> tuple[int, int]:
        if not self.level:
            return 0, 0
        mw = self.level.cols * TILE_SIZE
        mh = self.level.rows * TILE_SIZE
        ox = (CANVAS_W - mw) // 2
        oy = max(44, (CANVAS_H - mh) // 2)   # leave room for HUD bar
        return ox, oy

    def _draw_maze(self, sx: int = 0, sy: int = 0) -> None:
        if not self.level:
            return
        ox, oy = self._maze_offset()
        ox += sx; oy += sy

        self.canvas.create_rectangle(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")

        t = time.perf_counter()

        for entity in self.level.get_renderables():
            ex = entity.gx * TILE_SIZE + ox
            ey = entity.gy * TILE_SIZE + oy

            if isinstance(entity, Wall):
                w: Wall = entity
                if w.ghost:
                    if w.flash_frames > 0:
                        # glitch flash: alternate bright/dark
                        col = "#ffffff" if w.flash_frames % 4 < 2 else "#ff00ff"
                        self.canvas.create_rectangle(
                            ex, ey, ex+TILE_SIZE, ey+TILE_SIZE,
                            fill=col, outline="",
                        )
                    # invisible walls are invisible once flash done
                else:
                    self.canvas.create_rectangle(
                        ex, ey, ex+TILE_SIZE, ey+TILE_SIZE,
                        fill="#d4d4d4", outline="#999999", width=1,
                    )

            elif isinstance(entity, FakeExit):
                self._draw_exit_tile(ex, ey, "#00cc44", is_fake=True)

            elif isinstance(entity, (Exit, MovingExit)):
                if isinstance(entity, MovingExit):
                    # ghost trail
                    for i, (tgx, tgy) in enumerate(entity.ghost_trail):
                        a = (i + 1) / (len(entity.ghost_trail) + 1)
                        v = int(a * 60)
                        trail_col = f"#00{v:02x}44"
                        tx = tgx * TILE_SIZE + ox
                        ty = tgy * TILE_SIZE + oy
                        self.canvas.create_rectangle(
                            tx+4, ty+4, tx+TILE_SIZE-4, ty+TILE_SIZE-4,
                            fill=trail_col, outline="",
                        )
                pulse_col = self._pulse_green(t)
                self._draw_exit_tile(ex, ey, pulse_col, is_fake=False)

            elif isinstance(entity, TriggerTile):
                self.canvas.create_rectangle(
                    ex+2, ey+2, ex+TILE_SIZE-2, ey+TILE_SIZE-2,
                    fill="#1a001a", outline="",
                )

    def _pulse_green(self, t: float) -> str:
        v = int(160 + 95 * math.sin(t * 5.0))
        v = max(0, min(255, v))
        return f"#00{v:02x}44"

    def _draw_exit_tile(self, ex: float, ey: float, color: str, is_fake: bool) -> None:
        ts = TILE_SIZE
        # glow layers
        glow_colors = ["#003322", "#005533", color]
        margins     = [0, 2, 4]
        for col, m in zip(glow_colors, margins):
            self.canvas.create_rectangle(
                ex+m, ey+m, ex+ts-m, ey+ts-m,
                fill=col, outline="",
            )
        # label
        self.canvas.create_text(
            ex + ts//2, ey + ts//2, text="EXIT",
            font=("Courier", 6, "bold"), fill="#000000",
        )

    def _draw_player(self, sx: int, sy: int) -> None:
        if not self.player or not self.player.alive:
            return
        ox, oy = self._maze_offset()
        ox += sx; oy += sy

        p    = self.player
        cx   = p.gx * TILE_SIZE + TILE_SIZE / 2 + ox
        cy   = p.gy * TILE_SIZE + TILE_SIZE / 2 + oy
        bob  = math.sin(p.bob_timer) * 1.2
        cy  += bob

        hw   = (PLAYER_SIZE / 2) * p.squish_x
        hh   = (PLAYER_SIZE / 2) * p.squish_y

        # trail shadow
        self.canvas.create_rectangle(
            cx - hw + 2, cy - hh + 2, cx + hw + 2, cy + hh + 2,
            fill="#220000", outline="",
        )

        color = p.color
        if p.has_effect("invert_controls"):
            v = int(140 + 115 * abs(math.sin(time.perf_counter() * 9)))
            color = f"#{v:02x}00{v:02x}"

        self.canvas.create_rectangle(
            cx - hw, cy - hh, cx + hw, cy + hh,
            fill=color, outline="#ff8888", width=1,
        )

        # facing dot
        fd = {"right":(6,0),"left":(-6,0),"down":(0,6),"up":(0,-6)}.get(p.facing,(0,0))
        r  = 2.5
        self.canvas.create_oval(
            cx+fd[0]-r, cy+fd[1]-r, cx+fd[0]+r, cy+fd[1]+r,
            fill="#ffffff", outline="",
        )

    def _draw_player_dead(self, sx: int, sy: int) -> None:
        if not self.player:
            return
        ox, oy = self._maze_offset()
        ox += sx; oy += sy
        p    = self.player
        cx   = p.gx * TILE_SIZE + TILE_SIZE / 2 + ox
        cy   = p.gy * TILE_SIZE + TILE_SIZE / 2 + oy
        if p.flash_timer > 0:
            col = p.death_flash_color()
            hw = hh = PLAYER_SIZE / 2
            self.canvas.create_rectangle(
                cx-hw, cy-hh, cx+hw, cy+hh,
                fill=col, outline="",
            )
