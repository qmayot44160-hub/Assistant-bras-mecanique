"""
Mise à jour d'ARIA sans rien retélécharger à la main.

Appelé par run_local.bat au démarrage. Compare le dernier commit de GitHub
avec celui qu'on a, et ne retire l'archive que si ça a bougé.

Ce qu'il ne touche JAMAIS :
  - data/            la mémoire d'ARIA et son catalogue
  - run_local.bat    le lanceur est en train de s'exécuter : Windows lit le
                     fichier .bat au fur et à mesure, le remplacer en cours
                     de route fait sauter l'exécution n'importe où. On le
                     dépose à côté et on prévient.

Hors ligne, dépôt injoignable, n'importe quel pépin : on ne casse rien, on
laisse l'app démarrer avec ce qu'elle a déjà.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import urllib.request
import zipfile

REPO = "qmayot44160-hub/assistant-bras-mecanique"
BRANCH = "main"
API = "https://api.github.com/repos/%s/commits/%s" % (REPO, BRANCH)
ZIP = "https://codeload.github.com/%s/zip/refs/heads/%s" % (REPO, BRANCH)

ROOT = os.path.dirname(os.path.abspath(__file__))
STAMP = os.path.join(ROOT, ".aria-version")

# Jamais écrasés. `data` porte la mémoire, `run_local.bat` est en cours
# d'exécution pendant qu'on tourne.
KEEP = {"data", ".aria-version"}
DEFERRED = {"run_local.bat"}


def _current() -> str:
    try:
        with open(STAMP, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _latest() -> str:
    req = urllib.request.Request(API, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "aria-selfupdate",
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))["sha"]


def _download() -> zipfile.ZipFile:
    req = urllib.request.Request(ZIP, headers={"User-Agent": "aria-selfupdate"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return zipfile.ZipFile(io.BytesIO(r.read()))


def _apply(zf: zipfile.ZipFile) -> list[str]:
    """Recopie l'archive sur l'installation. Renvoie les fichiers différés."""
    # GitHub emballe tout dans un dossier <repo>-<branche>/ : on l'enlève.
    names = zf.namelist()
    if not names:
        return []
    prefix = names[0].split("/", 1)[0] + "/"

    deferred = []
    for name in names:
        if not name.startswith(prefix) or name.endswith("/"):
            continue
        rel = name[len(prefix):]
        if not rel:
            continue
        top = rel.split("/", 1)[0]
        if top in KEEP:
            continue

        data = zf.read(name)
        if rel in DEFERRED and os.path.exists(os.path.join(ROOT, rel)):
            # Même contenu : rien à signaler.
            dest = os.path.join(ROOT, rel)
            try:
                with open(dest, "rb") as f:
                    if f.read() == data:
                        continue
            except OSError:
                pass
            out = os.path.join(ROOT, rel + ".new")
            with open(out, "wb") as f:
                f.write(data)
            deferred.append(rel)
            continue

        dest = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tmp = dest + ".part"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dest)      # remplacement atomique
    return deferred


def main() -> int:
    if os.environ.get("ARIA_NO_UPDATE"):
        return 0
    try:
        latest = _latest()
    except Exception as e:
        print("      pas de reseau ou depot injoignable (%s), on garde la version locale."
              % type(e).__name__)
        return 0

    if latest == _current():
        print("      deja a jour.")
        return 0

    print("      nouvelle version disponible, telechargement...")
    try:
        zf = _download()
        deferred = _apply(zf)
    except PermissionError:
        # Cas classique : l'app a ete dezippee sur un disque ou un dossier
        # protege en ecriture. Rien ne pourra jamais s'y ecrire, ni la mise a
        # jour, ni la memoire d'ARIA.
        print("      ECRITURE REFUSEE dans %s" % ROOT)
        print("      Ce dossier est protege. Deplace ARIA ailleurs, par")
        print("      exemple dans %s, et relance." % os.path.join(
            os.path.expanduser("~"), "ARIA"))
        return 0
    except Exception as e:
        print("      mise a jour echouee (%s), on garde la version locale."
              % type(e).__name__)
        return 0

    try:
        with open(STAMP, "w", encoding="utf-8") as f:
            f.write(latest)
    except OSError:
        pass

    print("      mise a jour appliquee (%s)." % latest[:7])
    for rel in deferred:
        print("      NOTE: %s a change. Ferme cette fenetre, remplace" % rel)
        print("            %s par %s.new, puis relance." % (rel, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
