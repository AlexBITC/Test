# KI-Staunen Video-Engine – Hinweise für Claude

Blender-Engine (headless) für vertikale Kurzvideos (1080×1920, 30 fps) mit Kalle (Bäckermeister) und
Byte (KI-Kugel). Überblick, Voraussetzungen und Aufbau: `README.md`.

## Befehle
```bash
npm run preview -- episodes/<datei>.json --clean   # Kontaktbögen je Szene (out/work/<slug>/kontakt_szene*.png)
npm run final -- episodes/<datei>.json --clean     # komplettes Video nach out/<datei>.mp4
```
Bisher verwendete Umgebung für Final-Renders: `RENDER_ENGINE=workbench MB_SUBFRAMES=2 RENDER_SCALE=0.7 RENDER_WORKERS=3`.

## Regeln
- ElevenLabs-Key nur aus der Umgebung, nie in Code, JSON, Logs oder Commits.
- Verwendete Sprachdateien liegen in `out/cache/` (gitignored) und werden mit `git add -f` committet.
- Episoden-JSON in `episodes/`, Regie-Zusätze (Stimme, Pausen, Hook-Karte) in `episodes/<datei>.regie.json`.

## Folgenspezifische Assets
- Requisiten: `assets/props/<slug>.py` (Übersicht in `assets/manifest.json`), Import in der Regie über `sys.path`.
- Bildschirm-Inhalte: `assets/screens/<slug>.py` mit `frame(tl, szene, f)`; `engine/overlays.screen_frame` lädt die Datei
  automatisch. Die Bildfolge liegt auf dem Studio-Screen; die Regie kann sie per UV auch auf ein Laptop-Display legen
  (siehe `laptop_display` in `engine/choreo/viral.py`).

## Engine-Version
Die aktuelle Version steht in `engine/VERSION`.

### Erlaubte Werte im Episoden-JSON
- `reaktion`: `neutral`, `zweifel`, `staunen`, `schock`, `jubel`, `traurig` (ab 2.2), `geruehrt` (ab 2.4), siehe
  `characters.REAKTIONEN`
- `sprecher`: `kalle`, `byte`, `lea` (ab 2.4), `erzaehler` (ab 2.5, ohne sichtbare Figur)
- `set`: `theke`, `buero`, `studio`, `backstube` (ab 2.2), `stadtkarte` (ab 2.3), `spielwelt` (ab 2.5)
- `licht` (optional, ab 2.2): `nacht`, `frueh`, `morgen` für `backstube` und `theke`. Ohne Feld: Theke wie bisher,
  Backstube `frueh`.
- Stimme (optional, ab 2.3): `ton` (`begeistert`, `ruhig`, `nachdenklich`, `neugierig`, `verschmitzt`, `ueberzeugt`,
  `fragend`; ab 2.4 auch `genervt`, `enttaeuscht`, `geruehrt`, `stolz`; ab 2.5 `erzaehlend`), `betonung` (ein Wort aus dem Text), `tempo` (`langsam`, `normal`, `schnell`), `sprechtext` (nur für die
  Sprachausgabe, Untertitel bleiben `text`). Ohne diese Felder klingt eine Zeile wie bisher.
- `musik` (optional, ab 2.4): `hektisch`, `stille`, `neugierig`, `aufsteigend`, `warm`; ab 2.5 `trailer`, `spielerisch`. Ohne Feld in
  allen Szenen: keine Musik.
- `visual` (ab 2.4): Abschnitt `[AR] … [/AR]` = Einblendungen durch Leas Brille (Scanlines/Randschimmer automatisch,
  3D-Elemente über `engine/ar.py` in der Regie). Ab 2.5: `[GAME] … [/GAME]` = Spielwelt mit Spielanzeige (Zustand aus
  `W.hud_fn` der Regie), `[FACECAM:<figur>:<reaktion>]` = Facecam-Fenster mit der echten Figur (`kameras.zweitbild`).
- Regie-Datei (ab 2.4): `pegel_db` (`{"2": -4}` = Zeile 2 um 4 dB leiser abmischen), `zuruecknahme`
  (`{"zeilen": [2, 3], "db": -3, "wps_max": 2.2}` = Zusatz-Check im Stimmen-Bericht).

### 2.5 – Erzähler, Set „spielwelt“ (Aufbauspiel), Spielanzeige [GAME], Facecam, Übergänge Welt ↔ Spiel
| Bereich | Umsetzung |
|---|---|
| Erzähler (`sprecher: erzaehler`) | Keine sichtbare Figur, kein Mund. Stimme ElevenLabs `Daniel` (`onwK4e9ZLuTAKqWW03F9`, ruhig, tief, warm, klares Hochdeutsch), `ELEVENLABS_VOICE_ERZAEHLER` hat Vorrang; ID in `engine/voices.json`. `BASE_SETTINGS`/`TEMPO` kennen `erzaehler` (1,9–2,3 Wörter/s). Ton `erzaehlend` 0,55/0,30 (eleven_v3-Tag `[calm]`). Gleicher erweiterter Stimmen-Check; der Bericht vergleicht Erzähler und Kalle (Klangfarbe MFCC ≥ 25, langsamer, ruhigere Satzmelodie). In 2.5-Folgen sind `a` und `no` als schwäbische Wörter frei (`voicecheck.DIALECT_REF_25`, nur dort). Untertitel kursiv, weiß, feine goldene Kontur, ohne Sprecherfarbe, gleiche Position und Größe (`overlays.text_kursiv`) |
| Set `spielwelt` (`engine/spielwelt.py`) | Ursprung (200, 0, 0), nur gebaut, wenn eine Szene das Set nutzt. Die Stadt als Aufbauspiel nach dem Plan der `stadtkarte` (gleiche Viertel, Fluss, Brücke, Lage von Kalles Laden; Umrechnung x · 3, y · 7). Raster 1 Kachel = 1 m. Ebenen: `spiel_stadt` (Stadt bei `S.p(0, 0, 0)`), `spiel_laden` (Kalles Laden als Puppenhaus bei `S.laden_o` = `S.p(0, 70, 0)`), `filiale` (kleinere Variante bei `S.p(0, 90, 0)`). Aufbau aus dem Katalog `assets/spielwelt/` (je Objekt eine Datei mit `INFO`, `bauen()` und benannten Zuständen) nach `assets/spielwelt/manifest.json` (Größe, Anker, Rasterposition, Zustände; neu erzeugen mit `python3 assets/spielwelt/_manifest.py`). Instanzen: `S.inst[id]` |
| Stil | Isometrisch 35° von oben (Azimut 14°, lange Brennweite), Low-Poly mit runden Kanten (`SW.rbox`), warme satte Farben (Holz- und Teigtöne, Kalles Rot als Akzent, Bytes Türkis nur für Spiel-Oberfläche und Hilfe), feine dunkle Outlines (`outlines_fuer`: nach außen versetzte Hülle, Glas ausgenommen), weiche Schatten nach unten rechts. `render_stil(sc, an, f)` schaltet Rückseiten-Ausblendung, Schatten (je Wetter) und Kavität nur für Spielwelt-Frames um (`scene.render_frames`) |
| Wetter und Tageszeit | `wetter(T, S, [(frame, 'sonne'/'regen'/'abend'/'nacht')])`: tönt alle `sw_*`-Materialien, Himmel, Schatten (abends lang); Hooks der Objekte (Pfützen mit Ringen, Laternen an, Fenster leuchten, Schirme). `regen(...)` Tropfen; `S.wetter_an(name, f)` |
| Bewegung | `wegpunkte_fn` + `laufen` (Figuren und Fahrzeuge auf Wegpunkten, Beine schwingen), Zustandsfunktionen der Katalog-Objekte (Ofen, Theke, Kasse, Tonne, Filiale, Zug, Marker, Waren, Gedankenblasen) |
| Kameras | `spielwelt.spiel_stadt` (isometrische Totale, langsame Drift), `spiel_laden` (Puppenhaus-Ansicht, gleicher Winkel), `spiel_flug` (weicher Flug zwischen zwei Einstellungen). `kameras.ins_spiel` / `aus_spiel` (Flug in einen Bildschirm bzw. heraus, Pixel- und Scanline-Blitz 0,6 s in `composite.py`), `kameras.welt_zu_spiel` (Kamera steigt senkrecht auf, Morph der echten Welt in die Spielstadt über Kacheln, die umklappen; Ende exakt wie die Spielwelt-Einstellung), `kameras.zweitbild` |
| Zweitbild (`scene._zweitbilder`) | Zweiter Render-Durchgang nur in Frames mit Eintrag in `W.zweit`: Facecam (`<f>_fc.png`, 324×400, eigenes Set) und Morph-Ziel (`<f>_zw.png`). `composite.py` setzt die Facecam oben links unter der Spielanzeige ein (`FACECAM` = 60–384 × 716–1116, abgerundet) und morpht (`W.morph`); dazu `W.uebergaenge` (Pixel-Blitz) und `W.wackeln` (kleiner Screen-Shake). Ohne Einträge unverändert |
| Spielanzeige [GAME] (`engine/spielanzeige.py`) | Mit Pillow, Zustand pro Frame aus `W.hud_fn(f)` (in `anchors.json` als `hud`). Obere Leiste y 532–700 (unter der Hook-Zone): `TAG x` (64 px), Uhr mit Sonne/Mond (Uhrzeit optional, 60 px), Geldleiste (grün/rot, pulsiert in Gefahr), 5 Herzen, Mehlsack mit Füllstand. Aktionsleiste über den unteren 420 px: `BACKEN`, `PREIS`, `EINKAUF`, `BAUEN` (gedrückter Knopf leuchtet). Preisregler mit Brezel und Preis (64 px), Mengenregler mit Plus/Minus (Zahl oder Brezel-Stufen), Banner fällt von oben ein (≥ 80 px, Symbol, Wackeln), `PLEITE` (abgedunkelte Welt mit Lichtkegel, roter Schriftzug, Knopf `NOCHMAL`), Level-up (goldener Strahlenkranz, Konfetti), Erfolg mit Pokal, Mini-Byte-Tipp (türkise Sprechblase mit Pfeil), Missions-Schriftrolle mit Kästchen, Facecam-Rahmen (türkis, roter `LIVE`-Punkt). Rechts bleiben 160 px frei |
| Musik (`engine/musik.py`) | `trailer` (weite, ruhige Flächen über tiefem Grundton D, für den Erzähler) und `spielerisch` (Chiptune: Rechteck 25 %, Dreieck-Bass, Rausch-Hihat, 132 BPM), selbst erzeugt |
| Sound (`engine/sfx.py`) | `pop8`, `ding8` (8-Bit, nur in der Spielwelt), `schluessel` |
| Effekte im Katalog | `muenz_pop` (über der Kasse), `duftlinien`, `rauchwolke` (verbrannt), `sternchen` (Level-up), Regen und Pfützenringe, Screen-Shake (`W.wackeln`) |

Bisherige Folgen sind unverändert: Spielwelt, Zweitbild, Spielanzeige und die neuen Effekte entstehen nur, wenn eine Folge sie
nutzt (Regressionstest mit `folge-10-brezel-geheimnis` auf gleicher Timeline: 3D-Bilder bis auf Render-Rauschen gleich, 2D-Ebene
und Tonmischung bytegleich).

#### Objekt-Katalog `assets/spielwelt/` (Rasterposition in Metern relativ zur Ebene, Details in `manifest.json`)
| Objekt | Datei | Zustände | Rasterposition |
|---|---|---|---|
| baeckerei_klein | `assets/spielwelt/baeckerei_klein.py` | tag | Stadt (-6.4, -0.2), Stadt (-3.6, -0.2) |
| bahnhof | `assets/spielwelt/bahnhof.py` | tag, abend | Stadt (4.7, -9.6) |
| baum | `assets/spielwelt/baum.py` | ruhig, wiegen | 27× (Stadt, siehe Manifest) |
| blechwagen | `assets/spielwelt/blechwagen.py` | tag | Laden (0.88, 2.8), Filiale (0.66, 2) |
| bushaltestelle | `assets/spielwelt/bushaltestelle.py` | tag | Stadt (8.2, -3) |
| duftlinien | `assets/spielwelt/duftlinien.py` | aus, an | Laden (-0.6, -0.84), Laden (0.88, 2.8) |
| fachwerkhaus | `assets/spielwelt/fachwerkhaus.py` | tag, abend | 11× (Stadt, siehe Manifest) |
| fahrzeug | `assets/spielwelt/fahrzeug.py` | faehrt | Stadt (-8, -1.4), Stadt (6, -2.1), Stadt (9.5, -2.1) |
| filiale | `assets/spielwelt/filiale.py` | bauplatz, baustelle, eroeffnet | Stadt (4.4, -4) |
| gedankenblase | `assets/spielwelt/gedankenblase.py` | – | dynamisch (Regie) |
| kalles_laden | `assets/spielwelt/kalles_laden.py` | tag, abend, geschlossen | Stadt (-4.65, -8.75) |
| kasse | `assets/spielwelt/kasse.py` | zu, auf | Laden (2, -0.84), Filiale (1.5, -0.6) |
| kirche | `assets/spielwelt/kirche.py` | tag | Stadt (-6.1, 10) |
| knettisch | `assets/spielwelt/knettisch.py` | tag | Laden (-0.6, 1.61) |
| kunde | `assets/spielwelt/kunde.py` | laufen, warten, schirm | dynamisch (Regie) |
| laden_puppenhaus | `assets/spielwelt/laden_puppenhaus.py` | tag, abend, tuer_auf | Laden (0, 0), Filiale (0, 0) |
| lagerregal | `assets/spielwelt/lagerregal.py` | anzahl(0-6) | Laden (2.64, 2.8) |
| laptop_mini | `assets/spielwelt/laptop_mini.py` | an | Laden (3.1, -2.7) |
| laterne | `assets/spielwelt/laterne.py` | aus, an | 10× (Stadt, siehe Manifest) |
| marktplatz | `assets/spielwelt/marktplatz.py` | tag, abend | Stadt (-5, 3) |
| mini_byte | `assets/spielwelt/mini_byte.py` | schweben, zeigen | dynamisch (Regie) |
| mini_kalle | `assets/spielwelt/mini_kalle.py` | stehen, laufen, backen, kassieren, verzweifelt | dynamisch (Regie) |
| mini_lea | `assets/spielwelt/mini_lea.py` | stehen, laufen, backen, kassieren, daumen_hoch | dynamisch (Regie) |
| muenz_pop | `assets/spielwelt/muenz_pop.py` | pop | Laden (2, -0.84) |
| ofen | `assets/spielwelt/ofen.py` | aus, backt, fertig, verbrannt | Laden (-2.48, 2.38), Filiale (-1.86, 1.7) |
| rauchwolke | `assets/spielwelt/rauchwolke.py` | aus, an | Laden (-2.48, 2.2) |
| spielbrett | `assets/spielwelt/spielbrett.py` | trocken, nass | Stadt (0, 0) |
| spieler_marker | `assets/spielwelt/spieler_marker.py` | aus, schwebt, senkt | Stadt (-4.65, -8.75) |
| sternchen | `assets/spielwelt/sternchen.py` | aus, an | Stadt (4.4, -4), Laden (0, 0) |
| theke_auslage | `assets/spielwelt/theke_auslage.py` | menge(0-12 je Fach), halbpreis | Laden (-0.6, -0.84), Filiale (-0.45, -0.6) |
| tonne_reste | `assets/spielwelt/tonne_reste.py` | leer, fuellstand, voll | Laden (3.4, -0.2) |
| ware | `assets/spielwelt/ware.py` | – | dynamisch (Regie) |
| wuerfelhaus | `assets/spielwelt/wuerfelhaus.py` | tag, abend | 8× (Stadt, siehe Manifest) |
| zug | `assets/spielwelt/zug.py` | weg, einfahren, steht, ausfahren | Stadt (12, -12.2) |

### 2.4 – Lea (Azubi), feinere Gefühle, [AR], neue Kameras, Musikbett
| Bereich | Umsetzung |
|---|---|
| Figur Lea (`engine/lea.py`, Klasse `Lea`) | Gleiche Gelenk-Logik und Attributnamen wie Kalle (`root`, `body`, `hips`, `torso`, `sh`/`el`/`hand`/`finger`, `neck`, `head`, `eye`/`pupil`/`lid`, `brow`, `mouth`, `frown`, `hat` = Käppi), daher funktionieren `kalle_lipsync`, `kalle_look`, `pose`, `kalle_haende`, `kalle_react` auch für Lea. Schlanker und jünger, dunkelbrauner Zopf (`zopf_root`, Kette `zopf`, schwingt nach), Strähnen und Pony, weißes Bäckerkäppi, weiße Schürze ohne Mehlfleck (`apron_anchor` für den ersten Fleck), Ärmel hochgekrempelt, große Augen mit Iris, Wimpern, Lidern und Brauen. Mehl an den Fingern (`lea_mehl(T, l, fn)`), AR-Brille (`lea_brille(T, l, [(f, 'ab'|'auf'|'stirn')], aufleuchten=(f,))`). Wird nur gebaut, wenn eine Szene `sprecher: lea` hat (`W.lea`) |
| Lea Animation | `lea_idle` (Atmen, Gewicht, Zopf, Schürzenbänder, unregelmäßiges Blinzeln `lea_blinks`: 1,5–5 s, manchmal doppelt), `lea_lipsync` (Mund nach Lautstärke, Nicken bei betonten Wörtern), `lea_react` (alle Reaktionen; `traurig`: Kopf gesenkt, Zopf fällt nach vorn, Schultern ziehen hoch, Blick weicht aus, `weg` = Richtung) |
| Hände (Kalle und Lea) | `haende_rollen` (Strang rollen), `haende_schlingen` (heben, kreuzen, Schwung aus dem Handgelenk, andrücken; `schwung=False` = flach; `zeit=fn` für Zeitlupe), dazu wie bisher `kalle_haende(..., "kneten")` |
| Reaktion `geruehrt` (`characters.kalle_geruehrt`, `byte_geruehrt`) | Kalle und Lea: weiches Lächeln mit geschlossenem Mund (`k.smile`), glänzende Augen (feiner Lichtreflex `k.wet`), Brauen hoch und innen angehoben, Kopf leicht geneigt, Lider etwas gesenkt. Byte: Display-Augen als weiche, nach oben gebogene Bögen mit Glanzpunkt (`BYTE_EYES`), Brust-LED pulsiert langsam (0,3 Hz) und warm, Antenne neigt sich. `byte_face` mit Ausdruck `geruehrt` schaltet das automatisch |
| Stimme Lea (`engine/voices.json`, `engine/tts.py`) | ElevenLabs `Sarah` (`EXAVITQu4vr4xnSDxMaL`), `ELEVENLABS_VOICE_LEA` hat Vorrang. Casting gegen Jessica und Matilda: größter Klangfarben-Abstand zu Byte, 12 Halbtöne über Kalle. `BASE_SETTINGS`/`TEMPO` kennen `lea` |
| Neue Töne (`stimme.TON`) | genervt 0,35/0,45, enttaeuscht 0,60/0,20, geruehrt 0,65/0,20, stolz 0,45/0,35 (stability/style), eleven_v3-Tags dazu |
| Atmer (`stimme._atmer`, `_atmer_daempfen`) | In Folgen mit 2.4-Merkmalen (Lea, `musik`, neue Töne, `geruehrt`) bleibt ein Atmer vor dem ersten Wort erhalten (0,12–0,9 s, über −50 dB); laute Atmer (> −14 dB unter der Sprache) werden auf die Grenze gedämpft. Ältere Folgen klingen unverändert |
| Stimmen-Bericht | Lea gegen Kalle (Tonhöhe, Ziel ≥ 4 Halbtöne höher) und Lea gegen Byte (Klangfarbe: Abstand der mittleren MFCC 2–20, Ziel ≥ 25; dazu Tonhöhe). Regie `zuruecknahme`: Pegel der gesprochenen Abschnitte gegen den Folgen-Durchschnitt und Tempo; Regie `pegel_db` mischt Zeilen leiser ab (`stimme.pegel_anwenden`) |
| Ebene [AR] (`engine/ar.py`, `overlays.draw_ar`) | `holo_haende` + `holo_bewegen` (türkise, halbtransparente Hände mit Glüh-Hülle), `pfeil`, `schritt_kreis` (Nummer im Kreis), `bahn` + `bahn_zeichnen` (dünne Bewegungsbahn, auch grau), `bogen_punkte`, `einblenden`; 2D: ganz dezente Scanlines und türkiser Randschimmer in Szenen mit `[AR]`, ohne Flackern |
| Kameras (`engine/kameras.py`) | `pov(T, figur, f0, ziel_fn)` (Augenhöhe, Blick auf Hände und Tisch, Hände unten im Bild, leichte Kopfbewegung; `pov_kopf_ausblenden`), `zeitlupe_haende(ziel_fn, f0, f1)` mit `zeitlupe(f0, 0.25)` für die Animation und `mehlstaub_schwebend`, `durchs_fenster(sf, f0, f1)` mit `schaufenster(coll, S)` + `schaufenster_zeigen` (Ladenfront mit Glas, Spiegelstreifen, Markise, Schriftzug; nur bei Aufruf gebaut). Schnee am Rand nur mit Set `marktplatz`, das es nicht gibt |
| Überblendung (`engine/composite.py`, `scene.export_anchors`) | `W.cam.blenden = [(f_grenze, frames)]`: weiche Überblendung zwischen zwei Einstellungen (Rand-Frames beider Seiten gehalten); ohne Eintrag unverändert |
| Musikbett (`engine/musik.py`, `sfx.build_mix`) | Selbst erzeugt (Karplus-Strong-Pizzicato, additives Klavier, Pad), keine Dateien, keine Downloads. Pro Stimmung eine durchgehende Spur, pro Szene mit 0,5-s-Rampen ein- und ausgeblendet, 20 dB unter dem Sprachpegel. `stille` = keine Musik |
| Sound (`engine/sfx.py`) | `tuerglocke`, `rascheln` |
| Timeline | Feld `musik` wird durchgereicht (nur wenn gesetzt) |
| Licht | `apply_licht` lässt AR-Elemente und Leas Brillenglas ungetönt |

Bisherige Folgen sind unverändert: Lea, Schaufenster und Musik entstehen nur, wenn eine Folge sie nutzt; neue Bauteile an
Kalle und Byte (Lächeln, Augenglanz, Display-Augen `geruehrt`) sind standardmäßig unsichtbar.

### 2.3 – Set „stadtkarte“, natürlichere Stimme
| Bereich | Umsetzung |
|---|---|
| Set `stadtkarte` (`engine/stadtkarte.py`) | Ursprung (160, 0, 0), wird nur gebaut, wenn eine Szene das Set nutzt. Low-Poly-Kleinstadt auf schwebender runder Platte (Radius `S.r` 2,6, Oberfläche `S.pz` auf Thekenhöhe, leuchtender Rand), Fluss mit Brücke, Straßen. Viertel (`S.viertel`): `altstadt` (Fachwerkhäuser, Kirchturm, Marktplatz mit Weihnachtsbaum, zwei kleine Bäckereien mit Markisen = `S.baeckereien`), `neubaugebiet` (weiße Würfelhäuser, Rasen, Bäume, leere Straßen), `bahnhof` (Bahnhof mit Turmuhr und Anzeigetafel „7:15“, Gleise, Zug, Bushaltestelle, Kiosk, leerer Laden `S.laden`). Kalles Bäckerei vorn links mit rotem Brezel-Pin (`S.kalle_bk`). Lokale Koordinaten → Welt: `S.welt(x, y, z, f)` (berücksichtigt das Drehen der Platte) |
| Bewegung | `leben` (Wellen, Weihnachtskugeln funkeln, Kalle-Pin schwebt), `drehen(T, S, f0, f1, fn)` (Platte dreht sich, Datenebenen folgen), `bahnhofsuhr(T, S, minuten_fn, …)`, `zug_fahrt(T, S, f0, f_halt, f1)` |
| Datenebenen | `personen` (leuchtende Punkte auf Pfaden, Dichte `dichte_fn` 0..1), `pin` + `pin_steigen` + `pin_farbe` (nummerierte Pins mit Namensschild, steigen aus dem Boden, Farbe gelb/grau/grün), `konkurrenz` + `marker_setzen` (graue Brezel-Marker), `heatmap` (Schleier `rot`/`blau`), `info_karte` + `karte_zeigen` (schwebend, höchstens 3 Zeilen). Pins, Marker und Karten drehen sich zur Kamera (`billboard`). `ebenen_aus_visual(visual)` liest die nötigen Ebenen aus dem Feld `visual` |
| Kamera | `totale_oben(S)` (ganze Stadt), `tief_viertel(S, viertel, …)` (Dachhöhe), `drohnenflug(keys, ziele, lens, bank)` (Catmull-Rom-Flug, Schräglage in Kurven aus der geglätteten Gierrate, höchstens ±0,22 rad). Figuren: `S.kalle` (vorn an der Plattenkante), `S.byte` (schwebt darüber) |
| Culling (`engine/scene.py`) | `SET_X` kennt die Stadtkarte |
| Sound (`engine/sfx.py`) | `stadtrauschen` (3 s, leise), `zug` (Rumpeln und Schienenstöße), `grillen` (Zirpen) |
| Stimme (`engine/stimme.py`, `engine/render.py`) | Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext` laufen über `stimme.zeile`, alle anderen unverändert über den bisherigen Weg. `ton` → stability/style (begeistert 0,30/0,50, ruhig 0,60/0,15, nachdenklich 0,55/0,25, neugierig 0,40/0,35, verschmitzt 0,35/0,45, ueberzeugt 0,45/0,35, fragend 0,40/0,30), similarity_boost aus `engine/voices.json`. `tempo` (langsam 2,0–2,2, normal 2,3–2,6, schnell 2,6–2,9 Wörter/s) zuerst über ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), der Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %, wie bisher in der Engine). Toleranz ±0,05 Wörter/s. Zahlen im Sprechtext werden immer als Wörter ausgeschrieben. `betonung`: fällt die Betonung durch, bekommt das Wort im nächsten Versuch eine kleine Pause (Komma) davor (nur im Sprechtext). Untertitel-Wörter werden per Abgleich auf den Sprechtext abgebildet (Wort-Timing aus `/with-timestamps`) |
| Erweiterter Stimmen-Check (`stimme.messen`/`bewerten`) | Whisper (WER ≤ 10 %, schwäbische Wörter frei, Zahlen und Begriff exakt), Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil, pYIN), Frage steigt / Aussage fällt (letztes Wort gegen den Rest der Zeile; Zeilen, die mit „…“ enden, sind frei), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz außer nach „…“, Abstand Kalle/Byte ≥ 4 Halbtöne. Höchstens 3 Versuche; für Zeilen mit `ton` zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag), übernommen nur, wenn sie besser abschneidet (Bewertung nach Schwere: Anzahl der Abweichungen + Tempo-Abweichung + Wortfehler). Bericht: `out/<slug>_stimmen-check.md` |
| Whisper-Check (`engine/voicecheck.py`) | schwäbisch `kaufet`, `koiner` als erlaubte Abweichung; Ordinalzahl nach Artikel („a 2. Filiale“ → „zweite“) |
| Hook-Karte (`engine/overlays.py`) | kein angehängter Punkt nach „?“ oder „!“; passt eine Zeile nicht in die Karte, wird die Schrift verkleinert (bisherige Hooks passen und bleiben unverändert) |

Bisherige Folgen sind unverändert: Die Stadtkarte wird dort nicht gebaut, und Zeilen ohne die neuen Felder nutzen den
bisherigen Stimmen-Weg.

### 2.2 – Kalle detaillierter, Reaktion „traurig“, Set „backstube“, Lichtstimmungen
| Bereich | Umsetzung |
|---|---|
| Kalle (`Kalle._details_v22`) | Augenlider (`k.lid`, standardmäßig unsichtbar), Lachfalten an den Augen, Mehlspuren auf Händen und Unterarmen, Mehlstaub auf dem Mützenband, Schürzenbänder mit Schleife am Rücken (Enden schwingen in `kalle_idle` nach), Mundwinkel-Bogen für „traurig“ (`k.frown`) |
| Kalle Hände | `kalle_haende(T, k, art, f0, f1)`: `kneten`, `greifen`, `stuetzen` |
| Kalle „traurig“ | `kalle_react(..., "traurig")` bzw. `kalle_traurig`: Lider halb gesenkt, Brauen schräg nach innen, Mundwinkel nach unten, Schultern hängen, Kopf und Blick gesenkt (langsame Rampe) |
| Byte „traurig“ | Display-Augen als flache, nach außen abfallende Bögen; `byte_face` mit Ausdruck `traurig` ruft `byte_traurig` auf: Antenne knickt langsam ein, Brust-LED pulsiert langsamer und gedimmt, Halo kleiner |
| Set `backstube` (`build_world.build_backstube`) | Ursprung (120, 0, 0). Gemauerter Holzofen mit Glut (Rückwand links, Maul zur Kamera), Arbeitstisch mit Mehl, Teigresten, Teigschaber und Nudelholz, Teigknetmaschine „KNETER“, Blechwagen mit Brezeln, Mehlsäcke „WEIZEN 550“, Fenster zur Straße, Neonröhre, Mehl auf dem Boden, offene Tür mit Blick auf den Verkaufsraum und die Theke von hinten. Kameras: `S.cams["totale"]` (Ofen bis Tür), `S.cams["nah"]` (Arbeitstisch). Glut: `build_world.glut(T, S, f0, f1, level_fn)` |
| Lichtstimmungen (`build_world.apply_licht`) | Feld `licht` pro Szene. Workbench kennt kein Licht: die Stimmung tönt die Objektfarben aller Materialien (außer Byte und Leuchtteilen) während der Szene. `nacht`: dunkel, blaues Mondlicht durchs Fenster, nur Glut und Byte leuchten; `frueh`: Neonröhre an, kühl; `morgen`: warme Sonne, Lichtstrahl mit tanzendem Mehlstaub. In der Theke nur die Tönung |
| Sound (`engine/sfx.py`) | zwei leise Atmosphäre-Geräusche: `knistern` (Glut), `ticken` (Uhr) |
| Timeline (`engine/render.py`) | Szenenfeld `licht` wird durchgereicht |
| Licht-Abschnitte der Regie | `W.licht_extra = [(f0, f1, set, stimmung), ...]` hat Vorrang vor dem Feld `licht` (Neonröhre flackert an, Zeitraffer) |
| Culling (`engine/scene.py`) | `SET_X` kennt die Backstube |
| Hook-Karte (`engine/overlays.py`) | `gelb` aus mehreren Wörtern wird auch über einen Zeilenumbruch hervorgehoben (nur wenn das Stück in keiner Zeile ganz steht; bisherige Folgen unverändert) |

Bisherige Folgen sind unverändert, bis auf Kalles neue Details (Lachfalten, Mehlspuren, Mehlstaub auf der Mütze,
Schürzenbänder). Die Backstube liegt weit entfernt und ist in anderen Folgen nicht im Bild.

### 2.1 – Byte-Upgrade (nur Byte geändert)
Byte bekommt mehr Details, Form, Farbe, Größe und Antenne bleiben gleich. Alle Änderungen liegen in
`engine/characters.py` (Klasse `Byte`, Funktionen `byte_*`, `antenna_spring`). Die Helfer-Bytes aus
„Drei Helfer“ bleiben unverändert (`Helper` nutzt `v21=False`).

| Merkmal | Umsetzung |
|---|---|
| Display-Gesicht | Augen als glatte Leuchtformen statt Pixel, Glasreflex oben links, leuchtender Innenrand |
| Augen je Reaktion | `neutral` rund, `jubel` Halbmonde, `staunen` groß mit Glanzpunkt, `schock` Zickzack, `zweifel` schräg (halb geschlossen), dazu `wink` |
| Alte Ausdrucksnamen | `byte_face` setzt sie um: happy → jubel, surprised/curious → staunen, worried → schock, serious → zweifel |
| Nahtlinien | feine leuchtende Linien entlang der Kanten der Hülle (nicht auf der Vorderseite) |
| Lüftungsgitter | kleine Platte mit vier Lamellen oben seitlich |
| Status-LED | grüne LED auf der Brust; atmet im Ruhezustand, pulsiert beim Sprechen mit der Lautstärke (`byte_speak`) |
| Antenne | zwei Glieder; die leuchtende Spitze (mit Halo) schwingt verzögert nach (`antenna_spring`) |
| Arme mit Händen | `byte_arm` (Armhaltung), `byte_hand` (`rest`, `offen`, `point`, `grab`, `snap`), `byte_snap` (Schnippen), `byte_type` (Tippen); Ruhehaltung pendelt leicht |
| Schwebe-Effekt mit Schatten | `byte_shadow` (aus `byte_idle`): Scheibe auf der Fläche unter Byte (Raycast gegen die statische Szene), kleiner, je höher Byte schwebt |

Bestehende Regie-Dateien müssen nicht angepasst werden: `byte_idle`, `antenna_spring`, `byte_speak` und
`byte_face` bringen die neuen Merkmale automatisch mit.
