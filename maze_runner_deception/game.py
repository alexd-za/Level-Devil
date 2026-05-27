from __future__ import annotations
import tkinter as tk
import time
import math
import random
from typing import Optional, Callable
from dataclasses import dataclass, field

import sound
from entities import (
    Player, Wall, FakeWall, Exit, FakeExit, TriggerTile, MovingExit,
    Note, Enemy, TILE_SIZE, PLAYER_SIZE, PLAYER_GAP,
)
from levels import (
    Level, make_level,
    LEVEL_INTROS, LEVEL_COMPLETIONS, LEVEL_HINTS, LEVEL_ENDING,
    INTRO_TEXT, LAB_MESSAGES,
)
from ui import UIManager, CANVAS_W, CANVAS_H, BG, HUD_H
from leaderboard import save_score, top_scores

FRAME_MS     = 16
TOTAL_LEVELS = 5

SCORE_BASE       = 6000
SCORE_TIME_BONUS = 120
SCORE_DEATH_PEN  = 400

SHAKE_FRAMES   = 10
SHAKE_STRENGTH = 6

DARK_RADIUS    = 5.5   # tiles visible when darkness is active


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

class Camera:
    LERP_SPD = 9.0

    def __init__(self):
        self._x: float = 0.0
        self._y: float = 0.0
        self._map_w: int = 0
        self._map_h: int = 0

    def set_map(self, map_w_px: int, map_h_px: int) -> None:
        self._map_w = map_w_px
        self._map_h = map_h_px

    def snap(self, px: float, py: float) -> None:
        self._x = self._clamp_x(px - CANVAS_W / 2)
        self._y = self._clamp_y(py - (CANVAS_H - HUD_H) / 2)

    def follow(self, px: float, py: float, dt: float) -> None:
        tx = self._clamp_x(px - CANVAS_W / 2)
        ty = self._clamp_y(py - (CANVAS_H - HUD_H) / 2)
        self._x += (tx - self._x) * self.LERP_SPD * dt
        self._y += (ty - self._y) * self.LERP_SPD * dt

    def _clamp_x(self, x: float) -> float:
        if self._map_w <= CANVAS_W:
            return -(CANVAS_W - self._map_w) / 2
        return max(0.0, min(x, self._map_w - CANVAS_W))

    def _clamp_y(self, y: float) -> float:
        h = CANVAS_H - HUD_H
        if self._map_h <= h:
            return -(h - self._map_h) / 2
        return max(0.0, min(y, self._map_h - h))

    @property
    def ox(self) -> int:
        return int(-self._x)

    @property
    def oy(self) -> int:
        return int(-self._y) + HUD_H

    def visible_tile_range(self) -> tuple[int, int, int, int]:
        cs = max(0, int(self._x / TILE_SIZE) - 1)
        rs = max(0, int(self._y / TILE_SIZE) - 1)
        ce = cs + int(CANVAS_W / TILE_SIZE) + 4
        re = rs + int((CANVAS_H - HUD_H) / TILE_SIZE) + 4
        return cs, rs, ce, re


# ---------------------------------------------------------------------------
# Particle system
# ---------------------------------------------------------------------------

@dataclass
class Particle:
    x: float; y: float
    vx: float; vy: float
    life: float; max_life: float
    size: float; color: str


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def burst(self, px: float, py: float,
              color: str = "#ff3333", count: int = 16) -> None:
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(55, 175)
            ml    = random.uniform(0.3, 0.7)
            self.particles.append(Particle(
                x=px, y=py,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=ml, max_life=ml,
                size=random.uniform(2.0, 5.0),
                color=color,
            ))

    def update(self, dt: float) -> None:
        for p in self.particles:
            p.x  += p.vx * dt
            p.y  += p.vy * dt
            p.vy += 240 * dt
            p.vx *= 0.95
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0]

    def render(self, canvas: tk.Canvas) -> None:
        for p in self.particles:
            a  = max(0.0, p.life / p.max_life)
            s  = p.size * a
            # fade to black using base color lightness
            try:
                r = int(int(p.color[1:3], 16) * a)
                g = int(int(p.color[3:5], 16) * a)
                b = int(int(p.color[5:7], 16) * a)
                col = f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                col = p.color
            canvas.create_rectangle(
                p.x - s, p.y - s, p.x + s, p.y + s,
                fill=col, outline="",
            )


# ---------------------------------------------------------------------------
# Fade transition
# ---------------------------------------------------------------------------

class FadeTransition:
    SPEED = 3.5

    def __init__(self):
        self.alpha    = 0.0
        self._dir     = 0
        self._callback: Optional[Callable] = None
        self._called  = False

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
    PAUSED      = "paused"
    READING     = "reading"
    DEAD        = "dead"
    LEVEL_DONE  = "level_done"
    ENDING      = "ending"
    LEADERBOARD = "leaderboard"


# ---------------------------------------------------------------------------
# GameController
# ---------------------------------------------------------------------------

class GameController:
    def __init__(self, root: tk.Tk, canvas: tk.Canvas):
        self.root   = root
        self.canvas = canvas
        self.ui     = UIManager(canvas)

        sound.init()

        self.particles = ParticleSystem()
        self.fade      = FadeTransition()
        self.camera    = Camera()

        self._keys: set[str] = set()
        self._bind_keys()

        self.total_score  = 0
        self.total_deaths = 0
        self.current_lvl  = 1
        self.total_notes_found = 0

        self._session_flags: dict = {}

        self.state:  str             = GS.MENU
        self.level:  Optional[Level] = None
        self.player: Optional[Player] = None

        self._level_timer  = 0.0
        self._death_timer  = 0.0
        self._done_timer   = 0.0
        self._ending_tick  = 0
        self._level_score  = 0

        self._hint_text    = ""
        self._hint_shown   = False
        self._hint_timer   = 0.0

        self._invert_flash  = 0.0
        self._powerup_flash = 0.0
        self._glitch_frames = 0

        self._static_timer: float = 0.0
        self._paranoia_seed: int  = 0
        self._paranoia_flip_t: float = 0.0

        self._shake_rem = 0
        self._shake_off = (0, 0)

        self._blink_t   = 0.0
        self._blink     = True
        self._tick_count = 0

        self._note_lines: list[str] = []

        self._lab_msg: str      = ""
        self._lab_msg_timer: float = 0.0
        self._lab_msg_kind: str = ""

        self._leaderboard_scores: list[dict] = []

        self._admin_mode: bool  = False
        self._admin_noclip: bool = False
        self._admin_speed: bool  = False

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
        if k in ("quoteleft", "asciitilde", "dead_grave") or ev.char in ("`", "~"):
            k = "grave"
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
            elif k == "l":
                self._leaderboard_scores = top_scores()
                self.state = GS.LEADERBOARD

        elif self.state == GS.HELP:
            if k in ("escape", "h"):
                self.state = GS.MENU

        elif self.state == GS.LEADERBOARD:
            if k in ("escape", "l", "return", "enter"):
                self.state = GS.MENU

        elif self.state == GS.INTRO:
            if k in ("return", "enter"):
                if not self.ui._tw.is_done:
                    self.ui.skip_typewriter()
                else:
                    self._do_fade(self._start_playing)

        elif self.state == GS.PLAYING:
            if k == "r":
                self._do_fade(self._restart)
            elif k in ("escape", "p"):
                self.state = GS.PAUSED
            elif k == "grave":
                self._admin_mode = not self._admin_mode
            elif self._admin_mode:
                self._handle_admin_key(k)

        elif self.state == GS.PAUSED:
            if k in ("escape", "p"):
                self.state = GS.PLAYING
            elif k == "m":
                self._do_fade(self._go_menu)
            elif k == "grave":
                self._admin_mode = not self._admin_mode
            elif self._admin_mode:
                self._handle_admin_key(k)

        elif self.state == GS.READING:
            if k in ("return", "enter", "escape", "space"):
                self.state = GS.PLAYING

        elif self.state == GS.DEAD:
            if k in ("return", "enter", "r"):
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
            self._invert_flash  = max(0.0, self._invert_flash - dt)
        if self._powerup_flash > 0:
            self._powerup_flash = max(0.0, self._powerup_flash - dt)
        if self._lab_msg_timer > 0:
            self._lab_msg_timer = max(0.0, self._lab_msg_timer - dt)
        if self._static_timer > 0:
            self._static_timer  = max(0.0, self._static_timer - dt)
            if self._static_timer > 0:
                self._shake(4)

        if self._shake_rem > 0:
            self._shake_rem -= 1
            s = SHAKE_STRENGTH
            self._shake_off = (random.randint(-s, s), random.randint(-s, s))
        else:
            self._shake_off = (0, 0)

        if   self.state == GS.INTRO:      self._upd_intro(dt)
        elif self.state == GS.PLAYING:    self._upd_playing(dt)
        elif self.state == GS.DEAD:       self._upd_dead(dt)
        elif self.state == GS.LEVEL_DONE: self._upd_done(dt)
        elif self.state == GS.ENDING:
            self._ending_tick += 1
            self.ui.update_typewriter(dt)

    def _upd_intro(self, dt: float) -> None:
        self.ui.update_typewriter(dt)

    def _upd_playing(self, dt: float) -> None:
        if not self.player or not self.level:
            return
        self._level_timer += dt
        self.player.tick_effects(dt)

        if self.player.has_effect("paranoia"):
            self._paranoia_flip_t += dt
            if self._paranoia_flip_t > 0.35:
                self._paranoia_flip_t = 0.0
                self._paranoia_seed = random.randint(0, 9999)

        hint_cfg = LEVEL_HINTS.get(self.current_lvl)
        if hint_cfg and not self._hint_shown:
            self._hint_timer += dt
            if self._hint_timer >= hint_cfg[0]:
                self._hint_shown = True
                self._hint_text  = hint_cfg[1]

        dx, dy = self._get_input()
        xm, ym = self.player.get_input_multiplier()
        self.player.update(dx * xm, dy * ym, dt, self.level._wall_map)

        px_world = self.player.gx * TILE_SIZE + TILE_SIZE / 2
        py_world = self.player.gy * TILE_SIZE + TILE_SIZE / 2
        self.camera.follow(px_world, py_world, dt)

        event = self.level.update(dt, self.player)
        if event == "killed":
            if self.player and self.player.has_effect("shield"):
                del self.player.effects["shield"]
                self._shake(6)
                self._invert_flash = 0.2
            else:
                self._trigger_death()
        elif event == "level_complete":
            self._trigger_complete()
        elif event == "invert_applied":
            self._shake(8)
            self._invert_flash = 0.6
            sound.play("trigger")
            self._set_lab_msg("invert_controls")
        elif event == "darkness_applied":
            self._shake(5)
            sound.play("trigger")
            self._set_lab_msg("darkness")
        elif event == "speed_boost":
            self._shake(3)
            self._powerup_flash = 0.5
            sound.play("powerup")
            self._set_lab_msg("speed_boost")
        elif event == "shield":
            self._shake(3)
            self._powerup_flash = 0.5
            sound.play("shield")
            self._set_lab_msg("shield")
        elif event == "slow_motion":
            self._shake(5)
            self._powerup_flash = 0.3
            sound.play("slow")
            self._set_lab_msg("slow_motion")
        elif event == "paranoia_applied":
            self._shake(6)
            self._invert_flash = 0.3
            sound.play("glitch")
            self._set_lab_msg("paranoia")
        elif event == "gravity_applied":
            self._shake(5)
            self._invert_flash = 0.25
            sound.play("glitch")
            self._set_lab_msg("gravity")
        elif event == "static_burst":
            self._shake(14)
            self._static_timer = 1.5
            sound.play("static")
            self._set_lab_msg("static")
        elif event == "note_collected":
            if self.level._last_note:
                self._note_lines = list(self.level._last_note)
            self.total_score += 800
            self.total_notes_found += 1
            sound.play("note")
            self.state = GS.READING

        if self.level._glitch_countdown > 0:
            self._shake(8)

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
        self._hint_shown  = False
        self._hint_timer  = 0.0
        self._hint_text   = ""
        lines = LEVEL_INTROS.get(num, [f"LEVEL {num}"])
        self.ui.start_intro(lines)
        self.state = GS.INTRO

    def _start_playing(self) -> None:
        lv, start = make_level(self.current_lvl, self._session_flags)
        self.level  = lv
        self.player = Player(*start)
        mw, mh      = lv.pixel_size()
        self.camera.set_map(mw, mh)
        px0 = start[0] * TILE_SIZE + TILE_SIZE / 2
        py0 = start[1] * TILE_SIZE + TILE_SIZE / 2
        self.camera.snap(px0, py0)
        self._level_timer  = 0.0
        self._hint_shown   = False
        self._hint_timer   = 0.0
        self._hint_text    = ""
        self.state = GS.PLAYING

    def _restart(self) -> None:
        self._start_playing()

    def _trigger_death(self) -> None:
        sound.play("death")
        if self.player:
            self.player.die()
            cx, cy = self.player.center
            ox, oy = self.camera.ox, self.camera.oy
            px_screen = cx + ox
            py_screen = cy + oy
            self.particles.burst(px_screen, py_screen, "#ff3333", 18)
            self.total_deaths += 1
        if (self.level and self.current_lvl == 1
                and self.level._last_event_cause == "trap"):
            self._session_flags["l1_fake_seen"] = True
        self._death_timer = 0.0
        self._shake(SHAKE_FRAMES)
        lines = self.level.pick_death_message() if self.level else ["You died."]
        self.ui.start_intro(lines)
        self.state = GS.DEAD

    def _trigger_complete(self) -> None:
        sound.play("level_done")
        self._level_score = self._calc_score()
        self.total_score += self._level_score
        self._done_timer  = 0.0
        lines = LEVEL_COMPLETIONS.get(self.current_lvl, ["Level complete."])
        self.ui.start_intro(lines)
        self.state = GS.LEVEL_DONE

    def _advance(self) -> None:
        nxt = self.current_lvl + 1
        if nxt > TOTAL_LEVELS:
            self._prompt_leaderboard()
            ending_text = list(LEVEL_ENDING)
            if self.total_notes_found >= 8:
                ending_text = ending_text + [
                    "",
                    "ORACLE ADDENDUM:",
                    "Subject 47 recovered all 8 classified documents.",
                    "This was not anticipated.",
                    "We are impressed.",
                    "(We are also somewhat concerned.)",
                ]
            self.ui.start_intro(ending_text)
            self._ending_tick = 0
            self.state = GS.ENDING
        else:
            self._begin_level(nxt)

    def _prompt_leaderboard(self) -> None:
        import tkinter.simpledialog as sd
        name = sd.askstring(
            "FACILITY RECORDS",
            f"Subject 47 — Final score: {self.total_score:,}\n"
            f"Total deaths: {self.total_deaths}\n\n"
            "Enter your name for the leaderboard:",
            parent=self.root,
        )
        if name and name.strip():
            save_score(name.strip(), self.total_score, self.total_deaths)

    def _go_menu(self) -> None:
        self.total_score       = 0
        self.total_deaths      = 0
        self.current_lvl       = 1
        self.total_notes_found = 0
        self._session_flags    = {}
        self.level  = None
        self.player = None
        self.state  = GS.MENU

    def _do_fade(self, callback: Callable) -> None:
        if not self.fade.active:
            self.fade.start(callback)

    def _calc_score(self) -> int:
        deaths   = self.player.deaths if self.player else 0
        base     = SCORE_BASE * self.current_lvl
        time_bon = max(0, int((90 - self._level_timer) * SCORE_TIME_BONUS))
        death_pen = deaths * SCORE_DEATH_PEN
        return max(0, base + time_bon - death_pen)

    def _shake(self, frames: int) -> None:
        self._shake_rem = max(self._shake_rem, frames)

    def _set_lab_msg(self, effect: str) -> None:
        msgs = LAB_MESSAGES.get(effect)
        if msgs:
            self._lab_msg       = random.choice(msgs)
            self._lab_msg_timer = 5.0
            self._lab_msg_kind  = effect

    def _handle_admin_key(self, k: str) -> None:
        if k == "n" and self.player:
            self._admin_noclip = not self._admin_noclip
            self.player.noclip = self._admin_noclip
        elif k == "b" and self.player:
            self._admin_speed = not self._admin_speed
            if self._admin_speed:
                self.player.apply_effect("speed_boost", 9999.0)
            else:
                self.player.effects.pop("speed_boost", None)
        elif k == "k" and self.level:
            for e in self.level.enemies:
                e.alive = False
        elif k == "c" and self.level and self.player:
            for note in self.level.notes:
                if not note.collected:
                    note.collected = True
                    self.player.notes_found += 1
                    self.total_score += 800
                    self.total_notes_found += 1
        elif k in ("1", "2", "3", "4", "5"):
            self._do_fade(lambda n=int(k): self._begin_level(n))

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self) -> None:
        self.canvas.delete("all")
        ox, oy = self._shake_off

        if self.state == GS.MENU:
            self.ui.draw_main_menu(self._blink, self._tick_count)

        elif self.state == GS.HELP:
            self.ui.draw_help()

        elif self.state == GS.INTRO:
            self.ui.draw_level_intro()

        elif self.state in (GS.PLAYING, GS.DEAD, GS.PAUSED, GS.READING):
            self._draw_world(ox, oy)
            self.particles.render(self.canvas)

            if self.state in (GS.PLAYING, GS.PAUSED, GS.READING):
                eff = self.player.effects if self.player else {}
                invert_rem  = eff.get("invert_controls", 0.0)
                dark_rem    = eff.get("darkness",        0.0)
                speed_rem   = eff.get("speed_boost",     0.0)
                shield_rem  = eff.get("shield",          0.0)
                slow_rem    = eff.get("slow_motion",     0.0)
                paranoia_rem = eff.get("paranoia",       0.0)
                gravity_rem = eff.get("gravity",         0.0)

                disp_timer  = self._level_timer
                disp_score  = self.total_score
                disp_deaths = self.player.deaths if self.player else 0
                if paranoia_rem > 0:
                    _pr = random.Random(self._paranoia_seed)
                    disp_timer  = max(0.0, self._level_timer + _pr.uniform(-25, 50))
                    disp_score  = max(0, self.total_score + _pr.randint(-6000, 2000))
                    disp_deaths = max(0, disp_deaths + _pr.randint(-1, 4))

                self.ui.draw_hud(
                    self.current_lvl, disp_timer, disp_score,
                    disp_deaths,
                    self._hint_text if self._hint_shown else "",
                    invert_rem, dark_rem, speed_rem, shield_rem,
                    self.player.notes_found if self.player else 0,
                    self._lab_msg if self._lab_msg_timer > 0 else "",
                    self._lab_msg_timer,
                    self._lab_msg_kind,
                    slow_rem, paranoia_rem, gravity_rem,
                )
                if self._invert_flash > 0:
                    self.ui.draw_invert_flash(self._invert_flash * 3)
                if self._powerup_flash > 0:
                    self.ui.draw_powerup_flash(self._powerup_flash * 3)
                if self.state == GS.PAUSED:
                    self.ui.draw_pause()
                elif self.state == GS.READING and self._note_lines:
                    self.ui.draw_note_reading(self._note_lines)

            elif self.state == GS.DEAD:
                self.ui.draw_death(self._death_timer)

        elif self.state == GS.LEVEL_DONE:
            self._draw_world(0, 0)
            self.ui.draw_level_complete(self._level_score)

        elif self.state == GS.ENDING:
            self.ui.draw_ending(self._ending_tick)

        elif self.state == GS.LEADERBOARD:
            self.ui.draw_leaderboard(self._leaderboard_scores)

        if self._admin_mode:
            noclip_flag = self.player.noclip if self.player else False
            self.ui.draw_admin_panel(
                self.current_lvl, self._admin_noclip, self._admin_speed,
            )

        if self.fade.active:
            self.ui.draw_fade(self.fade.alpha)

    # ------------------------------------------------------------------
    # World rendering
    # ------------------------------------------------------------------

    def _draw_world(self, sx: int, sy: int) -> None:
        if not self.level:
            return
        ox = self.camera.ox + sx
        oy = self.camera.oy + sy
        cs, rs, ce, re = self.camera.visible_tile_range()
        ce = min(ce, self.level.cols)
        re = min(re, self.level.rows)

        self.canvas.create_rectangle(0, 0, CANVAS_W, CANVAS_H, fill=BG, outline="")
        self.ui.draw_starfield_raw(self.canvas, self._tick_count)
        self.canvas.create_rectangle(
            0, HUD_H, CANVAS_W, CANVAS_H, fill="#0a0a10", outline="")

        t = time.perf_counter()

        x0 = cs * TILE_SIZE + ox
        y0 = rs * TILE_SIZE + oy
        x1 = ce * TILE_SIZE + ox
        y1 = re * TILE_SIZE + oy
        for gx in range(cs, ce + 1):
            lx = gx * TILE_SIZE + ox
            self.canvas.create_line(lx, y0, lx, y1, fill="#2c2c3e", width=1)
        for gy in range(rs, re + 1):
            ly = gy * TILE_SIZE + oy
            self.canvas.create_line(x0, ly, x1, ly, fill="#2c2c3e", width=1)

        # Walls (viewport culled via wall_map)
        max_coord = self.level.cols + self.level.rows
        for gy in range(rs, re):
            for gx in range(cs, ce):
                key = (gx, gy)
                if key not in self.level._wall_map:
                    continue
                w = self.level._wall_map[key]
                ex = gx * TILE_SIZE + ox
                ey = gy * TILE_SIZE + oy
                self._draw_wall_tile(w, ex, ey, gx, gy, max_coord)

        # Ghost trails for moving exit
        if self.level.moving_exit:
            me = self.level.moving_exit
            for i, (tgx, tgy) in enumerate(me.ghost_trail):
                a = (i + 1) / (len(me.ghost_trail) + 1)
                v = int(a * 55)
                trail_col = f"#00{v:02x}33"
                tx = tgx * TILE_SIZE + ox
                ty = tgy * TILE_SIZE + oy
                self.canvas.create_rectangle(
                    tx + 5, ty + 5, tx + TILE_SIZE - 5, ty + TILE_SIZE - 5,
                    fill=trail_col, outline="",
                )

        # Exits
        for ex_ent in self.level.exits:
            if ex_ent.visible:
                ex = ex_ent.gx * TILE_SIZE + ox
                ey = ex_ent.gy * TILE_SIZE + oy
                self._draw_exit_tile(ex, ey, self._pulse_green(t), is_fake=False)

        if self.level.moving_exit:
            me = self.level.moving_exit
            ex = me.gx * TILE_SIZE + ox
            ey = me.gy * TILE_SIZE + oy
            self._draw_exit_tile(ex, ey, self._pulse_green(t), is_fake=False)

        for fe in self.level.fake_exits:
            if fe.visible:
                ex = fe.gx * TILE_SIZE + ox
                ey = fe.gy * TILE_SIZE + oy
                self._draw_exit_tile(ex, ey, "#00cc44", is_fake=True)

        # Notes
        for note in self.level.notes:
            if not note.collected:
                nx = note.gx * TILE_SIZE + ox
                ny = note.gy * TILE_SIZE + oy
                self._draw_note_icon(nx, ny, t)

        # Enemies
        for enemy in self.level.enemies:
            if enemy.alive:
                self._draw_enemy(enemy, ox, oy, t)

        # Player
        if self.player:
            if self.player.alive:
                self._draw_player(ox, oy, t)
            elif self.player.flash_timer > 0:
                self._draw_player_dead(ox, oy)

        # Darkness overlay
        if self.player and self.player.has_effect("darkness"):
            self._draw_darkness(ox, oy, cs, rs, ce, re, t)

        # Static burst overlay
        if self._static_timer > 0:
            self.ui.draw_static_overlay(min(1.0, self._static_timer / 0.6))

    # ------------------------------------------------------------------
    # Tile rendering helpers
    # ------------------------------------------------------------------

    def _draw_wall_tile(self, w: Wall, ex: float, ey: float,
                         gx: int, gy: int, max_coord: int) -> None:
        ts = TILE_SIZE
        if w.ghost:
            if w.flash_frames > 0:
                col = "#e0e0ff" if w.flash_frames % 4 < 2 else "#ff00cc"
                self.canvas.create_rectangle(
                    ex, ey, ex + ts, ey + ts, fill=col, outline="")
            return

        zone = (gx + gy) / max_coord
        r = int(0x68 + zone * 0x18)
        g = int(0x64 + zone * 0x14)
        b = int(0x72 + zone * 0x1c)

        if getattr(w, 'is_fake', False):
            b = min(255, b + 15)

        base_col = f"#{r:02x}{g:02x}{b:02x}"

        hl_r = min(255, r + 0x22)
        hl_g = min(255, g + 0x1c)
        hl_b = min(255, b + 0x26)
        hl_col = f"#{hl_r:02x}{hl_g:02x}{hl_b:02x}"

        sh_r = max(0, r - 0x18)
        sh_g = max(0, g - 0x14)
        sh_b = max(0, b - 0x1a)
        sh_col = f"#{sh_r:02x}{sh_g:02x}{sh_b:02x}"

        self.canvas.create_rectangle(
            ex, ey, ex + ts, ey + ts, fill=base_col, outline="")
        self.canvas.create_line(ex, ey, ex + ts, ey, fill=hl_col)
        self.canvas.create_line(ex, ey, ex, ey + ts, fill=hl_col)
        self.canvas.create_line(ex, ey + ts - 1, ex + ts, ey + ts - 1,
                                fill=sh_col)
        self.canvas.create_line(ex + ts - 1, ey, ex + ts - 1, ey + ts,
                                fill=sh_col)

    def _pulse_green(self, t: float) -> str:
        v = int(160 + 95 * math.sin(t * 5.0))
        v = max(0, min(255, v))
        return f"#00{v:02x}55"

    def _draw_exit_tile(self, ex: float, ey: float,
                         color: str, is_fake: bool) -> None:
        ts  = TILE_SIZE
        cx  = ex + ts // 2
        cy  = ey + ts // 2
        # Outer glow ring
        self.canvas.create_rectangle(
            ex, ey, ex + ts, ey + ts,
            fill="#001a0d", outline=color, width=2,
        )
        # Inner bright square
        self.canvas.create_rectangle(
            ex + 4, ey + 4, ex + ts - 4, ey + ts - 4,
            fill="#003820", outline="",
        )
        # Arrow symbol — clearly readable
        self.canvas.create_text(
            cx, cy, text="▶",
            font=("TkDefaultFont", 11, "bold"), fill=color,
        )

    def _draw_note_icon(self, nx: float, ny: float, t: float) -> None:
        ts    = TILE_SIZE
        pulse = 0.5 + 0.5 * math.sin(t * 3.5)
        v     = int(0x99 + pulse * 0x66)
        col   = f"#{v:02x}{int(v * 0.75):02x}00"
        glow  = f"#{min(255, v + 30):02x}{int((v + 20) * 0.5):02x}00"
        cx = nx + ts // 2
        cy = ny + ts // 2

        # Outer glow
        self.canvas.create_rectangle(
            nx + 3, ny + 2, nx + ts - 3, ny + ts - 2,
            fill="", outline=col, width=1,
        )
        # Paper body
        self.canvas.create_rectangle(
            nx + 5, ny + 4, nx + ts - 5, ny + ts - 4,
            fill="#100d00", outline=glow, width=1,
        )
        # Corner fold indicator
        self.canvas.create_polygon(
            nx + ts - 5, ny + 4,
            nx + ts - 5, ny + 9,
            nx + ts - 10, ny + 4,
            fill="#1e1600", outline=col, width=1,
        )
        # Lines on paper
        for i in range(3):
            ly = ny + 9 + i * 4
            lx0 = nx + 6 + (3 if i == 0 else 0)
            self.canvas.create_line(
                lx0, ly, nx + ts - 6, ly, fill=col, width=1,
            )
        # Exclamation / glow dot
        self.canvas.create_oval(
            cx - 2, cy + 3, cx + 2, cy + 7,
            fill=glow, outline="",
        )


    # ------------------------------------------------------------------
    # Enemy rendering
    # ------------------------------------------------------------------

    def _draw_enemy(self, enemy: Enemy, ox: int, oy: int, t: float) -> None:
        cx = enemy.gx_f * TILE_SIZE + TILE_SIZE / 2 + ox
        cy = enemy.gy_f * TILE_SIZE + TILE_SIZE / 2 + oy

        at = enemy._anim_timer
        in_wall = self.level._wall_map.get((int(enemy.gx_f), int(enemy.gy_f))) is not None

        pulse = 0.5 + 0.5 * math.sin(at * 5.0)
        glow_r = int(80 + pulse * 120)
        glow_col = f"#{glow_r:02x}0000"

        # Outer threat ring
        pr = 12 + math.sin(at * 3.0) * 1.5
        self.canvas.create_oval(
            cx - pr - 1, cy - pr - 1, cx + pr + 1, cy + pr + 1,
            fill="", outline=glow_col, width=1,
        )

        # Hexagonal drone body (6 pts)
        hw = 8.5
        ang_off = at * 0.8
        hex_pts = []
        for i in range(6):
            ang = ang_off + i * math.pi / 3
            hex_pts += [cx + hw * math.cos(ang), cy + hw * math.sin(ang)]
        self.canvas.create_polygon(hex_pts, fill="#3a0000", outline="#bb1100", width=1)

        # Inner core
        self.canvas.create_rectangle(
            cx - 5, cy - 5, cx + 5, cy + 5,
            fill="#660000", outline="#ff2200", width=1,
        )
        self.canvas.create_rectangle(
            cx - 2, cy - 2, cx + 2, cy + 2,
            fill="#ff0000", outline="",
        )

        # Rotating scanner arm
        scan_ang = at * 4.2
        scan_len = 10
        sx = cx + math.cos(scan_ang) * scan_len
        sy = cy + math.sin(scan_ang) * scan_len
        beam_v = int(120 + pulse * 135)
        self.canvas.create_line(
            cx, cy, sx, sy,
            fill=f"#{beam_v:02x}0000", width=1,
        )
        self.canvas.create_oval(
            sx - 2, sy - 2, sx + 2, sy + 2,
            fill="#ff3300", outline="",
        )

        # Three LED status dots (triangle pattern)
        for i, (lax, lay) in enumerate([
            (cx - 3.5, cy - 6.5),
            (cx + 3.5, cy - 6.5),
            (cx,       cy - 8.5),
        ]):
            phase = (at * 3.0 + i * 1.05) % (math.pi * 2)
            led_v = int(180 + 75 * math.sin(phase))
            led_col = f"#{led_v:02x}0000"
            self.canvas.create_oval(
                lax - 1.2, lay - 1.2, lax + 1.2, lay + 1.2,
                fill=led_col, outline="",
            )

        if in_wall:
            self.canvas.create_oval(
                cx - hw - 3, cy - hw - 3, cx + hw + 3, cy + hw + 3,
                fill="#000000", outline="", stipple="gray50",
            )

    # ------------------------------------------------------------------
    # Player rendering
    # ------------------------------------------------------------------

    def _draw_player(self, ox: int, oy: int, t: float) -> None:
        p  = self.player
        bob = math.sin(p.bob_timer) * 1.4
        cx = p.gx * TILE_SIZE + TILE_SIZE / 2 + ox
        cy = p.gy * TILE_SIZE + TILE_SIZE / 2 + oy + bob

        rx = (PLAYER_SIZE / 2) * p.squish_x
        ry = (PLAYER_SIZE / 2) * p.squish_y

        suit_col = p.color
        ring_col = "#ff5555"
        visor_col = "#88bbdd"
        chest_col = "#ff3333"

        if p.has_effect("invert_controls"):
            v = int(150 + 105 * abs(math.sin(t * 9.0)))
            suit_col  = f"#{v:02x}00{v:02x}"
            ring_col  = f"#{min(255,v+60):02x}44{min(255,v+60):02x}"
            visor_col = f"#ff00{min(255, v):02x}"
            chest_col = f"#{min(255, v):02x}00{min(255, v):02x}"
        elif p.has_effect("darkness"):
            suit_col  = "#a09000"
            ring_col  = "#ffee44"
            visor_col = "#ffee44"
            chest_col = "#ffcc00"
        elif p.has_effect("slow_motion"):
            suit_col  = "#223366"
            ring_col  = "#4488ff"
            visor_col = "#6699ff"
            chest_col = "#3366cc"
        elif p.has_effect("paranoia"):
            v = int(180 + 75 * abs(math.sin(t * 14.7)))
            suit_col  = f"#{v:02x}{max(0, v - 90):02x}00"
            ring_col  = "#ff8800"
            visor_col = "#ffaa33"
            chest_col = "#ff6600"
        elif p.has_effect("gravity"):
            suit_col  = "#1a4415"
            ring_col  = "#44dd22"
            visor_col = "#88ff55"
            chest_col = "#33aa11"

        # Drop shadow
        self.canvas.create_oval(
            cx - rx + 2, cy + ry * 0.5,
            cx + rx + 3, cy + ry + 4,
            fill="#060008", outline="",
        )

        # Outer glow / collar ring
        self.canvas.create_oval(
            cx - rx - 3, cy - ry - 3,
            cx + rx + 3, cy + ry + 3,
            fill="", outline=ring_col, width=2,
        )

        # Body suit
        self.canvas.create_oval(
            cx - rx, cy - ry, cx + rx, cy + ry,
            fill=suit_col, outline="",
        )

        # Suit shading (right side darker)
        shade_r = max(0, int(int(suit_col[1:3], 16) * 0.5))
        shade_g = max(0, int(int(suit_col[3:5], 16) * 0.5))
        shade_b = max(0, int(int(suit_col[5:7], 16) * 0.5))
        shade_col = f"#{shade_r:02x}{shade_g:02x}{shade_b:02x}"
        self.canvas.create_oval(
            cx, cy - ry * 0.85, cx + rx * 0.85, cy + ry * 0.85,
            fill=shade_col, outline="", stipple="gray50",
        )

        # Visor plate (upper portion)
        vr = rx * 0.72
        vy_top = cy - ry + 2
        vy_bot = cy - ry * 0.05
        self.canvas.create_oval(
            cx - vr, vy_top, cx + vr, vy_bot + vr * 0.7,
            fill="#080a0f", outline=visor_col, width=1,
        )

        # Visor reflection glint
        self.canvas.create_oval(
            cx - vr * 0.48, vy_top + 2,
            cx - vr * 0.05, vy_top + 2 + vr * 0.32,
            fill=visor_col, outline="",
        )

        # Chest emblem / ID badge
        bx = cx - rx * 0.22
        by_c = cy + ry * 0.22
        self.canvas.create_rectangle(
            bx, by_c - rx * 0.15,
            bx + rx * 0.44, by_c + rx * 0.15,
            fill=chest_col, outline="",
        )

        # Directional eyes inside visor
        eye_off = {
            "right": [(vr * 0.35, vr * 0.1), (vr * 0.35, vr * 0.5)],
            "left":  [(-vr * 0.35, vr * 0.1), (-vr * 0.35, vr * 0.5)],
            "down":  [(-vr * 0.25, vr * 0.45), (vr * 0.25, vr * 0.45)],
            "up":    [(-vr * 0.25, vr * 0.1), (vr * 0.25, vr * 0.1)],
        }
        pupil_dir = {
            "right": (0.9, 0.0), "left": (-0.9, 0.0),
            "down":  (0.0, 0.8), "up":   (0.0, -0.8),
        }
        vc_y = (vy_top + vy_bot + vr * 0.7) / 2
        pdx, pdy = pupil_dir.get(p.facing, (0.9, 0.0))
        for edx, edy in eye_off.get(p.facing, []):
            ex_ = cx + edx
            ey_ = vc_y - vr * 0.2 + edy
            self.canvas.create_oval(
                ex_ - 2.0, ey_ - 1.8, ex_ + 2.0, ey_ + 1.8,
                fill="#ffffff", outline="",
            )
            self.canvas.create_oval(
                ex_ + pdx * 0.8 - 1.1, ey_ + pdy * 0.8 - 1.1,
                ex_ + pdx * 0.8 + 1.1, ey_ + pdy * 0.8 + 1.1,
                fill="#000000", outline="",
            )

    def _draw_player_dead(self, ox: int, oy: int) -> None:
        p  = self.player
        cx = p.gx * TILE_SIZE + TILE_SIZE / 2 + ox
        cy = p.gy * TILE_SIZE + TILE_SIZE / 2 + oy
        if p.flash_timer > 0:
            col = p.death_flash_color()
            hw = hh = PLAYER_SIZE / 2
            self.canvas.create_oval(
                cx - hw, cy - hh, cx + hw, cy + hh,
                fill=col, outline="",
            )

    # ------------------------------------------------------------------
    # Darkness overlay
    # ------------------------------------------------------------------

    def _draw_darkness(self, ox: int, oy: int,
                        cs: int, rs: int, ce: int, re: int, t: float) -> None:
        if not self.player:
            return
        px, py = self.player.gx, self.player.gy
        dr = DARK_RADIUS
        flicker_r = dr - 0.5 + math.sin(t * 15.0) * 0.3
        ts = TILE_SIZE

        for gy in range(rs, re):
            row_y = gy * ts + oy
            dy2 = (gy - py) ** 2
            outer_r = dr + 0.5
            inner_r = dr - 0.5
            flick_end = flicker_r + 1.2

            if dy2 > outer_r * outer_r:
                row_x0 = cs * ts + ox
                row_x1 = ce * ts + ox
                self.canvas.create_rectangle(
                    row_x0, row_y, row_x1, row_y + ts,
                    fill="#000000", outline="")
                continue

            vis_half  = math.sqrt(max(0.0, inner_r * inner_r - dy2))
            edge_half = math.sqrt(max(0.0, outer_r * outer_r - dy2))
            vis_left  = int(px - vis_half)
            vis_right = int(math.ceil(px + vis_half))
            edge_left  = int(px - edge_half)
            edge_right = int(math.ceil(px + edge_half))

            if edge_left > cs:
                lx0 = cs * ts + ox
                lx1 = edge_left * ts + ox
                self.canvas.create_rectangle(
                    lx0, row_y, lx1, row_y + ts,
                    fill="#000000", outline="")
            if edge_right < ce:
                rx0 = edge_right * ts + ox
                rx1 = ce * ts + ox
                self.canvas.create_rectangle(
                    rx0, row_y, rx1, row_y + ts,
                    fill="#000000", outline="")

            for side_start, side_end in [(edge_left, vis_left), (vis_right, edge_right)]:
                for gx in range(max(cs, side_start), min(ce, side_end)):
                    ex = gx * ts + ox
                    self.canvas.create_rectangle(
                        ex, row_y, ex + ts, row_y + ts,
                        fill="#000000", outline="", stipple="gray50")

            if dy2 < flick_end * flick_end:
                flick_half = math.sqrt(max(0.0, flick_end * flick_end - dy2))
                flick_left  = int(px - flick_half)
                flick_right = int(math.ceil(px + flick_half))
                for side_start, side_end in [(flick_left, vis_left), (vis_right, flick_right)]:
                    for gx in range(max(cs, side_start), min(ce, side_end)):
                        dist = math.sqrt((gx - px) ** 2 + dy2)
                        if flicker_r < dist <= flick_end:
                            ex = gx * ts + ox
                            self.canvas.create_rectangle(
                                ex, row_y, ex + ts, row_y + ts,
                                fill="#000000", outline="", stipple="gray25")
