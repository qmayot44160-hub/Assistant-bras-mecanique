# Assistant bras mécanique - ARIA

Un cerveau pour un bras robotisé qui bouge seul et communique par hochements de
tête, dans l'esprit des bras d'atelier de type "Dummy". On construit d'abord en
**environnement virtuel**, puis on portera le cerveau vers le vrai bras.

## Vision

- Un bras articulé **autonome** : il s'ennuie, observe, réagit, s'exprime par gestes.
- Il **communique** par hochements (oui / non), inclinaisons de tête, etc.
- Un **cerveau en couches** : des réflexes rapides à la base, une intelligence
  (LLM) par-dessus, et plus tard une **mémoire** persistante.
- Cible finale : le même cerveau pilote un vrai bras physique.

## Architecture en couches

| Couche | Rôle | Où |
|--------|------|-----|
| **Corps** | cinématique du bras, gestes (oui, non, penche, salue, s'étire) | `web/` (3D navigateur) |
| **Réflexes** | respiration, suivi du regard, clignement, sursaut, oisiveté | `web/` (local, gratuit) |
| **Délibératif** | machine à états + décisions spontanées (ennui, énergie) | `web/` (local) |
| **IA / Dialogue** | compréhension du langage, décision des gestes | Claude (via l'artifact) |
| **Cerveau serveur** | logique centrale déportée (à venir) | `brain/` - Python, Railway |
| **Mémoire** | souvenirs persistants (à venir) | base côté serveur |

Le principe : chaque couche fonctionne seule. Si l'IA est absente, le corps garde
ses réflexes. C'est ce qui permettra, plus tard, de brancher le vrai bras sous le
même cerveau.

## Contenu actuel

- `web/index.html` - **prototype complet, un seul fichier autonome** : le bras 3D
  (Three.js), les réflexes, la machine à états, et la couche IA branchée sur Claude.
  S'ouvre dans n'importe quel navigateur. Hors ligne, il tourne en "réflexes seuls".
- `brain/` - **squelette du cerveau serveur** (Python, FastAPI + WebSocket) : la
  même logique en couches, déportée hors du navigateur. Émet des ordres abstraits
  (état, geste, pensée) que n'importe quel corps exécute. Prêt à déployer sur Railway.
  - `brain/brain.py` : la logique (réflexes, humeur, décisions, dialogue scripté avec un SEAM LLM)
  - `brain/main.py` : le serveur WebSocket + une page de test live
  - `brain/requirements.txt`, `brain/Procfile`, `brain/railway.json` : déploiement

## Feuille de route

- [x] Corps 3D virtuel qui bouge seul et hoche la tête
- [x] Réflexes scriptés (socle nerveux local)
- [x] Couche IA branchée (compréhension + décision)
- [x] Cerveau Python déporté - squelette (`brain/`, FastAPI + WebSocket), prêt pour Railway
- [x] Corps 3D piloté par le cerveau serveur (WebSocket)
- [x] Fiches pièces cliquables + catalogue éditable (BOM) + upload photo/fiche technique
- [x] Couche IA côté serveur (Claude comprend le langage libre), repli scripté automatique
- [x] Cerveau local : un vrai modèle qui pense chez toi (Ollama + GPU), sans API externe
- [ ] Mémoire persistante (le bras te reconnaît d'une visite à l'autre)
- [ ] Répertoire de gestes enrichi (pointer, suivre une trajectoire, saisir)
- [ ] Passage au vrai bras physique

## Lancer le prototype (corps 3D)

Ouvre `web/index.html` dans un navigateur. Rien à installer.

- Bouge la souris : le bras te suit du regard.
- Glisse pour tourner autour, molette pour zoomer.
- Parle-lui dans le champ du bas ; il répond par gestes.

## Lancer le cerveau (localement)

```bash
cd brain
pip install -r requirements.txt
uvicorn main:app --reload
```

Puis ouvre http://localhost:8000 : une page de test montre le cerveau vivre et
réagir. Le canal temps réel est sur `/ws`, la sonde de santé sur `/health`.

## Le cerveau : local, Claude, ou scripté

La variable d'environnement `BRAIN_MODE` (service Railway -> Variables) choisit
comment ARIA réfléchit :

- **`local`** (défaut) - un **vrai modèle de langage tourne sur le serveur**
  (llama.cpp, GGUF), aucun appel externe. ARIA pense par lui-même. `brain/local_brain.py`
  le charge en tâche de fond au démarrage ; tant qu'il n'est pas prêt, repli scripté.
- **`claude`** - le dialogue passe par l'API Claude (`brain/ai_layer.py`), plus
  malin mais externe et payant. Nécessite `ANTHROPIC_API_KEY` (et `ARIA_MODEL`
  optionnel, défaut `claude-opus-5` ; `claude-haiku-4-5` pour la vitesse).
- **`scripted`** - règles seules, zéro modèle.

### Le cerveau local (il pense tout seul, via Ollama)

Le cerveau local passe par **Ollama** : un modèle open-source tourne sur ta
machine, accéléré par ton GPU. Aucun appel externe. `brain/local_brain.py`
parle à Ollama en HTTP (`OLLAMA_HOST`, défaut `http://127.0.0.1:11434`), avec
le modèle `OLLAMA_MODEL` (défaut `qwen2.5:7b`). Le modèle **génère la
pensée/parole** d'ARIA ; le code traduit en geste (`_gesture_from`).

- **Recommandé sur ton PC** (RTX + 32 Go RAM) : un modèle 7B tourne bien et
  répond vite. Voir **[LOCAL_SETUP.md](LOCAL_SETUP.md)** et le lanceur
  **`run_local.bat`**.
- Sur un serveur sans Ollama (Railway), le cerveau local est simplement
  indisponible -> repli automatique sur les règles scriptées (ou `claude` si
  configuré). Railway reste ainsi la vitrine légère toujours en ligne.
- État en direct : `GET /health` (`mode`, `local.ready`, `local.error`).

## Déployer le cerveau sur Railway

Le repo se déploie **depuis la racine** : aucun réglage de Root Directory à faire.
La config est dans `railway.json` (racine).

1. Railway -> **New Project -> Deploy from GitHub repo** -> `Assistant-bras-mecanique`.
2. Railway lit `railway.json`, installe `requirements.txt` et lance
   `uvicorn brain.main:app`. La sonde `/health` confirme le démarrage.
3. Onglet **Settings -> Networking -> Generate Domain** pour l'URL publique.
4. À chaque `git push`, Railway redéploie tout seul.

## Les pièces (catalogue modulable)

Dans l'app 3D : **clique une pièce du bras** pour ouvrir sa fiche (rôle, à
imprimer ou acheter, composants, fils/connecteurs, photo, fiche technique),
ou le bouton **Pièces** pour le catalogue complet. Tout est **éditable** :
modifier une pièce, téléverser une photo (zoom) et un PDF de fiche technique,
ajouter une nouvelle pièce (upgrade), réinitialiser au catalogue de référence.

### Persistance : serveur ou navigateur (automatique)

L'app choisit selon son contexte :

- **Servie par le cerveau (Railway)** -> stockage **serveur** dans `DATA_DIR`
  (défaut `/data`) : `catalog.json` + fichiers dans `uploads/`, partagé entre
  tes appareils. Monte un **volume Railway sur `/data`** pour que ça survive
  aux redéploiements (sinon éphémère). Le volume s'ajoute par clic droit sur
  le service -> Attach Volume (ou Ctrl/Cmd+K -> « volume »).
- **Artifact claude.ai / fichier local** -> stockage **navigateur** (IndexedDB,
  repli localStorage), par appareil.

Les photos sont compressées avant stockage. API : `GET/POST/PUT/DELETE
/api/parts`, `POST /api/parts/{id}/upload`, `POST /api/reset`, `GET /api/files/{nom}`.

