from __future__ import annotations
import wave
import math
import array
import io
import threading
import subprocess
import shutil
import random as _rand

_RATE = 22050
_cache: dict[str, bytes] = {}
_aplay_available = False


def _gen_wav(samples: list[float]) -> bytes:
    data = array.array('h', [max(-32767, min(32767, int(s * 32767))) for s in samples])
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_RATE)
        wf.writeframes(data.tobytes())
    return buf.getvalue()


def _sine(freq: float, dur: float, amp: float = 0.6, fade: float = 0.05) -> list[float]:
    n = int(_RATE * dur)
    fade_s = int(_RATE * fade)
    out = []
    for i in range(n):
        t = i / _RATE
        v = amp * math.sin(2 * math.pi * freq * t)
        if i < fade_s:
            v *= i / fade_s
        if i > n - fade_s:
            v *= (n - i) / fade_s
        out.append(v)
    return out


def _build_death() -> bytes:
    s = []
    for freq, dur in [(440, 0.06), (330, 0.06), (220, 0.12)]:
        s += _sine(freq, dur, amp=0.7)
    n = int(_RATE * 0.18)
    for i in range(n):
        t = i / _RATE
        v = 0.35 * math.sin(2 * math.pi * 110 * t) * (1 - i / n)
        s.append(v)
    return _gen_wav(s)


def _build_level_done() -> bytes:
    freqs = [523, 659, 784, 1047]
    s = []
    for freq in freqs:
        s += _sine(freq, 0.10, amp=0.55)
    s += _sine(1047, 0.22, amp=0.6)
    return _gen_wav(s)


def _build_note() -> bytes:
    s = _sine(880, 0.04, amp=0.4)
    s += _sine(1108, 0.08, amp=0.35)
    return _gen_wav(s)


def _build_trigger() -> bytes:
    n = int(_RATE * 0.14)
    s = []
    for i in range(n):
        t = i / _RATE
        freq = 600 - 300 * (i / n)
        v = 0.5 * math.sin(2 * math.pi * freq * t) * (1 - i / n)
        s.append(v)
    return _gen_wav(s)


def _build_powerup() -> bytes:
    freqs = [523, 659, 784]
    s = []
    for freq in freqs:
        s += _sine(freq, 0.07, amp=0.45)
    return _gen_wav(s)


def _build_shield() -> bytes:
    s = _sine(392, 0.06, amp=0.4)
    s += _sine(523, 0.06, amp=0.4)
    s += _sine(659, 0.10, amp=0.45)
    return _gen_wav(s)


def _build_static() -> bytes:
    n = int(_RATE * 0.45)
    fade_s = int(_RATE * 0.08)
    s = []
    for i in range(n):
        v = _rand.uniform(-0.65, 0.65)
        if i < fade_s:
            v *= i / fade_s
        if i > n - fade_s:
            v *= (n - i) / fade_s
        s.append(v)
    s += _sine(220, 0.12, amp=0.3)
    return _gen_wav(s)


def _build_slow() -> bytes:
    freqs = [440, 369, 311, 261]
    s = []
    for i, freq in enumerate(freqs):
        amp = 0.5 - i * 0.05
        s += _sine(freq, 0.11, amp=amp)
    s += _sine(220, 0.18, amp=0.35, fade=0.08)
    return _gen_wav(s)


def _build_glitch() -> bytes:
    s = []
    for freq, dur, amp in [(1400, 0.025, 0.55), (700, 0.02, 0.45),
                           (1800, 0.018, 0.6), (350, 0.03, 0.35)]:
        s += _sine(freq, dur, amp)
    n = int(_RATE * 0.07)
    for i in range(n):
        v = 0.25 * _rand.uniform(-1, 1) * (1 - i / n)
        s.append(v)
    return _gen_wav(s)


def init() -> None:
    global _aplay_available
    _aplay_available = shutil.which("aplay") is not None
    _cache["death"]      = _build_death()
    _cache["level_done"] = _build_level_done()
    _cache["note"]       = _build_note()
    _cache["trigger"]    = _build_trigger()
    _cache["powerup"]    = _build_powerup()
    _cache["shield"]     = _build_shield()
    _cache["static"]     = _build_static()
    _cache["slow"]       = _build_slow()
    _cache["glitch"]     = _build_glitch()


def play(name: str) -> None:
    if not _aplay_available:
        return
    data = _cache.get(name)
    if not data:
        return

    def _run():
        try:
            proc = subprocess.Popen(
                ["aplay", "-q", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.communicate(input=data, timeout=3)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
