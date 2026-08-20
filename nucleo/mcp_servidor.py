#!/usr/bin/env python3
"""
Servidor MCP — dá ao Claude as ferramentas DESTE app.

Por que MCP e não o contrato JSON de antes: com `--mcp-config`, o `claude -p`
recebe estas ferramentas ao lado das dele (Bash, Read, Edit, Glob…) e das skills
que o usuário já tem instaladas. O modelo escolhe sozinho o que usar. O contrato
JSON anterior fazia o oposto — amarrava o Claude a seis ações e desligava tudo
que ele sabe fazer.

Fala JSON-RPC por stdin/stdout. Sem dependência: o app precisa empacotar.

⚠️ NADA de segredo passa por aqui. As chaves ficam no cofre do sistema; estas
ferramentas operam sobre o pipeline e o Adobe, nunca sobre credencial.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nucleo import adobe, gerar, pipeline, projetos  # noqa: E402

PROTOCOLO = "2025-06-18"

FERRAMENTAS = [
    {"name": "adobe_estado",
     "description": "Estado do Adobe agora: Premiere/After Effects aberto, projeto "
                    "carregado, sequências, qual está ativa, e se a ponte do Tools PRO "
                    "responde. Chame antes de mexer em qualquer coisa no Adobe.",
     "inputSchema": {"type": "object", "properties": {}}},

    {"name": "timeline_ler",
     "description": "Lê a TIMELINE da sequência ativa do Premiere: trilhas de vídeo e "
                    "áudio, cada clipe com nome e tempo de entrada/saída, trilhas mudas "
                    "e todos os marcadores com nome, comentário e tempo. Use isto quando "
                    "o usuário pedir para analisar, conferir ou mexer na timeline — o "
                    "material já está aberto na frente dele, não peça caminho de arquivo.",
     "inputSchema": {"type": "object", "properties": {}}},

    {"name": "adobe_verificar",
     "description": "Teste real da ponte do Tools PRO: confirma que dá para ler projeto, "
                    "sequência e timeline. Use se alguma ferramenta do Adobe falhar.",
     "inputSchema": {"type": "object", "properties": {}}},

    {"name": "adobe_extendscript",
     "description": "Executa ExtendScript dentro do Premiere pela ponte do Tools PRO. "
                    "Use para ler ou alterar a timeline. Devolve o que o script retornar.",
     "inputSchema": {"type": "object", "properties": {
         "codigo": {"type": "string", "description": "ExtendScript a executar"}},
         "required": ["codigo"]}},

    {"name": "projeto_criar",
     "description": "Cria um projeto de trabalho do Editor Automático a partir do "
                    "caminho do vídeo do body.",
     "inputSchema": {"type": "object", "properties": {
         "video": {"type": "string"}, "nome": {"type": "string"}},
         "required": ["video"]}},

    {"name": "projeto_estado",
     "description": "As 12 etapas do pipeline deste projeto: status de cada uma, o que "
                    "está liberado, o que está travado e por quê, e as aprovações já dadas.",
     "inputSchema": {"type": "object", "properties": {
         "projeto": {"type": "string"}}, "required": ["projeto"]}},

    {"name": "etapa_rodar",
     "description": "Executa uma etapa do pipeline. RECUSA se a anterior não estiver "
                    "aprovada — as travas são do app, não suas. Etapas que gastam crédito "
                    "(avatar, imagens, animacao, acabamento) exigem que o usuário tenha "
                    "autorizado explicitamente antes.",
     "inputSchema": {"type": "object", "properties": {
         "projeto": {"type": "string"}, "etapa": {"type": "string"},
         "motor": {"type": "string"}, "texto": {"type": "string"},
         "descricao": {"type": "string"}}, "required": ["projeto", "etapa"]}},

    {"name": "etapa_aprovar",
     "description": "Registra a aprovação do usuário e libera a próxima etapa. Só chame "
                    "quando ele disser claramente que aprova; copie a frase dele.",
     "inputSchema": {"type": "object", "properties": {
         "projeto": {"type": "string"}, "etapa": {"type": "string"},
         "frase": {"type": "string"}}, "required": ["projeto", "etapa", "frase"]}},

    {"name": "etapa_rejeitar",
     "description": "Marca a etapa como rejeitada com o motivo do usuário.",
     "inputSchema": {"type": "object", "properties": {
         "projeto": {"type": "string"}, "etapa": {"type": "string"},
         "motivo": {"type": "string"}}, "required": ["projeto", "etapa"]}},

    {"name": "item_julgar",
     "description": "Aprova, rejeita ou manda regerar UMA imagem ou vídeo nas etapas de "
                    "aprovação por item (img_ok, vid_ok). Só os aprovados seguem adiante.",
     "inputSchema": {"type": "object", "properties": {
         "projeto": {"type": "string"}, "etapa": {"type": "string"},
         "item": {"type": "string"}, "acao": {"type": "string"},
         "motivo": {"type": "string"}},
         "required": ["projeto", "etapa", "item", "acao"]}},

    {"name": "motores_listar",
     "description": "Catálogo de motores do Higgsfield com preço real de cada um e o "
                    "saldo do usuário. Use quando ele perguntar de custo ou pedir economia.",
     "inputSchema": {"type": "object", "properties": {
         "tipo": {"type": "string", "description": "imagem|video"},
         "quantos": {"type": "integer"}}, "required": ["tipo"]}},

    {"name": "projetos_listar",
     "description": "Projetos de trabalho já criados no Editor Automático.",
     "inputSchema": {"type": "object", "properties": {}}},
]


def _chamar(nome, a):
    quem = "usuário (pelo chat)"

    if nome == "adobe_estado":
        return adobe.estado()
    if nome == "timeline_ler":
        return adobe.timeline()
    if nome == "adobe_verificar":
        return adobe.verificar()
    if nome == "adobe_extendscript":
        return {"retorno": adobe.extendscript(a["codigo"])}
    if nome == "projetos_listar":
        return {"projetos": projetos.listar()}
    if nome == "projeto_criar":
        caminho = os.path.expanduser(a["video"])
        if not os.path.isfile(caminho):
            return {"erro": "arquivo não existe: " + caminho}
        p = projetos.criar(a.get("nome") or os.path.splitext(
            os.path.basename(caminho))[0], caminho)
        return {"projeto": p["id"], "fonte": p["plano"]["fonte"]}

    pid = a.get("projeto")
    if not pid:
        return {"erro": "falta o id do projeto"}
    est = projetos.estado_pipeline(pid)

    if nome == "projeto_estado":
        return pipeline.painel(est)

    if nome == "etapa_rodar":
        from app import rota_etapa_iniciar
        corpo = {k: v for k, v in a.items()
                 if k not in ("projeto", "etapa") and v is not None}
        try:
            r = rota_etapa_iniciar(pid, a["etapa"], corpo)
        except pipeline.Bloqueado as e:
            return {"recusado": True, "porque": str(e)}
        if r.get("longa"):
            return {"rodando": True, "tarefa": r["tarefa"]}
        d = pipeline.situacao(projetos.estado_pipeline(pid), a["etapa"])["dados"]
        return {"pronto": True, "aguardando_aprovacao": True, "dados": d}

    if nome == "etapa_aprovar":
        try:
            pipeline.aprovar(est, a["etapa"], quem, a.get("frase", ""))
        except pipeline.Bloqueado as e:
            return {"recusado": True, "porque": str(e)}
        projetos.gravar_pipeline(pid, est)
        return {"aprovada": a["etapa"], "proxima": pipeline.proxima(est)}

    if nome == "etapa_rejeitar":
        pipeline.rejeitar(est, a["etapa"], quem, a.get("motivo", ""))
        projetos.gravar_pipeline(pid, est)
        return {"rejeitada": a["etapa"]}

    if nome == "item_julgar":
        try:
            pipeline.julgar_item(est, a["etapa"], a["item"], a["acao"], quem,
                                 a.get("motivo", ""))
        except pipeline.Bloqueado as e:
            return {"recusado": True, "porque": str(e)}
        projetos.gravar_pipeline(pid, est)
        return {"saldo": pipeline.saldo_itens(est, a["etapa"])}

    if nome == "motores_listar":
        q = a.get("quantos") or 1
        return {"opcoes": (gerar.opcoes_imagem(q) if a["tipo"] == "imagem"
                           else gerar.opcoes_video({"inicio": 0, "fim": 5}, False, q)),
                "saldo": gerar.saldo()}

    return {"erro": "ferramenta desconhecida: " + nome}


def _responder(id_, resultado=None, erro=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if erro:
        msg["error"] = {"code": -32000, "message": erro}
    else:
        msg["result"] = resultado
    sys.stdout.write(json.dumps(msg, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()


def main():
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            req = json.loads(linha)
        except Exception:
            continue

        m, id_ = req.get("method"), req.get("id")

        if m == "initialize":
            _responder(id_, {"protocolVersion": PROTOCOLO,
                             "capabilities": {"tools": {}},
                             "serverInfo": {"name": "editor-automatico",
                                            "version": "1.0.0"}})
        elif m == "tools/list":
            _responder(id_, {"tools": FERRAMENTAS})
        elif m == "tools/call":
            p = req.get("params") or {}
            try:
                saida = _chamar(p.get("name"), p.get("arguments") or {})
                _responder(id_, {"content": [{"type": "text", "text": json.dumps(
                    saida, ensure_ascii=False, default=str)}]})
            except Exception as e:
                _responder(id_, {"content": [{"type": "text", "text": str(e)}],
                                 "isError": True})
        elif id_ is not None:
            _responder(id_, {})


if __name__ == "__main__":
    main()
