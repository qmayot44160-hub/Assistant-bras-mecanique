"""
Cerveau d'ARIA - couche déliberative + réflexes, en Python.

C'est le pendant serveur de la logique déjà présente dans web/index.html.
Le principe reste le même : des couches indépendantes.

  - reflexes / deliberatif : machine à états, humeur, décisions spontanées
    (ennui, énergie, oisiveté). Déterministe, sans dépendance externe.
  - dialogue : interprétation du langage. Ici en règles scriptées, avec un
    SEAM (interpret_ai) prévu pour brancher un LLM plus tard.

Le cerveau ne connaît pas le "corps" : il émet des ordres abstraits (état,
geste, pensée) que n'importe quel corps sait exécuter - le corps 3D du
navigateur aujourd'hui, le vrai bras demain.
"""

from __future__ import annotations
import random
import time
from dataclasses import dataclass, field

# Vocabulaire partagé avec le corps (voir web/index.html)
STATES = ("idle", "attentive", "curious", "happy", "confused", "sleep")
GESTURES = ("yes", "no", "tilt", "greet", "happy", "confused", "stretch", "startle", "none")


@dataclass
class Brain:
    awake: bool = True
    autonomy: bool = True
    state: str = "idle"
    energy: float = 0.9
    curiosity: float = 0.4
    boredom: float = 0.0
    attention_x: float = 0.0
    attention_y: float = 0.0
    _next_decision: float = 2.5
    _last_interact: float = field(default_factory=time.monotonic)

    # ---- sortie : le cerveau produit des évènements que le corps exécute ----
    def _ev(self, kind: str, **data) -> dict:
        return {"type": kind, **data}

    def snapshot(self) -> dict:
        """État courant, pour un client qui vient de se connecter."""
        return self._ev(
            "state",
            state=self.state,
            awake=self.awake,
            mood={
                "energy": round(self.energy, 3),
                "curiosity": round(self.curiosity, 3),
                "boredom": round(self.boredom, 3),
            },
        )

    def _set_state(self, s: str) -> list[dict]:
        if s == self.state:
            return []
        self.state = s
        return [self.snapshot()]

    # ---- perception : ce que le corps / l'humain envoie au cerveau ----
    def perceive_attention(self, x: float, y: float) -> list[dict]:
        self.attention_x = max(-1.0, min(1.0, x))
        self.attention_y = max(-0.8, min(0.8, y))
        self._last_interact = time.monotonic()
        self.boredom = max(0.0, self.boredom - 0.05)
        out = self._ev("attention", x=self.attention_x, y=self.attention_y)
        evs = [out]
        if self.awake and self.state == "idle":
            evs += self._set_state("attentive")
        return evs

    def perceive_poke(self) -> list[dict]:
        self._last_interact = time.monotonic()
        self.boredom = 0.0
        evs: list[dict] = []
        if not self.awake:
            evs += self.wake(by_user=True)
        else:
            evs += self._set_state("attentive")
            evs.append(self._ev("gesture", name="startle"))
        evs.append(self._ev("log", layer="reflexe", msg="sollicité par contact"))
        return evs

    def say_prefix(self, raw: str) -> list[dict]:
        """Partie commune quand l'humain parle : journal + réveil éventuel."""
        raw = (raw or "").strip()
        if not raw:
            return []
        evs: list[dict] = [self._ev("log", layer="dialogue", msg=f"« {raw} »")]
        if not self.awake:
            evs += self.wake(by_user=True)
        return evs

    def perceive_say(self, raw: str) -> list[dict]:
        raw = (raw or "").strip()
        if not raw:
            return []
        return self.say_prefix(raw) + self.interpret_scripted(raw)

    def apply_decision(self, d: dict) -> list[dict]:
        """Applique une décision de la couche IA (même vocabulaire que le scripté)."""
        if not isinstance(d, dict):
            return []
        self._last_interact = time.monotonic()
        self.boredom = max(0.0, self.boredom - 0.5)
        say = d.get("say") if isinstance(d.get("say"), str) else ""
        if d.get("sleep") is True:
            evs = [self._ev("thought", text=say)] if say else []
            return evs + self.sleep()
        st = d.get("state") if d.get("state") in ("idle", "attentive", "curious", "happy", "confused") else "attentive"
        evs = self._set_state(st)
        g = d.get("gesture")
        has_g = isinstance(g, str) and g in GESTURES and g != "none"
        if has_g:
            evs.append(self._ev("gesture", name=g))
        if say:
            evs.append(self._ev("thought", text=say))
        evs.append(self._ev("log", layer="dialogue", msg="IA -> " + st + ((" + " + g) if has_g else "")))
        return evs

    # ---- couche dialogue : règles (repli quand l'IA est absente) ----
    def interpret_scripted(self, raw: str) -> list[dict]:
        t = raw.lower()
        self._last_interact = time.monotonic()
        self.boredom = max(0.0, self.boredom - 0.5)

        def react(state, gesture, say):
            evs = self._set_state(state)
            if gesture and gesture in GESTURES and gesture != "none":
                evs.append(self._ev("gesture", name=gesture))
            if say:
                evs.append(self._ev("thought", text=say))
            return evs

        if any(w in t for w in ("bonjour", "salut", "coucou", "hey", "hello", "bonsoir")):
            self.energy = min(1.0, self.energy + 0.1)
            return react("happy", "greet", "Bonjour ! Content de te voir.")
        if any(w in t for w in ("bravo", "super", "génial", "genial", "merci", "gentil", "parfait")):
            self.energy = min(1.0, self.energy + 0.12)
            return react("happy", "happy", "Merci ! Ça me fait plaisir.")
        if any(w in t for w in ("danse", "bouge", "remue", "amuse")):
            return react("happy", "happy", "Regarde ça !")
        if any(w in t for w in ("dors", "dodo", "repos", "veille", "pause")):
            return self.sleep()
        if any(w in t for w in ("réveille", "reveille", "debout", "lève", "leve", "wake")):
            return self.wake(by_user=True) + react("attentive", "none", "Je suis réveillé.")
        if "?" in t:
            yes = random.random() < (0.45 + self.energy * 0.25)
            if yes:
                return react("happy", "yes", "Oui.") + [self._ev("log", layer="decision", msg="question -> OUI")]
            return react("confused", "no", "Non.") + [self._ev("log", layer="decision", msg="question -> NON")]
        return react("curious", "tilt", "En réflexes seuls, je ne saisis pas tout.")

    # SEAM : couche IA. À implémenter quand une clé LLM sera fournie
    # (variable d'environnement). Signature identique à interpret_scripted.
    def interpret_ai(self, raw: str) -> list[dict]:  # pragma: no cover
        raise NotImplementedError("couche IA non branchée (repli scripté actif)")

    # ---- actions haut niveau ----
    def sleep(self) -> list[dict]:
        self.awake = False
        return self._set_state("sleep") + [
            self._ev("thought", text="Je me mets en veille..."),
            self._ev("log", layer="etat", msg="passage en veille"),
        ]

    def wake(self, by_user: bool = False) -> list[dict]:
        was = self.awake
        self.awake = True
        self.energy = max(self.energy, 0.5)
        evs = self._set_state("attentive")
        if not was:
            evs += [
                self._ev("gesture", name="startle"),
                self._ev("thought", text="Oh ! Tu es là." if by_user else "Je me réveille."),
                self._ev("log", layer="etat", msg="réveil" + (" (sollicité)" if by_user else "")),
            ]
        return evs

    # ---- boucle : le cerveau vit tout seul ----
    def tick(self, dt: float) -> list[dict]:
        self.energy = max(0.0, self.energy - dt * 0.006)
        if self.awake:
            self.boredom = min(1.0, self.boredom + dt * 0.03)
            self.curiosity = max(0.15, self.curiosity - dt * 0.02)
        self._next_decision -= dt
        if self._next_decision > 0:
            return []
        self._next_decision = 3 + random.random() * 4
        return self.decide()

    def decide(self) -> list[dict]:
        if not self.autonomy or not self.awake:
            return []
        if self.energy < 0.16:
            return [self._ev("log", layer="decision", msg="énergie basse -> veille")] + self.sleep()
        if self.boredom > 0.8:
            self.boredom = 0.2
            return self._set_state("curious") + [
                self._ev("gesture", name="tilt"),
                self._ev("thought", text="Tu es toujours là ?"),
                self._ev("log", layer="decision", msg="ennui élevé -> cherche l'attention"),
            ]
        roll = random.random()
        if roll < 0.4:
            self.attention_x = random.uniform(-0.9, 0.9)
            self.attention_y = random.uniform(-0.6, 0.6)
            return self._set_state("idle") + [
                self._ev("attention", x=self.attention_x, y=self.attention_y),
                self._ev("log", layer="reflexe", msg="balaye l'atelier du regard"),
            ]
        if roll < 0.62:
            return self._set_state("idle") + [
                self._ev("gesture", name="stretch"),
                self._ev("log", layer="reflexe", msg="s'étire"),
            ]
        if roll < 0.78:
            return self._set_state("curious") + [
                self._ev("gesture", name="tilt"),
                self._ev("thought", text="Hmm."),
                self._ev("log", layer="decision", msg="observe quelque chose"),
            ]
        return self._set_state("idle")
