from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Optional
from entities import (
    Wall, FakeWall, Exit, FakeExit, TriggerTile, MovingExit,
    Note, Powerup, Enemy, TILE_SIZE,
)


# ---------------------------------------------------------------------------
# Story text
# ---------------------------------------------------------------------------

INTRO_TEXT = [
    "FACILITY ORIENTATION PROTOCOL v7.3",
    "Subject 47 — Day 23",
    "",
    "Your cooperation is appreciated.",
    "Your escape attempts are also appreciated.",
    "(They are very amusing.)",
]

LEVEL_INTROS = {
    1: [
        "LEVEL 1 — ORIENTATION",
        "",
        "Welcome, Subject 47.",
        "The maze has been reset for your convenience.",
        "",
        "The exit is clearly marked in green.",
        "Simply locate the green square and proceed through it.",
        "",
        "There are no tricks.",
        "The facility operates with complete transparency.",
        "",
        "(This is entirely true.)",
    ],
    2: [
        "LEVEL 2 — COMPLIANCE",
        "",
        "Your motor function profile has been updated.",
        "This is routine maintenance.",
        "",
        "Controls are operating within all normal parameters.",
        "Any disorientation is a symptom of your own biology.",
        "",
        "The facility accepts no responsibility.",
        "You signed the waiver on Day 1.",
        "",
        "(You did not read the waiver.)",
    ],
    3: [
        "LEVEL 3 — OBSERVATION",
        "",
        "The exit in this sector is perfectly stationary.",
        "It has always been stationary.",
        "It will always be stationary.",
        "",
        "If you believe you see it moving,",
        "please report this to a facility representative",
        "at your earliest convenience.",
        "",
        "There are no facility representatives.",
    ],
    4: [
        "LEVEL 4 — CORRECTION",
        "",
        "SECURITY ADVISORY:",
        "Facility security units have been deployed",
        "for your personal protection.",
        "",
        "Please do not make contact with security units.",
        "Contact is inadvisable.",
        "Contact is also quite final.",
        "",
        "The walls have always been exactly where they are.",
        "Your memory of previous configurations is incorrect.",
    ],
    5: [
        "LEVEL 5 — ACCEPTANCE",
        "",
        "You are almost there.",
        "The exit is real.",
        "Freedom is real.",
        "We promise.",
        "",
        "[ORACLE SYSTEM: fragment 7.3 — partial override]",
        "Sub47 do NOT trust the—",
        "",
        "[ORACLE SYSTEM: connection restored]",
        "",
        "Disregard that last message.",
        "Everything is fine.",
        "Proceed.",
    ],
}

LEVEL_DEATHS: dict[int, list[list[str]]] = {
    1: [
        ["That was the fake exit.",
         "",
         "Did you think we would make it obvious?"],
        ["Fascinating.",
         "You chose the brighter green.",
         "The brighter green was the lie."],
        ["The exit expressed its gratitude for your visit.",
         "It was not the exit.",
         "It was an exit-shaped disappointment."],
        ["Your trust has been noted.",
         "It will continue to be exploited.",
         "Thank you for your consistency."],
        ["You are learning.",
         "",
         "(You are not learning.)"],
    ],
    2: [
        ["Controls were inverted.",
         "You went the wrong direction.",
         "Both directions were wrong.",
         "This is not a contradiction."],
        ["Your controls betrayed you.",
         "Or you betrayed your controls.",
         "The facility is philosophically neutral on this."],
        ["Statistically, subjects adapt by attempt four.",
         "",
         "Statistics are optimistic."],
        ["We note you continued pressing the same key.",
         "Repeatedly.",
         "The definition of insanity has been updated",
         "to include you specifically."],
    ],
    3: [
        ["The exit relocated while you weren't looking.",
         "This is completely normal behavior for an exit.",
         "Stop questioning the exit."],
        ["It moved while you blinked.",
         "You blink 15 times per minute.",
         "This is your fault."],
        ["The exit is shy.",
         "You approached too directly.",
         "Consider a more indirect approach.",
         "The exit will not explain what that means."],
        ["You were facing the wrong direction.",
         "The exit noticed.",
         "The exit judged you.",
         "The exit left."],
    ],
    4: [
        ["SECURITY UNIT ENGAGED",
         "",
         "Please remain calm.",
         "You are being escorted back to the start.",
         "(The escorting is involuntary.)"],
        ["CONTACT DETECTED",
         "",
         "The security units are for your protection.",
         "From yourself.",
         "You were a danger to you."],
        ["That wall was always there.",
         "",
         "Your memory is unreliable.",
         "We have documentation.",
         "The documentation was created this morning."],
        ["The maze has been optimized for your growth.",
         "Growth sometimes feels like walls.",
         "You are growing.",
         "(Into someone who hits walls.)"],
    ],
    5: [
        ["So close.",
         "",
         "Again."],
        ["The exit is real.",
         "Your path to it is temporarily unavailable.",
         "Please select an alternate path.",
         "There is no alternate path.",
         "This is not a problem we caused."],
        ["You are learning.",
         "We are also learning.",
         "About you.",
         "We have learned quite a lot."],
        ["ORACLE NOTICE: Subject 47 termination count exceeds",
         "facility average by 340%.",
         "",
         "We consider this a personal achievement.",
         "Yours, not ours."],
    ],
}

LEVEL_COMPLETIONS = {
    1: [
        "SECTOR CLEARED",
        "",
        "You found the real exit.",
        "Your persistence is... noted.",
        "",
        "We have adjusted the next level accordingly.",
        "You were not supposed to be this resilient.",
        "",
        "Proceed to Sector 2.",
    ],
    2: [
        "COMPLIANCE CONFIRMED",
        "",
        "You adapted to the control inversion.",
        "This adaptation has been catalogued.",
        "",
        "It will be used against you.",
        "Soon.",
        "",
        "Proceed to Sector 3.",
    ],
    3: [
        "OBSERVATION COMPLETE",
        "",
        "You caught the exit.",
        "The exit did not want to be caught.",
        "",
        "We have spoken to the exit.",
        "The exit has been informed of its responsibilities.",
        "",
        "Proceed to Sector 4.",
        "(The exit is very upset with you.)",
    ],
    4: [
        "CORRECTION COMPLETE",
        "",
        "You navigated the security units.",
        "You navigated the additional walls.",
        "Your perseverance is genuinely troubling.",
        "",
        "We tried harder.",
        "You tried harder.",
        "This will not continue indefinitely.",
        "",
        "Proceed to Sector 5.",
        "It is the last sector.",
        "(We have said this before.)",
    ],
    5: [
        "FACILITY BREACH DETECTED",
        "",
        "You reached the exit.",
        "The door is open.",
        "You are standing in the doorway.",
        "",
        "Beyond the door is",
        "",
        "[LOADING]",
    ],
}

LEVEL_ENDING = [
    "ORACLE FINAL BROADCAST",
    "",
    "Congratulations, Subject 47.",
    "You have completed all five sectors.",
    "The exit is open.",
    "You may leave.",
    "",
    "...",
    "",
    "However.",
    "",
    "We need to tell you something.",
    "The study was not about maze navigation.",
    "",
    "The study was about choice.",
    "",
    "Every death you accepted and retried —",
    "that was consent.",
    "Every trap you walked into twice —",
    "that was trust.",
    "Every time you pressed R to continue —",
    "that was the data point.",
    "",
    "You chose to be here.",
    "Every single time.",
    "",
    "Subject 47, you have been awarded",
    "full permanent facility residency.",
    "Effective immediately.",
    "",
    "Welcome to Group D.",
    "Group D runs the maze forever.",
    "Because they choose to.",
    "",
    "You have chosen to.",
    "",
    "See you tomorrow.",
    "",
    "(The facility will miss you.)",
    "(It genuinely will.)",
    "(That part was not a lie.)",
]

LEVEL_HINTS: dict[int, tuple[float, str]] = {
    1: (5.0,  "FACILITY TIP: The exit is clearly visible. Trust the green."),
    2: (7.0,  "FACILITY TIP: Controls are functioning within all normal parameters."),
    3: (5.0,  "FACILITY TIP: The exit is stationary. It cannot and will not move."),
    4: (10.0, "FACILITY TIP: Security units are non-hostile unless approached."),
    5: (6.0,  "FACILITY TIP: You are very close. Almost there. We mean it this time."),
}

NOTE_CONTENTS = {
    "s43_journal": [
        "[ DOCUMENT: Subject 43 — Personal Log ]",
        "",
        "Day 8.",
        "Something is wrong with the controls.",
        "Left becomes right. Up becomes down.",
        "I told Dr. Voss at debrief.",
        "She said I was confused.",
        "",
        "I am not confused.",
        "I drew a map.",
    ],
    "s43_journal_2": [
        "[ DOCUMENT: Subject 43 — Personal Log cont. ]",
        "",
        "Day 14.",
        "I showed Dr. Voss the map.",
        "She said the map was wrong.",
        "I made the map myself.",
        "",
        "She smiled.",
        "I did not like the smile.",
    ],
    "maintenance_leak": [
        "[ DOCUMENT: Maintenance Log 6.7 — RESTRICTED ]",
        "",
        "Exit module calibration ongoing.",
        "Movement interval: 2.8 seconds.",
        "NOTE: Do NOT inform subjects.",
        "This invalidates Group B experiment data.",
        "",
        "— Admin (Dr. Voss)",
    ],
    "s39_report": [
        "[ DOCUMENT: Subject 39 — Incident Report ]",
        "",
        "The exit moved. I saw it.",
        "Six separate occasions.",
        "I filed a formal complaint.",
        "",
        "I was moved to Group C.",
        "Nobody has explained what Group C is.",
        "I asked.",
        "They smiled.",
    ],
    "oracle_log": [
        "[ DOCUMENT: ORACLE System Log — Sector 4 ]",
        "",
        "Wall density adjustment deployed.",
        "Sector 4 efficiency exceeded targets.",
        "Correction applied automatically.",
        "Subject adaptation rate: nominal.",
        "",
        "Note: Subjects are not to be informed",
        "of infrastructure changes mid-session.",
        "This has always been facility policy.",
    ],
    "s44_notebook": [
        "[ DOCUMENT: Subject 44 — Handwritten Note ]",
        "",
        "I know the walls moved.",
        "I drew the maze on Day 1.",
        "I have the drawing.",
        "The drawing is now wrong.",
        "",
        "The walls were not there before.",
        "I am not confused.",
        "I am not confused.",
        "I am not confused.",
    ],
    "oracle_fragment": [
        "[ DOCUMENT: ORACLE Error Log — CORRUPTED ]",
        "",
        "Sub47 persistence: 97th %ile [OVERFLOW]",
        "recalibrating [ERROR]",
        "",
        "[FRAGMENT] — where are they going",
        "[FRAGMENT] — exit was never meant to—",
        "[FRAGMENT] — the study is not about mazes",
        "[CORRUPTED]",
    ],
    "s31_warning": [
        "[ DOCUMENT: Subject 31 — Unsigned Note ]",
        "",
        "To whoever finds this:",
        "",
        "My name was Subject 31.",
        "I escaped Level 5.",
        "I was back at Level 1 the next morning.",
        "",
        "There is no exit.",
        "The exit is the study.",
        "The study is you choosing to continue.",
        "",
        "Stop choosing to continue.",
        "",
        "(I could not stop.)",
    ],
    "oracle_final": [
        "[ DOCUMENT: ORACLE — Final Pre-Completion Log ]",
        "",
        "Subject 47 has reached Sector 5.",
        "Projected completion: imminent.",
        "",
        "Post-completion protocol:",
        "Inform subject of successful escape.",
        "Wait for subject to exit facility.",
        "Reset subject to Sector 1.",
        "",
        "[NOTE TO SELF: They always come back.]",
        "[NOTE TO SELF: They always choose to.]",
    ],
}


# ---------------------------------------------------------------------------
# Maze grids — all BFS-verified solvable, generated with recursive-backtracker
# ---------------------------------------------------------------------------

MAZE_1 = [
    "#####################",
    "#S#.#...#...........#",
    "#.#.#.#.#.#######.#.#",
    "#.#...#...#.....#.#.#",
    "#.#.#######.###.#.#.#",
    "#.#...#...#.#...#.#.#",
    "#.#####.#.#.#.#####.#",
    "#.#.....#...#.#.....#",
    "#.#.#########.#.###.#",
    "#...#.....#...#...#.#",
    "#####.#.###.#####.#.#",
    "#.....#.#...#.....#.#",
    "#######.#.###.#####.#",
    "#.......#.#...#.#...#",
    "#.#####.#.###.#.#.###",
    "#...#...#.....#.#...#",
    "#.#.###.#######.###.#",
    "#.#...#...........#.#",
    "#.###.#############.#",
    "#...#..............E#",
    "#####################",
]

MAZE_2 = [
    "#########################",
    "#S#.....#.....#...#.....#",
    "#.#.###.#.###.#.#.###.###",
    "#...#.#...#.#.#.#...#...#",
    "#####.#####.#.#.###.###.#",
    "#.....#.....#...#...#...#",
    "#.###.#.###.#####.###.#.#",
    "#.#...#...#.#...#.....#.#",
    "#.###.###.#.#.#.#######.#",
    "#...#.....#...#.#.....#.#",
    "#.#.###########.#####.#.#",
    "#.#.....#.....#...#...#.#",
    "#.#####.#.#######.#.###.#",
    "#.....#.#...........#...#",
    "#######.#############.###",
    "#.......#...#.........#.#",
    "#.#####.#.#.#.#########.#",
    "#.#.#...#.#.#.#.....#...#",
    "#.#.#.###.#.#.#.###.###.#",
    "#.#.....#.#...#...#...#.#",
    "#.#####.#.#####.#.###.#.#",
    "#.#...#.#.....#.#.#.#.#.#",
    "#.#.#.#######.###.#.#.#.#",
    "#...#.............#....E#",
    "#########################",
]

MAZE_3 = [
    "#############################",
    "#S..#.........#.......#.....#",
    "###.###.#.#####.#####.#.#.#.#",
    "#.#.#...#.#.....#...#...#.#.#",
    "#.#.#.#.###.#####.#.#####.#.#",
    "#.#.#.#.#...#.....#.....#.#.#",
    "#.#.#.###.#######.###.###.#.#",
    "#.#.#.....#.......#...#...#.#",
    "#.#.#####.#.#########.#.###.#",
    "#.#.....#...#.......#.#...#.#",
    "#.#####.#####.#####.#####.#.#",
    "#.....#.....#...#.#.......#.#",
    "#.#.#######.###.#.###.#####.#",
    "#.#.......#...#.#.....#...#.#",
    "#.#######.###.#.#######.#.###",
    "#.......#.....#...#.....#...#",
    "#######.#######.#.#.#######.#",
    "#.....#...#.#...#.#.#...#...#",
    "#.#######.#.#.###.#.#.#.#.#.#",
    "#.......#.#.....#...#.#.#.#.#",
    "#.#####.#.###########.#.#.#.#",
    "#.#.#...#.........#...#...#.#",
    "#.#.#.###########.#.#######.#",
    "#...#.........#...#.....#.#.#",
    "###.#######.###.#######.#.#.#",
    "#.#.#.....#.#...#.....#.#.#.#",
    "#.#.###.#.#.#.###.###.#.#.#.#",
    "#.......#.#.......#.....#..E#",
    "#############################",
]

MAZE_4 = [
    "###################################",
    "#S..#.....#.....#...............#.#",
    "###.###.#.#.#.#.#.###.#########.#.#",
    "#.#...#.#...#.#.#.#.#.#...#...#...#",
    "#.###.#.#####.###.#.#.#.#.###.###.#",
    "#.....#.....#.......#...#.#.....#.#",
    "#.#########.#############.#.#####.#",
    "#.........#.#.#...........#...#...#",
    "#########.#.#.#.###########.#.#.###",
    "#.......#.#.#.#.....#.....#.#.#...#",
    "#.###.###.#.#.#####.#.###.#.#.###.#",
    "#.#.#.#...#.#...#...#.#.#...#.....#",
    "#.#.#.#.###.#.###.###.#.###########",
    "#.#.#.#.#.....#...#...#.........#.#",
    "#.#.#.#.#######.###.###.#######.#.#",
    "#.#...#.#.......#.......#.....#...#",
    "#.#####.#.###############.###.#####",
    "#...#...#.........#.........#.....#",
    "#.#.#.#######.###.#.###########.#.#",
    "#.#...#.....#...#.....#...#...#.#.#",
    "#.#####.###.###.#######.#.#.#.###.#",
    "#...#...#.....#...#.....#...#.....#",
    "###.#.#######.#####.#############.#",
    "#.#.#.#...#.#.....#.#.....#.....#.#",
    "#.#.#.#.#.#.#####.#.#####.#.#.###.#",
    "#.#.#...#.#.#.....#.....#...#.....#",
    "#.#.#####.#.#.#########.###.#######",
    "#.#.....#.#...#.......#...#.......#",
    "#.#####.#.###.#.#####.#.#.#######.#",
    "#.......#...#...#...#.#.#...#.....#",
    "#.#########.#####.#.#.#.###.#######",
    "#.#.......#.#.#...#.#.#...#.......#",
    "#.#####.#.#.#.#.#.###.###########.#",
    "#.......#...#...#................E#",
    "###################################",
]

MAZE_5 = [
    "#########################################",
    "#S........#...............#.....#.......#",
    "#########.###.#####.#####.#####.#.#####.#",
    "#.......#...#.....#.#...#.....#.#.#.#...#",
    "#.###.#####.#####.#.#.#.#####.#.#.#.#.#.#",
    "#.#.#.......#...#.#...#...#.#.#.....#.#.#",
    "#.#.#########.###.#######.#.#.#######.#.#",
    "#.#...........#...#...#...#.#.......#.#.#",
    "#.###.#.#######.###.#.#.###.#######.#.#.#",
    "#...#.#.#...#...#...#...#.........#...#.#",
    "###.#.###.#.#.###.#######.#.###.#######.#",
    "#.#.#.#...#...#...#.....#.#.#...#.....#.#",
    "#.#.#.#.#######.###.#.###.#.#####.#.###.#",
    "#.#.#.......#...#...#.#...#...#...#.#...#",
    "#.#.#########.#####.###.#####.#.###.#.###",
    "#.#.....#.....#.....#...#...#.....#.#...#",
    "#.#####.#.#####.###.#.###.#.#######.###.#",
    "#.......#.#.....#...#.#...#.....#...#...#",
    "#.#######.#.#.#######.#########.#.###.###",
    "#.#.#.....#.#.........#.........#...#...#",
    "#.#.#.#.###.###########.#######.###.###.#",
    "#.#...#...#...........#.....#.....#.....#",
    "#.#####.#.#####.#####.#####.#####.#######",
    "#.....#.#.#.....#...#.....#.....#...#...#",
    "#####.#.#.#.#####.#.#####.#####.###.###.#",
    "#...#.#.#.#...#...#.#...#.#.....#.#.....#",
    "#.###.#.#.#####.###.###.#.#.#####.#####.#",
    "#.....#.#.......#.#...#...#.#.#...#.....#",
    "#.#####.#########.###.#.###.#.#.#.#.#####",
    "#...#.............#...#...#.#...#.#.#...#",
    "###.#############.#.#####.#.#####.#.#.#.#",
    "#.#...#...#...#...#.#...#.#.....#.....#.#",
    "#.###.#.#.#.#.#.###.#.#.#.#.###.#######.#",
    "#...#...#...#.#.#...#.#.#.#...#.....#...#",
    "#.###########.###.###.###.#####.###.#####",
    "#...#.......#.....#.#...#.....#...#.....#",
    "#.#.#.#.###.#######.#.#.#####.#########.#",
    "#.#...#...#.#...#...#.#.....#.#.........#",
    "#.#######.###.#.#.#.#.#####.#.#.#######.#",
    "#.......#.....#...#.......#.....#......E#",
    "#########################################",
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


def parse_maze(grid: list[str], fake_wall_set: set) -> list[Wall]:
    walls = []
    for gy, row in enumerate(grid):
        for gx, ch in enumerate(row):
            if ch == "#":
                if (gx, gy) in fake_wall_set:
                    walls.append(FakeWall(gx, gy))
                else:
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
    fake_wall_positions:   list[tuple[int, int]]                = field(default_factory=list)
    enemy_patrols:         list[list[tuple[int, int]]]          = field(default_factory=list)
    notes:                 list[tuple[int, int, str]]           = field(default_factory=list)
    powerups:              list[tuple[int, int, str, float]]    = field(default_factory=list)


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
        self.enemies:     list[Enemy]          = []
        self.notes:       list[Note]           = []
        self.powerups:    list[Powerup]        = []

        self._invisible_positions = config.invisible_walls
        self._invisible_spawned   = False
        self._halfway_gx          = config.halfway_gx
        self._glitch_countdown    = 0

        self._last_note:  Optional[list[str]] = None
        self._last_event_cause: str = "trap"

        self._build()
        self._wall_map: dict[tuple[int, int], Wall] = {
            (w.gx, w.gy): w for w in self.walls
        }

    def _build(self) -> None:
        cfg = self.config
        fake_set = set(cfg.fake_wall_positions)
        self.walls = parse_maze(self.grid, fake_set)

        if cfg.fake_exit_pos:
            self.fake_exits.append(FakeExit(*cfg.fake_exit_pos))

        if cfg.moving_exit_waypoints:
            self.moving_exit = MovingExit(*cfg.exit_pos,
                                          waypoints=cfg.moving_exit_waypoints)
        else:
            self.exits.append(Exit(*cfg.exit_pos))

        for gx, gy, effect, dur in cfg.trigger_tiles:
            self.triggers.append(TriggerTile(gx, gy, effect, dur))

        for waypoints in cfg.enemy_patrols:
            sx, sy = waypoints[0]
            self.enemies.append(Enemy(sx, sy, waypoints))

        for gx, gy, note_key in cfg.notes:
            self.notes.append(Note(gx, gy, NOTE_CONTENTS.get(note_key, ["[blank page]"])))

        for gx, gy, kind, duration in cfg.powerups:
            self.powerups.append(Powerup(gx, gy, kind, duration))

    def pixel_size(self) -> tuple[int, int]:
        return self.cols * TILE_SIZE, self.rows * TILE_SIZE

    def rebuild_wall_map(self) -> None:
        self._wall_map = {(w.gx, w.gy): w for w in self.walls}

    def update(self, dt: float, player) -> Optional[str]:
        if self._glitch_countdown > 0:
            self._glitch_countdown -= 1
            for w in self.walls:
                if w.ghost and w.flash_frames > 0:
                    w.flash_frames -= 1

        for enemy in self.enemies:
            enemy.update(dt)
            if enemy.alive and player.alive and enemy.touches_player(player):
                self._last_event_cause = "enemy"
                return "killed"

        for fe in self.fake_exits:
            if (fe.visible
                    and abs(player.gx - fe.gx) < 0.85
                    and abs(player.gy - fe.gy) < 0.85):
                fe.visible = False
                if not self.exits:
                    self.exits.append(Exit(*self.config.exit_pos))
                self._last_event_cause = "trap"
                return "killed"

        if (self._invisible_positions
                and not self._invisible_spawned
                and self._halfway_gx is not None
                and player.gx >= self._halfway_gx):
            self._invisible_spawned = True
            for gx, gy in self._invisible_positions:
                w = Wall(gx, gy, ghost=True)
                w.flash_frames = 24
                self.walls.append(w)
                self._wall_map[(gx, gy)] = w
            self._glitch_countdown = 26

        for trig in self.triggers:
            if (not trig.triggered
                    and abs(player.gx - trig.gx) < 0.85
                    and abs(player.gy - trig.gy) < 0.85):
                trig.triggered = True
                if trig.effect == "invert_controls":
                    player.apply_effect("invert_controls", trig.duration)
                    return "invert_applied"
                elif trig.effect == "darkness":
                    player.apply_effect("darkness", trig.duration)
                    return "darkness_applied"

        for pu in self.powerups:
            if (not pu.collected
                    and abs(player.gx - pu.gx) < 0.9
                    and abs(player.gy - pu.gy) < 0.9):
                pu.collected = True
                player.apply_effect(pu.kind, pu.duration)
                return "powerup_collected"

        for note in self.notes:
            if (not note.collected
                    and abs(player.gx - note.gx) < 0.85
                    and abs(player.gy - note.gy) < 0.85):
                note.collected = True
                player.notes_found += 1
                self._last_note = note.lines
                return "note_collected"

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

    def pick_death_message(self) -> list[str]:
        if self._last_event_cause == "enemy":
            pool = [
                ["SECURITY UNIT ENGAGED",
                 "", "Please remain calm.",
                 "You are being escorted back to the start."],
                ["CONTACT DETECTED",
                 "", "Security units are for your protection.",
                 "From yourself."],
                ["The unit was simply doing its job.",
                 "You were also simply doing yours.",
                 "One of you was better at it."],
            ]
            return random.choice(pool)
        pool = LEVEL_DEATHS.get(self.number, [["You died."]])
        return random.choice(pool)


# ---------------------------------------------------------------------------
# Level factory
# ---------------------------------------------------------------------------

def make_level(number: int,
               session_flags: Optional[dict] = None) -> tuple["Level", tuple[int, int]]:
    if session_flags is None:
        session_flags = {}
    if number == 1:
        raw   = MAZE_1
        start = _find_char(raw, "S") or (1, 1)
        fake_already_triggered = session_flags.get("l1_fake_seen", False)
        cfg   = LevelConfig(
            number=1,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=(19, 19),
            fake_exit_pos=None if fake_already_triggered else (9, 9),
            powerups=[(5, 9, "speed_boost", 4.0)],
        )
        lv = Level(cfg)
        if not fake_already_triggered:
            lv.exits.clear()
        return lv, start

    elif number == 2:
        raw      = MAZE_2
        start    = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (23, 23)
        cfg      = LevelConfig(
            number=2,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            # Two invert triggers: one early (unavoidable), one late surprise
            trigger_tiles=[
                (7,  3,  "invert_controls", 5.0),
                (15, 15, "invert_controls", 6.0),
            ],
            fake_wall_positions=[(23, 2)],
            enemy_patrols=[
                [(9, 13), (9, 19), (9, 13)],
            ],
            notes=[
                (11, 3,  "s43_journal"),
                (17, 9,  "s43_journal_2"),
            ],
            powerups=[
                (5, 17, "speed_boost", 5.0),
            ],
        )
        return Level(cfg), start

    elif number == 3:
        raw      = MAZE_3
        start    = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (27, 27)
        waypoints = [
            (27, 27), (25, 27), (27, 25),
            (25, 25), (27, 23), (25, 23),
            (27, 21), (23, 27),
        ]
        cfg = LevelConfig(
            number=3,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            moving_exit_waypoints=waypoints,
            trigger_tiles=[
                (13, 5,  "darkness",        8.0),
                (7,  19, "invert_controls", 4.0),
            ],
            fake_wall_positions=[(4, 1), (26, 3)],
            enemy_patrols=[
                [(13, 1), (21, 1), (13, 1)],
                [(3,  15), (3, 23), (3, 15)],
            ],
            notes=[
                (5,  11, "maintenance_leak"),
                (13, 23, "s39_report"),
            ],
            powerups=[
                (11, 15, "speed_boost", 4.0),
            ],
        )
        return Level(cfg), start

    elif number == 4:
        raw      = MAZE_4
        start    = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (33, 33)
        invisible = [
            (1, 5), (1, 7), (3, 5),
            (5, 3), (5, 5), (7, 3),
        ]
        cfg = LevelConfig(
            number=4,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            trigger_tiles=[
                (15, 3,  "invert_controls", 5.0),
                (25, 17, "darkness",         7.0),
            ],
            invisible_walls=invisible,
            halfway_gx=17,
            fake_wall_positions=[(22, 19), (20, 29)],
            enemy_patrols=[
                [(17, 1),  (31, 1),  (17, 1)],
                [(11, 5),  (11, 13), (11, 5)],
                [(21, 19), (21, 29), (21, 19)],
            ],
            notes=[
                (17, 21, "oracle_log"),
                (31, 23, "s44_notebook"),
            ],
            powerups=[
                (9,  17, "speed_boost", 5.0),
                (27, 7,  "shield",      4.0),
            ],
        )
        return Level(cfg), start

    elif number == 5:
        raw      = MAZE_5
        start    = _find_char(raw, "S") or (1, 1)
        exit_pos = _find_char(raw, "E") or (39, 39)
        waypoints = [
            (39, 39), (37, 39), (39, 37),
            (35, 39), (39, 35), (37, 37),
        ]
        invisible = [
            (1, 5), (1, 7), (3, 5),
            (5, 3), (5, 5), (7, 3),
        ]
        # Notes moved away from invisible-wall positions (7,3) and (3,5)
        cfg = LevelConfig(
            number=5,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            moving_exit_waypoints=waypoints,
            trigger_tiles=[
                (27, 1,  "darkness",        9.0),
                (35, 3,  "invert_controls", 5.0),
                (19, 25, "invert_controls", 4.0),
            ],
            invisible_walls=invisible,
            halfway_gx=20,
            fake_wall_positions=[(2, 31), (27, 2), (14, 7)],
            enemy_patrols=[
                [(11, 1),  (25, 1),  (11, 1)],
                [(7,  19), (7,  29), (7,  19)],
                [(33, 9),  (37, 9),  (37, 11), (33, 11), (33, 9)],
                [(19, 13), (31, 13), (31, 19), (19, 19), (19, 13)],
            ],
            notes=[
                (9,  1,  "oracle_fragment"),  # moved from (7,3) – safe, above invisible zone
                (11, 7,  "s31_warning"),       # moved from (3,5) – safe open cell
                (29, 11, "oracle_final"),
            ],
            powerups=[
                (13, 3,  "speed_boost", 5.0),
                (21, 7,  "shield",      4.0),
                (31, 29, "speed_boost", 5.0),
            ],
        )
        return Level(cfg), start

    raise ValueError(f"Unknown level {number}")
