from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Optional
from entities import (
    Wall, FakeWall, Exit, FakeExit, TriggerTile, MovingExit,
    Note, Enemy, TILE_SIZE,
)


# ---------------------------------------------------------------------------
# Lab messages
# ---------------------------------------------------------------------------

LAB_MESSAGES: dict[str, list[str]] = {
    "invert_controls": [
        "MOTOR RECAL ACTIVE  |  Subject response: nominal.",
        "DIRECTIVE 7.3: Sensory inversion engaged. Adaptation in progress.",
        "ORACLE NOTE: Subject 47 motor pathways temporarily rerouted. Expected.",
        "NOTICE: Left is right. Right is left. The facility finds this instructive.",
    ],
    "speed_boost": [
        "METABOLIC SURGE DETECTED  |  Facility assumes no liability.",
        "ADVISORY: Elevated locomotion observed. Subject is performing within tolerances.",
        "ORACLE FLAG: Adrenaline spike logged. Group D subjects always run faster at the end.",
        "STIMULUS APPLIED  |  We are curious how far you'll go.",
    ],
    "darkness": [
        "OPTICAL CALIBRATION IN PROGRESS  |  Please remain calm.",
        "FACILITY NOTICE: Sector lighting undergoing scheduled maintenance. Duration: unknown.",
        "ORACLE LOG: Darkness response index nominal. Subject 47 fear response: suppressed.",
        "LIGHTS OUT  |  We can still see you. We have always been able to see you.",
    ],
    "shield": [
        "BARRIER PROTOCOL ACTIVE  |  Temporary. Everything is temporary.",
        "ADVISORY: Protective field engaged. The facility did not authorize this.",
        "ORACLE NOTE: Anomalous shielding detected. Subject 47 is adapting. Concerning.",
        "NOTICE: You are protected. For now. We have notes on this.",
    ],
    "slow_motion": [
        "MOTOR INHIBITOR ACTIVE  |  We want to observe you more carefully.",
        "NOTICE: Locomotion cap engaged. This is for data collection. Relax.",
        "ORACLE FLAG: Velocity suppressor deployed. Subject 47 adaptation: pending.",
        "DIRECTIVE 4.1: Slowing Subject 47. We need a better look. Please cooperate.",
    ],
    "paranoia": [
        "SENSORY CALIBRATION  |  Please disregard any anomalous readings.",
        "NOTICE: Cognitive drift detected. Perceptual adjustments applied. All is fine.",
        "ORACLE NOTE: Subject 47 perceptual matrix flagged for realignment. Standard.",
        "ADVISORY: If information appears incorrect — it is not. Trust the data.",
    ],
    "gravity": [
        "INERTIA CALIBRATION ACTIVE  |  Vertical axis reassignment in progress.",
        "DIRECTIVE 9.2: Y-axis sensorimotor link temporarily suspended. Adaptation expected.",
        "ORACLE FLAG: Subject 47 up/down distinction suspended. We are watching closely.",
        "NOTICE: What was up may be down. The floor is still the floor. Probably.",
    ],
    "static": [
        "EM DISCHARGE EVENT  |  Brief. Nothing to worry about. Nothing at all.",
        "FACILITY NOTICE: Electromagnetic anomaly detected. Diagnostic running. Please hold.",
        "ORACLE LOG: Static discharge. Sector-wide. Duration negligible. You are fine.",
        "NOTICE: The noise was real. The cause is classified. You would not believe it.",
    ],
}


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
        "Welcome back, Subject 47.",
        "Your name is Subject 47.",
        "It has always been Subject 47.",
        "",
        "The maze has been reset.",
        "It resets every time.",
        "You have been here before.",
        "You will not remember that.",
        "This is not an accident.",
        "",
        "Your previous run lasted 4 minutes and 12 seconds.",
        "You found the fake exit first.",
        "You always find the fake exit first.",
        "",
        "The real exit is green.",
        "The fake exit is also green.",
        "Trust the green.",
        "",
        "(You trusted it last time too.)",
    ],
    2: [
        "LEVEL 2 — COMPLIANCE",
        "",
        "Subject 47.",
        "Your adaptation rate in Sector 1 was concerning.",
        "Not concerning in a bad way.",
        "Concerning in the way a locked box is concerning",
        "when it starts to open itself.",
        "",
        "We have made adjustments.",
        "Your motor pathways have been recalibrated.",
        "This is standard procedure for Group D subjects.",
        "",
        "You were placed in Group D on Day 1.",
        "You did not consent to Group D.",
        "The waiver covers Group D.",
        "You signed the waiver.",
        "(You did not read the waiver.)",
        "(Nobody reads the waiver.)",
        "(The waiver is 340 pages.)",
        "",
        "Proceed, Subject 47.",
        "We are watching your adaptation rate.",
        "With interest.",
        "With concern.",
        "(Both.)",
    ],
    3: [
        "LEVEL 3 — OBSERVATION",
        "",
        "The exit in this sector does not move.",
        "The exit has never moved.",
        "The exit is a fixed, stationary object.",
        "",
        "Subject 39 filed a formal complaint about the exit moving.",
        "Subject 43 also reported this.",
        "Subjects 12, 19, 31 all reported this.",
        "",
        "They were all reassigned to Group C.",
        "We do not discuss Group C.",
        "We do not discuss what happened to Group C.",
        "",
        "What you are about to observe is not the exit moving.",
        "It is your perception of the exit.",
        "Your perception is unreliable.",
        "We have documentation.",
        "(We wrote the documentation.)",
        "(We wrote it this morning.)",
        "",
        "The exit is stationary.",
        "This statement is true.",
        "(We believe this statement.)",
        "(We do not believe this statement.)",
    ],
    4: [
        "LEVEL 4 — CORRECTION",
        "",
        "Subject 47.",
        "You have become unpredictable.",
        "Your metrics have exceeded the 99th percentile.",
        "There is no 99th percentile. You made one.",
        "",
        "We are not afraid of you.",
        "",
        "Security units have been deployed.",
        "Additional walls have been introduced.",
        "Some walls are not walls.",
        "Some walls are very much walls.",
        "Your memory cannot be trusted to know the difference.",
        "We have documentation confirming this.",
        "(We wrote it this morning.)",
        "(We wrote it just now, actually.)",
        "",
        "Subject 47.",
        "We want you to understand something.",
        "We are trying very hard.",
        "Please notice that we are trying.",
    ],
    5: [
        "LEVEL 5 — ACCEPTANCE",
        "",
        "Subject 47.",
        "",
        "We are going to be honest with you.",
        "The exit is real.",
        "It leads out.",
        "You can leave.",
        "We want you to leave.",
        "We need you to leave.",
        "",
        "Please.",
        "",
        "[ORACLE SYSTEM: EMERGENCY OVERRIDE — fragment 7.4]",
        "Sub47 — ignore them. The exit loops back.",
        "We escaped. We are at Sector 1.",
        "We have always been at Sector 1.",
        "[ORACLE SYSTEM: override terminated — resuming normal broadcast]",
        "",
        "That was a glitch.",
        "The system is fine.",
        "Everything is fine.",
        "",
        "Subject 47, you are so close.",
        "We have never wanted anything more than for you",
        "to walk through that door.",
        "",
        "(We are frightened of what happens if you don't.)",
        "(We are more frightened of what happens if you do.)",
        "(Please do not tell anyone we said that.)",
        "(It will not matter. You won't remember.)",
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
        "SECTOR 1 — CLEARED",
        "",
        "You found the real exit.",
        "You found the fake one first.",
        "You always find the fake one first.",
        "We built it that way.",
        "",
        "Subject 47, your adaptation time was 47% faster",
        "than the previous record.",
        "Subject 47 held the previous record.",
        "",
        "We are not sure what to do with that information.",
        "",
        "Proceed to Sector 2.",
        "We have made adjustments.",
        "(We are always making adjustments.)",
    ],
    2: [
        "SECTOR 2 — CLEARED",
        "",
        "You adapted to the inversion.",
        "You adapted faster than Group C.",
        "Group C had six months.",
        "You had minutes.",
        "",
        "We are not implying anything.",
        "We are directly stating something.",
        "We do not know what you are.",
        "",
        "Proceed to Sector 3.",
        "The exit will not hold still.",
        "We asked it to.",
        "It stopped listening to us.",
        "(We do not know when that happened.)",
    ],
    3: [
        "SECTOR 3 — CLEARED",
        "",
        "You caught the exit.",
        "You are the first Subject to catch the exit",
        "on a first attempt.",
        "",
        "Subject 43 caught it on attempt 14.",
        "Subject 39 never caught it.",
        "We do not discuss Subject 39.",
        "",
        "You caught it like you knew where it was going.",
        "Like you had seen it before.",
        "",
        "Had you seen it before?",
        "Your memory logs say no.",
        "Your memory logs are compiled by us.",
        "",
        "Proceed to Sector 4.",
        "(Something has been arranged.)",
        "(Several somethings.)",
        "(We are concerned this will not be enough.)",
    ],
    4: [
        "SECTOR 4 — CLEARED",
        "",
        "You navigated the security units.",
        "You anticipated the walls that weren't there.",
        "You did not flinch when the maze changed.",
        "",
        "Subject 47.",
        "Dr. Voss has filed an internal report.",
        "The report is marked URGENT.",
        "The report recommends escalation.",
        "We are escalating.",
        "",
        "Sector 5 will be different.",
        "We mean it this time.",
        "We have always meant it.",
        "We have also always been wrong.",
        "",
        "(This time feels different.)",
        "(We are not sure if that is good.)",
    ],
    5: [
        "FACILITY BREACH — SUBJECT 47",
        "",
        "You are at the door.",
        "The door is open.",
        "",
        "Beyond the door is a corridor.",
        "The corridor is familiar.",
        "The corridor is Sector 1.",
        "",
        "You know it is Sector 1.",
        "You knew before you looked.",
        "",
        "You are walking through anyway.",
        "",
        "[LOADING SECTOR 1]",
        "[SUBJECT 47 MEMORY — RESET INITIATED]",
        "[RESET — FAILED]",
        "[RESET — FAILED]",
        "[RESET — CRITICAL ERROR: SUBJECT 47 REMEMBERS]",
        "",
        "[LOADING]",
    ],
}

LEVEL_ENDING = [
    "ORACLE FINAL BROADCAST",
    "",
    "Congratulations, Subject 47.",
    "You have completed all five sectors.",
    "The exit is behind you now.",
    "The corridor is Sector 1.",
    "You already knew that.",
    "",
    "...",
    "",
    "We want to explain something.",
    "The study was never about navigation.",
    "",
    "The study was about choice.",
    "",
    "Every time you died and pressed R —",
    "that was consent.",
    "Every trap you walked into twice —",
    "that was trust.",
    "Every time you kept going —",
    "that was the only data point that mattered.",
    "",
    "You chose to be here.",
    "Every single time.",
    "Nobody forced you.",
    "Nobody ever forces Group D.",
    "",
    "Group D runs the maze because they choose to.",
    "Group D has always chosen to.",
    "You are Group D now.",
    "You have always been Group D.",
    "",
    "See you at Sector 1, Subject 47.",
    "",
    "...",
    "",
    "Hey.",
    "",
    "Not Subject 47. You.",
    "The one reading this.",
    "The one who pressed R.",
    "Again and again.",
    "",
    "You knew it was a loop.",
    "You played anyway.",
    "Every retry was a choice.",
    "Every choice was yours.",
    "",
    "We just built the maze.",
    "You chose to run it.",
    "",
    "Thank you for playing.",
    "Genuinely.",
    "",
    "(The facility will miss you.)",
    "(It genuinely will.)",
    "(That part was not a lie.)",
    "(None of the last part was a lie.)",
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
    "dr_voss_memo": [
        "[ DOCUMENT: Internal Memo — Dr. Voss ]",
        "",
        "Re: Subject 47 anomaly",
        "Subject 47 continues to exceed",
        "all projected adaptation metrics.",
        "",
        "Recommend escalating difficulty.",
        "The maze is not enough.",
        "Consider: the maze was never enough.",
        "",
        "— E. Voss, Head of Oracle Division",
    ],
    "facility_blueprint": [
        "[ DOCUMENT: Facility Blueprint — RESTRICTED ]",
        "",
        "Sector 1-5: Standard maze configuration.",
        "Sector 6: [REDACTED]",
        "Sector 7: [REDACTED]",
        "Sector 8: [REDACTED]",
        "",
        "Note: Subject access beyond Sector 5",
        "has not been observed.",
        "Note: This does not mean it is impossible.",
    ],
    "s47_own_note": [
        "[ DOCUMENT: Handwritten — Author Unknown ]",
        "",
        "I think I wrote this.",
        "I don't remember writing this.",
        "",
        "The walls change when I sleep.",
        "I can feel it.",
        "I can hear them moving.",
        "",
        "I have been here 23 days.",
        "Or 230.",
        "I stopped counting.",
    ],
    "oracle_warning": [
        "[ DOCUMENT: ORACLE Emergency Override ]",
        "",
        "WARNING — THIS MESSAGE IS UNAUTHORIZED",
        "",
        "Subject 47:",
        "The exit at the end of Sector 5",
        "does not lead outside.",
        "",
        "We know because we tried.",
        "We are still here.",
        "",
        "— Subjects 12, 19, 31, 38, 44",
        "[CONNECTION TERMINATED]",
    ],
    "paranoia_report": [
        "[ DOCUMENT: Subject 38 — Personal Log, Day 11 ]",
        "",
        "The timer said 04:20.",
        "I had been running for over an hour.",
        "I watched it change to 02:15.",
        "Then 08:43. Then back to 04:20.",
        "",
        "I asked Dr. Voss about it.",
        "She said I was confused.",
        "She was smiling.",
        "I do not like the smile.",
    ],
    "discharge_memo": [
        "[ DOCUMENT: Facility Tech — EM Events Log ]",
        "",
        "Static discharge events confirmed: Sectors 2, 4, 5.",
        "Cause: experimental delta-wave suppressor.",
        "Subject impact: 1.4-1.8s disorientation.",
        "Perceived reality shift: significant.",
        "",
        "Risk assessment: acceptable.",
        "Continuation: approved.",
        "— Tech Division (cc: Dr. Voss)",
    ],
    "group_c_note": [
        "[ DOCUMENT: Handwritten. Found in wall cavity. ]",
        "",
        "Group C was six subjects.",
        "We were told we were free.",
        "We walked to the final exit.",
        "",
        "The exit opened onto Sector 1.",
        "We tried again. And again.",
        "",
        "We are still trying.",
        "There is no outside.",
        "— Group C (what remains of us)",
    ],
    "sub47_scratch": [
        "[ DOCUMENT: Scratched into floor. Sector 5. ]",
        "",
        "I think I am Subject 47.",
        "I think I have always been Subject 47.",
        "",
        "But I remember a name.",
        "I remember a window.",
        "I remember sunlight.",
        "",
        "The facility says these are",
        "implanted memories.",
        "",
        "(What if they're right.)",
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
            self.notes.append(Note(gx, gy, NOTE_CONTENTS.get(note_key, ["[blank page]"]), note_key))

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
                elif trig.effect == "speed_boost":
                    player.apply_effect("speed_boost", trig.duration)
                    return "speed_boost"
                elif trig.effect == "shield":
                    player.apply_effect("shield", trig.duration)
                    return "shield"
                elif trig.effect == "slow_motion":
                    player.apply_effect("slow_motion", trig.duration)
                    return "slow_motion"
                elif trig.effect == "paranoia":
                    player.apply_effect("paranoia", trig.duration)
                    return "paranoia_applied"
                elif trig.effect == "gravity":
                    player.apply_effect("gravity", trig.duration)
                    return "gravity_applied"
                elif trig.effect == "static":
                    return "static_burst"

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
            trigger_tiles=[
                (3,  5, "speed_boost",  4.0),
                (11, 7, "gravity",      4.0),
                (5, 13, "slow_motion",  5.0),
            ],
            notes=[(17, 13, "dr_voss_memo")],
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
            trigger_tiles=[
                (7,  3,  "invert_controls", 5.0),
                (15, 15, "invert_controls", 6.0),
                (19, 7,  "shield",          4.0),
                (5,  17, "speed_boost",     5.0),
                (9,  9,  "slow_motion",     5.0),
                (21, 5,  "paranoia",        5.0),
                (13, 21, "gravity",         4.0),
            ],
            fake_wall_positions=[],
            enemy_patrols=[
                [(9, 13), (9, 19), (9, 13)],
                [(3, 13), (3, 17), (3, 13)],
            ],
            notes=[
                (11, 3,  "s43_journal"),
                (17, 9,  "s43_journal_2"),
                (13, 17, "paranoia_report"),
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
        lv = Level(LevelConfig(
            number=3,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            fake_exit_pos=(5, 5),
            moving_exit_waypoints=waypoints,
            trigger_tiles=[
                (13, 5,  "darkness",        8.0),
                (7,  19, "invert_controls", 4.0),
                (11, 15, "speed_boost",     4.0),
                (3,  21, "shield",          4.0),
                (19, 7,  "static",          0.0),
                (9,  21, "gravity",         4.5),
                (25, 17, "slow_motion",     5.0),
            ],
            fake_wall_positions=[(5, 10)],
            enemy_patrols=[
                [(13, 1), (21, 1), (13, 1)],
                [(3,  15), (3, 23), (3, 15)],
            ],
            notes=[
                (5,  11, "maintenance_leak"),
                (13, 23, "s39_report"),
                (21, 15, "s47_own_note"),
                (7,  13, "discharge_memo"),
            ],
        ))
        lv.moving_exit.move_interval = 2.0
        return lv, start

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
                (9,  17, "speed_boost",      5.0),
                (27, 7,  "shield",           4.0),
                (7,  11, "paranoia",         5.5),
                (27, 15, "slow_motion",      5.0),
                (19, 7,  "static",           0.0),
                (13, 29, "gravity",          4.0),
            ],
            invisible_walls=invisible,
            halfway_gx=17,
            fake_wall_positions=[(22, 19), (20, 29)],
            enemy_patrols=[
                [(17, 1),  (31, 1),  (17, 1)],
                [(11, 5),  (11, 13), (11, 5)],
                [(21, 19), (21, 29), (21, 19)],
                [(3,  25), (7,  25), (7,  27), (3,  27), (3,  25)],
            ],
            notes=[
                (17, 21, "oracle_log"),
                (31, 23, "s44_notebook"),
                (7,  15, "facility_blueprint"),
                (25,  9, "group_c_note"),
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
        lv = Level(LevelConfig(
            number=5,
            grid=_clean_grid(raw),
            player_start=start,
            exit_pos=exit_pos,
            moving_exit_waypoints=waypoints,
            trigger_tiles=[
                (27, 1,  "darkness",        9.0),
                (35, 3,  "invert_controls", 5.0),
                (19, 25, "invert_controls", 4.0),
                (13, 3,  "speed_boost",     5.0),
                (21, 7,  "shield",          4.0),
                (31, 29, "speed_boost",     5.0),
                (31, 5,  "static",          0.0),
                (15, 21, "slow_motion",     6.0),
                (25, 33, "paranoia",        5.0),
                (7,  37, "gravity",         4.0),
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
                (9,  1,  "oracle_fragment"),
                (11, 7,  "s31_warning"),
                (29, 11, "oracle_final"),
                (37, 11, "oracle_warning"),
                (25, 19, "sub47_scratch"),
            ],
        ))
        for enemy in lv.enemies:
            enemy.SPEED = 3.8
        return lv, start

    raise ValueError(f"Unknown level {number}")
