"""Kamera-Presets (Engine 2.4): pov, zeitlupe_haende, durchs_fenster.

Alle liefern fn(f) -> (pos, ziel, brennweite[, roll]) fuer W.cam.add_shot.
  pov(T, figur, f0, ziel_fn, ...)          Blick durch die Augen einer Figur (Augenhoehe ueber dem Root, leicht nach vorn)
                                           auf Haende und Arbeitstisch; natuerliche, kleine Kopfbewegung (Rauschen);
                                           unten im Bild die Haende. Mit [AR] liegen die Holo-Haende ueber den echten.
  zeitlupe_haende(ziel_fn, f0, f1, ...)    extreme Nahaufnahme, sehr langsame Drift; dazu zeitlupe(f0, 0.25) fuer die
                                           Animation (0,25-fache Geschwindigkeit) und mehlstaub_schwebend (Partikel).
                                           Weicher Hintergrund durch nahen Fokus (W.cam.focus_fn auf die Haende).
  durchs_fenster(T, W, S, f0, f1, ...)     baut (nur bei Aufruf) eine Ladenfront mit Schaufenster vor der Theke und
                                           liefert die Einstellung von aussen durchs Glas; leichte Spiegelung im Glas.
                                           Schnee am Rand nur, wenn ein Set 'marktplatz' existiert (in dieser Engine nicht).
"""
import math

from mathutils import Vector

import look as L
from anim import Noise, ease_in_out

FPS = 30


def zeitlupe(f0, faktor=0.25):
    """Zeit-Abbildung fuer Animationen in Zeitlupe: Frame f -> f0 + faktor * (f - f0)."""
    return lambda f: f0 + faktor * (f - f0)


def pov(T, figur, f0, ziel_fn, augen=1.98, vor=0.36, lens=20.0, seed=31, amp=1.0, blick_vor=0.55):
    """Blick durch die Augen von figur (root-Position aus T) auf den Tisch: Ziel = ziel_fn(f) (Haende) plus blick_vor
    Meter in Blickrichtung, damit die Haende unten im Bild liegen."""
    nz = (Noise(seed, 3, 0.35), Noise(seed + 1, 3, 0.3), Noise(seed + 2, 2, 0.5))

    def fn(f):
        root = Vector(T.loc(figur.root, f))
        rz = T.val(figur.root, "rotation_euler", 2, f)
        fwd = Vector((math.sin(rz), -math.cos(rz), 0))
        t = f / FPS
        auge = root + Vector((0, 0, augen)) + fwd * vor
        auge += Vector((0.012 * amp * nz[0](t), 0.008 * amp * nz[1](t), 0.01 * amp * nz[2](t)))
        ziel = Vector(ziel_fn(f)) + fwd * blick_vor + Vector((0.02 * amp * nz[1](t + 3), 0, 0.015 * amp * nz[0](t + 5)))
        return (auge, ziel, lens, 0.01 * amp * nz[2](t + 2))
    return fn


def zeitlupe_haende(ziel_fn, f0, f1, abstand=0.75, hoehe=0.14, seite=0.2, lens=50.0, drift=0.12):
    """Extreme Nahaufnahme der Haende: Kamera sehr nah, langsame Seitwaerts-Drift (wirkt wie Zeitlupe)."""
    def fn(f):
        t = ease_in_out((f - f0) / max(1, f1 - f0))
        z = Vector(ziel_fn(f))
        pos = z + Vector((seite + drift * (t - 0.5), -abstand, hoehe + 0.03 * math.sin(t * math.pi)))
        return (pos, z, lens)
    return fn


def mehlstaub_schwebend(T, coll, name, mitte, f0, f1, groesse=(0.35, 0.25, 0.25), n=40, seed=77):
    """Mehlstaub, der in der Luft schwebt (sehr langsam, fuer Zeitlupen-Nahaufnahmen)."""
    import props as PR
    return PR.ambient_motes(T, coll, name, tuple(mitte), groesse, n, seed, f0, f1, drift=0.012, scale=0.35)


def schaufenster(coll, S, y=-4.7, breite=8.0):
    """Ladenfront vor der Theke (Set S, z. B. 'theke'): Mauer mit grossem Schaufenster, Rahmen, Glas mit leichten
    Spiegelstreifen, Markise, Schriftzug 'BÄCKEREI'. Standardmaessig ausgeblendet (Scale 0); schaufenster_zeigen."""
    root = L.empty("sf_root", None, S.p(0, y, 0), coll)
    m_wall = L.mat("sf_wand", "#C9B79A", 0.7)
    m_rahmen = L.mat("sf_rahmen", "#3F5A78", 0.55)
    m_glas = L.mat("sf_glas", "#CFE6F2", 0.1, alpha=0.12)
    m_spiegel = L.mat("sf_spiegel", "#FFFFFF", 0.1, alpha=0.18)
    w0, w1, z0, z1 = -2.2, 2.0, 0.55, 2.75          # Fensteroeffnung (lokal)
    L.box("sf_wl", (breite / 2 + w0, 0.2, 4.0), m_wall, root, ((-breite / 2 + w0) / 2, 0, 2.0), coll)
    L.box("sf_wr", (breite / 2 - w1, 0.2, 4.0), m_wall, root, ((breite / 2 + w1) / 2, 0, 2.0), coll)
    L.box("sf_wu", (w1 - w0, 0.2, z0), m_wall, root, ((w0 + w1) / 2, 0, z0 / 2), coll)
    L.box("sf_wo", (w1 - w0, 0.2, 4.0 - z1), m_wall, root, ((w0 + w1) / 2, 0, (z1 + 4.0) / 2), coll)
    for x in (w0, w1):
        L.box(f"sf_rv{x}", (0.1, 0.24, z1 - z0 + 0.1), m_rahmen, root, (x, 0, (z0 + z1) / 2), coll)
    for z in (z0, z1):
        L.box(f"sf_rh{z}", (w1 - w0 + 0.1, 0.24, 0.1), m_rahmen, root, ((w0 + w1) / 2, 0, z), coll)
    L.box("sf_sprosse", (0.06, 0.22, z1 - z0), m_rahmen, root, ((w0 + w1) / 2 + 0.7, 0, (z0 + z1) / 2), coll)
    L.box("sf_glas", (w1 - w0, 0.02, z1 - z0), m_glas, root, ((w0 + w1) / 2, -0.05, (z0 + z1) / 2), coll)
    spiegel = []
    for j, (x, w) in enumerate([(-1.4, 0.35), (-0.9, 0.12), (1.2, 0.25)]):
        o = L.box(f"sf_spiegel{j}", (w, 0.005, (z1 - z0) * 1.15), m_spiegel, root, (x, -0.07, (z0 + z1) / 2), coll)
        o.rotation_euler = (0, 0.5, 0)
        spiegel.append(o)
    # Markise und Schriftzug
    for k in range(10):
        st = L.box(f"sf_markise{k}", (0.44, 0.7, 0.02), L.mat(f"sf_mk{k % 2}", ["#E5484D", "#F5F1E8"][k % 2], 0.6),
                   root, (-2.2 + 0.44 * k + 0.22, -0.4, 3.15), coll)
        st.rotation_euler = (-0.35, 0, 0)
    L.box("sf_schildbg", (2.4, 0.06, 0.4), L.mat("sf_schild", "#141228", 0.5), root, (-0.1, -0.12, 3.6), coll)
    L.text("sf_schrift", "BÄCKEREI", 0.3, L.mat("sf_schrift_gold", "#F2B45A", 0.4), root, (-0.1, -0.16, 3.5), coll,
           extrude=0.01, font=L.font())
    # Gehweg aussen
    L.box("sf_gehweg", (breite + 4, 3.0, 0.05), L.mat("sf_gehweg", "#8D8FA3", 0.75), root, (0, -1.6, -0.01), coll)
    root.scale = (0, 0, 0)
    return {"root": root, "spiegel": spiegel, "fenster": (w0, w1, z0, z1), "y": y, "S": S}


def schaufenster_zeigen(T, sf, f0, f1):
    """Ladenfront nur in [f0, f1) sichtbar; Spiegelstreifen gleiten langsam (leichte Spiegelung)."""
    T.set(sf["root"], "scale", lambda f: (1, 1, 1) if f0 <= f < f1 else (0, 0, 0), 0, max(f1 + 2, 2))
    for j, o in enumerate(sf["spiegel"]):
        x0 = o.location.x
        T.set(o, "location", lambda f, x0=x0, j=j: (x0 + 0.004 * (f - f0) * (1 + 0.3 * j), -0.07, o.location.z), f0, f1)


def durchs_fenster(sf, f0, f1, ziel=None, abstand=2.4, hoehe=1.55, lens=30.0, schwenk=0.35):
    """Einstellung von aussen durchs Schaufenster nach innen (leichte Seitwaerts-Fahrt)."""
    S = sf["S"]
    y = sf["y"]
    zl = Vector(ziel) if ziel is not None else S.p(0.2, -1.0, 1.25)

    def fn(f):
        t = ease_in_out((f - f0) / max(1, f1 - f0))
        pos = S.p(-schwenk + 2 * schwenk * t, y - abstand, hoehe)
        return (pos, zl, lens)
    return fn


def pov_kopf_ausblenden(T, figur, f0, f1):
    """Waehrend einer POV-Einstellung den eigenen Kopf mit Hals (mit Kaeppi, Zopf, Brille) ausblenden."""
    T.mul(figur.neck, "scale", lambda f: (0.0, 0.0, 0.0) if f0 <= f < f1 else (1.0, 1.0, 1.0), max(0, f0 - 1), f1 + 1)
