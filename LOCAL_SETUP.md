# Faire tourner le cerveau d'ARIA sur ton PC (RTX 2070 8 Go, 32 Go RAM)

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

Ta RTX 2070 a 8 Go de VRAM. Un 7B en Q4 pèse ~4,7 Go : il **tient entièrement
sur la carte**, cache de contexte compris. Aucune couche ne déborde sur le CPU,
les réponses sortent vite. Garde `qwen2.5:7b`, c'est le bon choix ici.

Si un jour tu veux plus malin, tu as la place pour un 13B en Q4 (~8 Go, ça
commencera à déborder un peu) ou un 14B. `qwen2.5:14b` vaut l'essai :

```
set OLLAMA_MODEL=qwen2.5:14b
run_local.bat
```

Le script affiche ta carte au démarrage, donc tu vois toujours sur quoi tu
tournes.

## Interrupteur

Le serveur choisit son cerveau via `BRAIN_MODE` : `local` (Ollama, défaut du
script), `claude` (API, nécessite `ANTHROPIC_API_KEY`), `scripted` (règles).
Si Ollama n'est pas lancé, ARIA retombe tout seul sur les règles.

## Y accéder depuis ton téléphone, et depuis dehors

Par défaut ARIA n'écoute que ce PC (`127.0.0.1`). C'est volontaire : ses
routes lisent sa mémoire, l'effacent, et acceptent des fichiers. Rien de tout
ça ne doit traîner sur un réseau sans serrure.

### La serrure

Définis `ARIA_PASSWORD` et tout passe par une page de connexion : les pages,
l'API, les fichiers 3D et le WebSocket. Le cookie est signé en HMAC-SHA256
avec une clé tirée au hasard, gardée dans `data/.session-key`, et vaut
30 jours. Sans mot de passe défini, rien ne change : l'usage local reste sans
friction.

`run_reseau.bat` te le demande au lancement et **refuse de démarrer si tu le
laisses vide**.

### Chez toi, sur ton wifi

Double-clique **`run_reseau.bat`**. Il affiche l'adresse à taper sur ton
téléphone, du genre `http://192.168.1.24:8000`. Le téléphone doit être sur le
même wifi. Windows demandera peut-être d'autoriser Python sur le réseau privé.

### Depuis dehors : Tailscale (recommandé)

C'est un réseau privé entre tes propres appareils. Rien n'est publié sur
internet, donc rien à se faire trouver par un robot d'exploration.

1. Installe Tailscale sur le PC et sur le téléphone : https://tailscale.com/download
2. Connecte les deux avec le même compte (gratuit pour un usage perso).
3. Lance `run_reseau.bat` sur le PC.
4. Sur le téléphone, ouvre `http://<nom-du-PC>:8000`, le nom que Tailscale
   affiche dans sa liste d'appareils.

Ça marche depuis n'importe où, en 4G comme en wifi. Le PC doit être allumé.

### Depuis dehors : Cloudflare Tunnel (URL publique)

Si tu veux une vraie adresse web, partageable :

```
cloudflared tunnel --url http://localhost:8000
```

Il te rend une URL en `trycloudflare.com`. Pas de redirection de port, pas
d'IP fixe. Mais c'est **public** : n'importe qui avec l'URL tombe sur ta page
de connexion, donc le mot de passe devient ta seule défense. Prends-en un
vrai. L'URL gratuite change à chaque lancement.

### Ce que Railway devient

Railway n'a pas de GPU, donc pas de cerveau local : son ARIA retombe sur ses
réflexes scriptés. Il reste utile comme vitrine, pour montrer l'atelier 3D
sans allumer le PC. Pour l'ARIA complète, c'est ton PC ou rien.

## Lui parler à la voix

Deux boutons dans la barre d'actions.

**Sa voix** fait lire ses réponses à haute voix. Ça passe par les voix
installées sur Windows, donc rien ne sort de ton PC. Si elle parle avec un
accent anglais, c'est qu'aucune voix française n'est installée : Paramètres ->
Heure et langue -> Voix -> ajouter des voix -> Français.

**Micro** ouvre l'écoute le temps d'une phrase, puis envoie automatiquement ce
que tu as dit. Pas d'écoute permanente : il faut cliquer à chaque fois.

Un point d'honnêteté sur le micro : la reconnaissance vocale utilisée est
celle du navigateur, et sur les navigateurs basés sur Chromium (Chrome, Edge,
Opera) **l'audio est envoyé chez l'éditeur** pour être transcrit. C'est le
seul morceau d'ARIA qui n'est pas local. Sa voix, son cerveau et sa mémoire,
eux, ne quittent pas la machine. Le jour où on branche Whisper sur le serveur
Python, ce bout redevient local lui aussi.

## Sa mémoire ne s'efface plus

Les échanges sont écrits dans `data/events.jsonl`, une ligne par phrase, en
ajout seul. Elle ne jette plus rien et ça ne la ralentit pas : le coût
d'écriture ne dépend pas de la taille du journal (0,01 ms, que le fichier
fasse 40 Ko ou 40 Mo). Compte environ 90 octets par échange, soit 9 Mo pour
100 000 phrases.

Les faits et les notes restent dans `memory.json`, qui lui est petit et
réécrit à chaque fois.

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
