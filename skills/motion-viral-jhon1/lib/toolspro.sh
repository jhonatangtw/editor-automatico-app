#!/usr/bin/env bash
# Fala com o Tools PRO (After Effects) por JSON-RPC, sem depender do MCP ter subido antes da sessão.
#   lib/toolspro.sh tools/list
#   lib/toolspro.sh call ae_titulos_info
#   lib/toolspro.sh call ae_legendas_importar '{"caminho":"/x/legendas.srt","ancora":"BC","margem":560,"tamanho":66,"fonte":"Inter-Bold"}'
# O token vem de `claude mcp get toolspro-ae`, que só responde com cwd em $HOME (escopo local) — por
# isso o cd. Sem token: "token ausente ou invalido" NÃO é token expirado, é cwd errado.
set -euo pipefail
PORTA="${MVJ_TP_PORT:-7843}"; SRV="${MVJ_TP_SERVER:-toolspro-ae}"
TOKEN="$(cd "$HOME" && claude mcp get "$SRV" 2>/dev/null | grep -o 'Bearer [^ ]*' | head -1 | cut -d' ' -f2 | tr -d '\r\n' || true)"
[ -n "$TOKEN" ] || { echo "sem token para $SRV — o servidor está registrado? (claude mcp list)" >&2; exit 3; }
case "${1:-}" in
  tools/list) BODY='{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' ;;
  call) [ -n "${2:-}" ] || { echo "uso: toolspro.sh call <tool> [json-args]" >&2; exit 64; }
        BODY="{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"$2\",\"arguments\":${3:-{\}}}}" ;;
  *) echo "uso: toolspro.sh tools/list | call <tool> [json-args]" >&2; exit 64 ;;
esac
RAW="$(curl -sS -m "${MVJ_TP_TIMEOUT:-120}" -X POST "http://127.0.0.1:$PORTA/mcp" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "$BODY" 2>&1)" || { echo "sem conexão na porta $PORTA — o After Effects e o painel Tools PRO estão abertos?" >&2; echo "$RAW" >&2; exit 2; }
printf '%s\n' "$RAW" | python3 -c '
import sys,json
raw=sys.stdin.read()
for l in raw.splitlines():
    s=(l[5:] if l.startswith("data:") else l).strip()
    if not s.startswith("{"): continue
    try: d=json.loads(s)
    except Exception: continue
    if "error" in d: print("ERRO:", d["error"]); sys.exit(1)
    r=d.get("result",d)
    if "tools" in r:
        for t in r["tools"]: print("-", t["name"], "|", (t.get("description","") or "")[:100].replace("\n"," "))
    else:
        for c in r.get("content",[]): print(c.get("text",""))
    sys.exit(0)
print("resposta inesperada:", raw[:300]); sys.exit(1)'
