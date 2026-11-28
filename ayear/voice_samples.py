"""Stimmproben (Satz 1+2). Schluessel nur aus ELEVENLABS_API_KEY; ist er leer, ersetzt der
authentifizierende Proxy der Cloud-Umgebung den Platzhalter."""
import json, os, sys, urllib.request
from pathlib import Path
KEY = os.environ.get("ELEVENLABS_API_KEY") or "proxy-injected"
OUT = Path(__file__).resolve().parent.parent / "out" / "ayear" / "proben"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True}
TEXT = "A year from now, you'll be somewhere. ... The only question is where."
CANDS = {"sedona": "Y02DpjDrIqEQiinPoGZG", "carolyn": "4rgssJ1pg3E9c0U78Iid", "emma": "Gdj2QBsAjgQnu3rwg2ZN",
         "pamela": "5WdslVl9OFNf1eZigGfk", "fernanda": "hnFidmF05jrIKH0LAjEc", "viktoria": "tPzOTlbmuCEa6h67Xb6k"}
for name, vid in CANDS.items():
    body = json.dumps({"text": TEXT, "model_id": "eleven_multilingual_v2", "voice_settings": SETTINGS}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_192",
                                 data=body, method="POST", headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        (OUT / f"probe_{name}.mp3").write_bytes(r.read())
