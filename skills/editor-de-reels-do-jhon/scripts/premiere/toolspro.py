# -*- coding: utf-8 -*-
"""Ponte com o Premiere pelo Tools PRO (painel › Conectar IA).

Usa o servidor MCP LOCAL que o próprio painel do aluno abre (127.0.0.1) e o
token que ELE gerou ao conectar — lido na hora do arquivo do painel, nunca
copiado para cá. Se o Claude já tiver a ferramenta `pr_extendscript` do Tools
PRO carregada, prefira chamá-la direto com o mesmo código (montar.py --so-gerar).

Precisa do "Modo avançado (ExtendScript)" ligado no painel (rodapé › Conectar IA).
"""
import json
import os
import sys
import urllib.error
import urllib.request

CONF = os.path.expanduser(os.environ.get("TOOLSPRO_CONF", "~/.editor-black-belt/mcp-ppro.json"))


def _conf():
    if not os.path.exists(CONF):
        sys.exit("x Tools PRO não conectado: no painel do Premiere, abra Conectar IA e conecte (fica salvo em %s)." % CONF)
    c = json.load(open(CONF))
    url = os.environ.get("TOOLSPRO_URL") or c.get("url") or "http://127.0.0.1:7842/mcp"
    tok = os.environ.get("TOOLSPRO_TOKEN") or c.get("token") or ""
    if c.get("avancado") is False:
        print("! O Modo avançado (ExtendScript) parece DESLIGADO no painel — ligue em Conectar IA › Modo avançado.", file=sys.stderr)
    return url, tok


def chamar(ferramenta, args, timeout=118):
    url, tok = _conf()
    corpo = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": ferramenta, "arguments": args}}).encode()
    req = urllib.request.Request(url, corpo, {"Authorization": "Bearer " + tok, "Content-Type": "application/json",
                                              "Accept": "application/json, text/event-stream"})
    try:
        bruto = urllib.request.urlopen(req, timeout=timeout).read().decode()
    except urllib.error.URLError as e:
        sys.exit("x Não consegui falar com o Tools PRO (%s). O Premiere está aberto com o painel carregado?" % e)
    except TimeoutError:
        sys.exit("x O Premiere não respondeu em %d s. Pode haver uma janela (diálogo) aberta travando o script: "
                 "olhe o Premiere, feche o diálogo com Cancelar e LEIA DE VOLTA antes de repetir." % timeout)
    if bruto.startswith("event:") or "\ndata:" in bruto:
        bruto = [L[5:].strip() for L in bruto.splitlines() if L.startswith("data:")][-1]
    d = json.loads(bruto)
    if "error" in d:
        sys.exit("x Tools PRO recusou: %s" % d["error"])
    txt = d["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except ValueError:
        return {"ok": not d["result"].get("isError"), "texto": txt}


def extendscript(codigo, timeout=118):
    """Roda ExtendScript no Premiere. Devolve {"ok", "retorno", "log"}."""
    r = chamar("pr_extendscript", {"codigo": codigo}, timeout)
    if not r.get("ok", False):
        msg = r.get("erro") or r.get("texto") or r
        if "avan" in str(msg).lower():
            sys.exit("x O Modo avançado (ExtendScript) está desligado. Ligue no painel: Conectar IA › Modo avançado.")
        sys.exit("x O script falhou no Premiere: %s\n  log: %s" % (msg, r.get("log")))
    return r.get("retorno"), r.get("log") or []
