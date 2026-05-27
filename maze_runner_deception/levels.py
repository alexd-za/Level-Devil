"""
levels.py — Level definitions, maze layouts, traps, and story text.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from entities import Wall, Exit, FakeExit, TriggerTile, MovingExit, Player, TILE_SIZE


# ---------------------------------------------------------------------------
# Story / dialogue text
# ---------------------------------------------------------------------------

INTRO_TEXT = "Subject 47, escape the facility.\nOr try."

LEVEL_INTROS = {
    1: [
        "LEVEL 1: ORIENTATION",
        "",
        "The maze is simple.",
        "The exit is clearly marked.",
        "We would never mislead you.",
    ],
    2: [
        "LEVEL 2: COMPLIANCE",
        "",
        "Your controls are perfectly normal.",
        "Any disorientation is your own.",
        "The facility accepts no responsibility.",
    ],
    3: [
        "LEVEL 3: OBSERVATION",
        "",
        "The exit is stationary.",
        "It has always been stationary.",
        "Your perception may require calibration.",
    ],
    4: [
        "LEVEL 4: CORRECTION",
        "",
        "The walls have always been there.",
        "You simply failed to notice them earlier.",
        "This is your fault.",
    ],
    5: [
        "LEVEL 5: ACCEPTANCE",
        "",
        "You are so close.",
        "Freedom is just ahead.",
        "We are very proud of your progress.",
    ],
}

LEVEL_DEATHS = {
    1: [
        "That was the fake exit.",
        "We did mention it might kill you.",
        "(We did not mention that.)",
    ],
    2: [
        "Your controls betrayed you.",
        "Or perhaps you betrayed your controls.",
        "Unclear.",
    ],
    3: [
        "The exit moved while you weren't looking.",
        "You were looking?",
        "Interesting.",
    ],
    4: [
        "That wall was always there.",
        "You are improving at failing.",
        "Keep going.",
    ],
    5: [
        "So close.",
        "Again.",
    ],
}

LEVEL_COMPLETIONS = {
    1: [
        "Impressive.",
        "You found the real exit.",
        "We will make the next one harder.",
    ],
    2: [
        "Control restored.",
        "You adapted.",
        "We have noted this.",
    ],
    3: [
        "The exit has been re-stabilized.",
        "For now.",
    ],
    4: [
        "You navigated the corrections.",
        "The maze is pleased.",
        "You should be suspicious.",
    ],
    5: [
        "FACILITY BREACH DETECTED",
        "",
        "Congratulations, Subject 47.",
        "You have escaped.",
        "",
        "The study is complete.",
        "You were never trying to escape.",
        "You were demonstrating obedience.",
        "",
        "Thank you for your cooperation.",
    ],
}


# ---------------------------------------------------------------------------
# Maze data helpers
# ---------------------------------------------------------------------------

def parse_maze(grid: list[str]) -> tuple[list[Wall], list[tuple[int, int]]]:
    """
    Parse a list of strings into wall list + open cell list.
    '#' = wall, anything else = open.
    Returns (walls, open_cells).
    """
    walls = []
    open_cells = []
    for gy, row in enumerate(grid):
        for gx, ch in enumerate(row):
            if ch == "#":
                walls.append(Wall(gx, gy))
            else:
                open_cells.append((gx, gy))
    return walls, open_cells


# ---------------------------------------------------------------------------
# Level data definitions
# ---------------------------------------------------------------------------

# Grid key:
#   # = wall
#   . = open path
#   S = player start
#   E = exit
#   F = fake exit
#   T = trigger tile (invert controls)
#   (level-specific chars explained per level)

MAZE_1 = [
    "#################",
    "#S..............#",
    "#.#############.#",
    "#.#...........#.#",
    "#.#.#########.#.#",
    "#.#.#.......#.#.#",
    "#.#.#.#####.#.#.#",
    "#.#.#.#F..#.#.#.#",
    "#.#.#.#...#.#.#.#",
    "#.#.#.#####.#.#.#",
    "#.#.#.......#.#.#",
    "#.#.#########.#.#",
    "#.#...........#.#",
    "#.#############.#",
    "#...............#",
    "#################",
]

# After fake exit triggers, the real exit appears at bottom-right
REAL_EXIT_1 = (15, 14)   # grid position of real exit after fake is triggered

MAZE_2 = [
    "###################",
    "#S................#",
    "#.###############.#",
    "#.#.............#.#",
    "#.#.###########.#.#",
    "#.#.#.........#.#.#",
    "#.#.#.#######.#.#.#",
    "#.#.#.#T....#.#.#.#",
    "#.#.#.#.....#.#.#.#",
    "#.#.#.#######.#.#.#",
    "#.#.#.........#.#.#",
    "#.#.###########.#.#",
    "#.#.............#.#",
    "#.###############.#",
    "#.................#",
    "#################E#",
    "###################",
]

MAZE_3 = [
    "#####################",
    "#S..................#",
    "#.#################.#",
    "#.#...............#.#",
    "#.#.#############.#.#",
    "#.#.#...........#.#.#",
    "#.#.#.#########.#.#.#",
    "#.#.#.#.......#.#.#.#",
    "#.#.#.#.#####.#.#.#.#",
    "#.#.#.#.#...#.#.#.#.#",
    "#.#.#.#.#.E.#.#.#.#.#",
    "#.#.#.#.#...#.#.#.#.#",
    "#.#.#.#.#####.#.#.#.#",
    "#.#.#.#.......#.#.#.#",
    "#.#.#.#########.#.#.#",
    "#.#.#...........#.#.#",
    "#.#.#############.#.#",
    "#.#...............#.#",
    "#.#################.#",
    "#...................#",
    "#####################",
]

MAZE_4 = [
    "#######################",
    "#S....................#",
    "#.#####################",
    "#.#...................#",
    "#.#.###################",
    "#.#.#.................#",
    "#.#.#.#################",
    "#.#.#.#...............#",
    "#.#.#.#.###############",
    "#.#.#.#.#.............#",
    "#.#.#.#.#.#############",
    "#.#.#.#.#.#...........#",
    "#.#.#.#.#.#.###########",
    "#.#.#.#.#.#.#.........#",
    "#.#.#.#.#.#.#.#########",
    "#.#.#.#.#.#.#.#.......#",
    "#.#.#.#.#.#.#.#.#######",
    "#.#.#.#.#.#.#.#.#.....E",
    "#.#.#.#.#.#.#.#.#######",
    "#.#.#.#.#.#.#.#.......#",
    "#.#.#.#.#.#.#.#########",
    "#.....................#",
    "#######################",
]

MAZE_5 = [
    "#########################",
    "#S......................#",
    "#.#######################",
    "#.#.....................#",
    "#.#.#####################",
    "#.#.#...................#",
    "#.#.#.###################",
    "#.#.#.#.................#",
    "#.#.#.#.#################",
    "#.#.#.#.#...............#",
    "#.#.#.#.#.###############",
    "#.#.#.#.#.#.............#",
    "#.#.#.#.#.#.#############",
    "#.#.#.#.#.#.#...........#",
    "#.#.#.#.#.#.#.###########",
    "#.#.#.#.#.#.#.#.........#",
    "#.#.#.#.#.#.#.#.#########",
    "#.#.#.#.#.#.#.#.#.......#",
    "#.#.#.#.#.#.#.#.#.#######",
    "#.#.#.#.#.#.#.#.#.#.....#",
    "#.#.#.#.#.#.#.#.#.#.###.#",
    "#.#.#.#.#.#.#.#.#.#.#E#.#",
    "#.#.#.#.#.#.#.#.#.#.###.#",
    "#....................#..#",
    "#########################",
]


# ---------------------------------------------------------------------------
# Level class
# ---------------------------------------------------------------------------

@dataclass
class LevelConfig:
    number: int
    grid: list[str]
    player_start: tuple[int, int]
    exit_pos: tuple[int, int]
    fake_exit_pos: Optional[tuple[int, int]] = None
    trigger_tiles: list[tuple[int, int, str, float]] = field(default_factory=list)
    moving_exit_waypoints: Optional[list[tuple[int, int]]] = None
    invisible_walls_after_halfway: list[tuple[int, int]] = field(default_factory=list)
    halfway_gx: Optional[int] = None   # x-trigger for invisible walls


class Level:
    def __init__(self, config: LevelConfig):
        self.number = config.number
        self.config = config
        self.grid = config.grid
        self.rows = len(self.grid)
        self.cols = max(len(r) for r in self.grid)

        self.walls: list[Wall] = []
        self.exits: list[Exit] = []
        self.fake_exits: list[FakeExit] = []
        self.triggers: list[TriggerTile] = []
        self.moving_exit: Optional[MovingExit] = None

        self._invisible_wall_positions = config.invisible_walls_after_halfway
        self._invisible_walls_spawned = False
        self._halfway_gx = config.halfway_gx

        self._build()

        # Level 1 specifics
        self._fake_triggered = False

    # ------------------------------------------------------------------
    def _build(self) -> None:
        cfg = self.config
        walls_raw, _ = parse_maze(self.grid)
        self.walls = walls_raw

        # place exits / fake exits from config
        if cfg.fake_exit_pos:
            self.fake_exits.append(FakeExit(*cfg.fake_exit_pos))

        if cfg.moving_exit_waypoints:
            self.moving_exit = MovingExit(
                *cfg.exit_pos,
                waypoints=cfg.moving_exit_waypoints,
            )
        else:
            self.exits.append(Exit(*cfg.exit_pos))

        for gx, gy, effect, dur in cfg.trigger_tiles:
            self.triggers.append(TriggerTile(gx, gy, effect, dur))

    # ------------------------------------------------------------------
    def pixel_size(self) -> tuple[int, int]:
        return self.cols * TILE_SIZE, self.rows * TILE_SIZE

    # ------------------------------------------------------------------
    def update(self, dt: float, player: Player) -> Optional[str]:
        """
        Tick level logic.  Returns an event string or None.
        Events: "killed", "level_complete", "invert_applied"
        """
        pgx = int(player.gx + 0.5)
        pgy = int(player.gy + 0.5)

        # Level 1 — fake exit check
        for fe in self.fake_exits:
            if fe.visible and abs(player.gx - fe.gx) < 0.9 and abs(player.gy - fe.gy) < 0.9:
                self._fake_triggered = True
                fe.visible = False
                # reveal real exit
                if not self.exits:
                    self.exits.append(Exit(*REAL_EXIT_1))
                return "killed"

        # Level 4 — invisible walls after halfway
        if (
            self._invisible_wall_positions
            and not self._invisible_walls_spawned
            and self._halfway_gx is not None
            and player.gx >= self._halfway_gx
        ):
            self._invisible_walls_spawned = True
            for gx, gy in self._invisible_wall_positions:
                w = Wall(gx, gy)
                self.walls.append(w)

        # Trigger tiles
        for trig in self.triggers:
            if (
                not trig.triggered
                and abs(player.gx - trig.gx) < 0.9
                and abs(player.gy - trig.gy) < 0.9
            ):
                trig.triggered = True
                if trig.effect == "invert_controls":
                    player.apply_effect("invert_controls", trig.duration)
                    return "invert_applied"

        # Moving exit (Level 3)
        if self.moving_exit:
            me = self.moving_exit
            me.move_timer += dt
            if me.move_timer >= me.move_interval:
                me.move_timer = 0.0
                # move only if player is NOT facing the exit
                ex_cx = me.gx + 0.5
                ey_cx = me.gy + 0.5
                dx = ex_cx - (player.gx + 0.5)
                dy = ey_cx - (player.gy + 0.5)
                facing_it = False
                if player.facing == "right" and dx > 0 and abs(dx) > abs(dy):
                    facing_it = True
                elif player.facing == "left" and dx < 0 and abs(dx) > abs(dy):
                    facing_it = True
                elif player.facing == "down" and dy > 0 and abs(dy) > abs(dx):
                    facing_it = True
                elif player.facing == "up" and dy < 0 and abs(dy) > abs(dx):
                    facing_it = True

                if not facing_it:
                    me.waypoint_index = (me.waypoint_index + 1) % len(me.waypoints)
                    nwp = me.waypoints[me.waypoint_index]
                    me.gx, me.gy = nwp

            # check reach
            if abs(player.gx - me.gx) < 0.9 and abs(player.gy - me.gy) < 0.9:
                return "level_complete"
        else:
            # Static exits
            for ex in self.exits:
                if ex.visible and abs(player.gx - ex.gx) < 0.9 and abs(player.gy - ex.gy) < 0.9:
                    return "level_complete"

        return None

    def get_all_renderable(self):
        """Return all entities for renderer."""
        items = list(self.walls)
        items += [fe for fe in self.fake_exits if fe.visible]
        items += [ex for ex in self.exits if ex.visible]
        for trig in self.triggers:
            if trig.visible:
                items.append(trig)
        if self.moving_exit:
            items.append(self.moving_exit)
        return items


# ---------------------------------------------------------------------------
# Level factory
# ---------------------------------------------------------------------------

def _find_char(grid: list[str], ch: str) -> Optional[tuple[int, int]]:
    for gy, row in enumerate(grid):
        for gx, c in enumerate(row):
            if c == ch:
                return gx, gy
    return None


def _clean_grid(grid: list[str]) -> list[str]:
    """Replace non-# chars with '.' for parse_maze."""
    cleaned = []
    for row in grid:
        cleaned.append("".join("#" if c == "#" else "." for c in row))
    return cleaned


def make_level(number: int) -> tuple[Level, tuple[int, int]]:
    """Factory: returns (Level, player_start_grid_pos)."""
    if number == 1:
        raw = MAZE_1
        start = _find_char(raw, "S") or (1, 1)
        fake = _find_char(raw, "F") or (7, 7)
        cfg = LevelConfig(
            number=1,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=REAL_EXIT_1,     # real exit hidden until fake triggered
            fake_exit_pos=fake,
        )
        lv = Level(cfg)
        # Remove the pre-built exit; it appears only after fake is triggered
        lv.exits.clear()
        return lv, start

    elif number == 2:
        raw = MAZE_2
        start = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (17, 15)
        trig = _find_char(raw, "T") or (7, 7)
        cfg = LevelConfig(
            number=2,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            trigger_tiles=[(trig[0], trig[1], "invert_controls", 4.0)],
        )
        return Level(cfg), start

    elif number == 3:
        raw = MAZE_3
        start = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (10, 10)
        # Moving exit waypoints — open cells in inner ring
        waypoints = [
            (10, 10), (10, 6), (14, 10), (10, 14), (6, 10),
        ]
        cfg = LevelConfig(
            number=3,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            moving_exit_waypoints=waypoints,
        )
        return Level(cfg), start

    elif number == 4:
        raw = MAZE_4
        start = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (22, 17)
        # Invisible walls that spawn when player crosses x=11
        invisible = [
            (3, 3), (3, 5), (5, 3), (7, 7), (9, 5), (11, 9),
        ]
        cfg = LevelConfig(
            number=4,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            invisible_walls_after_halfway=invisible,
            halfway_gx=11,
        )
        return Level(cfg), start

    elif number == 5:
        raw = MAZE_5
        start = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (21, 21)
        trig1 = (5, 5)
        trig2 = (12, 12)
        waypoints = [
            (21, 21), (21, 17), (17, 21), (13, 19), (19, 13),
        ]
        invisible = [(3, 3), (7, 3), (3, 7), (15, 15), (19, 19)]
        cfg = LevelConfig(
            number=5,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            trigger_tiles=[
                (trig1[0], trig1[1], "invert_controls", 3.0),
                (trig2[0], trig2[1], "invert_controls", 3.0),
            ],
            moving_exit_waypoints=waypoints,
            invisible_walls_after_halfway=invisible,
            halfway_gx=10,
        )
        lv = Level(cfg)
        return lv, start

    raise ValueError(f"Unknown level {number}")
