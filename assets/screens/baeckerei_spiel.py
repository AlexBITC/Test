"""Bildschirm-Inhalte fuer 'Diese Stadt ist ein Spiel' (folge-11-baeckerei-spiel).

frame(tl, szene, f) -> 1280x720-Bild fuer die Screen-Ebene (Buero-Monitor per UV, Studio-Screen) oder None.
Das Spielbild steht hochkant in der Mitte (wie im Handy-Format, Seitenraender dunkel mit feinem Raster), damit die
Kamerafahrten ins_spiel/aus_spiel nahtlos in das bildschirmfuellende Spiel uebergehen. Die Standbilder sind Renders
der Spielwelt (assets/screens/baeckerei_spiel/*_3d.png), die Spielanzeige kommt aus engine/spielanzeige.py.
"""
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

HIER = Path(__file__).resolve().parent / "baeckerei_spiel"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))
import spielanzeige as SA  # noqa: E402

NAVY = (20, 18, 40)
TOP = {"tag": 1, "geld": 0.5, "gewinn": True, "herzen": 4, "mehl": 0.9}


@lru_cache(maxsize=8)
def _spiel(name):
    """Hochkant-Spielbild (1080x1920) mit Spielanzeige, verkleinert auf 405x720."""
    datei = {"laden_pleite": "laden"}.get(name, name)
    bild = Image.open(HIER / f"{datei}_3d.png").convert("RGBA").resize((1080, 1920), Image.LANCZOS)
    hud = {"kalle_nah": {"top": dict(TOP), "aktion": {}},
           "laden_pleite": {"top": dict(TOP, tag=2, geld=0.03, gewinn=False, gefahr=True, herzen=1, mehl=0.0, nacht=True),
                            "pleite": {"f0": 0, "spot": None, "knopf_nach": 0}},
           "filiale": {"top": dict(TOP, tag=30, geld=1.0, herzen=5),
                       "levelup": {"f0": 0, "y": 1000}},
           "laden": {"top": dict(TOP), "aktion": {}}}[name]
    SA.draw_game(bild, hud, 40)
    return bild.convert("RGB").resize((405, 720), Image.LANCZOS)


@lru_cache(maxsize=1)
def _rahmen():
    img = Image.new("RGB", (1280, 720), NAVY)
    d = ImageDraw.Draw(img)
    for x in range(0, 1280, 40):
        d.line([(x, 0), (x, 720)], fill=(30, 28, 56), width=1)
    for y in range(0, 720, 40):
        d.line([(0, y), (1280, y)], fill=(30, 28, 56), width=1)
    return img


def _bild(name, f):
    img = _rahmen().copy()
    img.paste(_spiel(name), (437, 0))
    return img


def frame(tl, szene, f):
    i = szene["i"]
    name = {2: "kalle_nah", 3: "kalle_nah", 8: "laden_pleite", 11: "filiale", 12: "laden"}.get(i)
    if szene["set"] == "buero" and name:
        return _bild(name, f)
    if szene["set"] == "studio":
        return _bild("laden", f)
    return None
