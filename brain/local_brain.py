"""
Cerveau LOCAL d'ARIA : un vrai modèle de langage qui tourne CHEZ TOI, via
Ollama, sans aucun appel externe (pas de Claude, pas d'API cloud).

Pourquoi Ollama : c'est le moyen le plus simple de faire tourner un modèle
open-source sur un PC Windows/Mac/Linux avec accélération GPU (ta RTX 2060).
Tu installes Ollama, tu fais `ollama pull qwen2.5:7b`, et notre serveur lui
parle en local sur http://127.0.0.1:11434.

Le modèle GÉNÈRE la pensée/parole d'ARIA (une phrase courte) ; notre code la
traduit en état + geste. Aucune donnée ne sort de ta machine.

Réglages (variables d'environnement) :
  OLLAMA_HOST   (défaut http://127.0.0.1:11434)
  OLLAMA_MODEL  (défaut qwen2.5:7b)

Sur un serveur sans Ollama (ex. Railway), le ping échoue -> cerveau local
indisponible -> repli automatique sur les règles scriptées. Rien ne casse.
"""

from __future__ import annotations
import json
import os
import urllib.request

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

try:
    import memory
except ImportError:
    from brain import memory

LOCAL_SYSTEM = (
    "Tu es ARIA, un petit bras robotisé d'atelier : curieux, joueur, attachant. "
    "Tu réponds en français, en 1 ou 2 phrases naturelles (30 mots max), sans "
    "tiret cadratin. Pas de listes, pas d'explications longues : tu es un petit "
    "robot, pas un assistant.\n"
    "TU AS UNE MÉMOIRE. Quand on te donne ce dont tu te souviens, sers-t'en : "
    "appelle l'humain par son prénom si tu le connais, et si on te demande un "
    "souvenir qui y figure, réponds-le précisément. N'invente jamais un souvenir "
    "absent : dis alors que tu ne le sais pas encore."
)


_state = {"ready": False, "loading": False, "error": None}


def status() -> dict:
    return {"ready": _state["ready"], "loading": _state["loading"],
            "error": _state["error"], "host": OLLAMA_HOST, "model": OLLAMA_MODEL}


def available() -> bool:
    return _state["ready"]


def _ping() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_HOST + "/api/tags", timeout=2) as r:
            return r.status == 200
    except Exception as e:
        _state["error"] = f"Ollama injoignable ({type(e).__name__})"
        return False


def start_loading() -> None:
    """Vérifie qu'Ollama répond (le modèle se charge à la première requête)."""
    _state["loading"] = True
    _state["ready"] = _ping()
    if _state["ready"]:
        _state["error"] = None
        print("local_brain: Ollama OK ->", OLLAMA_HOST, "modèle", OLLAMA_MODEL)
    else:
        print("local_brain: indisponible ->", _state["error"])
    _state["loading"] = False


def _messages(text: str) -> list[dict]:
    """Système + mémoire + phrase de l'humain."""
    msgs = [{"role": "system", "content": LOCAL_SYSTEM}]
    try:
        ctx = memory.context()
        if ctx:
            msgs.append({"role": "system",
                         "content": "Ce dont tu te souviens de lui :\n" + ctx})
    except Exception:
        pass
    msgs.append({"role": "user", "content": (text or "").strip()})
    return msgs


def _generate(text: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": _messages(text),
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 80},
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA_HOST + "/api/chat", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    reply = ((data.get("message") or {}).get("content") or "").strip()
    reply = reply.replace("\n", " ").strip()
    if len(reply) > 160:
        reply = reply[:157].rstrip() + "..."
    return reply


def _gesture_from(user_text: str, reply: str) -> tuple[str, str]:
    t = (user_text or "").lower()
    r = (reply or "").lower()
    if any(w in t for w in ("bonjour", "salut", "coucou", "hey", "bonsoir")):
        return "happy", "greet"
    if any(w in r[:14] for w in ("oui", "ouais", "carrément", "bien sûr", "avec plaisir")):
        return "happy", "yes"
    if any(w in r[:14] for w in ("non", "nan", "jamais", "pas ")):
        return "confused", "no"
    if "?" in t:
        return "curious", "tilt"
    if any(w in r for w in ("super", "génial", "content", "cool", "j'adore", "j'aime")):
        return "happy", "happy"
    return "attentive", "tilt"


async def decide_json(brain, text: str):
    """Renvoie {state,gesture,say} produit par le modèle local, ou None (repli)."""
    if not available():
        return None
    try:
        import asyncio
        reply = await asyncio.to_thread(_generate, text)
        if not reply:
            return None
        state, gesture = _gesture_from(text, reply)
        return {"state": state, "gesture": gesture, "say": reply, "sleep": False}
    except Exception as e:
        print("local_brain: erreur inference ->", type(e).__name__, e)
        return None
