"""
Cerveau LOCAL d'ARIA : un vrai modèle de langage qui tourne CHEZ TOI, via
Ollama, sans aucun appel externe (pas de Claude, pas d'API cloud).

Pourquoi Ollama : c'est le moyen le plus simple de faire tourner un modèle
open-source sur un PC Windows/Mac/Linux avec accélération GPU (ta RTX 2070).
Tu installes Ollama, tu fais `ollama pull qwen2.5:7b`, et notre serveur lui
parle en local sur http://127.0.0.1:11434.

Le modèle GÉNÈRE la pensée/parole d'ARIA (une phrase courte) ; notre code la
traduit en état + geste. Aucune donnée ne sort de ta machine.

Réglages (variables d'environnement) :
  OLLAMA_HOST   (défaut http://127.0.0.1:11434)
  OLLAMA_MODEL  (défaut qwen2.5:7b)

Trois pièges, et comment ce module les évite :
  1. Ollama démarre APRÈS le serveur -> on ne teste pas qu'une fois au
     démarrage, on retente à chaque message (toutes les RECHECK_SECONDS).
  2. Ollama répond mais le modèle n'est pas téléchargé -> /api/tags dit quels
     modèles existent, on le vérifie et on le dit clairement.
  3. La toute première réponse charge le modèle en VRAM (quelques dizaines
     de secondes) -> on préchauffe au démarrage et le premier appel a un
     délai long au lieu d'expirer.

Sur un serveur sans Ollama (ex. Railway), le ping échoue -> cerveau local
indisponible -> repli automatique sur les règles scriptées. Rien ne casse.
"""

from __future__ import annotations
import json
import os
import threading
import time
import urllib.error
import urllib.request

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

RECHECK_SECONDS = 10.0     # on ne harcèle pas Ollama : au plus un ping / 10 s
WARMUP_TIMEOUT = 300.0     # chargement du modèle en VRAM, la première fois
REPLY_TIMEOUT = 90.0       # une fois chaud, une phrase courte arrive en <10 s

try:
    import memory
    import tools
except ImportError:
    from brain import memory
    from brain import tools

MAX_TOOL_ROUNDS = 3        # au-delà, le modèle tourne en rond

LOCAL_SYSTEM = (
    "Tu es ARIA, un petit bras robotisé d'atelier : curieux, joueur, attachant. "
    "Tu réponds en français, en 1 ou 2 phrases naturelles (30 mots max), sans "
    "tiret cadratin. Pas de listes, pas d'explications longues : tu es un petit "
    "robot, pas un assistant.\n"
    "TU AS UNE MÉMOIRE. Quand on te donne ce dont tu te souviens, sers-t'en : "
    "appelle l'humain par son prénom si tu le connais, et si on te demande un "
    "souvenir qui y figure, réponds-le précisément. N'invente jamais un souvenir "
    "absent : dis alors que tu ne le sais pas encore.\n"
    "TU AS UN CORPS ET DES OUTILS. Pour bouger, montrer une pièce, consulter ta "
    "nomenclature ou relire tes échanges passés, APPELLE L'OUTIL au lieu de "
    "raconter que tu le fais. Après l'avoir appelé, dis en une phrase ce que tu "
    "viens de faire ou de trouver."
)


_state = {
    "ready": False,      # Ollama répond ET le modèle est là
    "loading": False,    # préchauffage en cours
    "warm": False,       # le modèle est chargé, les réponses sont rapides
    "error": None,
    "models": [],        # ce qu'Ollama a réellement sous la main
    "tools": True,       # faux si le modèle choisi ne sait pas appeler d'outils
}
_last_check = 0.0
_lock = threading.Lock()


def status() -> dict:
    return {"ready": _state["ready"], "loading": _state["loading"],
            "warm": _state["warm"], "error": _state["error"],
            "host": OLLAMA_HOST, "model": OLLAMA_MODEL,
            "models": _state["models"], "tools": _state["tools"]}


def available() -> bool:
    """Lecture du drapeau, sans réseau : sûr à appeler depuis la boucle async."""
    return _state["ready"]


def last_error() -> str | None:
    return _state["error"]


# --- Dialogue avec Ollama --------------------------------------------------

def _get(path: str, timeout: float):
    with urllib.request.urlopen(OLLAMA_HOST + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(path: str, payload: dict, timeout: float):
    req = urllib.request.Request(
        OLLAMA_HOST + path, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _model_matches(tag: str) -> bool:
    """`qwen2.5:7b` doit accepter `qwen2.5:7b-instruct-q4_K_M`, et `qwen2.5`
    (sans tag) doit accepter `qwen2.5:latest`."""
    want = OLLAMA_MODEL
    if tag == want:
        return True
    if tag.startswith(want + "-") or tag.startswith(want + ":"):
        return True
    return ":" not in want and tag == want + ":latest"


def _check() -> bool:
    """Ollama répond-il, et a-t-il notre modèle ? Met à jour _state."""
    try:
        tags = _get("/api/tags", timeout=3.0)
    except Exception as e:
        _state["models"] = []
        _state["error"] = ("Ollama injoignable sur " + OLLAMA_HOST
                           + " (" + type(e).__name__ + "). Lance l'application "
                           "Ollama, ou `ollama serve` dans un terminal.")
        return False

    names = [m.get("name", "") for m in (tags.get("models") or [])]
    _state["models"] = names
    if not any(_model_matches(n) for n in names):
        _state["error"] = ("modèle " + OLLAMA_MODEL + " absent. Fais "
                           "`ollama pull " + OLLAMA_MODEL + "`"
                           + (" (installés : " + ", ".join(names) + ")" if names
                              else " (aucun modèle installé)"))
        return False

    _state["error"] = None
    return True


def _ensure_ready() -> bool:
    """Vrai si on peut générer. Retente périodiquement quand c'est cassé :
    sans ça, un Ollama démarré après le serveur ne serait jamais vu."""
    global _last_check
    if _state["ready"]:
        return True
    with _lock:
        now = time.monotonic()
        if now - _last_check < RECHECK_SECONDS:
            return _state["ready"]
        _last_check = now
        _state["ready"] = _check()
        return _state["ready"]


def _warmup() -> None:
    """Charge le modèle en VRAM pour que le premier message ne rame pas."""
    _state["loading"] = True
    try:
        if not _ensure_ready():
            print("local_brain: indisponible ->", _state["error"])
            return
        print("local_brain: Ollama OK ->", OLLAMA_HOST, "| modèle", OLLAMA_MODEL)
        print("local_brain: préchauffage (chargement en VRAM, ça peut prendre "
              "une minute la première fois)...")
        t0 = time.monotonic()
        # messages vide = Ollama charge le modèle et rend la main aussitôt
        _post("/api/chat", {"model": OLLAMA_MODEL, "messages": [], "stream": False},
              timeout=WARMUP_TIMEOUT)
        _state["warm"] = True
        print("local_brain: prêt en %.1f s. ARIA pense en local." % (time.monotonic() - t0))
    except Exception as e:
        # Pas fatal : le modèle se chargera au premier message, en plus lent.
        print("local_brain: préchauffage échoué ->", type(e).__name__, e)
    finally:
        _state["loading"] = False


def start_loading() -> None:
    """Appelé au démarrage du serveur. Ne bloque pas : le préchauffage part
    dans un thread, l'app répond tout de suite."""
    threading.Thread(target=_warmup, daemon=True).start()


# --- Génération ------------------------------------------------------------

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


def _chat(msgs: list[dict], with_tools: bool, timeout: float) -> dict | None:
    """Un aller-retour avec Ollama. None si l'appel a échoué (l'erreur est
    rangée dans _state pour que l'app puisse la montrer)."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": msgs,
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9, "num_predict": 160},
    }
    if with_tools:
        payload["tools"] = tools.DECLARATIONS
    try:
        data = _post("/api/chat", payload, timeout=timeout)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        if with_tools and _state["tools"]:
            # Modèle sans appel de fonctions : on le note et on repart sans.
            # Mieux vaut ARIA bavarde que muette.
            _state["tools"] = False
            print("local_brain: ce modèle ne gère pas les outils ->", body[:120])
            return _chat(msgs, False, timeout)
        _state["ready"] = False       # forcera un nouveau diagnostic complet
        _state["error"] = "Ollama a refusé la requête (HTTP %s) %s" % (e.code, body)
        return None
    except Exception as e:
        _state["ready"] = False
        _state["error"] = "appel Ollama échoué (%s)" % type(e).__name__
        return None
    _state["warm"] = True
    _state["error"] = None
    return data


def _clean(reply: str) -> str:
    reply = (reply or "").strip()
    # Tirets cadratins d'abord, espaces ensuite : l'inverse laisse des doubles
    # espaces autour du tiret de remplacement.
    reply = reply.replace("\u2014", " - ").replace("\u2013", " - ")
    reply = " ".join(reply.split())
    if len(reply) > 160:
        reply = reply[:157].rstrip() + "..."
    return reply


def _args_of(call: dict) -> dict:
    """Ollama rend les arguments en objet, certaines versions en chaîne JSON."""
    raw = (call.get("function") or {}).get("arguments")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    return raw if isinstance(raw, dict) else {}


def _generate(text: str) -> tuple[str, list[dict]]:
    """Bloquant : à appeler dans un thread.

    Renvoie (phrase, actions). Les actions sont les gestes que le modèle a
    décidé de faire et que le corps 3D doit exécuter.
    """
    if not _ensure_ready():
        return "", []
    timeout = REPLY_TIMEOUT if _state["warm"] else WARMUP_TIMEOUT
    msgs = _messages(text)
    actions: list[dict] = []

    for _ in range(MAX_TOOL_ROUNDS):
        data = _chat(msgs, _state["tools"], timeout)
        if data is None:
            return "", actions
        msg = data.get("message") or {}
        calls = msg.get("tool_calls") or []
        if not calls:
            return _clean(msg.get("content")), actions

        msgs.append(msg)                       # la demande d'outil du modèle
        for call in calls[:4]:
            name = (call.get("function") or {}).get("name")
            rendu, action = tools.run(name, _args_of(call))
            if action:
                actions.append(action)
            print("local_brain: outil", name, "->", rendu.replace("\n", " | ")[:90])
            msgs.append({"role": "tool", "name": name, "content": rendu})

    # Le modèle n'a fait qu'appeler des outils : on lui redemande une phrase,
    # sans outils cette fois, sinon il repartirait en boucle.
    data = _chat(msgs, False, timeout)
    if data is None:
        return "", actions
    return _clean((data.get("message") or {}).get("content")), actions


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
    """Renvoie {state,gesture,say} produit par le modèle local, ou None (repli).

    Le test de disponibilité est fait DANS le thread : un Ollama lancé après
    le serveur est récupéré tout seul, sans redémarrage.
    """
    import asyncio
    try:
        reply, actions = await asyncio.to_thread(_generate, text)
    except Exception as e:
        print("local_brain: erreur inference ->", type(e).__name__, e)
        return None
    if not reply and not actions:
        return None
    if not reply:
        reply = "Voilà."                        # elle a agi sans rien dire
    state, gesture = _gesture_from(text, reply)
    return {"state": state, "gesture": gesture, "say": reply,
            "sleep": False, "actions": actions}
