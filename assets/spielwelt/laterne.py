"""Strassenlaterne (gruen, rundes Glas). Zustaende: aus, an (warmes Leuchten, bei 'abend' automatisch an)."""
import look as L
import spielwelt as SW

INFO = {"name": "laterne", "groesse": [0.4, 0.4, 2.2], "anker": "mitte_unten", "zustaende": ["aus", "an"],
        "beschreibung": "Laterne, schaltet sich abends an"}


def bauen(coll, name, **kw):
    root = L.empty(name, coll=coll)
    L.cyl(f"{name}_mast", 0.06, 2.0, 8, SW.m("laterne", "#3E6B5A", 0.5), root, (0, 0, 1.0), coll)
    m_g = L.unique_mat(SW.m("laternenglas", "#E9E2CC", 0.3), f"sw_laterne_an_{name}")
    L.sphere(f"{name}_glas", 0.2, 10, 7, (1, 1, 1.1), m_g, root, (0, 0, 2.1), coll)
    L.cyl(f"{name}_kappe", 0.2, 0.1, 8, SW.m("laterne", "#3E6B5A", 0.5), root, (0, 0, 2.3), coll, r2=0.05)
    schein = L.cyl(f"{name}_schein", 0.9, 0.01, 18, SW.m("licht_schein", "#FFD27A", 0.3, alpha=0.35), root, (0, 0, 0.03), coll)
    schein.scale = (0, 0, 0)
    return SW.P(root=root, m_glas=m_g, schein=schein, wetter=lambda T, S, f0, f1: _an(T, S, m_g, schein, f0, f1))


def _an(T, S, m_g, schein, f0, f1):
    aus, an = L.srgb("#E9E2CC"), L.srgb("#FFD27A")

    def k(f):
        return max(S.wetter_an("abend", f), S.wetter_an("nacht", f))
    T.set(m_g, "diffuse_color", lambda f: tuple(aus[i] + (an[i] - aus[i]) * k(f) for i in range(3)) + (1,), f0, f1)
    T.set(schein, "scale", lambda f: (k(f), k(f), 1) if k(f) > 0.05 else (0, 0, 0), f0, f1)
