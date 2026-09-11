"""
Serrure d'ARIA.

Tant que le serveur n'écoute que sur 127.0.0.1, il n'y a rien à protéger :
seul ton PC peut lui parler. Dès qu'il sort sur le réseau (téléphone, tunnel,
accès depuis dehors), c'est autre chose. Les routes ouvertes permettent de
LIRE toute sa mémoire, de l'EFFACER, et de DÉPOSER des fichiers sur la
machine. Aucune ne doit traîner sans mot de passe.

Réglage : ARIA_PASSWORD.
  - vide            -> aucune serrure (usage local, comportement d'origine)
  - défini          -> il faut le mot de passe pour tout, /login compris

Le jeton est un cookie signé en HMAC-SHA256 avec une clé tirée au hasard et
gardée dans DATA_DIR/.session-key, donc rester connecté survit aux
redémarrages. Pas de base de comptes : un seul humain, un seul secret.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time

try:
    from catalog import DATA_DIR
except ImportError:
    from brain.catalog import DATA_DIR

PASSWORD = os.environ.get("ARIA_PASSWORD", "").strip()
COOKIE = "aria_session"
MAX_AGE = 30 * 24 * 3600          # 30 jours
_KEY_FILE = DATA_DIR / ".session-key"

# Chemins joignables sans jeton : sinon on ne pourrait jamais se connecter.
OPEN_PATHS = {"/login", "/api/login"}


def enabled() -> bool:
    return bool(PASSWORD)


def _key() -> bytes:
    """Clé de signature, tirée une fois puis relue. Si le disque refuse, on
    en garde une en mémoire : la serrure marche, mais il faudra se
    reconnecter après un redémarrage."""
    try:
        if _KEY_FILE.exists():
            raw = _KEY_FILE.read_bytes()
            if len(raw) >= 32:
                return raw
        raw = secrets.token_bytes(32)
        _KEY_FILE.write_bytes(raw)
        try:
            os.chmod(_KEY_FILE, 0o600)     # sans effet sous Windows, utile ailleurs
        except OSError:
            pass
        return raw
    except OSError:
        global _FALLBACK_KEY
        if not _FALLBACK_KEY:
            _FALLBACK_KEY = secrets.token_bytes(32)
        return _FALLBACK_KEY


_FALLBACK_KEY = b""


def _sign(payload: str) -> str:
    return hmac.new(_key(), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def make_token() -> str:
    issued = str(int(time.time()))
    return issued + "." + _sign(issued)


def valid_token(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    issued, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign(issued)):
        return False
    try:
        return time.time() - int(issued) < MAX_AGE
    except ValueError:
        return False


def check_password(given: str | None) -> bool:
    """Comparaison à temps constant : une comparaison normale fuit la
    longueur du préfixe correct, caractère par caractère."""
    if not PASSWORD:
        return True
    return hmac.compare_digest((given or "").strip(), PASSWORD)


LOGIN_PAGE = """<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ARIA</title>
<style>
 :root{color-scheme:dark}
 body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b0f14;
   color:#e8eef6;font:15px/1.5 ui-sans-serif,system-ui,Segoe UI,sans-serif}
 form{width:min(90vw,320px);display:grid;gap:14px;padding:28px;
   background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.1);border-radius:14px}
 h1{margin:0;font:600 17px/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em}
 p{margin:0;color:#8b97a8;font-size:13px}
 input{padding:11px 13px;border-radius:9px;border:1px solid rgba(255,255,255,.16);
   background:rgba(0,0,0,.3);color:inherit;font-size:15px}
 button{padding:11px;border-radius:9px;border:1px solid #34d3ee;background:rgba(52,211,238,.16);
   color:#34d3ee;font-size:15px;font-weight:600;cursor:pointer}
 button:hover{background:rgba(52,211,238,.26)}
 .err{color:#ff8f8f;font-size:13px}
</style>
<form method="post" action="/api/login">
  <h1>ARIA</h1>
  <p>Cet atelier est protégé.</p>
  <input type="password" name="password" placeholder="Mot de passe" autofocus
         autocomplete="current-password">
  __ERROR__
  <button type="submit">Entrer</button>
</form>
"""


def login_page(error: bool = False) -> str:
    return LOGIN_PAGE.replace(
        "__ERROR__", '<p class="err">Mot de passe incorrect.</p>' if error else "")
