from __future__ import annotations
import json
import os
from typing import Optional

_SCORES_FILE = os.path.join(os.path.dirname(__file__), "scores.json")
MAX_ENTRIES  = 10


def load_scores() -> list[dict]:
    try:
        with open(_SCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def save_score(name: str, score: int, deaths: int) -> None:
    entries = load_scores()
    entries.append({"name": name[:16], "score": score, "deaths": deaths})
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:MAX_ENTRIES]
    try:
        with open(_SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except OSError:
        pass


def top_scores() -> list[dict]:
    return load_scores()[:MAX_ENTRIES]
