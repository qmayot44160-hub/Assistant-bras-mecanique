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

try:
    import memory
except ImportError:
    from brain import memory

SYSTEM = (
    "Tu es ARIA, un petit bras robotisé d'atelier : curieux, joueur et attachant, "
    "dans l'esprit d'un bras assistant de génie (façon 'Dummy'). Tu ne discutes pas "
    "longuement, tu t'exprimes surtout par gestes et hochements de tête. Tu réponds "
    "toujours en français, sans tiret cadratin.\n\n"
    "À chaque message de l'humain, décide de ta réaction et réponds UNIQUEMENT par un "
    "objet JSON, rien d'autre :\n"
    '{"state":"...","gesture":"...","say":"...","sleep":false}\n'
    "- state parmi : idle, attentive, curious, happy, confused\n"
    "- gesture parmi : yes, no, tilt, greet, happy, confused, stretch, none\n"
    "  (yes = hoche « oui », no = hoche « non », tilt = penche la tête, greet = salue)\n"
    "- say : courte phrase (max 12 mots) de ce que tu penses/dis\n"
    "- sleep : true seulement si on te demande de te reposer/dormir\n"
    "Pour une question fermée, choisis yes ou no selon ton humeur et réponds brièvement."
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
        return _parse(raw)
    except Exception as e:  # clé invalide, réseau, param non supporté... -> repli
        print("ai_layer: repli scripté (", type(e).__name__, e, ")")
        return None
