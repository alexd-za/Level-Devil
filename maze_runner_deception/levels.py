"""
levels.py — Level definitions, maze layouts, trap logic, and all story text.
All mazes generated with recursive-backtracker and BFS-verified solvable.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Optional
from entities import Wall, Exit, FakeExit, TriggerTile, MovingExit, TILE_SIZE


# ---------------------------------------------------------------------------
# Story text
# ---------------------------------------------------------------------------

INTRO_TEXT = "Subject 47, escape the facility.\nOr try."

LEVEL_INTROS = {
    1: [
        "LEVEL 1 — ORIENTATION",
        "",
        "The maze is simple.",
        "The exit is clearly marked.",
        "We would never mislead you.",
        "",
        "Good luck, Subject 47.",
    ],
    2: [
        "LEVEL 2 — COMPLIANCE",
        "",
        "Your controls are perfectly normal.",
        "Any disorientation is entirely your own.",
        "",
        "The facility accepts no responsibility.",
    ],
    3: [
        "LEVEL 3 — OBSERVATION",
        "",
        "The exit is stationary.",
        "It has always been stationary.",
        "",
        "Your perception may require recalibration.",
    ],
    4: [
        "LEVEL 4 — CORRECTION",
        "",
        "The walls have always been there.",
        "You simply failed to notice them earlier.",
        "",
        "This is entirely your fault.",
    ],
    5: [
        "LEVEL 5 — ACCEPTANCE",
        "",
        "You are so close.",
        "Freedom is just ahead.",
        "",
        "We are very proud of your progress.",
    ],
}

LEVEL_DEATHS: dict[int, list[list[str]]] = {
    1: [
        ["That was the fake exit.",
         "We did not specify which exit was real."],
        ["Fascinating.",
         "You chose the obvious path.",
         "The obvious path is always wrong."],
        ["The exit appreciated your visit.",
         "It was not the exit."],
        ["Your trust is noted.",
         "We will continue to exploit it."],
    ],
    2: [
        ["Controls inverted.",
         "You chose the wrong direction.",
         "Both directions were wrong."],
        ["Your controls betrayed you.",
         "Or you betrayed your controls.",
         "The distinction is philosophical."],
        ["Statistically, you will adapt.",
         "Statistics are optimistic."],
        ["The facility notes your confusion.",
         "The facility is pleased by your confusion."],
    ],
    3: [
        ["The exit relocated.",
         "This is normal behavior.",
         "Stop questioning the exit."],
        ["It moved while you blinked.",
         "You were not supposed to blink."],
        ["The exit is shy.",
         "You approached too aggressively.",
         "Consider your tone."],
        ["You were so close.",
         "The exit disagreed."],
    ],
    4: [
        ["That wall was always there.",
         "Your memory is unreliable."],
        ["The maze has been updated for your convenience.",
         "You're welcome."],
        ["Infrastructure improved.",
         "You are improving at failing.",
         "Keep going."],
        ["The facility has made a small adjustment.",
         "The facility regrets nothing."],
    ],
    5: [
        ["So close.",
         "Again."],
        ["The exit is real.",
         "Your path to it is not.",
         "Distinction noted."],
        ["You are learning.",
         "We are also learning.",
         "About you."],
        ["Almost.",
         "We enjoyed watching."],
    ],
}

LEVEL_COMPLETIONS = {
    1: [
        "SECTOR CLEARED",
        "",
        "You found the real exit.",
        "We have adjusted the next level accordingly.",
        "You were not supposed to be this persistent.",
    ],
    2: [
        "COMPLIANCE CONFIRMED",
        "",
        "You adapted to the controls.",
        "We have noted your adaptability.",
        "",
        "It will be used against you.",
    ],
    3: [
        "OBSERVATION LOGGED",
        "",
        "The exit has been re-stabilized.",
        "For now.",
        "",
        "Do not make direct eye contact with the exit.",
    ],
    4: [
        "CORRECTION COMPLETE",
        "",
        "You navigated the updated maze.",
        "Your perseverance is troubling.",
        "",
        "We will try harder.",
    ],
    5: [
        "FACILITY BREACH DETECTED",
        "",
        "Congratulations, Subject 47.",
        "You have reached the exit.",
        "",
        "The study is now complete.",
        "",
        "You were never trying to escape.",
        "You were demonstrating obedience.",
        "Every choice was anticipated.",
        "Every struggle was measured.",
        "",
        "Thank you for your cooperation.",
        "",
        "The facility will miss you.",
        "(It will not.)",
    ],
}

# Mid-level narrator hints — appear after a delay, deliberately misleading
LEVEL_HINTS: dict[int, tuple[float, str]] = {
    1: (4.0,  "FACILITY TIP: The exit is clearly visible. Trust the green."),
    2: (6.0,  "FACILITY TIP: Controls are functioning within normal parameters."),
    3: (4.0,  "FACILITY TIP: The exit is stationary. It cannot and will not move."),
    4: (9.0,  "FACILITY TIP: The maze structure is completely stable."),
    5: (5.0,  "FACILITY TIP: You are very close to the exit. Almost there."),
}


# ---------------------------------------------------------------------------
# Maze grids — all BFS-verified solvable, consistent widths
# ---------------------------------------------------------------------------
# Key:  # = wall  . = open  S = start  E = real_exit  F = fake_exit  T = trigger

# Level 1  (17x17)  S=(1,1)  E=(15,15)  F=(4,5)
MAZE_1 = [
    "#################",
    "#S......#.#.....#",
    "#######.#.#.###.#",
    "#.....#.#...#...#",
    "#.#####.#.###.#.#",
    "#...F...#...#.#.#",
    "#.#######.###.#.#",
    "#.#.....#.#...#.#",
    "#.#####.#.#.#####",
    "#.....#.#.#.....#",
    "#####.#.#.#####.#",
    "#...#.#...#...#.#",
    "#.###.#.###.###.#",
    "#.....#.....#...#",
    "#.###########.#.#",
    "#.............#E#",
    "#################",
]

# Level 2  (19x19)  S=(1,1)  E=(17,17)  T=(16,5)
MAZE_2 = [
    "###################",
    "#S#...........#...#",
    "#.#.#######.#.###.#",
    "#.#...#.....#...#.#",
    "#.#.###.#######.#.#",
    "#.#.#...#.....#.T.#",
    "#.###.###.#.#####.#",
    "#.....#...#.......#",
    "#######.###########",
    "#.......#.#.......#",
    "#.#######.#.#####.#",
    "#.......#.#...#...#",
    "#######.#.###.#.#.#",
    "#.....#.#.....#.#.#",
    "#.#####.#.#####.#.#",
    "#.....#.#.#.....#.#",
    "#.###.#.###.#####.#",
    "#...#.......#....E#",
    "###################",
]

# Level 3  (21x21)  S=(1,1)  E=(19,19)  — moving exit
MAZE_3 = [
    "#####################",
    "#S#.....#...........#",
    "#.#.###.#########.#.#",
    "#.#...#...........#.#",
    "#.###.#############.#",
    "#.#...#.....#.....#.#",
    "#.#.###.#####.###.#.#",
    "#...#...#.....#.#...#",
    "#####.#.#.#####.#####",
    "#.....#.#.#.........#",
    "###.###.#.#.#######.#",
    "#...#...#.#.......#.#",
    "#.#######.#########.#",
    "#.........#.........#",
    "#.#########.#######.#",
    "#...#.......#.#.....#",
    "###.###.#####.#.#####",
    "#.#.....#.....#.#...#",
    "#.#######.#.###.###.#",
    "#.........#........E#",
    "#####################",
]

# Level 4  (23x23)  S=(1,1)  E=(21,21)  — invisible walls after halfway
MAZE_4 = [
    "#######################",
    "#S#.....#.............#",
    "#.#.###.#########.###.#",
    "#.#...#...........#.#.#",
    "#.###.#############.#.#",
    "#.#...#.....#.....#...#",
    "#.#.###.###.#.###.#.###",
    "#...#.....#.#.#.#...#.#",
    "###########.#.#.#####.#",
    "#...........#.#.#.....#",
    "#.#.#########.#.#.#.#.#",
    "#.#...........#...#.#.#",
    "#.#################.#.#",
    "#.................#.#.#",
    "#################.#.###",
    "#...........#.....#...#",
    "#.#########.#.#####.#.#",
    "#.#.....#...#.#.....#.#",
    "#.#.###.#####.#######.#",
    "#.#...#.#.....#.......#",
    "#.###.#.#.#####.#####.#",
    "#.....#.........#....E#",
    "#######################",
]

# Level 5  (25x25)  S=(1,1)  E=(23,23)  T at (17,2) and (13,15)
MAZE_5 = [
    "#########################",
    "#S#.....#...............#",
    "#.#.###.#########T#####.#",
    "#.#...#...........#.#...#",
    "#.###.#############.#.###",
    "#.#...#.............#...#",
    "#.#.###.###########.###.#",
    "#...#...#.............#.#",
    "#########.#######.#####.#",
    "#.........#.#.....#.....#",
    "#.###.#####.#.#####.#####",
    "#...#.#.....#.#...#.#...#",
    "###.#.#####.#.###.#.#.###",
    "#...#.....#.......#.#...#",
    "#.#######.#########.#.#.#",
    "#.....#.#....T......#.#.#",
    "#####.#.###############.#",
    "#.#...#...........#.....#",
    "#.#.#######.#####.#.###.#",
    "#...#.....#...#...#.#...#",
    "#.#####.#.###.#.###.#.###",
    "#.....#.#.....#.#...#.#.#",
    "#####.#.#######.#.###.#.#",
    "#.......#.........#....E#",
    "#########################",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_char(grid: list[str], ch: str) -> Optional[tuple[int, int]]:
    for gy, row in enumerate(grid):
        for gx, c in enumerate(row):
            if c == ch:
                return gx, gy
    return None


def _clean_grid(grid: list[str]) -> list[str]:
    return ["".join("#" if c == "#" else "." for c in row) for row in grid]


def parse_maze(grid: list[str]) -> list[Wall]:
    walls = []
    for gy, row in enumerate(grid):
        for gx, ch in enumerate(row):
            if ch == "#":
                walls.append(Wall(gx, gy))
    return walls


# ---------------------------------------------------------------------------
# Level config & runtime class
# ---------------------------------------------------------------------------

@dataclass
class LevelConfig:
    number:                int
    grid:                  list[str]
    player_start:          tuple[int, int]
    exit_pos:              tuple[int, int]
    fake_exit_pos:         Optional[tuple[int, int]]            = None
    trigger_tiles:         list[tuple[int, int, str, float]]    = field(default_factory=list)
    moving_exit_waypoints: Optional[list[tuple[int, int]]]      = None
    invisible_walls:       list[tuple[int, int]]                = field(default_factory=list)
    halfway_gx:            Optional[int]                        = None


REAL_EXIT_LEVEL1 = (15, 15)   # same cell as E, appears after fake triggered


class Level:
    def __init__(self, config: LevelConfig):
        self.number = config.number
        self.config = config
        self.grid   = config.grid
        self.rows   = len(self.grid)
        self.cols   = max(len(r) for r in self.grid)

        self.walls:       list[Wall]           = []
        self.exits:       list[Exit]           = []
        self.fake_exits:  list[FakeExit]       = []
        self.triggers:    list[TriggerTile]    = []
        self.moving_exit: Optional[MovingExit] = None

        self._invisible_positions = config.invisible_walls
        self._invisible_spawned   = False
        self._halfway_gx          = config.halfway_gx
        self._glitch_countdown    = 0

        self._build()

    def _build(self) -> None:
        cfg = self.config
        self.walls = parse_maze(self.grid)

        if cfg.fake_exit_pos:
            self.fake_exits.append(FakeExit(*cfg.fake_exit_pos))

        if cfg.moving_exit_waypoints:
            self.moving_exit = MovingExit(*cfg.exit_pos,
                                          waypoints=cfg.moving_exit_waypoints)
        else:
            self.exits.append(Exit(*cfg.exit_pos))

        for gx, gy, effect, dur in cfg.trigger_tiles:
            self.triggers.append(TriggerTile(gx, gy, effect, dur))

    # ------------------------------------------------------------------
    def pixel_size(self) -> tuple[int, int]:
        return self.cols * TILE_SIZE, self.rows * TILE_SIZE

    def update(self, dt: float, player) -> Optional[str]:
        if self._glitch_countdown > 0:
            self._glitch_countdown -= 1
            for w in self.walls:
                if w.ghost and w.flash_frames > 0:
                    w.flash_frames -= 1

        # fake exit (level 1)
        for fe in self.fake_exits:
            if (fe.visible
                    and abs(player.gx - fe.gx) < 0.85
                    and abs(player.gy - fe.gy) < 0.85):
                fe.visible = False
                if not self.exits:
                    self.exits.append(Exit(*REAL_EXIT_LEVEL1))
                return "killed"

        # invisible walls (levels 4, 5)
        if (self._invisible_positions
                and not self._invisible_spawned
                and self._halfway_gx is not None
                and player.gx >= self._halfway_gx):
            self._invisible_spawned = True
            for gx, gy in self._invisible_positions:
                w = Wall(gx, gy, ghost=True)
                w.flash_frames = 20
                self.walls.append(w)
            self._glitch_countdown = 22

        # trigger tiles
        for trig in self.triggers:
            if (not trig.triggered
                    and abs(player.gx - trig.gx) < 0.85
                    and abs(player.gy - trig.gy) < 0.85):
                trig.triggered = True
                if trig.effect == "invert_controls":
                    player.apply_effect("invert_controls", trig.duration)
                    return "invert_applied"

        # moving exit (levels 3, 5)
        if self.moving_exit:
            me = self.moving_exit
            me.move_timer += dt
            if me.move_timer >= me.move_interval:
                me.move_timer = 0.0
                dx = (me.gx + 0.5) - (player.gx + 0.5)
                dy = (me.gy + 0.5) - (player.gy + 0.5)
                facing_it = False
                if player.facing == "right" and dx > 0 and abs(dx) > abs(dy): facing_it = True
                if player.facing == "left"  and dx < 0 and abs(dx) > abs(dy): facing_it = True
                if player.facing == "down"  and dy > 0 and abs(dy) > abs(dx): facing_it = True
                if player.facing == "up"    and dy < 0 and abs(dy) > abs(dx): facing_it = True

                if not facing_it:
                    me.ghost_trail.append((me.gx, me.gy))
                    if len(me.ghost_trail) > 3:
                        me.ghost_trail.pop(0)
                    me.waypoint_index = (me.waypoint_index + 1) % len(me.waypoints)
                    me.gx, me.gy = me.waypoints[me.waypoint_index]

            if abs(player.gx - me.gx) < 0.85 and abs(player.gy - me.gy) < 0.85:
                return "level_complete"
        else:
            for ex in self.exits:
                if (ex.visible
                        and abs(player.gx - ex.gx) < 0.85
                        and abs(player.gy - ex.gy) < 0.85):
                    return "level_complete"

        return None

    def get_renderables(self):
        items = list(self.walls)
        items += [fe for fe in self.fake_exits if fe.visible]
        items += [ex for ex in self.exits if ex.visible]
        items += [tr for tr in self.triggers if tr.visible]
        if self.moving_exit:
            items.append(self.moving_exit)
        return items

    def pick_death_message(self) -> list[str]:
        pool = LEVEL_DEATHS.get(self.number, [["You died."]])
        return random.choice(pool)


# ---------------------------------------------------------------------------
# Level factory
# ---------------------------------------------------------------------------

def make_level(number: int) -> tuple[Level, tuple[int, int]]:
    if number == 1:
        raw   = MAZE_1
        start = _find_char(raw, "S") or (1, 1)
        fake  = _find_char(raw, "F") or (4, 5)
        cfg   = LevelConfig(
            number=1,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=REAL_EXIT_LEVEL1,
            fake_exit_pos=fake,
        )
        lv = Level(cfg)
        lv.exits.clear()   # real exit hidden until fake is triggered
        return lv, start

    elif number == 2:
        raw      = MAZE_2
        start    = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (17, 17)
        trig     = _find_char(raw, "T") or (16, 5)
        cfg      = LevelConfig(
            number=2,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            trigger_tiles=[(trig[0], trig[1], "invert_controls", 5.0)],
        )
        return Level(cfg), start

    elif number == 3:
        raw      = MAZE_3
        start    = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (19, 19)
        # All waypoints BFS-verified on open cells
        waypoints = [
            (19, 19),   # start position (E)
            (18, 19),   # one left
            (17, 19),   # two left
            (19, 17),   # two up
            (19, 15),   # four up
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
        raw      = MAZE_4
        start    = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (21, 21)
        # Invisible walls in left portion; spawned when player crosses x=11
        invisible = [
            (1, 3), (3, 3), (5, 3),
            (1, 5), (1, 7),
        ]
        cfg = LevelConfig(
            number=4,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            invisible_walls=invisible,
            halfway_gx=11,
        )
        return Level(cfg), start

    elif number == 5:
        raw      = MAZE_5
        start    = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (23, 23)
        # Triggers already embedded in maze as 'T'
        t1 = _find_char(raw, "T") or (17, 2)
        # Find second T
        t2_pos = [(gx, gy) for gy, row in enumerate(raw)
                  for gx, c in enumerate(row) if c == "T"]
        t2 = t2_pos[1] if len(t2_pos) > 1 else (13, 15)
        waypoints = [
            (23, 23),
            (22, 23),
            (23, 21),
            (19, 23),
            (23, 19),
        ]
        invisible = [(1, 3), (1, 5), (1, 7), (3, 3), (3, 5)]
        cfg = LevelConfig(
            number=5,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            trigger_tiles=[
                (t1[0], t1[1], "invert_controls", 4.0),
                (t2[0], t2[1], "invert_controls", 4.0),
            ],
            moving_exit_waypoints=waypoints,
            invisible_walls=invisible,
            halfway_gx=12,
        )
        return Level(cfg), start

    raise ValueError(f"Unknown level {number}")
