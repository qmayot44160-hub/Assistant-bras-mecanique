"""
Catalogue des pièces d'ARIA - nomenclature (BOM) modulable.

Calé sur le BOM RÉEL du modèle "Robotic Arm" (TomKnox) : bras à moteurs
pas-à-pas, entraînement par courroies/poulies T5, contrôleur Arduino Mega +
RAMPS 1.4, 6 drivers TB6560, alim 24V 320W, servo pour la pince.

Chaque pièce est reliée à une pièce du bras 3D (`mesh`). Éditable depuis
l'app. Les liens AliExpress/Amazon sont dans le BOM du projet (non recopiés).
"""

from __future__ import annotations
import json
import os
from pathlib import Path


def _resolve_data_dir() -> Path:
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


# --- BOM réel du "Robotic Arm" (TomKnox) ---------------------------------
SEED: list[dict] = [
    {
        "id": "base", "mesh": "base", "name": "Socle + plaque + pieds", "category": "impression",
        "role": "Base du bras montée sur une plaque, avec pieds TPU. Reçoit l'axe 1.",
        "qty": 1,
        "specs": {"plaque": "Bois 550×550×16 mm", "pieds": "TPU (~50 g)", "structure": "ABS/ASA/PETG/PC"},
        "print": {"couches": "0.2 mm", "matière": "PLA noir (support ~500 g) + TPU (pieds)"},
        "components": [{"name": "Plaque de base bois 550×550×16 mm", "qty": 1},
                       {"name": "Pieds imprimés TPU", "qty": "jeu"}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "STL feet + bottom-plate.",
    },
    {
        "id": "yaw", "mesh": "yaw", "name": "Axe 1 - rotation base", "category": "impression",
        "role": "Fait pivoter tout le bras. Entraînement par courroie/poulie.",
        "qty": 1,
        "specs": {"entraînement": "courroie T5"},
        "print": {"matière": "ABS/ASA/PETG/PC"},
        "components": [{"name": "Moteur NEMA23 (3 Nm, Ø8 mm, 3 A)", "qty": 1},
                       {"name": "Poulie T5 14 dents Ø8", "qty": 1},
                       {"name": "Roulement 608ZZ", "qty": "plusieurs"}],
        "wires": [{"from": "NEMA23 axe 1", "to": "Driver TB6560 (baie)", "type": "4 fils stepper"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "shoulder", "mesh": "shoulder", "name": "Axe 2 - épaule", "category": "impression",
        "role": "Lève / abaisse le bras. Axe le plus chargé.",
        "qty": 1,
        "specs": {"entraînement": "courroie T5"},
        "print": {"matière": "ABS/ASA/PETG/PC", "remplissage": "50%"},
        "components": [{"name": "Moteur NEMA23 (3 Nm)", "qty": 1},
                       {"name": "Poulie T5 + courroie", "qty": "-"}],
        "wires": [{"from": "NEMA23 axe 2", "to": "Driver TB6560", "type": "4 fils stepper"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "upper", "mesh": "upper", "name": "Bras (épaule-coude)", "category": "impression",
        "role": "Segment structurel entre l'axe 2 et l'axe 3.",
        "qty": 1,
        "specs": {"matière": "ABS/ASA/PETG/PC"},
        "print": {"couches": "0.2 mm", "remplissage": "30-40%"},
        "components": [{"name": "Tige lisse M8 (coupée à longueur)", "qty": 1},
                       {"name": "Coussinet auto-lubrifiant 8×12×20", "qty": "-"},
                       {"name": "Inserts filetés M3", "qty": "plusieurs"}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "elbow", "mesh": "elbow", "name": "Axe 3 - coude", "category": "impression",
        "role": "Plie l'avant-bras. Moteur réducté pour le couple.",
        "qty": 1,
        "specs": {},
        "print": {"couches": "0.2 mm", "remplissage": "50%"},
        "components": [{"name": "NEMA17 + réducteur planétaire 5:1 (2 Nm, step 0,35°)", "qty": 1}],
        "wires": [{"from": "NEMA17 réducté axe 3", "to": "Driver TB6560", "type": "4 fils stepper"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "forearm", "mesh": "forearm", "name": "Avant-bras (module 4)", "category": "impression",
        "role": "Segment entre le coude et le poignet.",
        "qty": 1,
        "specs": {"matière": "ABS/ASA/PETG/PC"},
        "print": {"couches": "0.2 mm", "remplissage": "30-40%"},
        "components": [{"name": "Tige lisse M8", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "wrist", "mesh": "wrist", "name": "Axe 4 - poignet", "category": "impression",
        "role": "Oriente le préhenseur (produit les hochements). Petits moteurs.",
        "qty": 1,
        "specs": {},
        "print": {"couches": "0.2 mm", "remplissage": "40%"},
        "components": [{"name": "NEMA17 (SM42HT47-1684 / SM42HT33-1334)", "qty": 2},
                       {"name": "NEMA14 (SM35HT36-1004A)", "qty": 1},
                       {"name": "Poulie T5 10 dents Ø5", "qty": 2}],
        "wires": [{"from": "Moteurs poignet", "to": "Drivers TB6560", "type": "4 fils stepper"}],
        "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "Répartition exacte des moteurs par axe : voir le guide d'assemblage.",
    },
    {
        "id": "head", "mesh": "head", "name": "Préhenseur 2 doigts (pince)", "category": "impression",
        "role": "Saisit les objets. Servo entraînant un train d'engrenages.",
        "qty": 1,
        "specs": {"fichiers": "gripper-left/right, servo-gear, idol-gear, pivot-arm"},
        "print": {"couches": "0.2 mm", "remplissage": "40%"},
        "components": [{"name": "Servo 180° 55 g, 13 kg·cm", "qty": 1},
                       {"name": "Engrenages imprimés (servo-gear + idol-gear)", "qty": "jeu"},
                       {"name": "Roulement 623ZZ / 624ZZ", "qty": "quelques"}],
        "wires": [{"from": "Servo pince", "to": "Arduino / RAMPS (broche servo)", "type": "câble servo 3 fils"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "eye", "mesh": "eye", "name": "Capteur / caméra (option ARIA)", "category": "electronique",
        "role": "Extension ARIA : capteur/LED pour l'expression et la vision. Hors modèle d'origine.",
        "qty": 1,
        "specs": {"type": "LED / mini-caméra"},
        "components": [{"name": "LED ou module caméra", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "Non présent sur le modèle TomKnox : ajout propre à ARIA.",
    },
    # --- Baie électronique ---------------------------------------------------
    {
        "id": "controller", "mesh": None, "name": "Arduino Mega + RAMPS 1.4", "category": "electronique",
        "role": "Le contrôleur : l'Arduino Mega porte le shield RAMPS qui distribue vers les drivers.",
        "qty": 1,
        "specs": {"carte": "Arduino Mega 2560", "shield": "RAMPS V1.4"},
        "components": [{"name": "Arduino Mega 2560", "qty": 1}, {"name": "RAMPS V1.4", "qty": 1},
                       {"name": "Câble USB 2.0 A/B 1,8 m", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "Firmware sur le dépôt GitHub du projet.",
    },
    {
        "id": "drivers", "mesh": None, "name": "Drivers pas-à-pas TB6560 + support", "category": "electronique",
        "role": "Pilotent les 6 moteurs pas-à-pas. Montés sur le support imprimé.",
        "qty": 6,
        "specs": {"modèle": "TB6560", "support": "STL support-drivers"},
        "components": [{"name": "Driver TB6560", "qty": 6}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "fan", "mesh": None, "name": "Ventilation", "category": "electronique",
        "role": "Refroidit les drivers et l'électronique.",
        "qty": 2,
        "specs": {},
        "components": [{"name": "Ventilateur axial 24V 80×80×25 mm", "qty": 1},
                       {"name": "Ventilateur axial 24V 50×50×15 mm", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "STL fan-module.",
    },
    {
        "id": "psu", "mesh": None, "name": "Alimentation 24V + convertisseur", "category": "electronique",
        "role": "Fournit le 24V des moteurs, plus un 12V pour l'électronique.",
        "qty": 1,
        "specs": {"alim": "24V 320W", "convertisseur": "24V -> 12V"},
        "components": [{"name": "Alimentation 24V 320W", "qty": 1},
                       {"name": "Convertisseur 24V->12V", "qty": 1},
                       {"name": "Câble secteur IEC 1,5 m", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "transmission", "mesh": None, "name": "Transmission (courroies, poulies, tiges)", "category": "achat",
        "role": "L'entraînement mécanique des axes.",
        "qty": 1,
        "specs": {},
        "components": [{"name": "Courroie crantée T5, 15 mm, 1,8 m (Breco)", "qty": 1},
                       {"name": "Poulie T5 14 dents Ø8", "qty": 3},
                       {"name": "Poulie T5 10 dents Ø5", "qty": 2},
                       {"name": "Tige lisse M8 (134 / 114 / 80 mm)", "qty": 3},
                       {"name": "Accouplement rigide 5->8 mm", "qty": 1},
                       {"name": "Coussinet auto-lubrifiant 5×8×10", "qty": 8},
                       {"name": "Coussinet auto-lubrifiant 8×12×20", "qty": 2},
                       {"name": "Tige filetée M8 L42 mm", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "covers", "mesh": None, "name": "Capots d'axes (cosmétique)", "category": "impression",
        "role": "Habillage des articulations. Impression PLA.",
        "qty": 1,
        "specs": {"fichiers": "cover-axis 2/3/4/4top", "matière": "PLA"},
        "print": {"couches": "0.2 mm", "remplissage": "15%"},
        "components": [], "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "hardware", "mesh": None, "name": "Roulements, inserts & visserie", "category": "achat",
        "role": "Toute la boulonnerie, les roulements et inserts filetés à chaud.",
        "qty": 1,
        "specs": {},
        "components": [{"name": "Roulement 608ZZ (8×22×7)", "qty": 10},
                       {"name": "Roulement 625ZZ (5×16×5)", "qty": 8},
                       {"name": "Roulement 624ZZ (4×13×5)", "qty": 9},
                       {"name": "Roulement 623ZZ (3×10×4)", "qty": 3},
                       {"name": "Insert laiton M3 (×20) et M4 (×3)", "qty": "kit"},
                       {"name": "Vis M3 / M4 / M5 (dont 120× M5×14)", "qty": "assortiment"},
                       {"name": "Écrous, locknuts, rondelles", "qty": "assortiment"}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "Détail complet des vis (M3x8..M3x40, M4x10..M4x60, M5x14/20, M8x65) dans le BOM.",
    },
    {
        "id": "filament", "mesh": None, "name": "Filaments", "category": "achat",
        "role": "Matières d'impression du projet.",
        "qty": 1,
        "specs": {},
        "components": [{"name": "ABS / ASA / PETG / PC (structure)", "qty": "~1 kg"},
                       {"name": "PLA noir (dont ~500 g pour le support)", "qty": "~750 g"},
                       {"name": "TPU blanc (pieds)", "qty": "~50 g"}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
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
