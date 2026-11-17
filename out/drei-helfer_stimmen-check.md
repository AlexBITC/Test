# Stimmen-Check: Byte schickt drei Helfer los

**Ergebnis:** nicht alle Zeilen bestanden (siehe unten)  
**Modell:** `eleven_v3`  
**Kalle:** Brian - Deep, Resonant and Comforting (`nPczCjzI2devNBz1zQrb`)  
**Byte:** Alice - Clear, Engaging Educator (`Xb7hH8MSUJpSbSDYk0k2`)  
**Stimmabstand:** Median-F0 Kalle 91 Hz, Byte 221 Hz → 15.4 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  
**Natürlichkeit (UTMOS22 strong):** nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.

| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | byte | 0% | 150 ✓ | 2.35 | 225 Hz | 4.2 st | 0.62 | 0.38 s | – | 1 | OK |
| 2 | kalle | 11% | – | 2.45 | 91 Hz | 4.2 st | 0.88 | 0.27 s | – | 3 | FAIL: WER 11% > 10 % |
| 3 | byte | 0% | – | 2.72 | 247 Hz | 4.4 st | 0.56 | 0.19 s | – | 1 | OK |
| 4 | byte | 0% | 18 ✓, 15,50 ✓ | 2.21 | 227 Hz | 4.7 st | 0.60 | 0.23 s | – | 1 | OK |
| 5 | byte | 0% | 2,50 ✓, 60 ✓, 150 ✓ | 2.06 | 216 Hz | 3.9 st | 0.64 | 0.26 s | – | 1 | OK |
| 6 | byte | 0% | – | 2.58 | 205 Hz | 5.5 st | 0.86 | 0.29 s | – | 1 | OK |
| 7 | byte | 0% | 1.800 ✓, Beschaffung ✓ | 2.35 | 186 Hz | 3.7 st | 0.52 | 0.19 s | – | 1 | OK |
| 8 | kalle | 0% | – | 2.60 | 70 Hz | 5.2 st | 0.75 | 0.30 s | – | 1 | OK |
| 9 | kalle | 10% | 150 ✓ | 2.71 | 117 Hz | 4.9 st | 0.88 | 0.58 s | – | 1 | OK |

## Hinweise

- eleven_v3 ignoriert den Parameter `speed`. Das Tempo wird deshalb tonhöhenerhaltend per Rubberband korrigiert (höchstens −12 % / +15 %); lange Pausen zwischen Wörtern werden vorher anhand des Pegels gekürzt.
- Jede Zeile endet mit einem `[pause]`-Tag; ohne ihn schneidet eleven_v3 das letzte Wort teils hart ab. Die Stille danach wird weggeschnitten.
- Emotions-Tags (nicht gesprochen, nicht im Untertitel): Kalle `[excited]` bei Jubel, `[shocked]` bei Schock.
- Byte wurde von Jessica auf Alice umgestellt: Jessica sprach „Helfer“/„Mehl“ in Tests als „Hefa“/„mir“; Alice sprach beide in 2 von 2 Testläufen korrekt.
- Zeile 2: Whisper hört „Mail-Angebote“ statt „Mehl-Angebote“ (1 von 9 Wörtern → 11 % WER). In isolierten Ausschnitten erkannte Whisper Kalles „Mehl“ teils korrekt – vermutlich teils Kontext-Bias („…im Postfach“), teils englisch gefärbte Aussprache der Stimme. Drei Versuche mit anderen Schreibweisen brachten keine Besserung; der beste Versuch wird verwendet. Der Untertitel zeigt den Originaltext.
- Die Ziffern in den Untertiteln bleiben unverändert; nur der Sprechtext schreibt Zahlen aus.

## Details pro Zeile

**1. byte:** „Kalle, du zahlst 150 Euro zu viel. Jeden Monat.“  
Sprechtext: „Kalle, du zahlst hundertfünfzig Euro zu viel. Jeden Monat.“  
Whisper: „Kalle, du zahlst 150 Euro zu viel. Jeden Monat.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x1.06  

**2. kalle:** „Ich hab drei Mehl-Angebote im Postfach. Aber null Zeit.“  
Sprechtext: „Ich hab drei Mehlangebote im Postfach. Aber null Zeit.“  
Whisper: „Ich habe drei Mail-Angebote im Postfach, aber null Zeit.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x1.00, WER 11%, 2.45 W/s, Schreibweise –, Fehler: WER 11% > 10 % – „Ich habe drei Mail-Angebote im Postfach, aber null Zeit.“
- Versuch 2: Stabilität 1.0, Seed 4217, Stretch x1.00, WER 11%, 2.23 W/s, Schreibweise {'Mehl-Angebote': 'Mehl Angebote'}, Fehler: WER 11% > 10 % – „Ich habe drei Mail-Angebote im Postfach, aber null Zeit.“
- Versuch 3: Stabilität 0.5, Seed 4234, Stretch x1.00, WER 11%, 2.26 W/s, Schreibweise {'Mehl-Angebote': 'Mehlangebote'}, Fehler: WER 11% > 10 % – „Ich habe drei Mail-Angebote im Postfach, aber null Zeit.“

**3. byte:** „Ich schick drei Helfer los. Du drückst nur auf Senden.“  
Sprechtext: „Ich schick drei Helfer los. Du drückst nur auf Senden.“  
Whisper: „Ich schick drei Helfer los. Du drückst nur auf Senden.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x1.00  

**4. byte:** „Helfer eins liest die Angebote. Gleiches Mehl: Du zahlst 18 Euro pro Sack, der Günstigste 15,50.“  
Sprechtext: „Helfer eins liest die Angebote. Gleiches Mehl: Du zahlst achtzehn Euro pro Sack, der Günstigste fünfzehn Euro fünfzig.“  
Whisper: „Helfer 1 liest die Angebote. Gleiches Mehl. Du zahlst 18 Euro pro Sack. Der günstigste 15,50 Euro.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x1.15  

**5. byte:** „Helfer zwei rechnet: 2,50 Euro weniger, mal 60 Säcke im Monat. Macht 150 Euro.“  
Sprechtext: „Helfer zwei rechnet: zwei Euro fünfzig weniger, mal sechzig Säcke im Monat. Macht hundertfünfzig Euro.“  
Whisper: „Helfer 2 rechnet. 2,50 Euro weniger. Mal 60 Säcke im Monat. Macht 150 Euro.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x1.15  

**6. byte:** „Helfer drei schreibt die Mail an den neuen Lieferanten. Höflich und mit Bitte um Probelieferung.“  
Sprechtext: „Helfer drei schreibt die Mail an den neuen Lieferanten. Höflich und mit Bitte um Probelieferung.“  
Whisper: „Helfer 3 schreibt die Mail an den neuen Lieferanten, höflich und mit Bitte um Probelieferung.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x1.00  

**7. byte:** „Das ist Beschaffung: das Richtige zum besten Preis einkaufen. Aufs Jahr sind das 1.800 Euro.“  
Sprechtext: „Das ist Beschaffung: das Richtige zum besten Preis einkaufen. Aufs Jahr sind das tausendachthundert Euro.“  
Whisper: „Das ist Beschaffung. Das Richtige zum besten Preiseinkaufen. Aufs Jahr sind das 1800 Euro.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x1.07  

**8. kalle:** „Gesendet! Des gibt's doch net!“  
Sprechtext: „Gesendet! Des gibt's doch net!“ – Tag [excited]  
Whisper: „Gesendet! Das gibt's doch nicht!“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x0.96  

**9. kalle:** „Moment … wie lang zahl ich schon 150 Euro zu viel?“  
Sprechtext: „Moment … wie lang zahl ich schon hundertfünfzig Euro zu viel?“ – Tag [shocked]  
Whisper: „Moment, wie lang zahle ich schon 150 Euro zu viel?“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": true}`, Seed 4200, Tempo-Stretch x0.88  

