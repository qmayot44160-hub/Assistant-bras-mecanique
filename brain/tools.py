"""
Les mains d'ARIA.

Jusqu'ici le modèle produisait une phrase, point. Il ne pouvait pas agir sur
ce qu'on a construit : ni bouger son bras, ni regarder ses propres pièces, ni
relire son journal. Ce module lui donne quatre gestes qu'il peut décider
d'appeler lui-même.

Deux familles :
  - AGIR     bouger, montrer_piece -> produisent un évènement que le corps 3D
             exécute. Le modèle reçoit juste une confirmation.
  - CONSULTER chercher_piece, fouiller_memoire -> ne changent rien, renvoient
             du texte que le modèle relit avant de répondre.

Le format des déclarations suit celui d'OpenAI, qu'Ollama reprend tel quel.
"""

from __future__ import annotations

import unicodedata

try:
    import catalog
    import memory
except ImportError:
    from brain import catalog
    from brain import memory

# Amplitudes réelles du bras (guide TomKnox / Moveo), en degrés. Le modèle
# propose ce qu'il veut, on borne : une consigne hors course casserait la pièce.
JOINTS = {
    "base":    (-60, 90),
    "epaule":  (-110, 110),
    "coude":   (-60, 90),
    "poignet": (-60, 90),
}
_JOINT_ALIAS = {
    "épaule": "epaule", "shoulder": "epaule", "bras": "epaule",
    "elbow": "coude", "avant-bras": "coude",
    "wrist": "poignet", "main": "poignet", "pince": "poignet",
    "yaw": "base", "socle": "base", "taille": "base",
}

DECLARATIONS = [
    {"type": "function", "function": {
        "name": "bouger",
        "description": "Bouge une articulation du bras vers un angle. "
                       "À utiliser quand on te demande de bouger, de te tourner, "
                       "de lever ou baisser quelque chose, ou de montrer un geste.",
        "parameters": {"type": "object", "properties": {
            "articulation": {"type": "string", "enum": list(JOINTS),
                             "description": "base, epaule, coude ou poignet"},
            "degres": {"type": "number",
                       "description": "angle visé en degrés, 0 = position neutre"},
        }, "required": ["articulation", "degres"]},
    }},
    {"type": "function", "function": {
        "name": "montrer_piece",
        "description": "Braque la vue 3D sur une de tes pièces et ouvre sa fiche. "
                       "À utiliser quand on te demande de montrer, désigner ou "
                       "pointer une pièce de ton corps.",
        "parameters": {"type": "object", "properties": {
            "piece": {"type": "string",
                      "description": "nom ou identifiant de la pièce, ex: coude, "
                                     "épaule, pince, carte Arduino"},
        }, "required": ["piece"]},
    }},
    {"type": "function", "function": {
        "name": "chercher_piece",
        "description": "Cherche dans ta nomenclature ce qui correspond à un mot "
                       "et renvoie les caractéristiques réelles. À utiliser pour "
                       "toute question sur tes composants, moteurs, dimensions, "
                       "matériaux ou quantités.",
        "parameters": {"type": "object", "properties": {
            "mot": {"type": "string", "description": "ce qu'on cherche, ex: moteur, courroie, alimentation"},
        }, "required": ["mot"]},
    }},
    {"type": "function", "function": {
        "name": "fouiller_memoire",
        "description": "Relit tes échanges passés à la recherche d'un sujet. "
                       "À utiliser quand on te demande ce qui a été dit avant, "
                       "et que ça ne figure pas dans ce dont tu te souviens déjà.",
        "parameters": {"type": "object", "properties": {
            "sujet": {"type": "string", "description": "le mot à retrouver"},
        }, "required": ["sujet"]},
    }},
]


def _fold(s: str) -> str:
    """Sans accents, en minuscules : « épaule » doit trouver « epaule »."""
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else (hi if v > hi else v)


# --- Exécution ------------------------------------------------------------

def _bouger(args: dict) -> tuple[str, dict | None]:
    nom = _fold(args.get("articulation"))
    nom = _JOINT_ALIAS.get(nom, nom)
    if nom not in JOINTS:
        return ("articulation inconnue, choisis parmi : " + ", ".join(JOINTS), None)
    try:
        deg = float(args.get("degres"))
    except (TypeError, ValueError):
        return ("angle illisible", None)

    lo, hi = JOINTS[nom]
    borne = _clamp(deg, lo, hi)
    action = {"type": "action", "name": "bouger", "articulation": nom, "degres": borne}
    if borne != deg:
        # On le dit au modèle : sinon il annonce un mouvement qui n'a pas eu lieu.
        return ("bougé à %g degrés : %g était hors course (%g a %g)"
                % (borne, deg, lo, hi), action)
    return ("%s bougée à %g degrés" % (nom, borne), action)


def _mots(s: str) -> list[str]:
    return [m for m in "".join(c if c.isalnum() else " " for c in _fold(s)).split() if m]


def _score(p: dict, t: str) -> float:
    """Plus c'est haut, mieux ça colle.

    Prendre la première correspondance ne marchait pas : « coude » tombait sur
    « Bras (épaule-coude) » avant « Axe 3 - coude », parce que le bras vient
    plus tôt dans la nomenclature. On classe, et à qualité égale on préfère le
    nom le plus court : le terme y pèse plus lourd, donc il le désigne mieux.
    """
    pid, nom, role = _fold(p.get("id")), _fold(p.get("name")), _fold(p.get("role"))
    if pid == t:
        base = 100.0
    elif nom == t:
        base = 95.0
    elif t in _mots(nom):
        base = 80.0
    elif t in pid:
        base = 60.0
    elif t in nom:
        base = 40.0
    elif t in role:
        base = 20.0
    else:
        return 0.0
    return base + (len(t) / max(len(nom), 1))


def _trouver_piece(terme: str) -> list[dict]:
    """Les pièces qui collent au terme, la meilleure en tête."""
    t = _fold(terme)
    if not t:
        return []
    notes = [(_score(p, t), p) for p in catalog.load()]
    notes = [(n, p) for n, p in notes if n > 0]
    notes.sort(key=lambda np: -np[0])
    return [p for _, p in notes]


def _montrer_piece(args: dict) -> tuple[str, dict | None]:
    trouves = _trouver_piece(args.get("piece", ""))
    if not trouves:
        return ("aucune pièce ne correspond à « %s »" % args.get("piece"), None)
    p = trouves[0]
    return ("vue braquée sur : " + p.get("name", p["id"]),
            {"type": "action", "name": "montrer_piece",
             "piece": p["id"], "nom": p.get("name", p["id"])})


def _resume_piece(p: dict) -> str:
    bouts = ["%s (%s)" % (p.get("name", p["id"]), p.get("category", "?"))]
    if p.get("qty"):
        bouts.append("quantité %s" % p["qty"])
    if p.get("role"):
        bouts.append(str(p["role"]))
    specs = p.get("specs") or {}
    if specs:
        bouts.append("; ".join("%s: %s" % (k, v) for k, v in list(specs.items())[:5]))
    return " - ".join(bouts)


def _chercher_piece(args: dict) -> tuple[str, dict | None]:
    trouves = _trouver_piece(args.get("mot", ""))
    if not trouves:
        return ("rien dans la nomenclature pour « %s »" % args.get("mot"), None)
    return ("\n".join(_resume_piece(p) for p in trouves[:4]), None)


def _fouiller_memoire(args: dict) -> tuple[str, dict | None]:
    sujet = args.get("sujet", "")
    lignes = memory.search(sujet, limit=6)
    if not lignes:
        return ("rien trouvé sur « %s » dans tes échanges passés" % sujet, None)
    return ("\n".join(lignes), None)


_HANDLERS = {
    "bouger": _bouger,
    "montrer_piece": _montrer_piece,
    "chercher_piece": _chercher_piece,
    "fouiller_memoire": _fouiller_memoire,
}


def run(name: str, args: dict) -> tuple[str, dict | None]:
    """Renvoie (texte rendu au modèle, évènement pour le corps 3D ou None)."""
    fn = _HANDLERS.get(name)
    if not fn:
        return ("outil inconnu : " + str(name), None)
    if not isinstance(args, dict):
        args = {}
    try:
        return fn(args)
    except Exception as e:                      # un outil cassé ne tue pas le tour
        return ("l'outil %s a échoué (%s)" % (name, type(e).__name__), None)
