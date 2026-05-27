# Maze Runner: Deception

> "Subject 47, escape the facility. Or try."

A psychological troll-platformer maze game built entirely with Python's standard library.
The facility is designed to study your obedience and hope.

---

## Setup

**Requirements:** Python 3.10+ (no external dependencies)

```bash
cd maze_runner_deception
python main.py
```

That's it.

---

## Controls

| Key | Action |
|-----|--------|
| `WASD` / Arrow Keys | Move |
| `R` | Restart current level |
| `ESC` | Return to main menu |
| `Enter` | Confirm / skip intro |

---

## Levels

### Level 1 — Orientation
The maze is simple. The exit is clearly marked.
**Trap:** The first exit you find kills you. The real exit appears afterward.
The facility did not consider this deceptive.

### Level 2 — Compliance
Your controls are perfectly normal.
**Trap:** A trigger tile in the maze inverts your controls for 4 seconds.
Any disorientation is your own fault.

### Level 3 — Observation
The exit is stationary. It has always been stationary.
**Trap:** The exit teleports to a new position every few seconds — *unless*
you are facing it directly. Observation prevents movement.

### Level 4 — Correction
The walls have always been there.
**Trap:** After crossing the maze halfway, invisible walls materialize
behind you. The maze you entered is not the maze you are in.

### Level 5 — Acceptance
You are so close. Freedom is just ahead.
**Trap:** Combines inverted controls, a moving exit, and invisible walls.
The ending explains everything.

---

## Scoring

```
Score = (5000 × level) + time_bonus − (200 × deaths)

Time bonus = max(0, (60 − elapsed_seconds) × 100)
```

Higher scores reward speed and surviving without dying.

---

## File Overview

```
maze_runner_deception/
│
├── main.py       Bootstrap, window setup, entry point
├── game.py       Game loop, input, collision, rendering
├── levels.py     Maze definitions, trap logic, story text
├── entities.py   Player, Wall, Exit, TriggerTile classes
├── ui.py         HUD, menus, overlays, transition screens
└── README.md     This file
```

### Architecture

- **`GameController`** (game.py) — central orchestrator; owns the `root.after()` loop
- **`GameState`** — enum-like string constants for scene management
- **`Level`** (levels.py) — owns wall/exit/trigger collections; ticks trap logic each frame
- **`Player`** (entities.py) — sub-tile movement with axis-separated collision resolution
- **`UIManager`** (ui.py) — all canvas drawing isolated from game logic

---

## The Traps (spoilers)

| Level | Trap | Trigger |
|-------|------|---------|
| 1 | Fake exit → instant death | Reaching the green tile |
| 2 | Control inversion | Stepping on invisible trigger tile |
| 3 | Exit teleports away | Not facing the exit every 2.5 s |
| 4 | Invisible walls spawn | Crossing x = halfway |
| 5 | All of the above | Existing |

---

## Notes

- The narrator is not reliable.
- The exit is not always where it appears to be.
- Your deaths have been logged.
- The facility thanks you for your cooperation.
