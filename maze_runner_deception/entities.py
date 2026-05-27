"""
entities.py — Player, Wall, Exit, and base entity logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


TILE_SIZE = 32  # pixels per grid cell


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

    def contains_point(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def center(self) -> tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h / 2

    def as_bbox(self) -> tuple[float, float, float, float]:
        return self.x, self.y, self.x + self.w, self.y + self.h


class Entity:
    def __init__(self, gx: int, gy: int, color: str = "white"):
        self.gx = gx   # grid x
        self.gy = gy   # grid y
        self.color = color
        self.visible = True

    @property
    def rect(self) -> Rect:
        return Rect(
            self.gx * TILE_SIZE,
            self.gy * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )

    def pixel_pos(self) -> tuple[float, float]:
        return self.gx * TILE_SIZE, self.gy * TILE_SIZE


class Wall(Entity):
    def __init__(self, gx: int, gy: int):
        super().__init__(gx, gy, color="white")
        self.solid = True


class FakeExit(Entity):
    """Looks like the exit but kills the player."""
    def __init__(self, gx: int, gy: int):
        super().__init__(gx, gy, color="#00cc44")
        self.is_fake = True


class Exit(Entity):
    def __init__(self, gx: int, gy: int):
        super().__init__(gx, gy, color="#00ff88")
        self.is_fake = False
        self.pulse = 0.0       # animation counter


class TriggerTile(Entity):
    """Invisible tile that fires an effect when stepped on."""
    def __init__(self, gx: int, gy: int, effect: str, duration: float = 3.0):
        super().__init__(gx, gy, color="#330033")
        self.effect = effect        # e.g. "invert_controls"
        self.duration = duration
        self.triggered = False
        self.visible = False        # invisible by default


class MovingExit(Exit):
    """Exit that relocates based on player facing direction."""
    def __init__(self, gx: int, gy: int, waypoints: list[tuple[int, int]]):
        super().__init__(gx, gy)
        self.waypoints = waypoints
        self.waypoint_index = 0
        self.move_timer = 0.0
        self.move_interval = 2.5   # seconds between moves


class Player:
    SPEED = 4.0           # tiles per second
    SIZE = TILE_SIZE - 6  # slightly smaller than a tile

    def __init__(self, gx: int, gy: int):
        self.gx: float = float(gx)
        self.gy: float = float(gy)
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.color = "#ff3333"
        self.deaths = 0
        self.alive = True

        # facing direction: "up", "down", "left", "right"
        self.facing = "right"

        # active status effects
        self.effects: dict[str, float] = {}   # effect_name -> remaining_seconds

    @property
    def rect(self) -> Rect:
        px = self.gx * TILE_SIZE + 3
        py = self.gy * TILE_SIZE + 3
        return Rect(px, py, self.SIZE, self.SIZE)

    @property
    def center(self) -> tuple[float, float]:
        return self.rect.center()

    def apply_effect(self, effect: str, duration: float) -> None:
        self.effects[effect] = duration

    def has_effect(self, effect: str) -> bool:
        return effect in self.effects and self.effects[effect] > 0

    def tick_effects(self, dt: float) -> None:
        expired = [k for k, v in self.effects.items() if v - dt <= 0]
        for k in expired:
            del self.effects[k]
        for k in self.effects:
            self.effects[k] -= dt

    def get_input_multiplier(self) -> tuple[int, int]:
        """Returns (x_mult, y_mult) — inverted if control-invert is active."""
        if self.has_effect("invert_controls"):
            return -1, -1
        return 1, 1

    def die(self) -> None:
        self.deaths += 1
        self.alive = False

    def respawn(self, gx: int, gy: int) -> None:
        self.gx = float(gx)
        self.gy = float(gy)
        self.vx = 0.0
        self.vy = 0.0
        self.alive = True
        self.effects.clear()

    def update(self, dx: float, dy: float, dt: float, walls: list[Wall]) -> None:
        """Move player with sub-tile collision resolution."""
        if not self.alive:
            return

        # update facing
        if dx > 0:
            self.facing = "right"
        elif dx < 0:
            self.facing = "left"
        elif dy > 0:
            self.facing = "down"
        elif dy < 0:
            self.facing = "up"

        step = self.SPEED * dt

        # resolve x then y independently to avoid corner sticking
        new_gx = self.gx + dx * step
        if not self._collides_walls(new_gx, self.gy, walls):
            self.gx = new_gx

        new_gy = self.gy + dy * step
        if not self._collides_walls(self.gx, new_gy, walls):
            self.gy = new_gy

        # clamp to reasonable bounds
        self.gx = max(0.0, self.gx)
        self.gy = max(0.0, self.gy)

    def _collides_walls(self, gx: float, gy: float, walls: list[Wall]) -> bool:
        px = gx * TILE_SIZE + 3
        py = gy * TILE_SIZE + 3
        player_rect = Rect(px, py, self.SIZE, self.SIZE)
        for w in walls:
            if not w.solid:
                continue
            if player_rect.intersects(w.rect):
                return True
        return False
