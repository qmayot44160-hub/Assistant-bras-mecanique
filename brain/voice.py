"""
La vraie voix d'ARIA, synthétisée chez toi.

La voix du navigateur (`speechSynthesis`) passe par les voix Windows : elles
sont locales, mais elles sonnent comme un GPS de 2009. Piper est un moteur
de synthèse neuronal qui tourne sur le processeur, pèse une soixantaine de Mo
par voix, et parle français correctement.

Tout reste local : le modèle de voix est un fichier ONNX sur ton disque, rien
n'est envoyé nulle part.

Réglages :
  PIPER_VOICE   nom de la voix (défaut fr_FR-siwis-medium)
  PIPER_SPEED   1.0 = normal, >1 plus lent (c'est `length_scale` chez Piper)

Si `piper-tts` n'est pas installé ou si la voix n'est pas téléchargée, ce
module se déclare simplement indisponible : le serveur répond 503 et la page
retombe sur la voix du navigateur. Rien ne casse, on perd juste la qualité.
"""

from __future__ import annotations

import io
import os
import threading
import time
import wave

try:
    from catalog import DATA_DIR
except ImportError:
    from brain.catalog import DATA_DIR

VOICE_NAME = os.environ.get("PIPER_VOICE", "fr_FR-siwis-medium").strip()
try:
    # length_scale chez Piper : >1 ralentit, <1 accélère.
    SPEED = float(os.environ.get("PIPER_SPEED", "1.0"))
except ValueError:
    SPEED = 1.0
VOICE_DIR = DATA_DIR / "voices"
MAX_CHARS = 400          # une réplique d'ARIA est courte ; au-delà c'est suspect

_state = {"ready": False, "loading": False, "error": None, "engine": None}
_lock = threading.Lock()


def status() -> dict:
    return {"ready": _state["ready"], "loading": _state["loading"],
            "error": _state["error"], "voice": VOICE_NAME,
            "dir": str(VOICE_DIR)}


def available() -> bool:
    return _state["ready"]


def _model_files() -> tuple[object, object]:
    return (VOICE_DIR / (VOICE_NAME + ".onnx"),
            VOICE_DIR / (VOICE_NAME + ".onnx.json"))


def _load() -> None:
    """Charge le modèle. Bloquant, lancé dans un thread au démarrage."""
    _state["loading"] = True
    try:
        try:
            from piper import PiperVoice
        except ImportError:
            _state["error"] = ("piper-tts n'est pas installé. Lance "
                               "Installer-la-voix.bat une fois.")
            return

        onnx, conf = _model_files()
        if not onnx.exists():
            _state["error"] = ("voix %s absente de %s. Lance "
                               "Installer-la-voix.bat une fois."
                               % (VOICE_NAME, VOICE_DIR))
            return

        t0 = time.monotonic()
        _state["engine"] = PiperVoice.load(
            str(onnx), str(conf) if conf.exists() else None)
        _state["ready"] = True
        _state["error"] = None
        print("voice: %s chargée en %.1f s" % (VOICE_NAME, time.monotonic() - t0))
    except Exception as e:
        _state["error"] = "chargement de la voix échoué (%s)" % type(e).__name__
        print("voice: ", _state["error"], e)
    finally:
        _state["loading"] = False


def start_loading() -> None:
    threading.Thread(target=_load, daemon=True).start()


def synth(text: str) -> bytes:
    """Renvoie un WAV complet, ou b"" si la voix n'est pas disponible.

    Bloquant : à appeler dans un thread. Le verrou est là parce qu'une session
    ONNX ne se partage pas entre appels simultanés.
    """
    text = (text or "").strip()[:MAX_CHARS]
    if not text or not _state["ready"]:
        return b""
    buf = io.BytesIO()
    try:
        from piper import SynthesisConfig
        cfg = SynthesisConfig(length_scale=SPEED) if SPEED != 1.0 else None
        with _lock:
            with wave.open(buf, "wb") as wav:
                _state["engine"].synthesize_wav(text, wav, syn_config=cfg)
    except Exception as e:
        _state["error"] = "synthèse échouée (%s)" % type(e).__name__
        print("voice:", _state["error"], e)
        return b""
    return buf.getvalue()
