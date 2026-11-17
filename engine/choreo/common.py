"""Gemeinsame Regie-Bausteine: Pfade, Pops, Szenen-Grundlagen (Positionen, Idle, Sprechen)."""
import math

from mathutils import Vector

import characters as C
import look as L
import props as PR
from anim import (ease_in, ease_out, ease_in_out, ease_out_back, spring, tween, window, pop, unpop, lerp,
                  impact_squash)

FPS = 30


def V(*a):
    return Vector(a[0]) if len(a) == 1 else Vector(a)


def path(keys, ease=ease_in_out):
    """keys: [(frame, Vector), ...] -> f(frame) mit Catmull-Rom-Kurve durch alle Punkte."""
    keys = [(f, Vector(p)) for f, p in keys]

    def fn(f):
        if f <= keys[0][0]:
            return tuple(keys[0][1])
        if f >= keys[-1][0]:
            return tuple(keys[-1][1])
        for i in range(len(keys) - 1):
            f0, p1 = keys[i]
            f1, p2 = keys[i + 1]
            if f0 <= f <= f1:
                t = ease((f - f0) / max(1e-6, f1 - f0))
                p0 = keys[i - 1][1] if i > 0 else p1 + (p1 - p2)
                p3 = keys[i + 2][1] if i + 2 < len(keys) else p2 + (p2 - p1)
                t2, t3 = t * t, t * t * t
                p = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                           (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
                return tuple(p)
        return tuple(keys[-1][1])
    return fn


def scale_fn(base, fn):
    return lambda f: (base * fn(f),) * 3


def pop_obj(T, obj, f_in, f_out=None, base=1.0, dur_in=8, dur_out=6):
    T.set(obj, "scale", lambda f: (base * PR_pop_life(f, f_in, f_out, dur_in, dur_out),) * 3, f_in - 1,
          (f_out + dur_out + 1) if f_out is not None else f_in + dur_in + 1)


def PR_pop_life(f, f_in, f_out, dur_in, dur_out):
    v = pop(f, f_in, dur_in)
    if f_out is not None and f > f_out:
        v *= unpop(f, f_out, dur_out)
    return v


def hidden(T, obj, f0, f1):
    T.set(obj, "scale", lambda f: (0, 0, 0), f0, f1)


class Ctx:
    """Bequemer Zugriff auf Timeline, Beats und Welt."""

    def __init__(self, W):
        self.W = W
        self.T = W.T
        self.k = W.kalle
        self.b = W.byte
        self.H = W.helpers
        self.sets = W.sets
        self.sc = W.tl["scenes"]
        self.N = W.n

    def s(self, i):
        return self.sc[i]

    def beat(self, i, name):
        s = self.sc[i]
        return max(s["f0"], s["beats"].get(name, s["f0"]))

    def word(self, i, name):
        """Frame, auf dem das Wort hoerbar beginnt (= Beat + 3)."""
        return self.beat(i, name) + 3

    def wordf(self, i, core):
        for w in self.sc[i]["words"]:
            if w["w"].strip(".,!?:…").lower() == core.lower():
                return w["f0"]
        return self.sc[i]["f0"]

    def cue(self, f, kind, gain=1.0):
        self.W.cues.append([int(f), kind, gain])

    def setp(self, name, x, y, z):
        return self.sets[name].o + Vector((x, y, z))
