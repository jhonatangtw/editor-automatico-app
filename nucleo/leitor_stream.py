"""
Leitor do `claude -p --output-format stream-json --verbose`.

Converte cada linha do CLI em PASSOS que a tela da Conversa desenha ao vivo:

  parcial    — o texto da resposta enquanto o Claude escreve (só com
               `--include-partial-messages`); vira `texto` quando o bloco fecha
  texto      — um bloco de texto pronto
  pensando   — o raciocínio, com a duração ("Pensou por 4 s")
  ferramenta — uma chamada: nome, entrada, estado (rodando/ok/erro), duração,
               resumo do resultado e o resultado (truncado)

Ordem dos eventos medida numa saída REAL do CLI 2.1.x (testes/dados/):
o evento `assistant` de um bloco chega ANTES do `content_block_stop` dele, e
cada bloco vem num `assistant` separado com o mesmo id de mensagem. Por isso
o casamento entre o bloco transmitido aos pedaços e o bloco final é por FILA
(o mais antigo ainda não confirmado), e o da ferramenta é pelo `id`.

Sem `--include-partial-messages` não existe `stream_event`: os blocos chegam
inteiros pelo `assistant` e tudo continua funcionando — só sem o texto
aparecendo letra a letra.

Este módulo não sabe nada de processo nem de tela: recebe linha, devolve passo.
É isso que deixa testar com uma gravação de verdade, sem gastar token.
"""

import json
import time

LIMITE_RESULTADO = 4000      # o que a tela abre ao clicar em "ver mais"
LIMITE_CAMPO = 2000          # cada campo da entrada de uma ferramenta
LIMITE_ENTRADA = 6000        # a entrada inteira, serializada


def _curto(t, n):
    t = t if isinstance(t, str) else json.dumps(t, ensure_ascii=False, default=str)
    return t if len(t) <= n else t[:n] + "…"


def resumo_entrada(entrada):
    """A linha curta ao lado do nome — o que o app sempre mostrou (`resumo`).
    Fica para as telas antigas e para o Codex; a tela nova monta o próprio
    rótulo a partir da `entrada`."""
    if not isinstance(entrada, dict) or not entrada:
        return ""
    for chave in ("query", "etapa", "codigo", "prompt", "texto", "video", "descricao",
                  "file_path", "command", "pattern", "path", "skill", "url"):
        if entrada.get(chave):
            v = str(entrada[chave]).replace("\n", " ")
            return v[:88] + ("…" if len(v) > 88 else "")
    return json.dumps(entrada, ensure_ascii=False, default=str)[:88]


def resumo_saida(bruto):
    t = bruto if isinstance(bruto, str) else json.dumps(bruto, ensure_ascii=False, default=str)
    t = " ".join(t.split())
    return t[:110] + ("…" if len(t) > 110 else "")


def entrada_enxuta(entrada):
    """A entrada guardada no passo. Inteira quando é pequena (a lista do
    TodoWrite precisa chegar intacta); campo a campo truncado quando não é —
    um `Write` de 40 KB não pode ir para cada pesquisa da tela."""
    if not isinstance(entrada, dict):
        return {}
    try:
        if len(json.dumps(entrada, ensure_ascii=False, default=str)) <= LIMITE_ENTRADA:
            return entrada
    except Exception:
        pass
    saida = {}
    for k, v in entrada.items():
        saida[k] = v if isinstance(v, (int, float, bool)) or v is None else _curto(v, LIMITE_CAMPO)
    return saida


def texto_do_resultado(conteudo):
    """O `content` de um tool_result: texto puro ou lista de blocos."""
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        partes = []
        for b in conteudo:
            if not isinstance(b, dict):
                partes.append(str(b))
            elif b.get("type") == "text":
                partes.append(b.get("text") or "")
            elif b.get("type") == "image":
                partes.append("[imagem]")
            else:
                partes.append(json.dumps(b, ensure_ascii=False, default=str))
        return "\n".join(partes)
    if conteudo is None:
        return ""
    return json.dumps(conteudo, ensure_ascii=False, default=str)


ESTADOS_TAREFA = {"pending": "pendente", "in_progress": "andamento", "completed": "feito"}


def tarefas_de(entrada):
    """A lista do TodoWrite no formato da tela: texto + estado em português."""
    itens = []
    for t in (entrada or {}).get("todos") or []:
        if not isinstance(t, dict):
            continue
        itens.append({"texto": str(t.get("content") or t.get("activeForm") or ""),
                      "ativo": str(t.get("activeForm") or t.get("content") or ""),
                      "estado": ESTADOS_TAREFA.get(t.get("status"), "pendente")})
    return itens


def _recusa(texto):
    """O portão do pipeline respondeu "não"? (o MCP do app devolve
    `{"recusado": true, "porque": …}` quando a etapa precisa de aprovação)."""
    try:
        d = json.loads(texto)
    except Exception:
        return None
    if isinstance(d, dict) and d.get("recusado"):
        return str(d.get("porque") or "")
    return None


class LeitorClaude:
    """Uma rodada do `claude -p`. Alimente com `linha()`; no fim, `finalizar()`."""

    def __init__(self, ao_vivo=None, relogio=time.time, midias=None):
        self.ao_vivo = ao_vivo
        # `midias(texto) -> [..]`: acha as entregas (imagem, vídeo, áudio) no
        # resultado INTEIRO da ferramenta — o `resultado` guardado é truncado
        # e uma lista de jobs do Higgsfield passa fácil dos 4 mil caracteres.
        # Injetado (nucleo.midia.detectar_permitidas) para o leitor seguir sem
        # saber de disco: os testes passam um detector falso.
        self.midias = midias
        self.agora = relogio
        self.passos = []
        self.erro = None
        self.uso = None
        self.sessao = None
        self.conectado = False
        self._abertos = {}                       # índice do bloco -> (tipo, passo)
        self._fila = {"text": [], "thinking": []}  # transmitidos, ainda sem o bloco final
        self._ferr = {}                          # tool_use_id -> passo
        self._ultimo = self.agora()

    # ------------------------------------------------------------ saída
    def _emitir(self, ev):
        self.passos.append(ev)
        if self.ao_vivo:
            self.ao_vivo(dict(ev))
        return len(self.passos) - 1

    def _atualizar(self, i, **campos):
        self.passos[i].update(campos)
        if self.ao_vivo:
            self.ao_vivo(dict(self.passos[i], indice=i, atualiza=True))

    # ------------------------------------------------------------ entrada
    def linha(self, bruto):
        bruto = (bruto or "").strip()
        if not bruto:
            return None
        try:
            ev = json.loads(bruto)
        except Exception:
            return None
        return self.evento(ev)

    def evento(self, ev):
        tipo = ev.get("type")
        sub = ev.get("parent_tool_use_id")      # dentro de um subagente
        try:
            if tipo == "system" and ev.get("subtype") == "init":
                self.conectado = True
                self.sessao = ev.get("session_id")
                return "init"
            if tipo == "stream_event":
                if not sub:
                    self._stream(ev.get("event") or {})
                return tipo
            if tipo == "assistant":
                self._assistente((ev.get("message") or {}).get("content") or [], sub)
            elif tipo == "user":
                self._resultados((ev.get("message") or {}).get("content") or [])
            elif tipo == "result":
                self._fim(ev)
            return tipo
        finally:
            self._ultimo = self.agora()

    # ------------------------------------------------------------ pedaços
    def _stream(self, e):
        k = e.get("type")
        if k == "message_start":
            self._abertos = {}
        elif k == "content_block_start":
            cb = e.get("content_block") or {}
            bt, idx = cb.get("type"), e.get("index")
            if bt == "text":
                i = self._emitir({"tipo": "parcial", "texto": cb.get("text") or ""})
                self._fila["text"].append(i)
                self._abertos[idx] = ("text", i)
            elif bt == "thinking":
                i = self._emitir({"tipo": "pensando", "estado": "rodando",
                                  "inicio": self.agora(), "texto": ""})
                self._fila["thinking"].append(i)
                self._abertos[idx] = ("thinking", i)
            elif bt == "tool_use":
                i = self._emitir({"tipo": "ferramenta", "id": cb.get("id"),
                                  "nome": cb.get("name"), "resumo": "", "entrada": {},
                                  "estado": "rodando", "inicio": self.agora()})
                self._ferr[cb.get("id")] = i
                self._abertos[idx] = ("tool", i)
        elif k == "content_block_delta":
            ab = self._abertos.get(e.get("index"))
            d = e.get("delta") or {}
            if not ab:
                return
            if ab[0] == "text" and d.get("type") == "text_delta":
                p = self.passos[ab[1]]
                self._atualizar(ab[1], texto=(p.get("texto") or "") + (d.get("text") or ""))
            elif ab[0] == "thinking" and d.get("type") == "thinking_delta" and d.get("thinking"):
                p = self.passos[ab[1]]
                self._atualizar(ab[1], texto=(p.get("texto") or "") + d["thinking"])
        elif k == "content_block_stop":
            ab = self._abertos.pop(e.get("index"), None)
            if not ab:
                return
            p = self.passos[ab[1]]
            if ab[0] == "thinking" and p.get("estado") == "rodando":
                self._atualizar(ab[1], estado="ok",
                                dur=round(self.agora() - (p.get("inicio") or self.agora()), 1))
            elif ab[0] == "text" and p.get("tipo") == "parcial":
                self._atualizar(ab[1], tipo="texto")

    def _assistente(self, blocos, sub):
        for b in blocos:
            k = b.get("type")
            if k == "text":
                if sub:
                    continue        # texto de subagente não é a resposta ao usuário
                t = b.get("text") or ""
                if self._fila["text"]:
                    self._atualizar(self._fila["text"].pop(0), tipo="texto", texto=t)
                elif t.strip():
                    self._emitir({"tipo": "texto", "texto": t})
            elif k == "thinking":
                if sub:
                    continue
                t = b.get("thinking") or ""
                if self._fila["thinking"]:
                    i = self._fila["thinking"].pop(0)
                    if t.strip():
                        self._atualizar(i, texto=t)
                else:
                    # sem os pedaços não há início medido: o intervalo desde o
                    # último evento é a melhor estimativa do tempo pensando
                    self._emitir({"tipo": "pensando", "estado": "ok", "texto": t,
                                  "dur": round(self.agora() - self._ultimo, 1)})
            elif k == "tool_use":
                nome, entrada = b.get("name"), b.get("input") or {}
                campos = {"nome": nome, "entrada": entrada_enxuta(entrada),
                          "resumo": resumo_entrada(entrada)}
                if nome == "TodoWrite":
                    campos["tarefas"] = tarefas_de(entrada)
                if sub:
                    campos["sub"] = True
                i = self._ferr.get(b.get("id"))
                if i is None:
                    ev = {"tipo": "ferramenta", "id": b.get("id"), "estado": "rodando",
                          "inicio": self.agora()}
                    ev.update(campos)
                    self._ferr[b.get("id")] = self._emitir(ev)
                else:
                    self._atualizar(i, **campos)

    def _resultados(self, blocos):
        if not isinstance(blocos, list):
            return
        for b in blocos:
            if not isinstance(b, dict) or b.get("type") != "tool_result":
                continue
            i = self._ferr.get(b.get("tool_use_id"))
            if i is None:
                continue
            p = self.passos[i]
            texto = texto_do_resultado(b.get("content"))
            campos = {"estado": "erro" if b.get("is_error") else "ok",
                      "saida": resumo_saida(texto),
                      "resultado": _curto(texto, LIMITE_RESULTADO),
                      "dur": round(self.agora() - (p.get("inicio") or self.agora()), 1)}
            if self.midias:
                try:
                    achadas = self.midias(texto)
                except Exception:
                    achadas = []
                if achadas:
                    campos["midias"] = achadas
            porque = _recusa(texto)
            if porque is not None:
                campos["recusado"] = True
                campos["porque"] = porque
            self._atualizar(i, **campos)

    def _fim(self, ev):
        if ev.get("is_error"):
            self.erro = str(ev.get("result") or "")
        u = ev.get("usage") or {}
        modelos = list((ev.get("modelUsage") or {}).keys())
        self.uso = {
            "custo_usd": ev.get("total_cost_usd"),
            "tokens_entrada": sum(int(u.get(k) or 0) for k in (
                "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
            "tokens_saida": int(u.get("output_tokens") or 0),
            "duracao_ms": ev.get("duration_ms"),
            "turnos": ev.get("num_turns"),
            "modelo": modelos[0] if modelos else None,
        }

    # ------------------------------------------------------------ fim
    def finalizar(self):
        """Fecha o que ficou aberto: texto transmitido vira texto; ferramenta
        sem resultado (processo encerrado no meio) fica marcada como tal."""
        for i, p in enumerate(self.passos):
            if p.get("tipo") == "parcial":
                p["tipo"] = "texto"
            elif p.get("tipo") == "pensando" and p.get("estado") == "rodando":
                p["estado"] = "ok"
                p["dur"] = round(self.agora() - (p.get("inicio") or self.agora()), 1)
            elif p.get("tipo") == "ferramenta" and p.get("estado") == "rodando":
                p["estado"] = "interrompido"
        self.passos = [p for p in self.passos
                       if not (p.get("tipo") == "texto" and not (p.get("texto") or "").strip())]
        if self.midias:
            for p in self.passos:
                if p.get("tipo") == "texto" and "midias" not in p:
                    try:
                        achadas = self.midias(p.get("texto") or "")
                    except Exception:
                        achadas = []
                    if achadas:
                        p["midias"] = achadas
        return self.passos

    def fala(self):
        return "\n\n".join(p["texto"] for p in self.passos
                           if p.get("tipo") == "texto" and (p.get("texto") or "").strip()).strip()
