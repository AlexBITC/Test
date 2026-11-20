"""Pipeline: Stimmen -> Stimmen-Check -> Timeline -> Screen-Texturen -> Blender-Render ->
Overlays -> Compositing -> Audio-Mix -> Encoding.

Aufruf:  npm run render -- episodes/<datei>.json [--stage voices|frames|style|contact|final] [--scale 0.6667]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from . import tts

ROOT = Path(__file__).resolve().parent.parent
ENGINE = Path(__file__).resolve().parent
FPS = 30
W, H = 1080, 1920
LEAD = 0.0           # Szene beginnt mit der Zeile (Szenenlaenge = Audiolaenge + 0,25 s)
TAIL = 0.25          # Pause nach jeder Zeile (Vorgabe)
BLENDER = os.environ.get("BLENDER", "blender")
os.environ.setdefault("EGL_PLATFORM", "surfaceless")   # Blender headless ohne GPU (Mesa llvmpipe)


def log(*a):
    print("[render]", *a, flush=True)


# ------------------------------------------------------------------ Stimmen
def _core(w: str) -> str:
    return re.sub(r"^[^\w]+|[^\w]+$", "", w).lower()


def voices_stage(ep: dict, work: Path) -> list:
    from . import voicecheck
    model = tts.pick_model()
    cfg = tts.load_voices(model)
    log("Modell:", model, "| Kalle:", cfg["voices"]["kalle"]["name"], "| Byte:", cfg["voices"]["byte"]["name"])
    alts = cfg.get("speech_alternatives", {})
    lines = []
    global quota_notes
    quota_notes = []
    for i, sz in enumerate(ep["szenen"]):
        role = sz["sprecher"]
        vid = role if model == "piper" else cfg["voices"][role]["voice_id"]
        tag = ""
        attempts = []
        overrides = {k: v for k, v in cfg.get("speech_overrides", {}).items() if k in sz["text"].split()}
        lt_all = cfg.get("line_tuning", {})
        lt_ep = lt_all.get(ep["slug"], {})               # Feinabstimmung je Folge (Schluessel = slug)
        overrides.update(lt_ep.get(str(i + 1), {}).get("speech", {}))
        lo, hi = tts.TEMPO[role]
        tune = lt_ep.get(str(i + 1), {})
        speed = tune.get("speed", tts.BASE_SETTINGS[role].get("speed", 1.0))
        for attempt in range(3):
            settings, seed = tts.line_settings(role, attempt, cfg, model)
            if attempt == 0 and tune:
                settings["stability"] = tune.get("stability", settings["stability"])
                settings["style"] = tune.get("style", settings["style"])
                seed = tune.get("seed", seed)
            if attempts:
                prev = attempts[-1]["check"]
                # Tempo ueber den API-Parameter 'speed' nachregeln (0,7-1,2)
                if any("Tempo" in x for x in prev["fails"]):
                    target = (lo + hi) / 2
                    speed = max(0.7, min(1.2, round(speed * target / max(0.5, prev["wps_raw"]), 2)))
                hyp = "".join(voicecheck.normalize(prev["transcript"]))
                # Aussprache-Alternativen fuer Woerter, die Whisper nicht erkannt hat
                for w in tts.split_words(sz["text"]):
                    c = re.sub(r"^[^\w]+|[^\w]+$", "", w)
                    key = w if w in alts else (c if c in alts else None)
                    if key and "".join(voicecheck.normalize(c)) not in hyp:
                        k = min(attempt - 1, len(alts[key]) - 1)
                        overrides[key] = alts[key][k]
            settings["speed"] = speed
            speech, spans = tts.speech_mapping(sz["text"], overrides)
            try:
                meta = tts.tighten(tts.synth(speech, vid, model, settings, tag, seed=seed))
            except RuntimeError as e:
                if "quota" in str(e) and attempts:
                    log(f"Szene {i+1}: ElevenLabs-Kontingent erschoepft -> beste vorhandene Variante")
                    quota_notes.append(i + 1)
                    break
                raise
            raw_words = tts.word_times(meta, spans)
            # Tempo: v3 ignoriert 'speed' -> tonhoehenerhaltend strecken/stauchen
            sp = [w for w in raw_words if re.search(r"\w", w["w"]) and w["end"] > w["start"]]
            n_w = len([w for w in tts.split_words(sz["text"]) if re.search(r"\w", w)])
            wps0 = n_w / max(0.1, sp[-1]["end"] - sp[0]["start"])
            factor = 1.0
            if wps0 > hi:
                factor = max(tts.STRETCH_LIMIT[0], (hi - 0.05) / wps0)
            elif wps0 < lo:
                factor = min(tts.STRETCH_LIMIT[1], (lo + 0.05) / wps0)
            if attempt == 0 and tune.get("stretch"):
                factor = tune["stretch"]
            meta = tts.stretch(meta, round(factor, 3), cfg.get("pitch_semitones", {}).get(role, 0.0))
            words = tts.word_times(meta, spans)
            chk = voicecheck.check_line(ROOT / meta["wav"], sz["text"], words, ep.get("begriff"), role)
            chk["stretch"] = factor
            chk["wps_raw"] = wps0
            attempts.append({"meta": meta, "words": words, "check": chk, "settings": settings, "seed": seed,
                             "overrides": dict(overrides), "speech": speech, "tag": tag})
            log(f"Szene {i+1} Versuch {attempt+1}: {'OK' if chk['ok'] else 'FAIL'} "
                f"WER={chk['wer']:.0%} {chk['wps']:.2f}W/s (roh {wps0:.2f}, x{factor:.2f}) F0={chk['f0_median']:.0f}Hz "
                f"±{chk['f0_std_st']:.1f}st UTMOS={chk['utmos']} {'(Cache)' if meta.get('cached') else ''} "
                f"| {chk['transcript']} | {chk['fails']}")
            if chk["ok"]:
                break
        best = min(attempts, key=lambda a: (len(a["check"]["fails"]), a["check"]["wer"]))
        best["n_attempts"] = len(attempts)
        best["all_attempts"] = [{"settings": a["settings"], "seed": a["seed"], "overrides": a["overrides"], "tag": a["tag"],
                                 "stretch": a["check"]["stretch"],
                                 "fails": a["check"]["fails"], "transcript": a["check"]["transcript"],
                                 "wer": a["check"]["wer"], "wps": a["check"]["wps"]} for a in attempts]
        lines.append(best)
    return lines, model, cfg


quota_notes = []


def _fmt(v):
    return '–' if v is None else f'{v:.2f}'


def voice_report(ep, lines, model, cfg, path: Path):
    from . import voicecheck
    kal = [l["check"]["f0_median"] for l in lines if l["check"]["speaker"] == "kalle"]
    byt = [l["check"]["f0_median"] for l in lines if l["check"]["speaker"] == "byte"]
    dist = 12 * math.log2(np.median(byt) / np.median(kal)) if kal and byt else 0
    ok_all = all(l["check"]["ok"] for l in lines)
    r = [f"# Stimmen-Check: {ep['titel']}", "",
         f"**Ergebnis:** {'alle Zeilen bestanden' if ok_all else 'nicht alle Zeilen bestanden (siehe unten)'}  ",
         f"**Modell:** `{model}`  ",
         f"**Kalle:** {cfg['voices']['kalle']['name']} (`{cfg['voices']['kalle']['voice_id']}`)  ",
         f"**Byte:** {cfg['voices']['byte']['name']} (`{cfg['voices']['byte']['voice_id']}`)  ",
         f"**Stimmabstand:** Median-F0 Kalle {np.median(kal):.0f} Hz, Byte {np.median(byt):.0f} Hz "
         f"→ {dist:.1f} Halbtöne ({'klar unterschiedlich' if abs(dist) >= 4 else 'zu ähnlich'})  ",
         f"**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  ",
         f"**Natürlichkeit (UTMOS22 strong):** "
         f"{'verfügbar' if voicecheck.utmos_status() is None else 'nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: ' + str(voicecheck.utmos_status()) + ')'}",
         "", "Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, "
         "kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.",
         "", "| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, l in enumerate(lines):
        c = l["check"]
        ex = ", ".join(f"{k} {'✓' if ok else '✗'}" for k, ok in c["exact"]) or "–"
        r.append(f"| {i+1} | {c['speaker']} | {c['wer']:.0%} | {ex} | {c['wps']:.2f} | {c['f0_median']:.0f} Hz | "
                 f"{c['f0_std_st']:.1f} st | {c['peak']:.2f} | {c['max_gap']:.2f} s | "
                 f"{_fmt(c['utmos'])} | "
                 f"{l['n_attempts']} | {'OK' if c['ok'] else 'FAIL: ' + '; '.join(c['fails'])} |")
    r += ["", "## Hinweise", "",
          f"- Modell `{model}` (Vorgabe). Wort-Timing der Untertitel aus dem Endpoint `/with-timestamps`"
          if model != "piper" else "- Piper-Fallback: Wort-Timing proportional zur Zeichenanzahl.",
          "- Stille am Zeilenanfang/-ende wird weggeschnitten, Pausen zwischen Wörtern werden auf 0,14–0,30 s begrenzt. "
          "Tempo: zuerst über den API-Parameter `speed`, Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %; "
          "Zeile 8 als kurzer Ausruf bewusst −21 %). Rubberband wurde ersetzt, weil es bei kurzen Ausrufen die "
          "Sprachmelodie messbar verflachte.",
          "- Tonhöhe gemessen mit pYIN auf 48 kHz (85-ms-Fenster); bei 16 kHz wurden kurze Ausrufe fälschlich als stimmlos/monoton gewertet.",
          "- Zeile 8 („Des gibt's doch net!“): aus allen erzeugten Varianten die lebendigste mit sauber erkanntem „net“ "
          "gewählt (Feinabstimmung in `engine/voices.json`). Das ElevenLabs-Kontingent ist erschöpft "
          "(Stand: 12 Credits); weitere Stimmen-Castings waren deshalb nicht möglich.",
          "- Schwäbische Wörter (net, i, des, verschlamp) dürfen in der Rücktranskription abweichen; Zahlwörter, "
          "„Code“ und „Marketing“ müssen exakt erkannt werden („Code“ würde bei falscher Aussprache als „Kot“ transkribiert).",
          "- Schreibweisen nur für die Sprachausgabe: siehe „Sprechtext“ je Zeile. Die Untertitel zeigen exakt den Episoden-Text.",
          "- Tonhöhe: keine Verschiebung; Byte (Laura) und Kalle (Brian) sind von Natur aus klar verschieden.",
          "", "## Details pro Zeile", ""]
    for i, l in enumerate(lines):
        c = l["check"]
        r += [f"**{i+1}. {c['speaker']}:** „{c['text']}“  ",
              f"Sprechtext: „{l['speech']}“{' – Tag ' + l['tag'] if l['tag'] else ''}  ",
              f"Whisper: „{c['transcript']}“  ",
              f"Einstellungen: `{json.dumps(l['settings'])}`, Seed {l['seed']}, Tempo-Stretch x{l['check']['stretch']:.2f}  "]
        if l["n_attempts"] > 1:
            for k, a in enumerate(l["all_attempts"]):
                r.append(f"- Versuch {k+1}: Stabilität {a['settings']['stability']}, Seed {a['seed']}, Stretch x{a['stretch']:.2f}, "
                         f"WER {a['wer']:.0%}, {a['wps']:.2f} W/s, Schreibweise {a['overrides'] or '–'}, "
                         f"Fehler: {'; '.join(a['fails']) or 'keine'} – „{a['transcript']}“")
        r.append("")
    path.write_text("\n".join(r) + "\n")


# ------------------------------------------------------------------ Stimmen aus dem Feld "tts" (Piper)
def rms_db(wav) -> float:
    y, sr = sf.read(str(wav), dtype="float32")
    return float(20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9))


def _check_tts_line(sz, i, meta, ep):
    from . import voicecheck
    wav = ROOT / meta["wav"]
    wwords, _ = tts.whisper_words(wav)
    dur = sf.info(str(wav)).duration
    words = tts.align_text_words(sz["text"], tts.strip_tags(sz["tts"]), wwords, dur)
    n_sp = len([w for w in tts.strip_tags(sz["tts"]).split() if re.search(r"\w", w)])
    chk = voicecheck.check_line(wav, sz["text"], words, ep.get("begriff"), sz["sprecher"], n_words=n_sp,
                                tempo=(2.0, 3.0) if i == 0 else (2.0, 2.8), pause_limit=0.4)
    chk["rms_db"] = rms_db(wav)
    return words, chk


def voices_stage_tts(ep: dict, work: Path):
    """Stimmen fuer Episoden mit Feld 'tts' (Untertitel = 'text'). Ohne ElevenLabs-Kontingent: Piper.
    Hook-Zeile: 3 Takes, bester (bestanden, hoechste Energie). Sonst bis zu 3 Versuche."""
    cfg = tts.load_voices.__wrapped__() if hasattr(tts.load_voices, "__wrapped__") else \
        json.loads(tts.VOICES_FILE.read_text())
    lines = []
    for i, sz in enumerate(ep["szenen"]):
        role, mood = sz["sprecher"], sz.get("stimmung", "")
        fix = cfg["piper"].get("zeilen", {}).get(str(sz.get("id", i + 1)), {})
        speech = tts.strip_tags(fix.get("tts", sz["tts"]))
        tag_removed = tts.strip_tags(sz["tts"]) != sz["tts"].strip()
        best_fix = fix.get("grund")
        attempts = []
        n_try = 3
        for attempt in range(n_try):
            if i == 0:
                voice = tts.piper_voice(cfg, role, mood, take=attempt)
            else:
                voice = tts.piper_voice(cfg, role, mood)
                voice.update(fix.get("stimme", {}))
                if attempt >= 1 and attempts:
                    prev = attempts[-1]["check"]
                    voice = dict(attempts[-1]["voice"])
                    if any("Tempo" in f for f in prev["fails"]):
                        lo, hi = (2.0, 2.8)
                        target = (lo + hi) / 2
                        voice["length_scale"] = round(voice.get("length_scale", 1.0) * prev["wps"] / target, 3)
                    else:
                        voice["noise_scale"] = 0.5 if attempt == 1 else 0.9
            alts = fix.get("alternativen", [])
            speech_k = tts.strip_tags(alts[attempt - 1]) if attempt >= 1 and len(alts) >= attempt else speech
            meta = tts.piper_synth(speech_k, voice)
            words, chk = _check_tts_line(sz, i, meta, ep)
            attempts.append({"meta": meta, "words": words, "check": chk, "voice": voice, "speech": speech_k})
            log(f"Szene {i+1} Versuch {attempt+1}: {'OK' if chk['ok'] else 'FAIL'} WER={chk['wer']:.0%} "
                f"{chk['wps']:.2f}W/s F0={chk['f0_median']:.0f}Hz ±{chk['f0_std_st']:.1f}st {chk['rms_db']:.1f}dB "
                f"{'(Cache)' if meta.get('cached') else ''}| {chk['transcript']} | {chk['fails']}")
            if chk["ok"] and i != 0:
                break
        ok = [a for a in attempts if a["check"]["ok"]]
        if i == 0 and ok:
            # hoechste Energie; bei Gleichstand (< 1 dB) der Take naeher an Kalles ueblicher Stimmlage (~120 Hz),
            # damit Kalle in der Hook-Zeile nicht wie eine andere Person klingt
            top_db = max(a["check"]["rms_db"] for a in ok)
            near = [a for a in ok if a["check"]["rms_db"] >= top_db - 1.0]
            best = min(near, key=lambda a: abs(math.log2(max(1.0, a["check"]["f0_median"]) / 120.0)))
        else:
            best = min(attempts, key=lambda a: (len(a["check"]["fails"]), a["check"]["wer"]))
        best["n_attempts"] = len(attempts)
        best["tag_removed"] = tag_removed
        best["fix"] = best_fix
        best["settings"] = best["voice"]
        best["seed"] = None
        best["tag"] = ""
        best["all_attempts"] = [{"voice": a["voice"], "fails": a["check"]["fails"], "transcript": a["check"]["transcript"],
                                 "wer": a["check"]["wer"], "wps": a["check"]["wps"], "rms_db": a["check"]["rms_db"],
                                 "f0": a["check"]["f0_median"], "f0_std": a["check"]["f0_std_st"]} for a in attempts]
        lines.append(best)
    return lines, "piper", cfg


def voice_report_tts(ep, lines, path: Path):
    from . import voicecheck
    kal = [l["check"]["f0_median"] for l in lines if l["check"]["speaker"] == "kalle"]
    byt = [l["check"]["f0_median"] for l in lines if l["check"]["speaker"] == "byte"]
    dist = 12 * math.log2(np.median(byt) / np.median(kal)) if kal and byt else 0
    ok_all = all(l["check"]["ok"] for l in lines)
    r = [f"# Stimmen-Check: {ep['titel']}", "",
         f"**Ergebnis:** {'alle Zeilen bestanden' if ok_all else 'nicht alle Zeilen bestanden (siehe unten)'}  ",
         "**Modell:** Piper (lokal, ONNX) – ElevenLabs nicht nutzbar: Kontingent des Free-Tarifs erschöpft "
         "(9.988 von 10.000 Zeichen, Reset am 13.12.2026); nötig wären mindestens 755 Zeichen.  ",
         "**Kalle:** Thorsten (`de_DE-thorsten-high`) bzw. derselbe Sprecher im Emotions-Modell "
         "(`de_DE-thorsten_emotional-medium`: surprised/amused/angry)  ",
         "**Byte:** Kerstin (`de_DE-kerstin-low`), Tempo je Zeile per length_scale geregelt (Ziel 2,0–2,8 W/s)  ",
         f"**Stimmabstand:** Median-F0 Kalle {np.median(kal):.0f} Hz, Byte {np.median(byt):.0f} Hz → {dist:.1f} Halbtöne "
         f"({'klar unterschiedlich' if abs(dist) >= 4 else 'zu ähnlich'})  ",
         "**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de, Wort-Zeitstempel für Lippensync und Untertitel  ",
         f"**Natürlichkeit (UTMOS):** nicht installiert/ladbar ({voicecheck.utmos_status() or 'Modell nicht vorhanden'})",
         "", "Grenzwerte: WER ≤ 10 % (Dialekt net/des frei), Zahlen und „Liquidität“ exakt, 2,0–2,8 Wörter/s "
         "(Hook bis 3,0; gezählt werden gesprochene tts-Wörter), Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, "
         "nicht abgeschnitten, keine Pause > 0,4 s.", "",
         "| # | Sprecher | Stimmung | WER | Zahlen/Begriff | W/s | F0 | Streuung | Pegel | Peak | Pause | Versuche | Status |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, (l, sz) in enumerate(zip(lines, ep["szenen"])):
        c = l["check"]
        ex = ", ".join(f"{k} {'✓' if ok else '✗'}" for k, ok in c["exact"]) or "–"
        r.append(f"| {i+1} | {c['speaker']} | {sz.get('stimmung','')} | {c['wer']:.0%} | {ex} | {c['wps']:.2f} | "
                 f"{c['f0_median']:.0f} Hz | {c['f0_std_st']:.1f} st | {c['rms_db']:.1f} dB | {c['peak']:.2f} | "
                 f"{c['max_gap']:.2f} s | {l['n_attempts']} | {'OK' if c['ok'] else 'FAIL: ' + '; '.join(c['fails'])} |")
    r += ["", "## Hinweise", "",
          "- Eingabe der Sprachausgabe ist das Feld `tts`; Untertitel und Bildzahlen nutzen `text` unverändert.",
          "- Audio-Tags (`[laughs]` in Szene 12) unterstützt Piper nicht; sie werden vor der Synthese entfernt.",
          "- Stille am Anfang/Ende wird abgeschnitten (Hook beginnt bei 0,00 s), Pausen in der Zeile auf 0,28 s gekürzt.",
          "- Hook-Zeile: 3 Takes (Thorsten high, Thorsten emotional „surprised“, „angry“); gewählt: bestandener Take "
          "mit der höchsten Energie.",
          "- Wort-Zeitstempel: Whisper-Wortzeiten, auf die Untertitel-Wörter abgebildet (Zahlen ausgeschrieben verglichen).",
          "- Cache: `out/cache/<hash>.wav/.json`, Hash aus tts, Stimme, Modell und Einstellungen.", "",
          "## Details pro Zeile", ""]
    for i, (l, sz) in enumerate(zip(lines, ep["szenen"])):
        c = l["check"]
        r += [f"**{i+1}. {c['speaker']}:** „{sz['text']}“  ", f"tts: „{l['speech']}“"
              f"{' (Tag entfernt)' if l.get('tag_removed') else ''}"
              f"{' – Schreibweise angepasst: ' + l['fix'] if l.get('fix') else ''}  ", f"Whisper: „{c['transcript']}“  ",
              f"Stimme: `{json.dumps({k: v for k, v in l['voice'].items() if k != 'url_sub'})}`  "]
        if l["n_attempts"] > 1:
            for k, a in enumerate(l["all_attempts"]):
                r.append(f"- Versuch/Take {k+1}: {a['voice'].get('model')} Sprecher {a['voice'].get('speaker')}, "
                         f"WER {a['wer']:.0%}, {a['wps']:.2f} W/s, F0 {a['f0']:.0f} Hz ±{a['f0_std']:.1f}, "
                         f"{a['rms_db']:.1f} dB, Fehler: {'; '.join(a['fails']) or 'keine'} – „{a['transcript']}“")
        r.append("")
    path.write_text("\n".join(r) + "\n")


# ------------------------------------------------------------------ ohne Stimme (Lesetempo)
def _syllables(word: str) -> int:
    w = word.lower()
    r = tts._num_token(re.sub(r"[^\w.,]", "", w).strip(".,"))
    if r:
        w = r[0]
    return max(1, len(re.findall(r"[aeiouäöüy]+", w)))


def voices_stage_none(ep: dict, regie: dict):
    """Keine Stimme: Wortzeiten aus Silbenzahl und Satzzeichen, skaliert auf das Lesetempo der Figur.
    Pausen vor Pointen aus der Regie-Datei (pause_vor_szene)."""
    rate = regie.get("woerter_pro_sekunde", {"kalle": 2.7, "byte": 2.6})
    pause = {int(k): float(v) for k, v in regie.get("pause_vor_szene", {}).items()}
    lines = []
    for i, sz in enumerate(ep["szenen"]):
        ws = tts.split_words(sz["text"])
        real = [w for w in ws if re.search(r"\w", w)]
        lead = pause.get(i + 1, 0.0)
        units = []
        for w in ws:
            if not re.search(r"\w", w):
                units.append((w, 0.0, 0.15))
                continue
            gap = 0.28 if w[-1] in ".!?…" else 0.14 if w[-1] in ",:;" else 0.0
            units.append((w, _syllables(w), gap))
        dur_target = len(real) / rate.get(sz["sprecher"], 2.6)
        syl = sum(u[1] for u in units)
        gaps = sum(u[2] for u in units[:-1])
        per = max(0.12, (dur_target - gaps) / max(1, syl))
        t, words = lead, []
        for k, (w, sy, gap) in enumerate(units):
            d = sy * per
            words.append({"w": w, "start": t, "end": t + d})
            t += d + (gap if k < len(units) - 1 else 0.0)
        lines.append({"meta": {"wav": None}, "words": words, "check": {"dur": t, "ok": True}, "n_attempts": 0})
    return lines


def synthetic_envelopes(words, n_frames, lead_s=0.0):
    """Mund-Huellkurve ohne Audio: pro Silbe ein Oeffnungs-Puls, Equalizer daraus mit festem Seed."""
    import random as _r
    amp = np.zeros(n_frames)
    for w in words:
        sy = _syllables(w["w"]) if re.search(r"\w", w["w"]) else 0
        if sy == 0 or w["end"] <= w["start"]:
            continue
        a, b = (w["start"] + lead_s) * FPS, (w["end"] + lead_s) * FPS
        for f in range(int(a), min(n_frames, int(math.ceil(b)) + 1)):
            x = (f - a) / max(1e-6, b - a)
            amp[f] = max(amp[f], 0.35 + 0.65 * abs(math.sin(math.pi * x * sy)))
    rr = _r.Random(len(words) * 7 + 3)
    eq = [[round(min(1.2, v * (0.5 + rr.random() * 0.7)), 3) for _ in range(5)] for v in amp]
    return amp.round(3).tolist(), eq


# ------------------------------------------------------------------ Timeline
def _envelopes(wav: Path, n_frames: int, lead_s: float):
    y, sr = sf.read(str(wav), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    hop = sr // FPS
    pad = np.concatenate([np.zeros(int(lead_s * sr), np.float32), y, np.zeros(sr, np.float32)])
    amp, eq = [], []
    win = np.hanning(hop * 2)
    edges = [80, 300, 700, 1500, 3000, 6000]
    freqs = np.fft.rfftfreq(hop * 2, 1 / sr)
    for f in range(n_frames):
        seg = pad[f * hop: f * hop + hop * 2]
        if len(seg) < hop * 2:
            seg = np.pad(seg, (0, hop * 2 - len(seg)))
        amp.append(float(np.sqrt(np.mean(seg ** 2))))
        sp = np.abs(np.fft.rfft(seg * win))
        eq.append([float(np.mean(sp[(freqs >= a) & (freqs < b)])) for a, b in zip(edges, edges[1:])])
    amp = np.array(amp)
    ref = np.percentile(amp[amp > 1e-4], 95) if np.any(amp > 1e-4) else 1
    amp = np.clip(amp / ref, 0, 1.3)
    eq = np.array(eq)
    eq = np.clip(eq / (np.percentile(eq, 95, axis=0) + 1e-9), 0, 1.2)
    return amp.round(3).tolist(), eq.round(3).tolist()


def build_timeline(ep: dict, lines: list) -> dict:
    scenes, f = [], 0
    for i, (sz, l) in enumerate(zip(ep["szenen"], lines)):
        dur = l["check"]["dur"]
        m = re.search(r"plus (\d+(?:,\d+)?) s Halt", sz.get("visual", ""))
        hold = float(m.group(1).replace(",", ".")) if m else 0.0
        ld = LEAD + l.get("lead", 0.0)                  # Pause vor der Zeile (Regie: pause_vor_szene)
        n = int(round((ld + dur + TAIL + hold) * FPS))
        words = []
        hl = {h.lower() for h in sz.get("highlight", [])}
        hl |= {_core(x) for h in sz.get("highlight", []) if " " in h for x in h.split()}   # Mehrwort-Highlights
        for w in l["words"]:
            words.append({"w": w["w"], "start": w["start"] + ld, "end": w["end"] + ld,
                          "f0": f + int(round((w["start"] + ld) * FPS)),
                          "f1": f + int(round((w["end"] + ld) * FPS)),
                          "hl": _core(w["w"]) in hl or w["w"].strip(".,!?:").lower() in hl})
        beats = {}
        for phrase in re.findall(r"Beat bei '([^']+)'", sz.get("visual", "")):
            toks = [_core(t) for t in phrase.split()]
            for k in range(len(words)):
                if [_core(x["w"]) for x in words[k:k + len(toks)]] == toks:
                    beats[phrase] = words[k]["f0"] - 3   # Aktion startet 3 Frames vor dem Wort
                    break
            else:
                log(f"WARN Szene {i+1}: Beat-Wort '{phrase}' nicht gefunden")
        if l["meta"]["wav"] is None:
            amp, eq = synthetic_envelopes(l["words"], n, LEAD)
        else:
            amp, eq = _envelopes(ROOT / l["meta"]["wav"], n, ld)
        beat_list = []
        for bt in sz.get("beats", []) if isinstance(sz.get("beats"), list) else []:
            core = _core(bt["wort"])
            fw = next((w["f0"] for w in words if _core(w["w"]) == core), None)
            if fw is None:
                log(f"WARN Szene {i+1}: Beat-Wort '{bt['wort']}' nicht gefunden")
                fw = f + 6
            beats[bt["wort"]] = fw - 3          # Aktion startet 3 Frames vor dem Wort
            beat_list.append({"wort": bt["wort"], "f_word": fw, "f_beat": fw - 3, "sound": bt.get("sound", "none"),
                              "aktion": bt.get("aktion", "")})
        scenes.append({"i": i, "sprecher": sz["sprecher"], "text": sz["text"], "highlight": sz.get("highlight", []),
                       "beat_list": beat_list, "reaktion_kalle": sz.get("reaktion_kalle"), "start": sz.get("start", ""),
                       "ausdruck_byte": sz.get("ausdruck_byte"), "screen": sz.get("screen"),
                       "overlay": sz.get("overlay"), "kamera": sz.get("kamera"), "stimmung": sz.get("stimmung"),
                       "reaktion": sz.get("reaktion", sz.get("reaktion_kalle", "neutral")), "set": sz["set"], "kapitel": sz.get("kapitel"),
                       "visual": sz.get("visual", ""), "f0": f, "f1": f + n, "n": n,
                       "audio_f": f + int(round(ld * FPS)), "audio_start": f / FPS + ld,
                       "wav": l["meta"]["wav"], "dur": dur, "hold": hold, "words": words, "beats": beats, "amp": amp, "eq": eq})
        f += n
    return {"slug": ep["slug"], "titel": ep["titel"], "hook": ep.get("hook", ""), "loop": ep.get("loop"), "begriff": ep.get("begriff", ""),
            "kapitel": ep.get("kapitel", []), "fps": FPS, "width": W, "height": H, "frames": f, "scenes": scenes}


def write_timing(tl, path: Path):
    r = [f"# Timing: {tl['titel']}", "", f"{tl['frames']} Frames = {tl['frames']/FPS:.2f} s bei {FPS} fps. "
         "Beat-Aktion startet 3 Frames vor dem Wort, Sound exakt auf dem Wort.", "",
         "| Szene | Start | Ende | Dauer | Sprecher | Text |", "|---|---|---|---|---|---|"]
    for s in tl["scenes"]:
        r.append(f"| {s['i']+1} | {s['f0']/FPS:.2f} s (F{s['f0']}) | {s['f1']/FPS:.2f} s (F{s['f1']}) | "
                 f"{s['n']/FPS:.2f} s | {s['sprecher']} | {s['text']} |")
    r += ["", "## Beats", "", "| Szene | Wort | Wort hörbar | Aktion startet | Sound | Aktion |", "|---|---|---|---|---|---|"]
    for s in tl["scenes"]:
        for b in s.get("beat_list", []):
            r.append(f"| {s['i']+1} | {b['wort']} | {b['f_word']/FPS:.2f} s (F{b['f_word']}) | "
                     f"{b['f_beat']/FPS:.2f} s (F{b['f_beat']}) | {b['sound']} | {b['aktion'][:90]}… |")
    path.write_text("\n".join(r) + "\n")


# ------------------------------------------------------------------ Blender
def run_blender(timeline_path: Path, mode: str, extra: list, log_path: Path):
    cmd = [BLENDER, "-b", "--factory-startup", "--python", str(ENGINE / "scene.py"), "--",
           str(timeline_path), mode] + [str(e) for e in extra]
    with open(log_path, "a") as lf:
        p = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        tail = "".join(open(log_path).readlines()[-40:])
        raise RuntimeError(f"Blender-Fehler ({mode}), siehe {log_path}:\n{tail}")


def render_frames_parallel(tl_path: Path, frames: list, workers: int, scale: float, outdir: Path, logdir: Path):
    """Rendert die angegebenen Frames mit mehreren Blender-Prozessen."""
    outdir.mkdir(parents=True, exist_ok=True)
    todo = [f for f in frames if not (outdir / f"{f:05d}.png").exists()]
    if not todo:
        return
    chunks = [todo[k::workers] for k in range(workers)]
    procs = []
    for k, ch in enumerate(chunks):
        if not ch:
            continue
        lst = logdir / f"frames_{k}.txt"
        lst.write_text(",".join(map(str, ch)))
        cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "--python", str(ENGINE / "scene.py"),
               "--", str(tl_path), "frames", str(lst), str(outdir), str(scale)]
        lf = open(logdir / f"blender_{k}.log", "w")
        procs.append((subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT), lf))
    t0 = time.time()
    while any(p.poll() is None for p, _ in procs):
        time.sleep(15)
        done = len([f for f in frames if (outdir / f"{f:05d}.png").exists()])
        el = time.time() - t0
        log(f"  {done}/{len(frames)} Frames, {el/60:.1f} min")
    for p, lf in procs:
        lf.close()
        if p.returncode != 0:
            raise RuntimeError(f"Blender-Worker fehlgeschlagen, siehe {logdir}")
    missing = [f for f in frames if not (outdir / f"{f:05d}.png").exists()]
    if missing:
        raise RuntimeError(f"{len(missing)} Frames fehlen (Blender-Fehler?), siehe {logdir}/blender_*.log")


# ------------------------------------------------------------------ Hilfen fuer Stufen
def start_anchors(tl_path: Path, work: Path):
    out = work / "anchors.json"
    if out.exists() and out.stat().st_mtime > tl_path.stat().st_mtime:
        return None
    cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "--python", str(ENGINE / "scene.py"), "--",
           str(tl_path), "anchors", str(out)]
    return subprocess.Popen(cmd, stdout=open(work / "anchors.log", "w"), stderr=subprocess.STDOUT)


def wait(p):
    if p is not None and p.wait() != 0:
        raise RuntimeError("Anker-Durchlauf fehlgeschlagen (anchors.log)")


def contact_frames(s):
    """6 Frames pro Szene: Anfang, Beats (Wort-Einsatz), Ende."""
    fr = [s["f0"] + 1]
    fr += sorted({min(s["f1"] - 2, b + 3) for b in s["beats"].values()})
    fr.append(s["f1"] - 2)
    fr = sorted(set(fr))
    while len(fr) < 6:
        gaps = [(fr[k + 1] - fr[k], k) for k in range(len(fr) - 1)]
        g, k = max(gaps)
        fr.insert(k + 1, fr[k] + g // 2)
    while len(fr) > 6:
        gaps = [(fr[k + 1] - fr[k], k) for k in range(1, len(fr) - 2)]
        g, k = min(gaps)
        fr.pop(k + 1)
    return fr


def contact_sheets(tl, work: Path, frames_dir: Path):
    from . import composite
    out = []
    cdir = work / "contact"
    cdir.mkdir(exist_ok=True)
    whips = json.loads((work / "anchors.json").read_text()).get("whips", [])
    for s in tl["scenes"]:
        fr = contact_frames(s)
        for f in fr:
            composite.compose_one(tl, f, frames_dir, work / "overlay", cdir / f"c_{f:05d}.png", whips=whips)
        lst = cdir / f"s{s['i']+1}.txt"
        lst.write_text("".join(f"file 'c_{f:05d}.png'\n" for f in fr))
        sheet = ROOT / "out" / "work" / tl["slug"] / f"kontakt_szene{s['i']+1}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                        "scale=360:640,tile=6x1:padding=6:color=0x1b1830", "-frames:v", "1", str(sheet)], check=True)
        out.append((s["i"] + 1, fr, sheet))
    return out


# ------------------------------------------------------------------ Website (Grundlage aller Code-/Website-Bilder)
def website_stage(force=False):
    """Echte Zeilenzahl (wc -l) -> website/meta.json, Playwright-Aufnahmen, Code-Texturen, Geraete-Texturen."""
    from . import codetex, textures
    web = ROOT / "website"
    meta_p = web / "meta.json"
    n = int(subprocess.run(["wc", "-l", str(web / "index.html")], capture_output=True, text=True,
                           check=True).stdout.split()[0])
    if n < 200:
        raise RuntimeError(f"website/index.html hat nur {n} Zeilen (mindestens 200 verlangt)")
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    stale = force or meta.get("zeilen") != n or not (web / "shots" / "boxen.json").exists() or \
        (web / "index.html").stat().st_mtime > (web / "shots" / "boxen.json").stat().st_mtime
    meta.update({"datei": "index.html", "zeilen": n, "ermittelt_mit": "wc -l"})
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    if stale:
        log("Website: Playwright-Aufnahmen ...")
        subprocess.run(["node", str(web / "capture.js")], check=True)
    codetex.build()
    textures.build()
    log(f"Website: {n} Zeilen (wc -l), Playwright: {json.loads(meta_p.read_text()).get('playwright', {})}")
    return n


# ------------------------------------------------------------------ Render-Engine waehlen
def choose_engine(tl_path: Path, tl: dict, work: Path, workers: int) -> dict:
    """Vorgabe: zuerst Eevee. 10 Frames rendern, Gesamtzeit hochrechnen; > 30 min -> Workbench.
    Laeuft Eevee nicht, Cycles (CPU, 16 Samples, Denoiser) ebenso pruefen."""
    out = work / "engine.json"
    forced = os.environ.get("RENDER_ENGINE")
    if forced:
        info = {"engine": forced, "grund": "per RENDER_ENGINE gesetzt"}
        if out.exists():
            old = json.loads(out.read_text())
            info["benchmark"] = old.get("benchmark")
        out.write_text(json.dumps(info, indent=2, ensure_ascii=False))
        return info
    if out.exists():
        return json.loads(out.read_text())
    n = tl["frames"]
    frames = [int(i * (n - 1) / 9) for i in range(10)]
    bench = {}
    choice = None
    for eng, scale in (("eevee", 0.6667), ("cycles", 0.6667)):
        bdir = work / f"bench_{eng}"
        bdir.mkdir(exist_ok=True)
        lst = bdir / "frames.txt"
        lst.write_text(",".join(map(str, frames)))
        env = dict(os.environ, RENDER_ENGINE=eng)
        t0 = time.time()
        p = subprocess.run([BLENDER, "-b", "--factory-startup", "--python", str(ENGINE / "scene.py"), "--",
                            str(tl_path), "frames", str(lst), str(bdir), str(scale)], env=env,
                           capture_output=True, text=True, timeout=3600)
        times = [float(m) for m in re.findall(r"\[scene\] Frame \d+ ([\d.]+)s", p.stdout)]
        ok = p.returncode == 0 and len(times) == 10
        per = sum(times) / len(times) if times else None
        est = per * n / workers / 60 if per else None
        bench[eng] = {"ok": ok, "sekunden_pro_frame": per, "hochrechnung_min": est, "wand_s": time.time() - t0,
                      "aufloesung": scale}
        log(f"Benchmark {eng}: {'OK' if ok else 'FEHLER'}, {per and round(per, 1)} s/Frame -> "
            f"{est and round(est)} min fuer {n} Frames ({workers} Prozesse)")
        if ok:
            choice = eng if est <= 30 else "workbench"
            break
    info = {"engine": choice or "workbench", "benchmark": bench,
            "grund": "Hochrechnung <= 30 min" if choice in ("eevee", "cycles") else
                     "Hochrechnung > 30 min -> Workbench (Flat Lighting, Texturen, Kavitaet)"}
    out.write_text(json.dumps(info, indent=2, ensure_ascii=False))
    return info


# ------------------------------------------------------------------ Haupt
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--stage", default="all", choices=["voices", "timeline", "style", "contact", "final", "all"])
    ap.add_argument("--scale", type=float, default=float(os.environ.get("RENDER_SCALE", "0.6667")))
    ap.add_argument("--workers", type=int, default=int(os.environ.get("RENDER_WORKERS", "2")))
    ap.add_argument("--frames", default="")
    ap.add_argument("--clean", action="store_true", help="gerenderte Frames/Anker verwerfen (nach Aenderungen)")
    args = ap.parse_args()

    ep_path = (ROOT / args.episode) if not os.path.isabs(args.episode) else Path(args.episode)
    ep = json.loads(ep_path.read_text())
    regie_p = ep_path.with_name(ep_path.stem + ".regie.json")
    regie = json.loads(regie_p.read_text()) if regie_p.exists() else {}
    slug = ep["slug"]
    stem = ep_path.stem
    work = ROOT / "out" / "work" / slug
    work.mkdir(parents=True, exist_ok=True)
    if args.clean:
        for d in ("frames", "overlay", "contact"):
            shutil.rmtree(work / d, ignore_errors=True)
        (work / "anchors.json").unlink(missing_ok=True)

    # 0) echte Website (Zeilenzahl, Screenshots, Code-Texturen)
    if ep["slug"] == "website":
        website_stage()
    # 1) Stimmen + Check (REUSE_TIMELINE=1: vorhandene Timeline fuer Style-Tests wiederverwenden)
    if os.environ.get("REUSE_TIMELINE") == "1" and (work / "timeline.json").exists() and args.stage == "style":
        tl = json.loads((work / "timeline.json").read_text())
        tl_path = work / "timeline.json"
        log(f"Timeline wiederverwendet: {tl['frames']} Frames")
    elif regie.get("stimme") == "keine":
        lines, model = voices_stage_none(ep, regie), "keine"
        (ROOT / "out" / f"{slug}_stimmen-check.md").write_text(
            f"# Stimmen-Check: {ep['titel']}\n\nEntfällt: Diese Folge hat auf Wunsch keine Stimme. Untertitel im Lesetempo "
            f"(Kalle 2,8 / Byte 2,6 Wörter/s), Mundbewegung aus Silben-Hüllkurve, Tonspur nur Soundeffekte.\n")
    elif any("tts" in sz for sz in ep["szenen"]):
        lines, model, cfg = voices_stage_tts(ep, work)
        voice_report_tts(ep, lines, ROOT / "out" / f"{slug}_stimmen-check.md")
    else:
        lines, model, cfg = voices_stage(ep, work)
        for k, v in regie.get("pause_vor_szene", {}).items():   # Pause vor Pointen auch mit Stimme
            lines[int(k) - 1]["lead"] = float(v)
        voice_report(ep, lines, model, cfg, ROOT / "out" / f"{slug}_stimmen-check.md")
    if os.environ.get("REUSE_TIMELINE") != "1" or args.stage != "style":
        tl = build_timeline(ep, lines)
        tl["model"] = model
        if regie.get("hook_karte"):                 # Hook-Karte ab Frame 0 mit Hervorhebung (Regie-Datei)
            tl["hook"] = dict(regie["hook_karte"], gesprochen=ep.get("hook", ""))
        tl_path = work / "timeline.json"
        old = tl_path.read_text() if tl_path.exists() else None
        new = json.dumps(tl, ensure_ascii=False)
        if old != new:
            tl_path.write_text(new)
        log(f"Timeline: {tl['frames']} Frames = {tl['frames']/FPS:.2f} s")
        if any(s_.get("beat_list") for s_ in tl["scenes"]):
            write_timing(tl, ROOT / "out" / f"{slug}_timing.md")
        for s in tl["scenes"]:
            log(f"  Szene {s['i']+1}: {s['f0']}-{s['f1']} ({s['n']/FPS:.2f}s) Beats {s['beats']}")
    if args.stage in ("voices", "timeline"):
        return

    from . import overlays, sfx, composite
    overlays.screen_textures(tl, work / "screen")
    frames_dir = work / "frames"
    t0 = time.time()
    if args.stage in ("style", "contact"):
        if args.stage == "style":
            frames = [int(x) for x in args.frames.split(",")]
        else:
            frames = sorted({f for s in tl["scenes"] for f in contact_frames(s)})
        pa = start_anchors(tl_path, work)
        render_frames_parallel(tl_path, frames, args.workers, args.scale, frames_dir, work)
        wait(pa)
        overlays.overlay_frames(tl, work / "overlay", frames, work / "anchors.json")
        if args.stage == "style":
            whips = json.loads((work / "anchors.json").read_text()).get("whips", [])
            for f in frames:
                composite.compose_one(tl, f, frames_dir, work / "overlay", work / f"style_{f:05d}.png", whips=whips)
        else:
            for i, fr, sheet in contact_sheets(tl, work, frames_dir):
                log(f"Kontaktbogen Szene {i}: Frames {fr} -> {sheet}")
        log(f"fertig in {(time.time()-t0)/60:.1f} min")
        return

    eng = choose_engine(tl_path, tl, work, args.workers)
    os.environ["RENDER_ENGINE"] = eng["engine"]
    if eng["engine"] == "workbench" and "RENDER_SCALE" not in os.environ:
        args.scale = 1.0
    if eng["engine"] == "workbench" and "MB_SUBFRAMES" not in os.environ and ep["slug"] not in ("website", "drei-helfer"):
        os.environ["MB_SUBFRAMES"] = "2"       # Motion Blur an (2 Unterbilder, 180 Grad)
    log(f"Render-Engine: {eng['engine']} ({eng['grund']}), Aufloesung {args.scale:.0%}, "
        f"Motion Blur: {'an (2 Unterbilder)' if os.environ.get('MB_SUBFRAMES') == '2' else 'aus'}")
    frames = list(range(tl["frames"]))
    pa = start_anchors(tl_path, work)
    render_frames_parallel(tl_path, frames, args.workers, args.scale, frames_dir, work)
    log(f"3D-Render fertig in {(time.time()-t0)/60:.1f} min")
    wait(pa)
    overlays.overlay_frames(tl, work / "overlay", frames, work / "anchors.json")
    mix = sfx.build_mix(tl, work)
    out_mp4 = ROOT / "out" / f"{stem}.mp4"
    composite.encode(tl, frames_dir, work / "overlay", mix, out_mp4, args.scale)
    log(f"FERTIG: {out_mp4} ({out_mp4.stat().st_size/1e6:.1f} MB) in {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
