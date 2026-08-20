# -*- coding: utf-8 -*-
"""Roda ExtendScript no Premiere/AE pela porta de debug do painel CEP.

Serve para o que o Tools PRO nao expoe: criar sequencia, editar marcador,
ler e alterar escala de clipe.

    python3 cep.py 'app.project.name'
    python3 cep.py script.jsx

Descobrir a porta:  curl http://127.0.0.1:8860/json/list
(paineis CEP costumam abrir em 8860-8864)

CSInterface normalmente NAO esta no escopo global do painel — use __adobe_cep__.
"""
import asyncio, json, sys, urllib.request
import websockets

PORT = 8860

async def _run(jsx, port=PORT, timeout=900):
    alvos = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5))
    url = alvos[0]["webSocketDebuggerUrl"]
    async with websockets.connect(url, max_size=64*1024*1024, open_timeout=20, ping_interval=None) as ws:
        expr = ("new Promise(function(res){try{__adobe_cep__.evalScript(%s,function(r){res(r);});}"
                "catch(e){res('ERR:'+e);}})" % json.dumps(jsx))
        await ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
            "expression": expr, "awaitPromise": True, "returnByValue": True, "userGesture": True}}))
        while True:
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout))
            if m.get("id") == 1:
                if "exceptionDetails" in m:
                    return "CDP_ERR:" + str(m["exceptionDetails"])[:300]
                return m.get("result", {}).get("result", {}).get("value")

def run(jsx, port=PORT, timeout=900):
    return asyncio.run(_run(jsx, port, timeout))

if __name__ == "__main__":
    src = sys.argv[1]
    jsx = open(src, encoding="utf-8").read() if src.endswith(".jsx") else src
    print(run(jsx))
