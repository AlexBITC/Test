"""Erzeugt assets/spielwelt/manifest.json: Objekte (Groesse, Anker, Zustaende aus INFO jeder Datei) und Platzierungen
(Rasterposition je Ebene). Aufruf: python3 assets/spielwelt/_manifest.py"""
import ast, glob, json, os
K = os.path.dirname(os.path.abspath(__file__))
objekte = {}
for f in sorted(glob.glob(os.path.join(K, "*.py"))):
    n = os.path.basename(f)[:-3]
    if n.startswith("_"):
        continue
    t = ast.parse(open(f).read())
    konst = {}
    for node in t.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                konst[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    for node in t.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "INFO":
            d = {}
            for k, v in zip(node.value.keys, node.value.values):
                try:
                    d[k.value] = konst[v.id] if isinstance(v, ast.Name) else ast.literal_eval(v)
                except Exception:
                    d[k.value] = None
            objekte[n] = {"datei": f"assets/spielwelt/{n}.py", "groesse_m": d["groesse"], "anker": d["anker"],
                          "zustaende": d["zustaende"], "beschreibung": d.get("beschreibung") or ""}
P = []
def pl(objekt, id_, x, y, ebene="spiel_stadt", z=0.0, drehung=0, outline=True, **par):
    e = {"objekt": objekt, "id": id_, "raster": [x, y], "ebene": ebene}
    if z: e["z"] = z
    if drehung: e["drehung"] = drehung
    if par: e["parameter"] = par
    if not outline: e["outline"] = False
    P.append(e)
pl("spielbrett", "sw_brett", 0, 0, outline=False)
# ALTSTADT (stadtkarte -1,5 / 0,5)
pl("marktplatz", "sw_markt", -5.0, 3.0)
for k, (x, y, rot) in enumerate([(-8.6, 6.6, 0), (-6.8, 6.6, 0), (-5.0, 6.6, 0), (-3.7, 7.4, 0), (-8.8, 3.0, -90), (-8.8, 0.6, -90),
                                 (-8.6, 9.6, 0), (-3.9, 10.4, 0), (-8.4, 12.6, 0), (-6.4, 13.4, 0), (-4.3, 13.8, 0)]):
    pl("fachwerkhaus", f"sw_fw{k}", x, y, drehung=rot, farbe=k, hoehe=1.5 + 0.25 * (k % 3))
pl("kirche", "sw_kirche", -6.1, 10.0)
pl("baeckerei_klein", "sw_bk_rot", -6.4, -0.2, farbe="#D8473F")
pl("baeckerei_klein", "sw_bk_blau", -3.6, -0.2, farbe="#3D7BD9")
pl("kalles_laden", "sw_kalle", -4.65, -8.75)
pl("spieler_marker", "sw_marker", -4.65, -8.75, z=2.6, outline=False)
# NEUBAUGEBIET (stadtkarte 1,3 / 1,3)
for k, (x, y) in enumerate([(3.4, 8.8), (6.2, 8.8), (9.0, 8.8), (3.4, 14.5), (6.2, 14.5), (9.0, 14.5), (3.4, 19.2), (7.0, 19.2)]):
    pl("wuerfelhaus", f"sw_wh{k}", x, y)
# BAHNHOF (stadtkarte 1,05 / -1,1)
pl("bahnhof", "sw_bahnhof", 4.7, -9.6, gleis_y=-2.6)
pl("zug", "sw_zug", 12.0, -12.2, z=0.15)
pl("bushaltestelle", "sw_bus_halt", 8.2, -3.0)
pl("filiale", "sw_filiale", 4.4, -4.0)
# Baeume, Laternen, Fahrzeuge
for k, (x, y, s) in enumerate([(4.8, 9.8, 1.0), (7.6, 9.8, 0.9), (4.8, 15.4, 1.1), (7.6, 15.4, 0.9), (10.3, 17.0, 1.0), (2.4, 17.0, 0.9),
                               (5.2, 17.3, 1.0), (8.7, 17.4, 0.8), (10.2, 21.0, 1.1), (5.2, 21.4, 1.0), (2.5, 21.6, 0.9), (10.2, 11.0, 0.8),
                               (2.6, 11.0, 0.9), (-9.6, -4.5, 1.0), (-9.6, -8.2, 1.1), (-7.8, -12.2, 0.9), (-3.3, -14.0, 1.0),
                               (-9.8, 15.4, 1.0), (-7.2, 16.6, 1.1), (-4.8, 17.6, 0.9), (-9.6, 19.8, 1.0), (-6.0, 20.6, 0.9),
                               (9.9, -7.0, 0.9), (-9.5, -15.5, 1.0), (-6.0, -16.5, 0.9), (2.5, -16.0, 1.0), (7.5, -16.5, 0.9)]):
    pl("baum", f"sw_baum{k}", x, y, s=s)
for k, (x, y) in enumerate([(-7.8, -2.8), (-3.4, -2.8), (2.4, -2.8), (7.0, -0.8), (-7.4, 1.2), (-3.2, 1.0), (2.4, 5.2), (0.2, 10.0),
                            (-5.8, -10.9), (0.6, -7.2)]):
    pl("laterne", f"sw_lat{k}", x, y)
pl("fahrzeug", "sw_auto_rot", -8.0, -1.4, drehung=90, typ="auto", farbe="#E2483F")
pl("fahrzeug", "sw_auto_blau", 6.0, -2.1, drehung=-90, typ="auto", farbe="#3D7BD9")
pl("fahrzeug", "sw_bus", 9.5, -2.1, drehung=-90, typ="bus")
pl("sternchen", "sw_sterne_filiale", 4.4, -4.0, z=0.8, outline=False)
# KALLES LADEN als Puppenhaus (Ebene spiel_laden, B 8 x T 7)
L = "spiel_laden"
pl("laden_puppenhaus", "sw_ph", 0, 0, ebene=L)
pl("theke_auslage", "sw_theke", -0.6, -0.84, ebene=L, preise=["1,20 €", "0,40 €", "2,50 €"])
pl("kasse", "sw_kasse", 2.0, -0.84, ebene=L, z=1.0)
pl("ofen", "sw_ofen", -2.48, 2.38, ebene=L)
pl("knettisch", "sw_knettisch", -0.6, 1.61, ebene=L)
pl("blechwagen", "sw_blechwagen", 0.88, 2.8, ebene=L)
pl("lagerregal", "sw_lager", 2.64, 2.8, ebene=L)
pl("tonne_reste", "sw_tonne", 3.4, -0.2, ebene=L)
pl("laptop_mini", "sw_laptop", 3.1, -2.7, ebene=L, z=0.79)
pl("muenz_pop", "sw_muenzen", 2.0, -0.84, ebene=L, z=1.7, outline=False)
pl("duftlinien", "sw_duft_theke", -0.6, -0.84, ebene=L, z=1.5, outline=False)
pl("duftlinien", "sw_duft_wagen", 0.88, 2.8, ebene=L, z=1.7, outline=False)
pl("rauchwolke", "sw_rauch", -2.48, 2.2, ebene=L, z=2.4, outline=False)
pl("sternchen", "sw_sterne_laden", 0.0, 0.0, ebene=L, z=1.0, outline=False)
# FILIALE 2 als kleinere Variante (Ebene filiale, B 6 x T 5)
F = "filiale"
pl("laden_puppenhaus", "sw_fph", 0, 0, ebene=F, breite=6.0, tiefe=5.0, filiale=True)
pl("theke_auslage", "sw_ftheke", -0.45, -0.6, ebene=F, preise=["1,20 €", "0,40 €", "2,50 €"])
pl("kasse", "sw_fkasse", 1.5, -0.6, ebene=F, z=1.0)
pl("ofen", "sw_fofen", -1.86, 1.7, ebene=F)
pl("blechwagen", "sw_fwagen", 0.66, 2.0, ebene=F)
man = {"version": "2.5", "raster_m": 1.0,
       "ebenen": {"spiel_stadt": [0, 0, 0], "spiel_laden": [0, 70, 0], "filiale": [0, 90, 0]},
       "umrechnung_stadtkarte": {"x": 3.0, "y": 7.0},
       "hinweis": "raster = Kachel-Position (x, y) in Metern relativ zur Ebene; z = Hoehe; drehung in Grad um Z",
       "objekte": objekte, "platzierungen": P}
json.dump(man, open(os.path.join(K, "manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(objekte), "Objekte,", len(P), "Platzierungen")
