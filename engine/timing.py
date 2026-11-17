"""Gemeinsame Zeitpunkte fuer Overlays/Screen-Texturen (Python) und Regie (Blender): beide muessen exakt
dieselben Frames verwenden."""


def word_f(s, core):
    for w in s["words"]:
        if w["w"].strip(".,!?:–").lower() == core.lower():
            return w["f0"]
    return None


def counter_window(s):
    """Code-Zaehler/Code-Turm: ab Szenenbeginn bis 78 % der Szene (Turm fertig, bevor der Teig ueber
    den Rand kommt)."""
    return s["f0"] + 4, s["f0"] + int(0.78 * s["n"])


def calc_times(s):
    """Rechnung: linker Teil beim Wort 'fünf', Summe zaehlt ab kurz vor 'tausend' hoch."""
    t1 = (word_f(s, "fünf") or s["f0"] + 10) - 3
    t2 = (word_f(s, "tausend") or s["f0"] + 60) - 6
    return t1, t2
