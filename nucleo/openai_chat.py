"""
O ChatGPT conduzindo a conversa do app, pela API oficial.

Espelha o laço de ferramentas que já existia para a chave do Claude, com duas
diferenças que importam:

  * **Streaming de verdade.** A resposta vai chegando na tela enquanto é
    escrita, em vez de aparecer inteira no fim.
  * **HTTP puro.** Sem SDK: o app empacota com PyInstaller e cada dependência a
    mais é uma chance a mais de o pacote quebrar na máquina do aluno. A API é
    JSON sobre HTTPS; o SDK não estava resolvendo nenhum problema nosso.

⚠️ O executor de ferramentas é o MESMO do Claude (`conversa._executar`), então o
ChatGPT passa pelos mesmos portões: se tentar gerar b-roll antes da aprovação do
planejamento, recebe o `Bloqueado` e tem que explicar ao usuário. Não existe
caminho por fora do pipeline para nenhum dos dois.
"""

import json
import time
import urllib.error
import urllib.request

from . import ia, rede

def _api():
    """Endereço da API. Configurável porque nem todo mundo fala com a OpenAI
    direto — Azure e proxy de empresa existem — e porque é o que permite testar
    o laço inteiro contra um servidor de mentira, sem gastar token."""
    import os
    return (os.environ.get("OPENAI_BASE_URL") or ia._do_arquivo_env("OPENAI_BASE_URL")
            or "https://api.openai.com/v1").rstrip("/")
VOLTAS = 12          # teto de idas e voltas de ferramenta numa rodada


class SemChave(RuntimeError):
    pass


class FalhaOpenAI(RuntimeError):
    pass


def _cabecalhos(k):
    return {"Authorization": "Bearer " + k, "Content-Type": "application/json",
            "Accept": "text/event-stream", "User-Agent": "EditorAutomatico"}


def _ferramentas():
    """Converte o catálogo do app para o formato de function calling."""
    from . import conversa
    return [{"type": "function",
             "function": {"name": f["name"], "description": f["description"],
                          "parameters": f["input_schema"]}}
            for f in conversa.FERRAMENTAS]


def _explicar(e):
    """Erro de API vira frase acionável. 'HTTP 429' não diz a ninguém o que
    fazer — e mensagem que não ensina vira chamado de suporte."""
    if isinstance(e, urllib.error.HTTPError):
        try:
            d = json.loads(e.read().decode("utf-8", "ignore"))
            msg = ((d.get("error") or {}).get("message") or "").strip()
        except Exception:
            msg = ""
        if e.code == 401:
            return ("A OPENAI_API_KEY foi recusada. Confira se copiou inteira e "
                    "se ela ainda existe no painel da OpenAI.")
        if e.code == 403:
            return "Essa chave não tem permissão para este modelo. " + msg
        if e.code == 404:
            return "modelo_nao_encontrado: " + msg
        if e.code == 429:
            return ("A OpenAI recusou por limite: ou é cota/crédito da conta, ou "
                    "muitas chamadas em pouco tempo. " + msg)
        if e.code in (500, 502, 503, 529):
            return "A OpenAI está fora do ar agora. Tente de novo em alguns minutos."
        return "A OpenAI recusou (HTTP %s). %s" % (e.code, msg)
    if isinstance(e, urllib.error.URLError):
        # "Connection refused" não diz nada a quem não é de rede
        return ("Não consegui alcançar a OpenAI. Confira a internet — e, se você "
                "está numa rede de empresa, se api.openai.com não está bloqueada. "
                "(%s)" % str(getattr(e, "reason", e))[:80])
    return rede.explicar(e)


def _modelos_disponiveis(k):
    req = urllib.request.Request(_api() + "/models", headers=_cabecalhos(k))
    with urllib.request.urlopen(req, timeout=30, context=rede.contexto()) as r:
        d = json.loads(r.read())
    return [m["id"] for m in d.get("data", [])]


def _melhor_modelo(k):
    """Se o modelo pedido não existe nesta conta, escolhe o melhor que existe.

    Sem isto, o app quebraria toda vez que a OpenAI aposentasse um nome — e o
    aluno veria "modelo não encontrado" sem ter o que fazer."""
    try:
        nomes = _modelos_disponiveis(k)
    except Exception:
        return None
    for prefixo in ("gpt-5.1", "gpt-5", "gpt-4.1", "gpt-4o"):
        casa = sorted((n for n in nomes if n.startswith(prefixo)), reverse=True)
        # nomes com data no fim ordenam bem; o "puro" costuma ser o apelido estável
        exato = [n for n in casa if n == prefixo]
        if exato:
            return exato[0]
        if casa:
            return casa[0]
    return nomes[0] if nomes else None


def testar():
    """Prova a chave sem gastar token: listar modelos não cobra."""
    k, origem = ia.chave("chatgpt")
    if not k:
        return {"ok": False, "msg": "Sem a OPENAI_API_KEY."}
    try:
        nomes = _modelos_disponiveis(k)
    except Exception as e:
        m = _explicar(e)
        if m.startswith("modelo_nao_encontrado"):
            m = "A conta respondeu, mas o modelo pedido não existe nela."
        return {"ok": False, "msg": m}
    pedido = ia.modelo_chatgpt()
    tem = pedido in nomes
    return {"ok": True, "origem": origem, "modelos": len(nomes),
            "modelo": pedido if tem else (_melhor_modelo(k) or pedido),
            "msg": ("Conectado." if tem else
                    "Conectado, mas “%s” não existe nesta conta — vou usar “%s”."
                    % (pedido, _melhor_modelo(k) or "?"))}


# ---------------------------------------------------------------- streaming

def _stream(k, corpo, ao_vivo, ao_texto):
    """Uma chamada. Devolve (texto, chamadas_de_ferramenta, motivo_de_parada).

    O corpo do SSE chega em pedaços `data: {...}`; um pedaço pode partir no meio
    de uma linha, então guardamos o resto para a próxima leitura."""
    req = urllib.request.Request(
        _api() + "/chat/completions", method="POST",
        data=json.dumps(corpo).encode("utf-8"), headers=_cabecalhos(k))

    texto, chamadas, motivo = "", {}, None
    with urllib.request.urlopen(req, timeout=300, context=rede.contexto()) as r:
        resto = ""
        while True:
            pedaco = r.read(2048)
            if not pedaco:
                break
            resto += pedaco.decode("utf-8", "ignore")
            while "\n" in resto:
                linha, _, resto = resto.partition("\n")
                linha = linha.strip()
                if not linha.startswith("data:"):
                    continue
                dado = linha[5:].strip()
                if dado == "[DONE]":
                    return texto, chamadas, motivo
                try:
                    ev = json.loads(dado)
                except Exception:
                    continue
                escolha = (ev.get("choices") or [{}])[0]
                delta = escolha.get("delta") or {}
                if escolha.get("finish_reason"):
                    motivo = escolha["finish_reason"]
                if delta.get("content"):
                    texto += delta["content"]
                    ao_texto(texto)
                for tc in delta.get("tool_calls") or []:
                    i = tc.get("index", 0)
                    c = chamadas.setdefault(i, {"id": "", "nome": "", "args": ""})
                    if tc.get("id"):
                        c["id"] = tc["id"]
                    fn = tc.get("function") or {}
                    if fn.get("name"):
                        c["nome"] += fn["name"]
                    if fn.get("arguments"):
                        c["args"] += fn["arguments"]
    return texto, chamadas, motivo


def conversar(cid, pid, msgs, quem, ao_vivo):
    """Uma rodada completa, com quantas idas de ferramenta forem precisas."""
    from . import conversa

    k, _ = ia.chave("chatgpt")
    if not k:
        raise SemChave(
            "Sem a OPENAI_API_KEY. Ponha a chave no ambiente ou no arquivo %s "
            "e escolha o ChatGPT de novo." % ia.ENV)

    modelo = ia.modelo_chatgpt()
    contexto = conversa._contexto_ambiente(pid)

    # HISTÓRICO SEPARADO POR PROVEDOR: o ChatGPT vê a conversa dele, não a do
    # Claude. Misturar as duas faria cada um responder sobre o que o outro fez
    # como se tivesse feito — e as ferramentas já executadas não voltam atrás.
    api = [{"role": "system", "content": conversa.SISTEMA + "\n\n" + contexto}]
    for m in msgs:
        if m.get("role") not in ("user", "assistant"):
            continue
        if m.get("provedor") not in (None, "chatgpt"):
            continue
        api.append({"role": m["role"], "content": m.get("content") or ""})

    passos = []

    def emitir(ev):
        passos.append(ev)
        ao_vivo and ao_vivo(ev)
        return len(passos) - 1

    def atualizar(i, ev):
        passos[i] = ev
        ao_vivo and ao_vivo(dict(ev, indice=i, atualiza=True))

    resposta = ""
    for volta in range(VOLTAS):
        i_parcial = emitir({"tipo": "parcial", "texto": ""})

        def ao_texto(acumulado, _i=i_parcial):
            atualizar(_i, {"tipo": "parcial", "texto": acumulado})

        corpo = {"model": modelo, "stream": True, "messages": api,
                 "tools": _ferramentas(), "tool_choice": "auto"}
        try:
            texto, chamadas, motivo = _stream(k, corpo, ao_vivo, ao_texto)
        except urllib.error.HTTPError as e:
            explicacao = _explicar(e)
            if explicacao.startswith("modelo_nao_encontrado") and volta == 0:
                outro = _melhor_modelo(k)
                if outro and outro != modelo:
                    atualizar(i_parcial, {"tipo": "aviso",
                                          "texto": "“%s” não existe nesta conta; "
                                                   "usando “%s”." % (modelo, outro)})
                    modelo = outro
                    continue
            if explicacao.startswith("modelo_nao_encontrado"):
                explicacao = ("O modelo “%s” não existe nesta conta da OpenAI, e "
                              "não achei outro compatível. Defina OPENAI_MODEL "
                              "com um modelo que a sua conta tenha." % modelo)
            raise FalhaOpenAI(explicacao)
        except Exception as e:
            raise FalhaOpenAI(_explicar(e))

        if texto.strip():
            atualizar(i_parcial, {"tipo": "texto", "texto": texto})
            resposta = (resposta + "\n\n" + texto).strip() if resposta else texto
        else:
            passos.pop(i_parcial) if i_parcial == len(passos) - 1 else None

        if motivo != "tool_calls" and not chamadas:
            break

        api.append({"role": "assistant", "content": texto or None,
                    "tool_calls": [{"id": c["id"], "type": "function",
                                    "function": {"name": c["nome"], "arguments": c["args"] or "{}"}}
                                   for c in chamadas.values()]})

        for c in chamadas.values():
            try:
                entrada = json.loads(c["args"] or "{}")
            except Exception:
                entrada = {}
            i = emitir({"tipo": "ferramenta", "nome": c["nome"],
                        "resumo": conversa._resumo_entrada(c["nome"], entrada),
                        "estado": "rodando"})
            try:
                saida = conversa._executar(pid, c["nome"], entrada, quem)
                erro = bool(isinstance(saida, dict) and saida.get("erro"))
                if isinstance(saida, dict) and saida.get("criado") and not pid:
                    pid = saida["criado"]
            except Exception as e:
                saida, erro = {"erro": str(e)}, True
            atualizar(i, {"tipo": "ferramenta", "nome": c["nome"],
                          "resumo": conversa._resumo_entrada(c["nome"], entrada),
                          "estado": "erro" if erro else "ok",
                          "saida": conversa._resumo_saida(saida)})
            msgs.append({"role": "ferramenta", "nome": c["nome"], "entrada": entrada,
                         "saida": saida, "provedor": "chatgpt", "quando": time.time()})
            api.append({"role": "tool", "tool_call_id": c["id"],
                        "content": json.dumps(saida, ensure_ascii=False,
                                              default=str)[:6000]})
    else:
        resposta += ("\n\n(parei em %d idas de ferramenta nesta rodada — "
                     "me diga como seguir.)" % VOLTAS)

    return resposta.strip(), [p for p in passos if p["tipo"] != "parcial"], pid, modelo
