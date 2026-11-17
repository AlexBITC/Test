"""Generische Regie fuer neue Episoden ohne eigenes Choreo-Modul:
Set-Wechsel mit Whip-Pan, Kalle/Byte am Set-Platz, Idle, Sprechen, Reaktion auf das erste
Highlight-Wort, Push-in-Kamera, Punch-ins auf Highlights."""
import math

import characters as C
from anim import ease_out, lerp
from choreo.common import Ctx, V


def direct(W):
    c = Ctx(W)
    T, k, b, N = c.T, c.k, c.b, c.N
    C.kalle_idle(T, k, 0, N - 1)
    C.byte_idle(T, b, 0, N - 1)
    C.byte_blinks(T, b, 0, N - 1)
    C.antenna_spring(T, b, 2, N - 1)
    C.byte_face(T, b, [(0, "neutral")], 0, N - 1)
    for h in W.helpers:
        T.set(h.root, "scale", lambda f: (0, 0, 0), 0, 1)
    W.anchors["kalle_face"] = k.head
    W.anchors["byte"] = b.body
    prev = None
    for i, s in enumerate(c.sc):
        st = c.sets[s["set"]]
        f0, f1 = s["f0"], s["f1"]
        T.set(k.root, "location", lambda f, p=V(st.kalle): tuple(p), f0, f1)
        T.set(b.root, "location", lambda f, p=V(st.byte): tuple(p), f0, f1)
        o = st.o

        def shot(f, o=o, f0=f0, f1=f1):
            t = ease_out((f - f0) / (f1 - f0))
            return (o + V(0.25, lerp(-3.8, -3.2, t), 2.2), o + V(0.1, 0.2, 1.95), lerp(35, 45, t))
        W.cam.add_shot(f0, f1, shot)
        if prev is not None and prev != s["set"]:
            W.cam.whips.append((f0, 1))
            c.cue(f0 - 5, "whoosh", 0.9)
        prev = s["set"]
        if s["sprecher"] == "kalle":
            C.kalle_lipsync(T, k, s, f0, f1)
        else:
            C.byte_speak(T, b, s, f0, f1)
        hl = [w for w in s["words"] if w["hl"]]
        for w in hl:
            W.cam.punch.append(w["f0"])
        if hl:
            C.kalle_react(T, k, s.get("reaktion", "neutral"), hl[0]["f0"], hold=30, speaking=s["sprecher"] == "kalle")
    W.cam.focus_fn = lambda f: tuple(V(T.loc(k.root, f)) + V(0, -0.25, 1.95))
