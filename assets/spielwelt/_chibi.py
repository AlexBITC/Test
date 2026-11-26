"""Gemeinsamer Chibi-Bauplan (grosser Kopf, kleiner Koerper) fuer Mini-Kalle, Mini-Lea und die Kunden."""
import look as L
import spielwelt as SW


def koerper(coll, name, hemd, hose="#3B4A6E", haut="#F0BE96", h=1.0, kopf=0.33, schuerze=None):
    """Grundfigur, Hoehe h (m). Rueckgabe: dict mit root, body, kopf, arm_l/arm_r (Pivots), bein_l/bein_r (Pivots)."""
    root = L.empty(name, coll=coll)
    body = L.empty(f"{name}_body", root, (0, 0, 0), coll)
    s = h
    beine = []
    for sx in (-1, 1):
        b = L.empty(f"{name}_bein{sx}", body, (sx * 0.08 * s, 0, 0.26 * s), coll)
        SW.rbox(f"{name}_bm{sx}", (0.1 * s, 0.11 * s, 0.26 * s), SW.m(f"hose{hose}", hose, 0.6), b, (0, 0, -0.13 * s), coll, r=0.04 * s)
        SW.rbox(f"{name}_schuh{sx}", (0.12 * s, 0.17 * s, 0.07 * s), SW.m("schuh", "#2E2A33", 0.6), b, (0, -0.03 * s, -0.25 * s), coll,
                r=0.03 * s)
        beine.append(b)
    SW.rbox(f"{name}_rumpf", (0.36 * s, 0.26 * s, 0.34 * s), SW.m(f"hemd{hemd}", hemd, 0.6), body, (0, 0, 0.43 * s), coll, r=0.1 * s)
    if schuerze:
        SW.rbox(f"{name}_schuerze", (0.3 * s, 0.04 * s, 0.36 * s), SW.m(f"schuerze{schuerze}", schuerze, 0.6), body,
                (0, -0.13 * s, 0.4 * s), coll, r=0.04 * s)
    arme = []
    for sx in (-1, 1):
        a = L.empty(f"{name}_arm{sx}", body, (sx * 0.2 * s, 0, 0.55 * s), coll)
        SW.rbox(f"{name}_am{sx}", (0.09 * s, 0.09 * s, 0.24 * s), SW.m(f"hemd{hemd}", hemd, 0.6), a, (0, 0, -0.1 * s), coll, r=0.04 * s)
        L.sphere(f"{name}_hand{sx}", 0.05 * s, 8, 5, (1, 1, 1), SW.m(f"haut{haut}", haut, 0.6), a, (0, 0, -0.24 * s), coll)
        arme.append(a)
    kopf_p = L.empty(f"{name}_kopfp", body, (0, 0, 0.62 * s), coll)
    L.sphere(f"{name}_kopf", kopf * s, 12, 8, (1, 0.95, 1), SW.m(f"haut{haut}", haut, 0.6), kopf_p, (0, 0, kopf * s), coll)
    for sx in (-1, 1):
        L.sphere(f"{name}_auge{sx}", 0.045 * s, 8, 6, (0.9, 0.5, 1.2), SW.m("auge", "#1E1A2A", 0.4), kopf_p,
                 (sx * 0.11 * s, -kopf * s * 0.9, kopf * s * 1.05), coll)
        L.sphere(f"{name}_glanz{sx}", 0.015 * s, 6, 4, (1, 1, 1), SW.m("weiss", "weiss", 0.4), kopf_p,
                 (sx * 0.11 * s + 0.015 * s, -kopf * s * 0.97, kopf * s * 1.12), coll)
        L.sphere(f"{name}_wange{sx}", 0.05 * s, 8, 5, (1, 0.4, 0.7), SW.m("wange", "#F29C8A", 0.7), kopf_p,
                 (sx * 0.2 * s, -kopf * s * 0.78, kopf * s * 0.8), coll)
    return {"root": root, "body": body, "kopf": kopf_p, "arm_l": arme[1], "arm_r": arme[0], "bein_l": beine[1],
            "bein_r": beine[0], "s": s, "kr": kopf * s}


def haar(coll, name, d, farbe, stil="kurz"):
    """Frisur auf dem Chibi-Kopf: kurz (Kappe bis zum Hinterkopf), lang (dazu Haare bis zur Schulter), dutt, zoepfe."""
    k, s, kr = d["kopf"], d["s"], d["kr"]
    m = SW.m(f"haar{farbe}", farbe, 0.6)
    L.sphere(f"{name}_haar", kr * 1.06, 10, 6, (1.0, 1.0, 0.72), m, k, (0, 0.035 * s, kr * 1.3), coll)
    L.sphere(f"{name}_hinterkopf", kr * 1.04, 10, 6, (1.0, 0.75, 0.95), m, k, (0, 0.09 * s, kr * 1.05), coll)
    if stil == "lang":
        SW.rbox(f"{name}_lang", (kr * 1.9, 0.12 * s, kr * 1.3), m, k, (0, kr * 0.55, kr * 0.55), coll, r=0.05 * s)
    elif stil == "dutt":
        L.sphere(f"{name}_dutt", 0.12 * s, 10, 6, (1, 1, 1), m, k, (0, 0.1 * s, kr * 2.1), coll)
    elif stil == "zoepfe":
        for sx in (-1, 1):
            L.sphere(f"{name}_zopf{sx}", 0.07 * s, 8, 5, (1, 1, 1.6), m, k, (sx * kr * 1.05, 0.05 * s, kr * 0.75), coll)
