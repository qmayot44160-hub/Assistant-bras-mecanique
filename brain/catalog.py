"""
Catalogue des pièces d'ARIA - la nomenclature (BOM) modulable.

Chaque pièce du bras 3D est reliée à une fiche : rôle, à imprimer ou à
acheter, composants, fils/connecteurs, prix indicatif, photo et fiche
technique (téléversées par l'utilisateur). Tout est éditable depuis l'app.

Persistance : un fichier JSON + un dossier d'uploads dans DATA_DIR. Sur
Railway, monter un Volume (ex. sur /data) pour que les modifs et les
fichiers survivent aux redéploiements. Sans volume, tout repart du
catalogue de référence (SEED) au prochain déploiement.
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


# --- Catalogue de référence : petit bras de bureau ~5-6 DDL ---------------
# Composants réels et courants (servos, ESP32, PCA9685...). Les prix sont
# INDICATIFS, à vérifier chez ton fournisseur. Les liens sont laissés vides,
# à toi de les remplir avec tes vraies sources.
SEED: list[dict] = [
    {
        "id": "base", "mesh": "base", "name": "Socle", "category": "impression",
        "role": "Base stable qui supporte tout le bras et loge le roulement de rotation.",
        "qty": 1,
        "specs": {"matériau": "PLA ou PETG", "remplissage": "40%", "dimensions": "~Ø120 mm"},
        "print": {"couches": "0.2 mm", "supports": "non", "temps": "~4 h"},
        "components": [
            {"name": "Roulement à billes 608ZZ", "qty": 1},
            {"name": "Lest (métal/sable) pour la stabilité", "qty": 1},
        ],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "yaw", "mesh": "yaw", "name": "Plateau tournant (rotation base)", "category": "impression",
        "role": "Fait pivoter tout le bras à gauche/droite (axe yaw).",
        "qty": 1,
        "specs": {"matériau": "PLA/PETG", "remplissage": "40%"},
        "print": {"couches": "0.2 mm", "supports": "oui (léger)", "temps": "~3 h"},
        "components": [
            {"name": "Servo MG996R (couple ~10 kg·cm)", "qty": 1},
            {"name": "Palonnier + vis", "qty": 1},
        ],
        "wires": [{"from": "Servo yaw", "to": "PCA9685 canal 0", "type": "câble servo 3 fils"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "shoulder", "mesh": "shoulder", "name": "Articulation épaule", "category": "impression",
        "role": "Lève et abaisse le bras supérieur. C'est l'axe le plus sollicité.",
        "qty": 1,
        "specs": {"matériau": "PETG conseillé (effort)", "remplissage": "50%"},
        "print": {"couches": "0.2 mm", "supports": "oui", "temps": "~4 h"},
        "components": [
            {"name": "Servo MG996R (ou 2 en tandem pour le couple)", "qty": 1},
            {"name": "Axe + roulement", "qty": 1},
        ],
        "wires": [{"from": "Servo épaule", "to": "PCA9685 canal 1", "type": "câble servo 3 fils"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "upper", "mesh": "upper", "name": "Bras supérieur", "category": "impression",
        "role": "Segment entre l'épaule et le coude.",
        "qty": 1,
        "specs": {"matériau": "PLA/PETG", "remplissage": "30%", "dimensions": "~215 mm"},
        "print": {"couches": "0.2 mm", "supports": "non", "temps": "~3 h"},
        "components": [{"name": "Inserts filetés M3 (optionnel)", "qty": 4}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "elbow", "mesh": "elbow", "name": "Articulation coude", "category": "impression",
        "role": "Plie l'avant-bras.",
        "qty": 1,
        "specs": {"matériau": "PETG", "remplissage": "50%"},
        "print": {"couches": "0.2 mm", "supports": "oui", "temps": "~3 h"},
        "components": [
            {"name": "Servo MG996R", "qty": 1},
            {"name": "Axe + roulement", "qty": 1},
        ],
        "wires": [{"from": "Servo coude", "to": "PCA9685 canal 2", "type": "câble servo 3 fils"}],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "forearm", "mesh": "forearm", "name": "Avant-bras", "category": "impression",
        "role": "Segment entre le coude et le poignet.",
        "qty": 1,
        "specs": {"matériau": "PLA/PETG", "remplissage": "30%", "dimensions": "~190 mm"},
        "print": {"couches": "0.2 mm", "supports": "non", "temps": "~2.5 h"},
        "components": [], "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "wrist", "mesh": "wrist", "name": "Poignet (pan/tilt)", "category": "impression",
        "role": "Oriente la tête : c'est ce qui produit les hochements oui/non.",
        "qty": 1,
        "specs": {"matériau": "PLA/PETG", "remplissage": "30%"},
        "print": {"couches": "0.2 mm", "supports": "oui (léger)", "temps": "~2 h"},
        "components": [{"name": "Micro-servo SG90", "qty": 2}],
        "wires": [
            {"from": "Servo poignet pitch (oui)", "to": "PCA9685 canal 3", "type": "câble servo 3 fils"},
            {"from": "Servo poignet yaw (non)", "to": "PCA9685 canal 4", "type": "câble servo 3 fils"},
        ],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "head", "mesh": "head", "name": "Tête / support caméra", "category": "impression",
        "role": "Boîtier expressif qui porte l'œil (caméra + LED).",
        "qty": 1,
        "specs": {"matériau": "PLA", "remplissage": "20%"},
        "print": {"couches": "0.2 mm", "supports": "oui", "temps": "~2 h"},
        "components": [{"name": "Vis M2 pour la caméra", "qty": 4}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "eye", "mesh": "eye", "name": "Œil (caméra + LED)", "category": "electronique",
        "role": "La caméra (vision) et l'anneau LED qui exprime l'humeur par la couleur.",
        "qty": 1,
        "specs": {"type": "Caméra CSI/USB + anneau LED RGB"},
        "components": [
            {"name": "Module caméra (ESP32-CAM ou USB)", "qty": 1},
            {"name": "Anneau LED WS2812 (NeoPixel)", "qty": 1},
        ],
        "wires": [
            {"from": "LED WS2812 DIN", "to": "ESP32 GPIO (data)", "type": "fil signal + 5V + GND"},
        ],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    # --- Système (non visible sur le modèle 3D) ---------------------------
    {
        "id": "controller", "mesh": None, "name": "Contrôleur ESP32", "category": "electronique",
        "role": "Le cerveau embarqué : Wi-Fi, reçoit les ordres et pilote les servos via le driver.",
        "qty": 1,
        "specs": {"type": "ESP32 DevKit", "logique": "3.3V"},
        "components": [],
        "wires": [
            {"from": "ESP32 SDA/SCL", "to": "PCA9685 (I2C)", "type": "2 fils I2C + 3.3V + GND"},
        ],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "Wi-Fi pour parler au cerveau serveur.",
    },
    {
        "id": "driver", "mesh": None, "name": "Driver servos PCA9685", "category": "electronique",
        "role": "Pilote jusqu'à 16 servos en PWM sur un simple bus I2C.",
        "qty": 1,
        "specs": {"type": "PCA9685 16 canaux", "bus": "I2C"},
        "components": [],
        "wires": [
            {"from": "PCA9685 V+", "to": "Alimentation 5-6V", "type": "câble d'alim (fort courant)"},
        ],
        "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "psu", "mesh": None, "name": "Alimentation 5-6V", "category": "electronique",
        "role": "Fournit le courant des servos (séparé de l'ESP32).",
        "qty": 1,
        "specs": {"tension": "5-6V", "courant": "≥ 5A conseillé"},
        "components": [{"name": "Condensateur 1000µF sur l'alim servos", "qty": 1}],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None,
        "notes": "Masse commune ESP32 / PCA9685 / alim obligatoire.",
    },
    {
        "id": "wiring", "mesh": None, "name": "Câblage", "category": "achat",
        "role": "Les fils qui relient tout.",
        "qty": 1,
        "specs": {},
        "components": [
            {"name": "Rallonges servo (M/F)", "qty": 6},
            {"name": "Fils Dupont M/M, M/F, F/F", "qty": 1},
            {"name": "Gaine / spirale de cablage", "qty": 1},
        ],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "connectors", "mesh": None, "name": "Connecteurs & interrupteur", "category": "achat",
        "role": "Connexions propres et démontables.",
        "qty": 1,
        "specs": {},
        "components": [
            {"name": "Connecteurs JST", "qty": 1},
            {"name": "Bornier à vis", "qty": 1},
            {"name": "Interrupteur + prise DC", "qty": 1},
        ],
        "wires": [], "links": [], "price": "~", "photo": None, "datasheet": None, "notes": "",
    },
    {
        "id": "hardware", "mesh": None, "name": "Visserie & roulements", "category": "achat",
        "role": "Toute la boulonnerie mécanique.",
        "qty": 1,
        "specs": {},
        "components": [
            {"name": "Vis M3 (assortiment) + écrous", "qty": 1},
            {"name": "Roulements 608ZZ", "qty": 2},
            {"name": "Inserts filetés M3 à chaud", "qty": 1},
        ],
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
