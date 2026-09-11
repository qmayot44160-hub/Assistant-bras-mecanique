# Faire tourner le cerveau d'ARIA sur ton PC (RTX 2060, 32 Go)

Objectif : un vrai modèle qui pense **chez toi**, accéléré par ta carte
graphique, sans rien envoyer dans le cloud. On utilise **Ollama** (le plus
simple sous Windows) + notre serveur ARIA.

## 1. Installer Ollama

1. Télécharge et installe Ollama : https://ollama.com/download
2. (Optionnel mais conseillé, vu ton stockage) ranger les modèles sur `F:` :
   Panneau de configuration -> Variables d'environnement -> nouvelle variable
   système `OLLAMA_MODELS` = `F:\ollama-models`. Puis redémarre Ollama.

## 2. Installer Python

https://www.python.org/downloads/ - **coche « Add python.exe to PATH »** pendant
l'installation.

## 3. Récupérer ARIA sur F:

Le plus simple : télécharge le dépôt en ZIP depuis GitHub
(`Assistant-bras-mecanique` -> bouton Code -> Download ZIP), dézippe-le dans
`F:\` (par ex. `F:\Assistant-bras-mecanique`).

## 4. Lancer

Double-clique **`run_local.bat`**. Il enchaîne tout seul :

1. trouve Python (`python` ou le lanceur `py`) et Ollama, et affiche ta carte,
2. **démarre le service Ollama s'il est éteint** et attend qu'il réponde,
3. télécharge le modèle seulement s'il manque (~4,7 Go, une seule fois),
4. installe les dépendances Python, démarre le serveur, et ouvre la page.

La page s'ouvre sur **http://127.0.0.1:8000** : c'est ARIA, avec son cerveau
local sur ta RTX. Aucun appel externe.

**La toute première réponse peut prendre une minute** : le modèle se charge
dans la VRAM. Le script le précharge au démarrage, donc si tu attends que la
fenêtre soit calme avant de parler, c'est déjà chaud.

## Sa mémoire

Tout ce qu'ARIA retient de toi (prénom, goûts, notes, échanges) est écrit dans
le dossier `data/` créé à côté de l'app, dans le fichier `memory.json`. Rien ne
sort de ton PC.

Dis-lui « je m'appelle... », « j'habite à... » ou « retiens que... » et elle le
garde. Le bouton **Mémoire** dans l'app montre ce qu'elle sait et permet
d'oublier une chose précise, ou tout.

Comme c'est un simple fichier, tu peux le sauvegarder, le copier sur une autre
machine, ou le supprimer pour repartir de zéro.

## En local, rien ne part dans le cloud

Le cerveau tourne sur ta RTX via Ollama, la mémoire est sur ton disque. Aucune
clé API, aucun crédit, aucun appel externe. Le seul compromis : ARIA n'existe
que quand ton PC est allumé et que cette fenêtre reste ouverte.

## Choisir un autre modèle

Avant de lancer, tu peux définir une variable `OLLAMA_MODEL`. Selon l'envie :

| Modèle (`OLLAMA_MODEL`) | Taille | Pour quoi |
|---|---|---|
| `qwen2.5:3b` | ~2 Go | plus rapide, un peu moins malin |
| `qwen2.5:7b` (défaut) | ~4,7 Go | bon compromis, très bon en français |
| `llama3.1:8b` | ~4,9 Go | alternative solide |

Ta RTX 2060 a 6 Go de VRAM. Un 7B en Q4 pèse ~4,7 Go : il rentre presque en
entier, le reste passe sur le CPU (tu as 32 Go de RAM, large). Ça marche, mais
si tu trouves ARIA lente à répondre, **passe en `qwen2.5:3b`** : il tient
entièrement sur la carte et répond quasi instantanément. Pour deux phrases de
petit robot, la différence de finesse ne se voit pas.

```
set OLLAMA_MODEL=qwen2.5:3b
run_local.bat
```

## Interrupteur

Le serveur choisit son cerveau via `BRAIN_MODE` : `local` (Ollama, défaut du
script), `claude` (API, nécessite `ANTHROPIC_API_KEY`), `scripted` (règles).
Si Ollama n'est pas lancé, ARIA retombe tout seul sur les règles.

## Quand ARIA répond bêtement

Ça veut presque toujours dire qu'elle est retombée sur ses réflexes scriptés,
pas qu'elle est bête. Deux façons de voir pourquoi :

- **dans l'app** : le journal affiche la raison en clair, par exemple
  `cerveau local indisponible -> modèle qwen2.5:7b absent. Fais ollama pull...`
- **en détail** : ouvre http://127.0.0.1:8000/health, la section `local` donne
  l'hôte, le modèle demandé, la liste de ce qu'Ollama a vraiment, et l'erreur.

| Ce que dit le journal | Quoi faire |
|---|---|
| `Ollama injoignable` | Ollama est éteint. Lance l'app Ollama, ou `ollama serve`. |
| `modèle ... absent` | `ollama pull qwen2.5:7b` (le script le fait pour toi). |
| `Ollama a refusé (HTTP 404)` | Nom de modèle mal orthographié dans `OLLAMA_MODEL`. |
| rien, mais c'est long | Premier message : le modèle se charge en VRAM. Patiente. |

Pas besoin de redémarrer ARIA : si tu lances Ollama après coup, elle le
retrouve toute seule en une dizaine de secondes.
