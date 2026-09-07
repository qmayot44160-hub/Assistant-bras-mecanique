"""
Catalogue des pièces d'ARIA - la nomenclature (BOM) modulable.

Calé sur le modèle imprimable "Robotic Arm" (TomKnox, base Arduino) : bras
4 axes + préhenseur 2 doigts à engrenages, baie électronique (Arduino +
drivers + ventilateur), capots par axe, pieds. Les références exactes des
moteurs/électronique vivent dans le BOM GitHub du projet ; ici on décrit la
structure et on marque "à confirmer" ce qui n'est pas certain.

Chaque pièce est reliée à une pièce du bras 3D (champ `mesh`). Tout est
éditable depuis l'app (fiche, photo, PDF). Prix INDICATIFS.
"""

from __future__ import annotations
import json
import os
from pathlib import Path


def _resolve_data_dir() -> Path:
    """DATA_DIR si accessible en écriture (Railway volume), sinon ./data local."""
    candidate = Path(os.environ.get("DATA_DIR", "/data"))
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        probe = candidate / ".wtest"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return candidate
    except Exception:
        local = Path(__file__).resolve().parent.parent / "data"
        local.mkdir(parents=True, exist_ok=True)
        return local


DATA_DIR = _resolve_data_dir()
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CATALOG_FILE = DATA_DIR / "catalog.json"


# --- Catalogue de référence : "Robotic Arm" TomKnox (Arduino, 4 axes + pince) ---
# BOM détaillé + firmware : dépôt GitHub du projet (source de vérité).
# Les modèles de moteurs sont une hypothèse raisonnable, à confirmer via le BOM.
SEED: list[dict] = [
    {
        "id": "base", "mesh": "base", "name": "Socle + pieds", "category": "impression",
        "role": "Base du bras et pieds antidérapants. Reçoit l'axe 1 (rotation).",
        "qty": 1,
        "specs": {"fichiers": "feet, bottom-plate", "matière structure": "PETG/ASA/ABS/PC", "pieds": "TPU (flexible)"},
        "print": {"couches": "0.2 mm", "remplissage": "40%", "supports": "selon pièce"},
        "components": [{"name": "Inserts filetés M3 à chaud", "qty": "plusieurs"},
                       {"name": "Vis M3", "qty": "assortiment"}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "STL 0007-0801 (feet), 0007-0501 (bottom-plate). Réf. exactes : BOM GitHub.",
    },
    {
        "id": "yaw", "mesh": "yaw", "name": "Axe 1 - rotation base (module 1)", "category": "impression",
        "role": "Fait pivoter tout le bras (rotation autour de la verticale).",
        "qty": 1,
        "specs": {"fichiers": "0007-0101/0102/0103 (1m1/1m2/1m3)"},
        "print": {"couches": "0.2 mm", "remplissage": "40%"},
        "components": [{"name": "Moteur pas-à-pas NEMA17 (à confirmer)", "qty": 1},
                       {"name": "Roulement", "qty": 1}],
        "wires": [{"from": "Moteur axe 1", "to": "Driver 1 (baie électronique)", "type": "4 fils stepper"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "shoulder", "mesh": "shoulder", "name": "Axe 2 - épaule (module 2)", "category": "impression",
        "role": "Lève / abaisse le bras. Axe le plus sollicité.",
        "qty": 1,
        "specs": {"fichiers": "0007-0201..0205 (2m1, 2m2m, 2m2h, t2m1bd, t2m1bi)"},
        "print": {"couches": "0.2 mm", "remplissage": "50%", "matière": "PETG/ASA conseillé"},
        "components": [{"name": "Moteur pas-à-pas NEMA17 (à confirmer)", "qty": 1},
                       {"name": "Roulement / axe", "qty": 1}],
        "wires": [{"from": "Moteur axe 2", "to": "Driver 2", "type": "4 fils stepper"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "upper", "mesh": "upper", "name": "Bras (liaison épaule-coude)", "category": "impression",
        "role": "Segment structurel entre l'axe 2 et l'axe 3.",
        "qty": 1,
        "specs": {"matière": "PETG/ASA/ABS/PC"},
        "print": {"couches": "0.2 mm", "remplissage": "30-40%"},
        "components": [{"name": "Inserts filetés M3", "qty": "plusieurs"}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "elbow", "mesh": "elbow", "name": "Axe 3 - coude (module 3)", "category": "impression",
        "role": "Plie l'avant-bras.",
        "qty": 1,
        "specs": {"fichiers": "0007-0301..0304 (3m1, 3m2, 3m2c, t3m1c)"},
        "print": {"couches": "0.2 mm", "remplissage": "50%"},
        "components": [{"name": "Moteur pas-à-pas NEMA17 (à confirmer)", "qty": 1}],
        "wires": [{"from": "Moteur axe 3", "to": "Driver 3", "type": "4 fils stepper"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "forearm", "mesh": "forearm", "name": "Avant-bras (module 4)", "category": "impression",
        "role": "Segment entre le coude et le poignet.",
        "qty": 1,
        "specs": {"fichiers": "0007-0401..0404 (4m1, 4m2, 4m2c, t4m1e)"},
        "print": {"couches": "0.2 mm", "remplissage": "30-40%"},
        "components": [], "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "wrist", "mesh": "wrist", "name": "Axe 4 - poignet (module 4)", "category": "impression",
        "role": "Oriente le préhenseur (produit les hochements oui/non).",
        "qty": 1,
        "specs": {"fichiers": "module 4"},
        "print": {"couches": "0.2 mm", "remplissage": "40%"},
        "components": [{"name": "Moteur pas-à-pas / servo (à confirmer)", "qty": 1}],
        "wires": [{"from": "Moteur axe 4", "to": "Driver 4", "type": "à confirmer"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "head", "mesh": "head", "name": "Préhenseur 2 doigts (pince)", "category": "impression",
        "role": "Saisit les objets. Entraîné par un servo via un train d'engrenages.",
        "qty": 1,
        "specs": {"fichiers": "0007-0503/0504 (gripper L/R), 0505 (idol-gear), 0507 (servo-gear), 0506 (pivot-arm), 0502 (cylinder), 0508 (top-plate)"},
        "print": {"couches": "0.2 mm", "remplissage": "40%"},
        "components": [{"name": "Micro-servo (pince, à confirmer)", "qty": 1},
                       {"name": "Vis / axes des engrenages", "qty": "plusieurs"}],
        "wires": [{"from": "Servo pince", "to": "Arduino (PWM)", "type": "câble servo 3 fils"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "Pince à engrenages : servo-gear + idol-gear + pivot-arm.",
    },
    {
        "id": "eye", "mesh": "eye", "name": "Capteur / caméra (option ARIA)", "category": "electronique",
        "role": "Ajout ARIA : petit capteur/LED pour l'expression et la vision. Optionnel (hors modèle d'origine).",
        "qty": 1,
        "specs": {"type": "LED / mini-caméra"},
        "components": [{"name": "LED ou module caméra", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "Non présent sur le modèle TomKnox : extension propre à ARIA.",
    },
    # --- Baie électronique (module 6) + covers -------------------------------
    {
        "id": "controller", "mesh": None, "name": "Arduino (contrôleur)", "category": "electronique",
        "role": "Le cerveau embarqué : lit les ordres et pilote moteurs + servo.",
        "qty": 1,
        "specs": {"type": "Arduino (Uno/Mega, à confirmer BOM)"},
        "components": [], "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "Firmware sur le dépôt GitHub du projet.",
    },
    {
        "id": "drivers", "mesh": None, "name": "Drivers moteurs + support", "category": "electronique",
        "role": "Pilotent les moteurs pas-à-pas. Montés sur le support imprimé.",
        "qty": 1,
        "specs": {"fichiers": "0007-0603 (support-drivers)", "type": "A4988/DRV8825/TMC (à confirmer)"},
        "components": [{"name": "Drivers pas-à-pas", "qty": 4}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "fan", "mesh": None, "name": "Module ventilation", "category": "electronique",
        "role": "Refroidit les drivers moteurs.",
        "qty": 1,
        "specs": {"fichiers": "0007-0602 (fan-module)"},
        "components": [{"name": "Ventilateur (30/40 mm, à confirmer)", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "psu", "mesh": None, "name": "Alimentation", "category": "electronique",
        "role": "Fournit le courant des moteurs et de l'électronique.",
        "qty": 1,
        "specs": {"tension": "12V typique steppers (à confirmer BOM)"},
        "components": [], "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "covers", "mesh": None, "name": "Capots d'axes (cosmétique)", "category": "impression",
        "role": "Habillage des articulations. Impression PLA (cosmétique).",
        "qty": 1,
        "specs": {"fichiers": "0007-0701..0704 (cover-axis 2/3/4/4top)", "matière": "PLA"},
        "print": {"couches": "0.2 mm", "remplissage": "15%"},
        "components": [], "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "hardware", "mesh": None, "name": "Visserie, inserts & roulements", "category": "achat",
        "role": "Toute la boulonnerie et les inserts filetés à chaud.",
        "qty": 1,
        "specs": {},
        "components": [{"name": "Inserts filetés M3 à chaud", "qty": "kit"},
                       {"name": "Vis M3 (assortiment) + écrous", "qty": "kit"},
                       {"name": "Roulements", "qty": "plusieurs"}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "Outils utiles : fer à souder, kit inserts à chaud, clés Allen/Torx.",
    },
]


def load() -> list[dict]:
    if CATALOG_FILE.exists():
        try:
            return json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    save([dict(p) for p in SEED])
    return [dict(p) for p in SEED]


def save(parts: list[dict]) -> None:
    CATALOG_FILE.write_text(json.dumps(parts, ensure_ascii=False, indent=2), encoding="utf-8")


def get(pid: str) -> dict | None:
    return next((p for p in load() if p.get("id") == pid), None)


def upsert(part: dict) -> dict:
    pid = str(part.get("id") or "").strip()
    if not pid:
        raise ValueError("id manquant")
    parts = load()
    for i, p in enumerate(parts):
        if p.get("id") == pid:
            parts[i] = {**p, **part}
            save(parts)
            return parts[i]
    parts.append(part)
    save(parts)
    return part


def delete(pid: str) -> bool:
    parts = load()
    kept = [p for p in parts if p.get("id") != pid]
    if len(kept) == len(parts):
        return False
    save(kept)
    return True


def reset() -> list[dict]:
    save([dict(p) for p in SEED])
    return load()
