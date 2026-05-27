from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional

TILE_SIZE   = 26
PLAYER_GAP  = 3
PLAYER_SIZE = TILE_SIZE - PLAYER_GAP * 2


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    def intersects(self, other: "Rect") -> bool:
        return (
            self.x < other.x + other.w
            and self.x + self.w > other.x
            and self.y < other.y + other.h
            and self.y + self.h > other.y
        )

    def center(self) -> tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h / 2

    def as_bbox(self) -> tuple[float, float, float, float]:
        return self.x, self.y, self.x + self.w, self.y + self.h


class Entity:
    def __init__(self, gx: int, gy: int, color: str = "white"):
        self.gx    = gx
        self.gy    = gy
        self.color = color
        self.visible = True

    @property
    def rect(self) -> Rect:
        return Rect(self.gx * TILE_SIZE, self.gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)


class Wall(Entity):
    def __init__(self, gx: int, gy: int, ghost: bool = False):
        super().__init__(gx, gy, color="white")
        self.solid        = True
        self.ghost        = ghost
        self.flash_frames = 0


class FakeWall(Wall):
    """Renders identically to a real wall but player walks straight through."""
    def __init__(self, gx: int, gy: int):
        super().__init__(gx, gy, ghost=False)
        self.solid   = False
        self.is_fake = True


class FakeExit(Entity):
    def __init__(self, gx: int, gy: int):
        super().__init__(gx, gy, color="#00cc44")
        self.is_fake = True


class Exit(Entity):
    def __init__(self, gx: int, gy: int):
        super().__init__(gx, gy, color="#00ff88")
        self.is_fake = False


class TriggerTile(Entity):
    def __init__(self, gx: int, gy: int, effect: str, duration: float = 3.0):
        super().__init__(gx, gy, color="#330033")
        self.effect    = effect
        self.duration  = duration
        self.triggered = False
        self.visible   = False


class MovingExit(Exit):
    def __init__(self, gx: int, gy: int, waypoints: list[tuple[int, int]]):
        super().__init__(gx, gy)
        self.waypoints      = waypoints
        self.waypoint_index = 0
        self.move_timer     = 0.0
        self.move_interval  = 2.8
        self.ghost_trail: list[tuple[int, int]] = []



class Note(Entity):
    """Collectible lore fragment scattered through the maze."""
    def __init__(self, gx: int, gy: int, lines: list[str]):
        super().__init__(gx, gy, color="#ffcc00")
        self.lines     = lines
        self.collected = False


class Enemy(Entity):
    """Patrolling security unit. Kills on contact."""
    SPEED = 2.8

    def __init__(self, gx: int, gy: int, waypoints: list[tuple[int, int]]):
        super().__init__(gx, gy, color="#cc2200")
        self.gx_f: float = float(gx)
        self.gy_f: float = float(gy)
        self.waypoints   = waypoints
        self.wp_index    = 0
        self.alive       = True
        self._anim_timer = 0.0

    @property
    def center_px(self) -> tuple[float, float]:
        return (self.gx_f * TILE_SIZE + TILE_SIZE / 2,
                self.gy_f * TILE_SIZE + TILE_SIZE / 2)

    def update(self, dt: float) -> None:
        if not self.alive or not self.waypoints:
            return
        tx, ty = self.waypoints[self.wp_index]
        dx = tx - self.gx_f
        dy = ty - self.gy_f
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.08:
            self.wp_index = (self.wp_index + 1) % len(self.waypoints)
        else:
            step = self.SPEED * dt
            self.gx_f += (dx / dist) * min(step, dist)
            self.gy_f += (dy / dist) * min(step, dist)
        self._anim_timer += dt

    def touches_player(self, player) -> bool:
        return (abs(self.gx_f - player.gx) < 0.75
                and abs(self.gy_f - player.gy) < 0.75)


class Player:
    SPEED = 5.5

    def __init__(self, gx: int, gy: int):
        self.gx: float = float(gx)
        self.gy: float = float(gy)
        self.color  = "#dd2222"
        self.deaths = 0
        self.alive  = True
        self.facing = "right"

        self.effects: dict[str, float] = {}

        self.squish_x:  float = 1.0
        self.squish_y:  float = 1.0
        self.bob_timer: float = 0.0
        self._is_moving       = False

        self.flash_timer: float = 0.0
        self.flash_phase: float = 0.0

        self.notes_found: int = 0

    @property
    def rect(self) -> Rect:
        px = self.gx * TILE_SIZE + PLAYER_GAP
        py = self.gy * TILE_SIZE + PLAYER_GAP
        return Rect(px, py, PLAYER_SIZE, PLAYER_SIZE)

    @property
    def center(self) -> tuple[float, float]:
        return self.rect.center()

    def apply_effect(self, effect: str, duration: float) -> None:
        self.effects[effect] = duration

    def has_effect(self, effect: str) -> bool:
        return self.effects.get(effect, 0.0) > 0

    def tick_effects(self, dt: float) -> None:
        for k in list(self.effects):
            self.effects[k] -= dt
            if self.effects[k] <= 0:
                del self.effects[k]

    def get_input_multiplier(self) -> tuple[int, int]:
        if self.has_effect("invert_controls"):
            return -1, -1
        return 1, 1

    def die(self) -> None:
        self.deaths     += 1
        self.alive       = False
        self.flash_timer = 0.35
        self.flash_phase = 0.0

    def respawn(self, gx: int, gy: int) -> None:
        self.gx = float(gx)
        self.gy = float(gy)
        self.alive       = True
        self.flash_timer = 0.0
        self.effects.clear()
        self.squish_x = 1.0
        self.squish_y = 1.0

    def update(self, dx: float, dy: float, dt: float, wall_map: dict) -> None:
        if not self.alive:
            self._tick_death_flash(dt)
            return

        self._is_moving = (dx != 0 or dy != 0)
        self._tick_animation(dx, dy, dt)

        if   dx > 0: self.facing = "right"
        elif dx < 0: self.facing = "left"
        elif dy > 0: self.facing = "down"
        elif dy < 0: self.facing = "up"

        spd  = self.SPEED * (1.85 if self.has_effect("speed_boost") else 1.0)
        step = spd * dt

        new_gx = self.gx + dx * step
        if not self._collides(new_gx, self.gy, wall_map):
            self.gx = new_gx
        elif dy == 0 and dx != 0:
            frac = self.gy - math.floor(self.gy)
            if frac < 0.28:
                self.gy = max(0.0, self.gy - min(frac, step * 1.5))
            elif frac > 0.72:
                self.gy = self.gy + min(1.0 - frac, step * 1.5)

        new_gy = self.gy + dy * step
        if not self._collides(self.gx, new_gy, wall_map):
            self.gy = new_gy
        elif dx == 0 and dy != 0:
            frac = self.gx - math.floor(self.gx)
            if frac < 0.28:
                self.gx = max(0.0, self.gx - min(frac, step * 1.5))
            elif frac > 0.72:
                self.gx = self.gx + min(1.0 - frac, step * 1.5)

        self.gx = max(0.0, self.gx)
        self.gy = max(0.0, self.gy)

    def _tick_animation(self, dx: float, dy: float, dt: float) -> None:
        target_sx = target_sy = 1.0
        if dx != 0:
            target_sx, target_sy = 0.78, 1.25
        elif dy != 0:
            target_sx, target_sy = 1.25, 0.78

        spd = 12.0
        self.squish_x += (target_sx - self.squish_x) * spd * dt
        self.squish_y += (target_sy - self.squish_y) * spd * dt

        if self._is_moving:
            self.bob_timer += dt * 11.0
        else:
            self.bob_timer += dt * 2.2

    def _tick_death_flash(self, dt: float) -> None:
        if self.flash_timer > 0:
            self.flash_timer -= dt
            self.flash_phase += dt * 30.0

    def death_flash_color(self) -> str:
        v = int(abs(math.sin(self.flash_phase)) * 255)
        return f"#{v:02x}0000"

    def _collides(self, gx: float, gy: float, wall_map: dict) -> bool:
        px = gx * TILE_SIZE + PLAYER_GAP
        py = gy * TILE_SIZE + PLAYER_GAP
        pr = Rect(px, py, PLAYER_SIZE, PLAYER_SIZE)
        tx = int(gx)
        ty = int(gy)
        for cy in range(ty - 1, ty + 3):
            for cx in range(tx - 1, tx + 3):
                w = wall_map.get((cx, cy))
                if w and w.solid and pr.intersects(w.rect):
                    return True
        return False
