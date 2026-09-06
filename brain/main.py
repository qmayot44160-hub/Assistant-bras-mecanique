"""
Serveur du cerveau d'ARIA.

Expose :
  - GET  /            page de test live (log + champ de dialogue)
  - GET  /health      sonde de santé (pour Railway)
  - WS   /ws          canal temps réel corps <-> cerveau

Le cerveau (voir brain.py) vit dans une boucle de fond et diffuse ses
décisions à tous les clients connectés. N'importe quel corps peut s'y
brancher : la page de test ici, le corps 3D plus tard, le vrai bras un jour.
"""

from __future__ import annotations
import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

try:
    # lancé depuis le dossier brain/  (uvicorn main:app)
    from brain import Brain
except ImportError:
    # lancé depuis la racine du repo  (uvicorn brain.main:app, cf. Railway)
    from brain.brain import Brain

app = FastAPI(title="Cerveau ARIA")
brain = Brain()

TICK_HZ = 8  # fréquence de la boucle de vie du cerveau


class Hub:
    """Garde les connexions ouvertes et diffuse les évènements du cerveau."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def join(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def leave(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, events: list[dict]) -> None:
        if not events:
            return
        payload = [json.dumps(e) for e in events]
        async with self._lock:
            dead: list[WebSocket] = []
            for ws in self._clients:
                try:
                    for msg in payload:
                        await ws.send_text(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._clients.discard(ws)


hub = Hub()


@app.on_event("startup")
async def _start_loop() -> None:
    async def life() -> None:
        dt = 1.0 / TICK_HZ
        while True:
            await asyncio.sleep(dt)
            events = brain.tick(dt)
            if events:
                await hub.broadcast(events)

    asyncio.create_task(life())


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "state": brain.state, "awake": brain.awake}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await hub.join(ws)
    # état initial pour le nouvel arrivant
    await ws.send_text(json.dumps(brain.snapshot()))
    await ws.send_text(json.dumps({"type": "log", "layer": "etat", "msg": "corps connecté"}))
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            events = handle(msg)
            await hub.broadcast(events)
    except WebSocketDisconnect:
        await hub.leave(ws)
    except Exception:
        await hub.leave(ws)


def handle(msg: dict) -> list[dict]:
    """Traduit un message du corps en perception pour le cerveau."""
    kind = msg.get("type")
    if kind == "say":
        return brain.perceive_say(str(msg.get("text", "")))
    if kind == "attention":
        return brain.perceive_attention(float(msg.get("x", 0)), float(msg.get("y", 0)))
    if kind == "poke":
        return brain.perceive_poke()
    if kind == "sleep":
        return brain.sleep()
    if kind == "wake":
        return brain.wake(by_user=True)
    return []


PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cerveau ARIA</title>
<style>
  :root{color-scheme:dark}
  body{margin:0;background:#0a0d13;color:#e6edf3;font:15px/1.5 system-ui,sans-serif;
    display:flex;flex-direction:column;height:100vh}
  header{padding:16px 20px;border-bottom:1px solid rgba(120,150,180,.18);display:flex;
    align-items:center;gap:12px}
  h1{font-size:16px;letter-spacing:.14em;margin:0}
  .dot{width:9px;height:9px;border-radius:50%;background:#34d3ee;box-shadow:0 0 10px #34d3ee}
  #state{margin-left:auto;font:13px ui-monospace,monospace;color:#8aa0b6}
  #log{flex:1;overflow-y:auto;padding:16px 20px;font:13px/1.6 ui-monospace,monospace;
    display:flex;flex-direction:column-reverse;gap:2px}
  .row{display:flex;gap:8px}
  .layer{flex:0 0 auto}
  .reflexe{color:#5a6b7d}.decision{color:#34d3ee}.dialogue{color:#f5a623}.etat{color:#38e08a}
  .thought{color:#e6edf3}
  .msg{color:#8aa0b6}
  form{display:flex;gap:8px;padding:14px 20px;border-top:1px solid rgba(120,150,180,.18)}
  input{flex:1;background:rgba(0,0,0,.3);border:1px solid rgba(120,150,180,.34);border-radius:10px;
    padding:11px 13px;color:#e6edf3;font:15px system-ui;outline:none}
  input:focus{border-color:#34d3ee}
  button{background:#34d3ee;color:#0a0d13;border:0;border-radius:10px;padding:0 18px;font-weight:600;cursor:pointer}
</style></head><body>
<header><span class="dot" id="dot"></span><h1>CERVEAU ARIA</h1><span id="state">connexion...</span></header>
<div id="log"></div>
<form id="f"><input id="i" placeholder="Parle au cerveau... (page de test)" autocomplete="off"><button>Envoyer</button></form>
<script>
const logEl=document.getElementById('log'), stateEl=document.getElementById('state');
function add(layer,msg){const r=document.createElement('div');r.className='row';
  const l=document.createElement('span');l.className='layer '+layer;l.textContent=layer.toUpperCase();
  const m=document.createElement('span');m.className='msg';m.textContent=msg;
  r.append(l,m);logEl.prepend(r);}
const proto=location.protocol==='https:'?'wss':'ws';
let ws;
function connect(){
  ws=new WebSocket(proto+'://'+location.host+'/ws');
  ws.onmessage=e=>{const d=JSON.parse(e.data);
    if(d.type==='state'){stateEl.textContent=d.state+' · '+(d.awake?'éveillé':'veille');}
    else if(d.type==='thought'){add('thought','💭 '+d.text);}
    else if(d.type==='gesture'){add('decision','geste -> '+d.name);}
    else if(d.type==='log'){add(d.layer,d.msg);}
  };
  ws.onclose=()=>{stateEl.textContent='déconnecté';setTimeout(connect,1500);};
}
connect();
document.getElementById('f').onsubmit=ev=>{ev.preventDefault();
  const i=document.getElementById('i');if(!i.value.trim()||ws.readyState!==1)return;
  ws.send(JSON.stringify({type:'say',text:i.value}));i.value='';};
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return PAGE
