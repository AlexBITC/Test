"""Stimmen für compose.py: ElevenLabs (Standard) oder Piper (offline), Cache nach Text-Hash.

Cache: cache/voices/<hash>.wav + <hash>.json  (Hash über Backend, Stimme, Einstellungen, Text, Pipeline-Version)
Ergebnis je Zeile: {"wav": Pfad relativ zu ROOT, "dur": s, "words": [{"w", "start", "end"}], "backend": ...}

Backend-Wahl: --tts elevenlabs|piper|auto (auto = ElevenLabs, bei Fehler Piper).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from . import tts

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "voices"
PIPELINE = "v1"            # erhöhen, wenn sich die Nachbearbeitung ändert (invalidiert den Cache)
PIPER_DIR = Path(os.environ.get("PIPER_DIR", "/opt/piper-voices"))
PIPER_VOICES = {"kalle": "de_DE-thorsten-high", "byte": "de_DE-kerstin-low"}
PIPER_LENGTH = {"kalle": 1.0, "byte": 0.95}     # < 1 = schneller
SR = 48000


def log(*a):
    print("[voice]", *a, flush=True)


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]


def _rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


# ---------------------------------------------------------------- Tonhöhe/Tempo
def has_ffmpeg_rubberband() -> bool:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return " rubberband " in out


def rubberband(src: Path, dst: Path, tempo: float = 1.0, pitch_st: float = 0.0):
    """Tempo (>1 schneller) und Tonhöhe (Halbtöne, Formanten erhalten): ffmpeg-Filter oder rubberband-CLI."""
    if has_ffmpeg_rubberband():
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af",
                        f"rubberband=tempo={tempo:.4f}:pitch={2 ** (pitch_st / 12):.5f}:pitchq=quality:"
                        f"formant=preserved:transients=smooth", "-ar", str(SR), "-ac", "1", str(dst)], check=True)
    elif shutil.which("rubberband"):
        tmp = dst.with_suffix(".rb.wav")
        subprocess.run(["rubberband", "-q", "-3", "-F", "--tempo", f"{tempo:.4f}", "-p", f"{pitch_st:.3f}",
                        str(src), str(tmp)], check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-ar", str(SR), "-ac", "1", str(dst)], check=True)
        tmp.unlink()
    else:
        log("WARNUNG: kein rubberband – Tempo/Tonhöhe bleiben unverändert")
        shutil.copy(src, dst)


# ---------------------------------------------------------------- Piper
_PIPER = {}


def _piper_voice(role):
    if role not in _PIPER:
        from piper import PiperVoice
        model = PIPER_DIR / f"{PIPER_VOICES[role]}.onnx"
        if not model.exists():
            raise RuntimeError(f"Piper-Stimme fehlt: {model} (./setup.sh ausführen)")
        _PIPER[role] = PiperVoice.load(str(model))
    return _PIPER[role]


def _voiced_span(y, sr):
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) for i in range(0, max(1, len(y) - hop), hop)])
    thr = max(rms.max() * 10 ** (-38 / 20), 1e-4)
    loud = np.nonzero(rms > thr)[0]
    if not len(loud):
        return 0.0, len(y) / sr, rms, thr
    return loud[0] * 0.01, (loud[-1] + 1) * 0.01, rms, thr


def _estimate_words(text: str, speech: str, spans, y, sr):
    """Piper liefert keine Wort-Zeitstempel: Sprechdauer anteilig nach Sprechtext-Länge verteilen,
    Pausen im Pegel an Satzzeichen ausrichten."""
    t0, t1, rms, thr = _voiced_span(y, sr)
    weights = []
    for w, s, e in spans:
        piece = speech[s:e]
        n = len(re.sub(r"[^\w]", "", piece))
        pause = 0.0
        if re.search(r"[.!?…]$", w):
            pause = 3.5
        elif re.search(r"[,:;]$", w):
            pause = 2.0
        weights.append((max(n, 1) + 1.5 if n else 0.0, pause))
    total = sum(a + b for a, b in weights) or 1.0
    scale = (t1 - t0) / total
    out, t = [], t0
    for (w, s, e), (a, b) in zip(spans, weights):
        st, en = t, t + a * scale
        out.append({"w": w, "start": round(float(st), 3), "end": round(float(en), 3)})
        t = en + b * scale
    return out


def synth_piper(role: str, text: str, pitch_st: float) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    speech, spans = tts.speech_mapping(text)
    key = _hash(["piper", PIPELINE, PIPER_VOICES[role], PIPER_LENGTH[role], pitch_st, speech])
    meta_p, wav_p = CACHE / f"{key}.json", CACHE / f"{key}.wav"
    if meta_p.exists() and wav_p.exists():
        return dict(json.loads(meta_p.read_text()), cached=True)
    from piper import SynthesisConfig
    v = _piper_voice(role)
    raw = CACHE / f"{key}_raw.wav"
    with wave.open(str(raw), "wb") as wf:
        v.synthesize_wav(speech, wf, syn_config=SynthesisConfig(length_scale=PIPER_LENGTH[role]))
    mid = CACHE / f"{key}_mid.wav"
    rubberband(raw, mid, 1.0, pitch_st) if abs(pitch_st) > 0.01 else \
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-ar", str(SR), "-ac", "1", str(mid)], check=True)
    y, sr = sf.read(str(mid), dtype="float32")
    t0, t1, _, _ = _voiced_span(y, sr)
    a, b = max(0, int((t0 - 0.04) * sr)), min(len(y), int((t1 + 0.16) * sr))
    y = y[a:b].copy()
    n = min(int(0.03 * sr), len(y))
    y[-n:] *= np.linspace(1, 0, n) ** 2
    sf.write(str(wav_p), y, sr, subtype="PCM_16")
    raw.unlink(missing_ok=True)
    mid.unlink(missing_ok=True)
    words = _estimate_words(text, speech, spans, y, sr)
    meta = {"backend": "piper", "voice": PIPER_VOICES[role], "text": text, "speech": speech,
            "wav": _rel(wav_p), "dur": round(len(y) / sr, 3), "words": words}
    meta_p.write_text(json.dumps(meta, ensure_ascii=False))
    return dict(meta, cached=False)


# ---------------------------------------------------------------- ElevenLabs
def synth_elevenlabs(role: str, text: str, reaktion: str, cfg: dict, model: str) -> dict:
    """Ein Versuch mit den Grund-Einstellungen; Tempo-Korrektur und Tonhöhe wie in der alten Pipeline."""
    vid = cfg["voices"][role]["voice_id"]
    settings, seed = tts.line_settings(role, 0, cfg, model)
    tag = tts.REACTION_TAG.get(role, {}).get(reaktion, "") if role == "kalle" and reaktion in ("jubel", "schock") else ""
    pitch = cfg.get("pitch_semitones", {}).get(role, 0.0)
    speech, spans = tts.speech_mapping(text)
    key = _hash(["elevenlabs", PIPELINE, vid, model, settings, seed, tag, pitch, speech])
    meta_p = CACHE / f"{key}.json"
    if meta_p.exists():
        m = json.loads(meta_p.read_text())
        if (ROOT / m["wav"]).exists():
            return dict(m, cached=True)
    tts.CACHE = CACHE / "elevenlabs"
    raw = tts.tighten(tts.synth(speech, vid, model, settings, tag, seed=seed))
    words = tts.word_times(raw, spans)
    sp = [w for w in words if re.search(r"\w", w["w"]) and w["end"] > w["start"]]
    lo, hi = tts.TEMPO[role]
    wps = len(sp) / max(0.1, sp[-1]["end"] - sp[0]["start"]) if sp else lo
    factor = 1.0
    if wps > hi:
        factor = max(tts.STRETCH_LIMIT[0], (hi - 0.05) / wps)
    elif wps < lo:
        factor = min(tts.STRETCH_LIMIT[1], (lo + 0.05) / wps)
    wav_p = CACHE / f"{key}.wav"
    if abs(factor - 1) > 0.01 or abs(pitch) > 0.01:
        rubberband(ROOT / raw["wav"], wav_p, factor, pitch)
    else:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(ROOT / raw["wav"]), "-ar", str(SR), "-ac", "1",
                        str(wav_p)], check=True)
    words = [{"w": w["w"], "start": round(w["start"] / factor, 3), "end": round(w["end"] / factor, 3)} for w in words]
    meta = {"backend": "elevenlabs", "voice": vid, "model": model, "text": text, "speech": speech, "tag": tag,
            "stretch": factor, "wav": _rel(wav_p), "dur": round(sf.info(str(wav_p)).duration, 3), "words": words}
    meta_p.write_text(json.dumps(meta, ensure_ascii=False))
    return dict(meta, cached=False)


# ---------------------------------------------------------------- Einstieg
def lines(ep: dict, backend: str = "auto") -> list:
    CACHE.mkdir(parents=True, exist_ok=True)
    cfg, model = None, None
    if backend in ("auto", "elevenlabs"):
        try:
            model = os.environ.get("ELEVENLABS_MODEL") or json.loads(tts.VOICES_FILE.read_text()).get("model") \
                or tts.pick_model()
            cfg = tts.load_voices(model)
        except Exception as e:  # noqa: BLE001
            if backend == "elevenlabs":
                raise
            log(f"ElevenLabs nicht erreichbar ({e}) – nehme Piper")
            backend = "piper"
    pitch_cfg = json.loads(tts.VOICES_FILE.read_text()).get("pitch_semitones", {}) if tts.VOICES_FILE.exists() else {}
    out = []
    if backend in ("auto", "elevenlabs"):
        try:
            for i, sz in enumerate(ep["szenen"]):
                m = synth_elevenlabs(sz["sprecher"], sz["text"], sz.get("reaktion", ""), cfg, model)
                log(f"Szene {i+1} {sz['sprecher']}: elevenlabs {m['dur']:.2f}s {'(Cache)' if m.get('cached') else ''}")
                out.append(m)
            return out
        except Exception as e:  # noqa: BLE001
            if backend == "elevenlabs":
                raise
            # keine gemischten Stimmen in einer Episode: komplett auf Piper
            log(f"WARNUNG: ElevenLabs-Fehler ({str(e)[:300]}) – ganze Episode mit Piper")
            out = []
    for i, sz in enumerate(ep["szenen"]):
        role = sz["sprecher"]
        m = synth_piper(role, sz["text"], pitch_cfg.get(role, 0.0) + (2.0 if role == "byte" else 0.0))
        log(f"Szene {i+1} {role}: piper {m['dur']:.2f}s {'(Cache)' if m.get('cached') else ''}")
        out.append(m)
    return out
