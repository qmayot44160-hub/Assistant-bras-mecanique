"""
Cerveau LOCAL d'ARIA : un vrai modèle de langage qui tourne sur le serveur,
sans aucun appel externe (pas de Claude, pas d'API).

Contrainte assumée : sur Railway (CPU, RAM limitée) on charge un petit modèle
quantifié GGUF via llama.cpp (~0,5 Md de paramètres). Il « pense » vraiment
(passage dans un réseau de neurones) mais reste modeste et lent.

Design : le modèle GÉNÈRE la pensée/parole d'ARIA (une courte phrase). Notre
code traduit ensuite ça en état + geste (heuristique). Ça joue sur la force
d'un petit modèle (générer une phrase) au lieu de sa faiblesse (produire du
JSON strict).

Chargement en tâche de fond au démarrage : le serveur reste réactif, et tant
que le modèle n'est pas prêt on retombe sur les réflexes scriptés. Robuste :
toute erreur laisse simplement le cerveau local indisponible.
"""

from __future__ import annotations
import os
import threading

MODEL_REPO = os.environ.get("LOCAL_MODEL_REPO", "Qwen/Qwen2.5-0.5B-Instruct-GGUF")
MODEL_FILE = os.environ.get("LOCAL_MODEL_FILE", "qwen2.5-0.5b-instruct-q4_k_m.gguf")
MODEL_DIR = os.environ.get("MODEL_DIR", "/data/models")

LOCAL_SYSTEM = (
    "Tu es ARIA, un petit bras robotisé d'atelier : curieux, joueur, attachant. "
    "Tu réponds en français, en UNE seule phrase courte (max 15 mots), sans tiret cadratin. "
    "Tu ne donnes pas de listes, pas d'explications longues : tu es un petit robot, pas un assistant."
)

_state = {"ready": False, "loading": False, "error": None}
_llm = None
_lock = threading.Lock()


def status() -> dict:
    return {"ready": _state["ready"], "loading": _state["loading"], "error": _state["error"],
            "model": MODEL_FILE}


def available() -> bool:
    return _state["ready"] and _llm is not None


def _resolve_dir() -> str:
    for d in (MODEL_DIR, os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "models")):
        try:
            os.makedirs(d, exist_ok=True)
            t = os.path.join(d, ".wtest"); open(t, "w").close(); os.remove(t)
            return d
        except Exception:
            continue
    return "."


def _load():
    global _llm
    try:
        from huggingface_hub import hf_hub_download
        from llama_cpp import Llama
        path = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir=_resolve_dir())
        _llm = Llama(
            model_path=path,
            n_ctx=1024,
            n_threads=max(2, (os.cpu_count() or 2)),
            n_batch=64,
            verbose=False,
        )
        _state["ready"] = True
        print("local_brain: modèle prêt (", MODEL_FILE, ")")
    except Exception as e:  # deps absentes, RAM, réseau HF, fichier introuvable...
        _state["error"] = f"{type(e).__name__}: {e}"
        print("local_brain: indisponible ->", _state["error"])
    finally:
        _state["loading"] = False


def start_loading() -> None:
    """Lance le chargement du modèle en tâche de fond (une seule fois)."""
    if _state["loading"] or _state["ready"]:
        return
    _state["loading"] = True
    threading.Thread(target=_load, daemon=True).start()


def _generate(text: str) -> str:
    """Inference bloquante (protégée par un verrou : llama.cpp n'est pas thread-safe)."""
    with _lock:
        out = _llm.create_chat_completion(
            messages=[
                {"role": "system", "content": LOCAL_SYSTEM},
                {"role": "user", "content": (text or "").strip()},
            ],
            max_tokens=64,
            temperature=0.7,
            top_p=0.9,
        )
    reply = (out["choices"][0]["message"]["content"] or "").strip()
    # garder une seule phrase courte
    reply = reply.replace("\n", " ").strip()
    if len(reply) > 160:
        reply = reply[:157].rstrip() + "..."
    return reply


def _gesture_from(user_text: str, reply: str, brain) -> tuple[str, str]:
    """Traduit texte utilisateur + réponse du modèle en (état, geste)."""
    t = (user_text or "").lower()
    r = (reply or "").lower()
    if any(w in t for w in ("bonjour", "salut", "coucou", "hey", "bonsoir")):
        return "happy", "greet"
    if any(w in r[:12] for w in ("oui", "ouais", "carrément", "bien sûr", "avec plaisir")):
        return "happy", "yes"
    if any(w in r[:12] for w in ("non", "nan", "jamais", "pas ")):
        return "confused", "no"
    if "?" in t:
        return "curious", "tilt"
    if any(w in r for w in ("super", "génial", "content", "cool", "j'adore")):
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
        state, gesture = _gesture_from(text, reply, brain)
        return {"state": state, "gesture": gesture, "say": reply, "sleep": False}
    except Exception as e:
        print("local_brain: erreur inference ->", type(e).__name__, e)
        return None
