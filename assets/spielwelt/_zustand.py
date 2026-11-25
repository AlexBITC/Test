"""Gemeinsame Hilfen fuer den Spielwelt-Katalog: Zustands-Plan auswerten, Objekt zur Iso-Kamera drehen."""
import math

NEIGUNG = math.radians(35)
AZIMUT = math.radians(14)


def aktiv(plan, f, start=None):
    """plan: [(frame, zustand), ...] -> Zustand bei Frame f."""
    cur = start if start is not None else (plan[0][1] if plan else None)
    for fr, z in sorted(plan, key=lambda p: p[0]):
        if fr <= f:
            cur = z
    return cur


def seit(plan, f):
    """Frames seit dem letzten Zustandswechsel."""
    last = None
    for fr, z in sorted(plan, key=lambda p: p[0]):
        if fr <= f:
            last = fr
    return f - last if last is not None else 10 ** 6


def zur_kamera(obj):
    """Vorderseite (-Y) zur festen Iso-Kamera drehen (35 Grad Neigung, 14 Grad Azimut)."""
    obj.rotation_euler = (-NEIGUNG + math.pi / 2 - math.pi / 2, 0, AZIMUT)
    obj.rotation_euler = (-NEIGUNG, 0, AZIMUT)
