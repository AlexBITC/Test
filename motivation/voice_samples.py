"""Erzeugt Stimmproben (Satz 1+2) fuer die Stimmen-Auswahl."""
import json, os, sys, urllib.request, base64, subprocess
from pathlib import Path
API = "https://api.elevenlabs.io"
KEY = os.environ.get("ELEVENLABS_API_KEY") or "proxy-injected"  # Proxy ersetzt den Platzhalter
OUT = Path(__file__).resolve().parent.parent / "out" / "motivation" / "proben"
SETTINGS = {"stability": 0.40, "similarity_boost": 0.80, "style": 0.30, "use_speaker_boost": True}
TEXT = "You said you'd start tomorrow. ... That was a year ago."
CANDS = {"vivie": "z7U1SjrEq4fDDDriOQEN", "mariana": "OB0Jj6v9DGLLgz8dD57i", "missb": "PFqo8D2UY6vd5tzJUrsl", "viktoria": "tPzOTlbmuCEa6h67Xb6k", "cate": "J64VNrjLE6uKFBKlxfSJ"}
for name, vid in CANDS.items():
    body = json.dumps({"text": TEXT, "model_id": "eleven_multilingual_v2", "voice_settings": SETTINGS}).encode()
    req = urllib.request.Request(f"{API}/v1/text-to-speech/{vid}?output_format=mp3_44100_192", data=body,
                                 method="POST", headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        (OUT / f"probe_{name}.mp3").write_bytes(r.read())
    print("ok", name)
