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

## 5. En faire une vraie application

Une fois que ça marche, tu n'as plus besoin de la fenêtre noire.

Double-clique **`Creer-raccourci.bat`**, une seule fois. Il pose un raccourci
**ARIA** sur ton Bureau, avec son icône.

Le raccourci démarre ARIA **fenêtre réduite** : elle part directement dans la
barre des tâches, tu ne l'as plus sous les yeux, et la page s'ouvre toute
seule au bout de 30 à 60 secondes.

Pourquoi réduite et pas invisible : un lancement totalement caché qui échoue
ne peut rien te dire. Réduite, elle ne gêne pas, et si un jour ça coince tu
cliques dessus dans la barre des tâches et tu vois l'erreur.

Pour l'arrêter, deux façons : Ctrl+C dans la fenêtre, ou le bouton
**⏻ Éteindre** dans la barre d'actions de la page. Ce bouton n'apparaît que
sur le PC qui héberge ARIA, et le serveur refuse l'extinction demandée depuis
un autre appareil : pas de risque de la couper d'un doigt qui glisse depuis le
téléphone.

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

**Sa voix** fait lire ses réponses à haute voix. Deux moteurs possibles,
tous les deux locaux.

Par défaut elle utilise les voix installées sur Windows. Ça marche sans rien
installer, mais ça sonne comme un GPS de 2009. Si elle parle avec un accent
anglais, c'est qu'aucune voix française n'est présente : Paramètres -> Heure et
langue -> Voix -> ajouter des voix -> Français.

Pour une vraie voix, lance **`Installer-la-voix.bat`** une fois. Il installe
Piper, un moteur de synthèse neuronal, et télécharge une voix française
(~250 Mo de moteur, ~65 Mo de voix). Ensuite ARIA parle avec, et le journal
affiche `voix activée (Piper, synthèse locale)` au lieu de `(navigateur)`.

Piper tourne sur le processeur, pas sur la carte graphique : il n'entre pas en
concurrence avec le cerveau pour la VRAM. Si le moteur ou la voix disparaît,
la page retombe toute seule sur la voix du navigateur en le disant.

Pour changer de voix, avant de relancer l'installateur :

```
set PIPER_VOICE=fr_FR-tom-medium
Installer-la-voix.bat
```

`fr_FR-siwis-medium` (défaut, féminine), `fr_FR-tom-medium` (masculine) et
`fr_FR-upmc-medium` sont les plus propres. `PIPER_SPEED` règle le débit :
au-dessus de 1 elle ralentit, en dessous elle accélère.

**Micro** ouvre l'écoute et **la garde ouverte**. Tu parles, chaque phrase
terminée part toute seule, et tu peux enchaîner sans rien retoucher. Un second
clic ferme le micro.

Le navigateur ferme sa session d'écoute tout seul après un silence : on la
relance à chaque fois. Si elle meurt trois fois de suite en moins d'une
seconde, c'est que le navigateur refuse pour de bon, et là on arrête en le
disant.

Quand ARIA parle à voix haute, ce que le micro capte est sa propre voix : ces
phrases-là sont ignorées, sinon elle se répondrait à elle-même en boucle.

**Le micro ne marche que dans Chrome ou Edge.** Opera, Brave et Vivaldi sont
pourtant des dérivés de Chromium, mais la reconnaissance vocale n'est pas du
code local : c'est un service Google auquel ces navigateurs n'ont pas accès.
L'API existe, elle démarre, et elle échoue aussitôt.

Un point d'honnêteté sur le micro : la reconnaissance vocale utilisée est
celle du navigateur, et sur les navigateurs basés sur Chromium (Chrome, Edge,
Opera) **l'audio est envoyé chez l'éditeur** pour être transcrit. C'est le
seul morceau d'ARIA qui n'est pas local. Sa voix, son cerveau et sa mémoire,
eux, ne quittent pas la machine. Le jour où on branche Whisper sur le serveur
Python, ce bout redevient local lui aussi.

## Elle peut agir, pas seulement parler

Le modèle dispose de quatre outils qu'il décide d'appeler lui-même :

| Tu dis | Elle appelle | Ce qui se passe |
|---|---|---|
| « lève ton bras », « tourne-toi » | `bouger` | l'articulation part à l'angle voulu, puis se relâche au bout de 9 s |
| « montre-moi le coude » | `montrer_piece` | la vue 3D se braque dessus et ouvre sa fiche |
| « il me faut quoi comme moteur ? » | `chercher_piece` | elle lit la vraie nomenclature avant de répondre |
| « qu'est-ce que je t'ai dit sur les courroies ? » | `fouiller_memoire` | elle relit son journal au lieu de deviner |

Le journal des couches affiche une ligne `OUTIL` à chaque fois, tu vois donc
exactement ce qu'elle fait.

Les angles sont bornés aux amplitudes réelles du bras (base -60 à +90, épaule
-110 à +110, coude et poignet -60 à +90). Si le modèle demande plus, on borne
**et on le lui dit**, sinon il annoncerait un mouvement qui n'a pas eu lieu.

Ça demande un modèle qui sait appeler des fonctions. `qwen2.5:7b` le fait. Si
tu en choisis un qui ne le sait pas, ARIA le détecte au premier refus et
repart sans outils : elle parle, mais elle n'agit plus.

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
