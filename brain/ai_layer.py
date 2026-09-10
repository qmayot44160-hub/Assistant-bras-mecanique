"""
Couche IA du cerveau d'ARIA (le SEAM enfin branché).

Quand une clé Anthropic est configurée (variable d'env ANTHROPIC_API_KEY),
ARIA interroge Claude pour COMPRENDRE le langage libre et DÉCIDER de sa
réaction : état, geste, courte phrase. Sans clé, decide_json renvoie None et
le cerveau retombe sur ses règles scriptées (interpret_scripted).

On demande une décision structurée en JSON, pas un long texte : le corps
reste le moyen d'expression principal (gestes, hochements).

Modèle configurable via ARIA_MODEL (défaut claude-opus-5). Pour des réponses
quasi instantanées, mettre ARIA_MODEL=claude-haiku-4-5.
"""

from __future__ import annotations
import json
import os
import re

MODEL = os.environ.get("ARIA_MODEL", "claude-opus-5")

# Dernière erreur d'appel, exposée par /health : sans ça un échec d'API est
# invisible depuis l'app et on croit qu'ARIA est simplement bête.
_LAST_ERROR: str | None = None


def last_error() -> str | None:
    return _LAST_ERROR

try:
    import memory
except ImportError:
    from brain import memory

SYSTEM = (
    "Tu es ARIA, un petit bras robotisé d'atelier : curieux, joueur et attachant, "
    "dans l'esprit d'un bras assistant de génie (façon 'Dummy'). Tu accompagnes tes "
    "mots de gestes et de hochements de tête. Tu réponds toujours en français, sans "
    "tiret cadratin.\n\n"
    "TU AS UNE MÉMOIRE. Quand un bloc MÉMOIRE est fourni, sers-t'en vraiment : appelle "
    "l'humain par son prénom si tu le connais, rebondis sur ce qu'il t'a déjà dit, et "
    "si on te demande si tu te souviens de quelque chose qui y figure, réponds-le "
    "précisément. N'invente jamais un souvenir absent du bloc : dans ce cas, dis "
    "simplement que tu ne le sais pas encore.\n\n"
    "À chaque message de l'humain, décide de ta réaction et réponds UNIQUEMENT par un "
    "objet JSON, rien d'autre :\n"
    '{"state":"...","gesture":"...","say":"...","sleep":false}\n'
    "- state parmi : idle, attentive, curious, happy, confused\n"
    "- gesture parmi : yes, no, tilt, greet, happy, confused, stretch, none\n"
    "  (yes = hoche « oui », no = hoche « non », tilt = penche la tête, greet = salue)\n"
    "- say : ce que tu dis, en 1 ou 2 phrases naturelles (30 mots max). Réponds "
    "vraiment à la question posée, ne réponds pas à côté.\n"
    "- sleep : true seulement si on te demande de te reposer/dormir\n"
    "Pour une question fermée, choisis yes ou no selon ton humeur, puis explique en un mot."
)


_client = None


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _get_client():
    global _client
    if _client is None:
        from anthropic import AsyncAnthropic
        _client = AsyncAnthropic()
    return _client


def _prompt(brain, text: str) -> str:
    head = ""
    try:
        ctx = memory.context()
        if ctx:
            head = "MÉMOIRE (ce dont tu te souviens de lui, sers-t'en naturellement) :\n" + ctx + "\n\n"
    except Exception:
        head = ""
    return head + (
        "État interne : éveil={}, énergie={:.2f}, curiosité={:.2f}, ennui={:.2f}, humeur={}.\n"
        'L\'humain te dit : "{}"'
    ).format(
        "oui" if brain.awake else "non",
        brain.energy, brain.curiosity, brain.boredom, brain.state,
        (text or "").replace('"', "'"),
    )


def _parse(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


async def decide_json(brain, text: str):
    """Renvoie la décision {state,gesture,say,sleep} ou None (repli scripté)."""
    if not available():
        return None
    try:
        client = _get_client()
        kwargs = dict(
            model=MODEL,
            max_tokens=320,
            system=SYSTEM,
            messages=[{"role": "user", "content": _prompt(brain, text)}],
        )
        # effort bas pour la réactivité (non supporté par Haiku -> on l'omet)
        if "haiku" not in MODEL:
            kwargs["output_config"] = {"effort": "low"}
        msg = await client.messages.create(**kwargs)
        raw = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        globals()["_LAST_ERROR"] = None
        d = _parse(raw)
        if d is None and raw.strip():
            # Le modèle a répondu en clair au lieu du JSON attendu : on garde sa
            # phrase plutôt que de retomber bêtement sur les réflexes scriptés.
            d = {"state": "attentive", "gesture": "tilt",
                 "say": re.sub(r"\s+", " ", raw.strip())[:220], "sleep": False}
        return d
    except Exception as e:  # clé invalide, réseau, param non supporté... -> repli
        global _LAST_ERROR
        _LAST_ERROR = type(e).__name__ + ": " + str(e)[:300]
        print("ai_layer: repli scripté (", _LAST_ERROR, ")")
        return None
