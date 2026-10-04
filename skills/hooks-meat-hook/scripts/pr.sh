#!/bin/bash
# uso: pr.sh arquivo.js  -> roda ExtendScript no Premiere via Tools PRO (7842)
TK="${TOOLSPRO_TOKEN:-$(cd "$HOME" && claude mcp get toolspro-pr 2>&1 | sed -nE 's/.*Bearer ([^ ]+).*/\1/p')}"
python3 - "$1" "$TK" <<'PY'
import json,sys,urllib.request
code=open(sys.argv[1]).read()
body=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"pr_extendscript","arguments":{"codigo":code}}}).encode()
r=urllib.request.Request("http://127.0.0.1:7842/mcp",body,{"Authorization":"Bearer "+sys.argv[2],"Content-Type":"application/json","Accept":"application/json, text/event-stream"})
out=json.loads(urllib.request.urlopen(r,timeout=300).read())
t=out["result"]["content"][0]["text"]
try: print(json.dumps(json.loads(t),ensure_ascii=False,indent=1))
except Exception: print(t)
PY
