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

Double-clique **`run_local.bat`**. Il va, la première fois :
- vérifier Ollama et Python,
- installer les dépendances Python (légères),
- télécharger le modèle `qwen2.5:7b` (~4,7 Go, une seule fois),
- démarrer le serveur.

Puis ouvre **http://127.0.0.1:8000** : c'est ARIA, avec son cerveau local qui
tourne sur ta RTX. Parle-lui, il réfléchit tout seul (aucun appel externe).

## Choisir un autre modèle

Avant de lancer, tu peux définir une variable `OLLAMA_MODEL`. Selon l'envie :

| Modèle (`OLLAMA_MODEL`) | Taille | Pour quoi |
|---|---|---|
| `qwen2.5:3b` | ~2 Go | plus rapide, un peu moins malin |
| `qwen2.5:7b` (défaut) | ~4,7 Go | bon compromis, très bon en français |
| `llama3.1:8b` | ~4,9 Go | alternative solide |

Ta RTX 2060 (6 Go) accélère une partie du modèle ; le reste passe sur le CPU
(tu as 32 Go de RAM, large). Un 7B tourne confortablement.

## Interrupteur

Le serveur choisit son cerveau via `BRAIN_MODE` : `local` (Ollama, défaut du
script), `claude` (API, nécessite `ANTHROPIC_API_KEY`), `scripted` (règles).
Si Ollama n'est pas lancé, ARIA retombe tout seul sur les règles.
