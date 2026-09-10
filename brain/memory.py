"""
Mémoire d'ARIA.

Deux niveaux, comme chez nous :
  - les FAITS   : ce qui dure (ton prénom, ce que tu aimes). Peu nombreux, stables.
  - les NOTES   : ce que tu lui demandes explicitement de retenir.
  - les ÉVÈNEMENTS : le fil des échanges récents, pour le contexte immédiat.

Persisté dans DATA_DIR/memory.json (volume Railway), donc ça survit aux
redéploiements. Le contexte est réinjecté dans le cerveau à chaque phrase,
c'est ce qui fait qu'ARIA "se souvient".
"""

from __future__ import annotations
import json
import re
import time
from pathlib import Path

try:
    from catalog import DATA_DIR          # lancé depuis brain/
except ImportError:
    from brain.catalog import DATA_DIR    # lancé depuis la racine

MEMORY_FILE = DATA_DIR / "memory.json"

MAX_EVENTS = 400      # on garde le fil récent, pas toute l'histoire
MAX_NOTES = 120
CONTEXT_EVENTS = 8    # nombre d'échanges réinjectés dans le prompt

_EMPTY = {"facts": {}, "notes": [], "events": []}


def _read() -> dict:
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        for k, v in _EMPTY.items():
            data.setdefault(k, type(v)())
        return data
    except Exception:
        return {"facts": {}, "notes": [], "events": []}


def _write(data: dict) -> None:
    try:
        MEMORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load() -> dict:
    return _read()


def clear() -> dict:
    _write({"facts": {}, "notes": [], "events": []})
    return _read()


# --- Écriture -------------------------------------------------------------
def set_fact(key: str, value: str) -> None:
    key = (key or "").strip().lower()[:40]
    value = (value or "").strip()[:200]
    if not key or not value:
        return
    data = _read()
    data["facts"][key] = {"v": value, "ts": time.time()}
    _write(data)


def forget_fact(key: str) -> bool:
    data = _read()
    if key in data["facts"]:
        del data["facts"][key]
        _write(data)
        return True
    return False


def add_note(text: str) -> None:
    text = (text or "").strip()[:280]
    if not text:
        return
    data = _read()
    if any(n["t"].lower() == text.lower() for n in data["notes"]):
        return                                    # pas de doublon
    data["notes"].append({"t": text, "ts": time.time()})
    data["notes"] = data["notes"][-MAX_NOTES:]
    _write(data)


def forget_note(index: int) -> bool:
    data = _read()
    if 0 <= index < len(data["notes"]):
        data["notes"].pop(index)
        _write(data)
        return True
    return False


def add_event(role: str, text: str) -> None:
    text = (text or "").strip()[:400]
    if not text:
        return
    data = _read()
    data["events"].append({"r": role, "t": text, "ts": time.time()})
    data["events"] = data["events"][-MAX_EVENTS:]
    _write(data)


# --- Extraction automatique de faits depuis une phrase --------------------
_PATTERNS = [
    (re.compile(r"\bje m'appelle\s+([\w\-' ]{2,30})", re.I), "prénom"),
    (re.compile(r"\bmon (?:pré)?nom,?\s*(?:c'est|est)\s+([\w\-' ]{2,30})", re.I), "prénom"),
    (re.compile(r"\bj'ai\s+(\d{1,2})\s+ans\b", re.I), "âge"),
    (re.compile(r"\bje (?:suis|bosse|travaille) (?:comme|en tant que)\s+([\w\-' ]{2,40})", re.I), "métier"),
    (re.compile(r"\bj'habite (?:à|a|en|au)\s+([\w\-' ]{2,40})", re.I), "lieu"),
]
_NOTE_RE = re.compile(r"\b(?:retiens|souviens-toi|rappelle-toi|note)\s+(?:bien\s+)?(?:que\s+)?(.{3,240})", re.I)
_LIKE_RE = re.compile(r"\bj'(?:aime|adore)\s+(?!pas\b)(.{2,80})", re.I)
_DISLIKE_RE = re.compile(r"\bje (?:déteste|hais)\s+(.{2,80})|\bj'aime pas\s+(.{2,80})", re.I)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip(" .,;:!?").strip()


# Un fait est court : on coupe à la première conjonction ou ponctuation,
# sinon "je m'appelle Quentin et j'aime les robots" donne un prénom absurde.
_CUT_RE = re.compile(r"\s+(?:et|mais|puis|donc|car|ou|avec|parce)\b|[,;:!?\.]|\bj'", re.I)


def _cut_fact(s: str) -> str:
    s = _clean(s)
    m = _CUT_RE.search(s)
    if m:
        s = s[:m.start()]
    return _clean(s)


def learn_from(text: str) -> list[str]:
    """Extrait des faits d'une phrase. Renvoie la liste de ce qui a été retenu."""
    learned: list[str] = []
    t = (text or "").strip()
    if not t:
        return learned

    for rx, key in _PATTERNS:
        m = rx.search(t)
        if m:
            val = _cut_fact(m.group(1))
            if val:
                set_fact(key, val)
                learned.append(f"{key} : {val}")

    m = _NOTE_RE.search(t)
    if m:
        note = _clean(m.group(1))
        if note:
            add_note(note)
            learned.append(note)

    m = _LIKE_RE.search(t)
    if m:
        v = _clean(m.group(1))
        if v:
            add_note(f"aime {v}")
            learned.append(f"aime {v}")

    m = _DISLIKE_RE.search(t)
    if m:
        v = _clean(m.group(1) or m.group(2))
        if v:
            add_note(f"n'aime pas {v}")
            learned.append(f"n'aime pas {v}")

    return learned


# --- Lecture pour le prompt ----------------------------------------------
def context(max_events: int = CONTEXT_EVENTS) -> str:
    """Bloc de contexte compact réinjecté dans le cerveau."""
    data = _read()
    parts: list[str] = []

    facts = data.get("facts") or {}
    if facts:
        parts.append("Ce que tu sais de lui : "
                     + " ; ".join(f"{k} = {v['v']}" for k, v in facts.items()))

    notes = data.get("notes") or []
    if notes:
        recent = [n["t"] for n in notes[-6:]]
        parts.append("À retenir : " + " ; ".join(recent))

    events = data.get("events") or []
    if events and max_events > 0:
        lines = []
        for e in events[-max_events:]:
            who = "lui" if e.get("r") == "user" else "toi"
            lines.append(f"{who}: {e.get('t','')}")
        parts.append("Échanges récents :\n" + "\n".join(lines))

    return "\n".join(parts)


def stats() -> dict:
    data = _read()
    return {
        "facts": len(data.get("facts") or {}),
        "notes": len(data.get("notes") or []),
        "events": len(data.get("events") or []),
        "file": str(MEMORY_FILE),
    }
