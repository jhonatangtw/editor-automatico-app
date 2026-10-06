# Servidor intermediário (proxy) — quando o navegador não pode chamar a API direto

Use só se aparecer erro de CORS / "Failed to fetch", ou se o aluno quiser
publicar a plataforma. A ideia: a página chama `http://localhost:8787/api/...`,
e este servidor repassa para a API do Higgsfield **acrescentando a chave, que ele
lê de uma variável de ambiente**. A chave nunca fica na página nem no código.

Python puro (vem no Mac; no Windows, o Python do python.org), sem instalar nada.
A URL base, o nome do cabeçalho e o prefixo da autenticação vêm **do setup prompt
do Higgsfield** (variáveis `HIGGSFIELD_API_BASE`, `HIGGSFIELD_AUTH_HEADER`,
`HIGGSFIELD_AUTH_PREFIX`) — não invente: o formato está lá.

```python
# proxy.py — NÃO escreva a chave aqui. Ela vem do ambiente:
#   Mac:      export HIGGSFIELD_API_KEY="..." && python3 proxy.py
#   Windows:  set HIGGSFIELD_API_KEY=... && python proxy.py
import os, sys, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.environ.get("HIGGSFIELD_API_BASE", "")          # a URL base que o setup prompt indica
CHAVE = os.environ.get("HIGGSFIELD_API_KEY", "")
if not BASE or not CHAVE:
    sys.exit("Defina HIGGSFIELD_API_BASE e HIGGSFIELD_API_KEY no ambiente antes de rodar.")
ORIGEM = os.environ.get("ORIGEM_PERMITIDA", "null")       # "null" = index.html aberto do disco

# Nome do cabeçalho e prefixo da autenticação: copie do setup prompt do Higgsfield.
CABECALHO = os.environ.get("HIGGSFIELD_AUTH_HEADER", "")   # ex.: o nome que a documentação indicar
PREFIXO = os.environ.get("HIGGSFIELD_AUTH_PREFIX", "")     # ex.: a palavra antes da chave, se houver (com espaço)
if not CABECALHO:
    sys.exit("Defina HIGGSFIELD_AUTH_HEADER (e HIGGSFIELD_AUTH_PREFIX, se a documentação pedir).")

def autenticar(cab):
    cab[CABECALHO] = PREFIXO + CHAVE

class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", ORIGEM)
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def _repassar(self, metodo):
        if not self.path.startswith("/api/"):
            self.send_response(404); self._cors(); self.end_headers(); return
        corpo = self.rfile.read(int(self.headers.get("Content-Length") or 0)) or None
        cab = {"Content-Type": self.headers.get("Content-Type", "application/json")}
        autenticar(cab)
        req = urllib.request.Request(BASE.rstrip("/") + self.path[4:], data=corpo, headers=cab, method=metodo)
        try:
            r = urllib.request.urlopen(req, timeout=120); cod, dados = r.status, r.read()
        except urllib.error.HTTPError as e:
            cod, dados = e.code, e.read()
        self.send_response(cod); self._cors()
        self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(dados)

    def do_GET(self):  self._repassar("GET")
    def do_POST(self): self._repassar("POST")
    def log_message(self, *a): pass   # não imprime cabeçalhos (onde a chave passa)

print("proxy em http://localhost:8787  (Ctrl+C para parar)")
ThreadingHTTPServer(("127.0.0.1", 8787), H).serve_forever()
```

Na página, troque a URL base das chamadas por `http://localhost:8787/api` e
esconda a tela de chave (quem guarda a chave agora é o servidor).

Cuidados:
- Escuta só em `127.0.0.1` — ninguém da rede usa a sua chave.
- `ORIGEM_PERMITIDA`: deixe `null` para `index.html` aberto do disco; se servir a página por `http://localhost:XXXX`, use essa origem. Nunca `*` se for publicar.
- Para publicar de verdade, a chave vai nas variáveis de ambiente do serviço de hospedagem — e a plataforma precisa de login, senão qualquer visitante gasta os seus créditos.
- `.gitignore` com `.env` se algum dia usar arquivo de ambiente; nunca commitar.
