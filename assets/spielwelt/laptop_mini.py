"""Winziger Laptop im Buero-Eck, auf dem Mini-Byte sitzt (Display zeigt eine Mini-Spielstadt). Zustand: an."""
import look as L
import spielwelt as SW

INFO = {"name": "laptop_mini", "groesse": [0.6, 0.45, 0.45], "anker": "mitte_unten", "zustaende": ["an"],
        "beschreibung": "Buero-Eck mit Mini-Byte"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    SW.rbox(f"{name}_basis", (0.6, 0.42, 0.04), SW.m("laptop", "#B9BCCB", 0.4), root, (0, 0, 0.02), coll, r=0.02)
    deckel = L.empty(f"{name}_deckel", root, (0, 0.2, 0.04), coll)
    deckel.rotation_euler = (-0.25, 0, 0)
    SW.rbox(f"{name}_dk", (0.6, 0.03, 0.4), SW.m("laptop", "#B9BCCB", 0.4), deckel, (0, 0, 0.2), coll, r=0.02)
    SW.rbox(f"{name}_disp", (0.52, 0.02, 0.32), SW.m("tuerkis_disp", "#1E6A66", 0.3), deckel, (0, -0.02, 0.2), coll, r=0.02)
    for k in range(4):
        L.box(f"{name}_px{k}", (0.08, 0.01, 0.06), SW.m("tuerkis", "tuerkis", 0.3, emit="#2EE6D6", strength=2.5), deckel,
              (-0.15 + 0.1 * k, -0.035, 0.12 + 0.05 * (k % 2)), coll)
    return SW.P(root=root, sitz=(0, 0.3, 0.55))
