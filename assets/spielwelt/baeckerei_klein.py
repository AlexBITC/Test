"""Kleine Konkurrenz-Baeckerei der Altstadt mit gestreifter Markise und Schild 'BÄCKER'. Zustand: tag."""
import look as L
import spielwelt as SW

INFO = {"name": "baeckerei_klein", "groesse": [1.8, 1.6, 2.6], "anker": "mitte_unten", "zustaende": ["tag"],
        "beschreibung": "Konkurrenz (zwei Stueck, wie in der Stadtkarte)"}


def bauen(coll, name, farbe="#3D7BD9", **kw):
    import fachwerkhaus as FH
    h = FH.bauen(coll, name, farbe=2, hoehe=1.5)
    for s_ in range(7):
        st = L.box(f"{name}_mk{s_}", (0.24, 0.55, 0.03), SW.m(f"mk{farbe}{s_ % 2}", [farbe, "weiss"][s_ % 2], 0.6), h.root,
                   (-0.72 + 0.24 * s_, -0.95, 1.05), coll)
        st.rotation_euler = (-0.45, 0, 0)
    SW.rbox(f"{name}_schild", (1.2, 0.06, 0.28), SW.m("schild_navy", "#1E2A44", 0.5), h.root, (0, -0.76, 1.32), coll, r=0.05)
    SW.text(f"{name}_t", "BÄCKER", 0.2, SW.m("schild_weiss", "weiss", 0.5), h.root, (0, -0.8, 1.25), coll)
    return h
