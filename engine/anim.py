"""Animations-Grundlagen: Easing mit Overshoot, Federn, Rauschen (Seed) und ein Layer-System,
das Funktionen der Zeit in Keyframes (ein Key pro Frame, linear) backt.

Layer-Arten pro Kanal:
  set  – ueberschreibt ab f0 (haelt den Wert vor f0 bzw. nach f1)
  add  – addiert innerhalb [f0, f1]
  mul  – multipliziert innerhalb [f0, f1]
"""
import math
import random

import bpy
from bpy_extras import anim_utils


# ------------------------------------------------------------------ Easing
def clamp01(t):
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def lerp(a, b, t):
    return a + (b - a) * t


def ease_in(t):
    t = clamp01(t)
    return t * t * t


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_quint(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 5


def ease_out_back(t, s=1.70158):
    """Overshoot ~10 % bei s=1.70158."""
    t = clamp01(t)
    c3 = s + 1
    return 1 + c3 * (t - 1) ** 3 + s * (t - 1) ** 2


def ease_in_back(t, s=1.70158):
    t = clamp01(t)
    return (s + 1) * t ** 3 - s * t ** 2


def spring(t_sec, freq=2.2, zeta=0.28):
    """Gedaempfte Schwingung: 1 bei t=0, klingt gegen 0 ab."""
    if t_sec <= 0:
        return 1.0
    w = 2 * math.pi * freq
    wd = w * math.sqrt(max(1e-6, 1 - zeta * zeta))
    return math.exp(-zeta * w * t_sec) * math.cos(wd * t_sec)


def tween(f, f0, f1, a, b, ease=ease_in_out):
    if f1 <= f0:
        return b if f >= f0 else a
    return lerp(a, b, ease((f - f0) / (f1 - f0)))


def window(f, f0, f1, fade_in=6, fade_out=6, ease=ease_in_out):
    """0 -> 1 -> 0 Huellkurve."""
    if f <= f0 or f >= f1:
        return 0.0
    a = ease((f - f0) / max(1, fade_in))
    b = ease((f1 - f) / max(1, fade_out))
    return min(a, b, 1.0)


def pop(f, f0, dur=8, overshoot=1.10):
    """Scale-Pop 0 -> ~110 % -> 100 %."""
    if f <= f0:
        return 0.0
    t = (f - f0) / dur
    if t >= 1:
        return 1.0
    s = 1.70158 * (overshoot - 1) / 0.1
    return max(0.0, ease_out_back(t, s))


def unpop(f, f0, dur=6):
    """100 % -> 108 % -> 0 (Antizipation, dann weg)."""
    if f <= f0:
        return 1.0
    t = (f - f0) / dur
    if t >= 1:
        return 0.0
    return max(0.0, 1 - ease_in_back(t, 2.2))


def pop_life(f, f_in, f_out=None, dur_in=8, dur_out=6):
    v = pop(f, f_in, dur_in)
    if f_out is not None and f > f_out:
        v *= unpop(f, f_out, dur_out)
    return v


def impact_squash(f, f_hit, amount=0.2, freq=3.0, fps=30, pre=4):
    """(xy, z)-Multiplikatoren: Stretch im Fall, Squash beim Aufprall, Feder zurueck."""
    if f < f_hit - pre:
        return 1.0, 1.0
    if f < f_hit:
        k = (f - (f_hit - pre)) / pre
        z = 1 + 0.12 * k
        return 1 / math.sqrt(z), z
    t = (f - f_hit) / fps
    z = 1 - amount * spring(t, freq, 0.32)
    xy = 1 + amount * spring(t, freq, 0.32)
    return xy, z


class Noise:
    """Glattes, deterministisches 1D-Rauschen (Summe von Sinus mit Seed-Phasen)."""

    def __init__(self, seed, octaves=3, base=0.35):
        r = random.Random(seed)
        self.p = [(base * (1.9 ** k) * r.uniform(0.8, 1.25), r.uniform(0, 2 * math.pi), 0.55 ** k)
                  for k in range(octaves)]
        self.norm = sum(a for _, _, a in self.p)

    def __call__(self, t):
        return sum(a * math.sin(2 * math.pi * fr * t + ph) for fr, ph, a in self.p) / self.norm


# ------------------------------------------------------------------ Layer-System
class Tracks:
    def __init__(self, fps=30):
        self.fps = fps
        self.ch = {}

    def _chan(self, target, path, index):
        key = (target.as_pointer(), path, index)
        if key not in self.ch:
            v = getattr(target, path)
            base = v[index] if index is not None and index >= 0 else v
            self.ch[key] = {"t": target, "path": path, "index": index, "base": float(base), "layers": []}
        return self.ch[key]

    def _reg(self, kind, target, path, fn, f0, f1, index):
        f0, f1 = int(math.floor(f0)), int(math.ceil(f1))
        val = getattr(target, path)
        if index is None and hasattr(val, "__len__"):
            n = len(val)
            for k in range(n):
                self._chan(target, path, k)["layers"].append((kind, (lambda f, k=k: fn(f)[k]), f0, f1))
        else:
            self._chan(target, path, index if index is not None else -1)["layers"].append((kind, fn, f0, f1))

    def set(self, target, path, fn, f0, f1, index=None):
        self._reg("set", target, path, fn, f0, f1, index)

    def add(self, target, path, fn, f0, f1, index=None):
        self._reg("add", target, path, fn, f0, f1, index)

    def mul(self, target, path, fn, f0, f1, index=None):
        self._reg("mul", target, path, fn, f0, f1, index)

    def const(self, target, path, value, f0, f1, index=None):
        """haelt einen Wert ab f0 (z. B. Teleport an Szenengrenzen)."""
        self._reg("set", target, path, (lambda f: value), f0, f1, index)

    def value(self, ch, f):
        v = ch["base"]
        sets = [l for l in ch["layers"] if l[0] == "set"]
        if sets:
            cur = None
            for l in sets:
                if l[2] <= f:
                    if cur is None or l[2] >= cur[2]:
                        cur = l
            if cur is None:
                cur = min(sets, key=lambda l: l[2])
            _, fn, a, b = cur
            v = fn(min(max(f, a), b))
        for kind, fn, a, b in ch["layers"]:
            if kind == "add" and a <= f <= b:
                v += fn(f)
        for kind, fn, a, b in ch["layers"]:
            if kind == "mul" and a <= f <= b:
                v *= fn(f)
        return v

    def val(self, target, path, index, f):
        key = (target.as_pointer(), path, index)
        if key in self.ch:
            return self.value(self.ch[key], f)
        v = getattr(target, path)
        return v[index] if index is not None and index >= 0 else v

    def loc(self, obj, f):
        return [self.val(obj, "location", k, f) for k in range(3)]

    def eval_obj_loc(self, obj, f):
        """Lokale Position eines Objekts zum Frame f (nur aus registrierten Layern)."""
        out = []
        for k in range(3):
            key = (obj.as_pointer(), "location", k)
            out.append(self.value(self.ch[key], f) if key in self.ch else obj.location[k])
        return out

    def bake(self, fs, fe, loop_frames=0, loop_start=None):
        """loop_frames > 0: Kanaele, die das ganze Video abdecken, gleiten in den letzten
        loop_frames Frames exakt auf ihren Wert von Frame loop_start (Standard fs) zurueck
        (nahtloser Loop; mit loop_start > fs bleibt davor ein 'in'-Teil unveraendert)."""
        ls = fs if loop_start is None else loop_start
        n_keys = 0
        for ch in self.ch.values():
            if not ch["layers"]:
                continue
            a = max(fs, min(l[2] for l in ch["layers"]) - 1)
            b = min(fe, max(l[3] for l in ch["layers"]) + 1)
            frames = list(range(a, b + 1))
            vals = [self.value(ch, f) for f in frames]
            if loop_frames and a <= ls and b >= fe:
                v0 = vals[frames.index(ls)]
                for i, f in enumerate(frames):
                    if f >= fe - loop_frames:
                        w = ease_in_out((f - (fe - loop_frames)) / loop_frames)
                        vals[i] = vals[i] + (v0 - vals[i]) * w
            fc = _fcurve(ch["t"], ch["path"], ch["index"])
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(frames))
            co = []
            for f, v in zip(frames, vals):
                co += [f, v]
            fc.keyframe_points.foreach_set("co", co)
            fc.keyframe_points.foreach_set("interpolation", [1] * len(frames))  # LINEAR
            fc.update()
            n_keys += len(frames)
        return n_keys


def _fcurve(owner, prop, index):
    idx = index if (index is not None and index >= 0) else 0
    if index is not None and index >= 0:
        owner.keyframe_insert(prop, index=index, frame=-10000)
    else:
        owner.keyframe_insert(prop, frame=-10000)
    idb = owner.id_data
    ad = idb.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    path = owner.path_from_id(prop)
    for fc in cb.fcurves:
        if fc.data_path == path and fc.array_index == idx:
            return fc
    raise RuntimeError(f"FCurve nicht gefunden: {path}[{idx}]")
