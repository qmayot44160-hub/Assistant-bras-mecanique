"""
Mémoire d'ARIA.

Deux niveaux, comme chez nous :
  - les FAITS   : ce qui dure (ton prénom, ce que tu aimes). Peu nombreux, stables.
  - les NOTES   : ce que tu lui demandes explicitement de retenir.
  - les ÉVÈNEMENTS : le fil des échanges récents, pour le contexte immédiat.

Deux fichiers, parce que les trois n'ont pas le même rythme :
  - DATA_DIR/memory.json   faits + notes. Petit, réécrit en entier, sans souci.
  - DATA_DIR/events.jsonl  le fil, une ligne JSON par échange, en AJOUT SEUL.

Pourquoi séparer : avant, chaque message relisait et réécrivait tout le
fichier. Mesuré : 1,8 ms à 400 échanges, mais 511 ms à 100 000 et 2,1 s à
400 000. D'où un plafond de 400 qui faisait tout oublier à ARIA. En ajoutant
une ligne au bout, le coût ne dépend plus de la taille : la mémoire peut
grandir sans fin sans jamais ralentir.

Le contexte est réinjecté dans le cerveau à chaque phrase, c'est ce qui fait
qu'ARIA "se souvient".
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

MEMORY_FILE = DATA_DIR / "memory.json"      # faits + notes
EVENTS_FILE = DATA_DIR / "events.jsonl"     # le fil, en ajout seul

MAX_NOTES = 5000      # une note pèse ~80 octets : de la place pour des années
CONTEXT_EVENTS = 8    # nombre d'échanges réinjectés dans le prompt
VIEW_EVENTS = 200     # ce qu'on renvoie au panneau Mémoire (pas tout le fil)

_EMPTY = {"facts": {}, "notes": []}
_count = None         # nombre d'échanges, compté une fois puis incrémenté


def _read() -> dict:
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        for k, v in _EMPTY.items():
            data.setdefault(k, type(v)())
        _migrate(data)
        return data
    except Exception:
        return {"facts": {}, "notes": []}


def _migrate(data: dict) -> None:
    """Ancienne version : les échanges vivaient dans memory.json. On les
    déverse une fois dans le journal, puis on retire la clé."""
    old = data.pop("events", None)
    if not old:
        return
    try:
        with EVENTS_FILE.open("a", encoding="utf-8") as f:
            for e in old:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        _write(data)
    except Exception:
        pass


def _write(data: dict) -> None:
    try:
        MEMORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _tail(n: int) -> list[dict]:
    """Les n dernières lignes du journal, sans relire tout le fichier :
    on remonte depuis la fin par blocs jusqu'à en avoir assez."""
    if n <= 0:
        return []
    try:
        size = EVENTS_FILE.stat().st_size
    except OSError:
        return []
    chunk, buf, pos = 64 * 1024, b"", size
    try:
        with EVENTS_FILE.open("rb") as f:
            while pos > 0 and buf.count(b"\n") <= n:
                step = min(chunk, pos)
                pos -= step
                f.seek(pos)
                buf = f.read(step) + buf
    except OSError:
        return []
    out = []
    for line in buf.decode("utf-8", "replace").splitlines()[-n:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue                      # ligne tronquée (coupure de courant)
    return out


def count_events() -> int:
    """Compté une seule fois au démarrage, puis tenu à jour à chaque ajout."""
    global _count
    if _count is None:
        try:
            with EVENTS_FILE.open("rb") as f:
                _count = sum(1 for line in f if line.strip())
        except OSError:
            _count = 0
    return _count


def load() -> dict:
    data = _read()
    data["events"] = _tail(VIEW_EVENTS)    # l'interface n'affiche pas 100 000 lignes
    return data


def clear() -> dict:
    global _count
    _write({"facts": {}, "notes": []})
    try:
        EVENTS_FILE.unlink()
    except OSError:
        pass
    _count = 0
    return load()


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
    """Une ligne ajoutée au bout du journal. Coût constant quelle que soit la
    taille du fil : c'est ce qui permet de ne plus rien jeter."""
    global _count
    text = (text or "").strip()[:400]
    if not text:
        return
    try:
        with EVENTS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"r": role, "t": text, "ts": time.time()},
                               ensure_ascii=False) + "\n")
        if _count is not None:
            _count += 1
    except Exception:
        pass


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

    events = _tail(max_events) if max_events > 0 else []
    if events:
        lines = []
        for e in events:
            who = "lui" if e.get("r") == "user" else "toi"
            lines.append(f"{who}: {e.get('t','')}")
        parts.append("Échanges récents :\n" + "\n".join(lines))

    return "\n".join(parts)


def stats() -> dict:
    data = _read()
    return {
        "facts": len(data.get("facts") or {}),
        "notes": len(data.get("notes") or []),
        "events": count_events(),
        "file": str(MEMORY_FILE),
        "journal": str(EVENTS_FILE),
    }
