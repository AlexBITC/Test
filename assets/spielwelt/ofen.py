"""Ofen mit Fortschrittsbalken ueber der Tuer: fuellt sich (orange), wird gruen bei 'fertig', raucht schwarz bei
'verbrannt'; Glut im Fenster. Zustaende: aus, backt, fertig, verbrannt."""
import math

import look as L
import spielwelt as SW
import _zustand as Z

INFO = {"name": "ofen", "groesse": [2.0, 1.4, 2.4], "anker": "mitte_unten", "zustaende": ["aus", "backt", "fertig", "verbrannt"],
        "beschreibung": "Backofen der Backstube"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    SW.rbox(f"{name}_k", (2.0, 1.3, 1.9), SW.m("ofen", "#C9C2BE", 0.5), root, (0, 0, 0.95), coll, r=0.1)
    SW.rbox(f"{name}_ziegel", (2.1, 1.35, 0.3), SW.m("ofen_ziegel", "#B5543A", 0.7), root, (0, 0, 2.0), coll, r=0.08)
    m_glut = L.unique_mat(SW.m("glut", "#5A2A18", 0.4), f"sw_glut_{name}")
    SW.rbox(f"{name}_fenster", (1.2, 0.08, 0.6), m_glut, root, (0, -0.66, 0.9), coll, r=0.08)
    L.box(f"{name}_griff", (1.0, 0.08, 0.08), SW.m("metall", "#8A8EA6", 0.4), root, (0, -0.72, 1.35), coll)
    bar = L.empty(f"{name}_bar", root, (0, -0.7, 1.68), coll)
    SW.rbox(f"{name}_barbg", (1.5, 0.06, 0.2), SW.m("bar_bg", "#2A2238", 0.5), bar, (0, 0, 0), coll, r=0.05)
    fill = L.empty(f"{name}_fillp", bar, (-0.7, -0.03, 0), coll)
    m_fill = L.unique_mat(SW.m("bar_fill", "#F29A3E", 0.4), f"sw_ui_bar_{name}")
    L.box(f"{name}_fill", (1.4, 0.04, 0.12), m_fill, fill, (0.7, 0, 0), coll)
    rauch = L.empty(f"{name}_rauch", root, (0, -0.4, 2.3), coll)
    puffs = [L.ico(f"{name}_r{k}", 0.25, 1, (1, 1, 1), SW.m("rauch", "#2E2A33", 0.8), rauch, (0, 0, 0), coll) for k in range(6)]
    rauch.scale = (0, 0, 0)
    return SW.P(root=root, fill=fill, m_fill=m_fill, m_glut=m_glut, rauch=rauch, puffs=puffs)


def zustand(T, o, plan, fortschritt_fn, f0, f1):
    """plan: [(frame, zustand)]; fortschritt_fn(f) 0..1 waehrend 'backt'."""
    orange, gruen, grau = L.srgb("#F29A3E"), L.srgb("#3DDC84"), L.srgb("#555060")
    glut_an, glut_aus = L.srgb("#FF8A2E"), L.srgb("#5A2A18")

    def p(f):
        z = Z.aktiv(plan, f, "aus")
        return {"aus": 0.0, "backt": max(0.02, min(1.0, fortschritt_fn(f))), "fertig": 1.0, "verbrannt": 1.0}[z]
    T.set(o.fill, "scale", lambda f: (max(0.001, p(f)), 1, 1), f0, f1)
    T.set(o.m_fill, "diffuse_color", lambda f: {"fertig": gruen, "verbrannt": grau}.get(Z.aktiv(plan, f, "aus"), orange), f0, f1)
    T.set(o.m_glut, "diffuse_color", lambda f: glut_an if Z.aktiv(plan, f, "aus") in ("backt", "verbrannt") else glut_aus, f0, f1)
    T.set(o.rauch, "scale", lambda f: (1, 1, 1) if Z.aktiv(plan, f, "aus") == "verbrannt" else (0, 0, 0), f0, f1)
    for k, r in enumerate(o.puffs):
        T.set(r, "location", lambda f, k=k: (0.15 * math.sin(f * 0.1 + k), 0, ((f * 0.03 + k * 0.35) % 2.0)), f0, f1)
        T.set(r, "scale", lambda f, k=k: ((0.5 + ((f * 0.03 + k * 0.35) % 2.0)),) * 3, f0, f1)
