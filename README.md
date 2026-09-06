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
- [ ] Brancher le corps 3D sur le cerveau serveur (WebSocket)
- [ ] Couche IA côté serveur (SEAM `interpret_ai`, clé LLM en variable d'env)
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

## Déployer le cerveau sur Railway

Le repo se déploie **depuis la racine** : aucun réglage de Root Directory à faire.
La config est dans `railway.json` (racine).

1. Railway -> **New Project -> Deploy from GitHub repo** -> `Assistant-bras-mecanique`.
2. Railway lit `railway.json`, installe `requirements.txt` et lance
   `uvicorn brain.main:app`. La sonde `/health` confirme le démarrage.
3. Onglet **Settings -> Networking -> Generate Domain** pour l'URL publique.
4. À chaque `git push`, Railway redéploie tout seul.

