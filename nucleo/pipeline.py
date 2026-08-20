"""
O motor de etapas — o coração do app.

Regra única, e tudo aqui existe para sustentá-la:

    NENHUMA ETAPA AVANÇA OU GASTA CRÉDITO SEM APROVAÇÃO DO USUÁRIO.

Isso não é preferência de fluxo, é dinheiro. Gerar 40 b-rolls com o insert no
ponto errado custa crédito real e o retrabalho é o mais caro da operação. Por
isso o portão não é um aviso na tela que dá pra ignorar: é `pode_iniciar()`,
que o servidor consulta antes de qualquer chamada paga. Se a etapa anterior não
foi aprovada, a chamada nem sai.

Duas travas separadas, de propósito:

  ORDEM      — nenhuma etapa começa antes da anterior estar CONCLUÍDA.
  APROVAÇÃO  — etapa que gasta crédito exige aprovação EXPLÍCITA da anterior,
               registrada com nome e hora. Não basta estar concluída.

A segunda existe porque "concluído" pode ser automático (o app terminou de
processar); "aprovado" nunca é — só o humano gera.
"""

import json
import os
import time

# ---------------------------------------------------------------- estados

PENDENTE   = "pendente"
GERANDO    = "em_geracao"
AGUARDANDO = "aguardando_aprovacao"
APROVADO   = "aprovado"
REJEITADO  = "rejeitado"
CONCLUIDO  = "concluido"

ROTULO = {
    PENDENTE:   "pendente",
    GERANDO:    "em geração",
    AGUARDANDO: "aguardando aprovação",
    APROVADO:   "aprovado",
    REJEITADO:  "rejeitado",
    CONCLUIDO:  "concluído",
}

# ---------------------------------------------------------------- etapas
# `gasta` marca as etapas que consomem crédito de plataforma. São as que o
# portão protege com rigor máximo — nelas, "concluído sem aprovação" não passa.

ETAPAS = [
    {"id": "analise",    "n": 1,  "nome": "Análise inicial",
     "resumo": "Identifica projeto, sequência ativa, arquivos, formato e copy.",
     "gasta": False, "auto": True},

    {"id": "copy",       "n": 2,  "nome": "Verificação da copy",
     "resumo": "Compara a copy com a fala real: divergências, pronúncia, trechos ausentes, repetições.",
     "gasta": False, "auto": True},

    {"id": "marcacao",   "n": 3,  "nome": "Marcação da timeline",
     "resumo": "Marcadores sincronizados com a fala — vermelho b-roll, azul lettering, roxo decisão.",
     "gasta": False, "auto": True},

    {"id": "plano",      "n": 4,  "nome": "Aprovação do planejamento",
     "resumo": "O mapa completo da timeline. A geração visual só começa depois daqui.",
     "gasta": False, "auto": False, "portao_duro": True},

    {"id": "avatar",     "n": 5,  "nome": "Criação dos avatares",
     "resumo": "Opções de personagem, aparência, figurino e identidade visual.",
     "gasta": True,  "auto": False},

    {"id": "imagens",    "n": 6,  "nome": "Imagens de B-roll",
     "resumo": "Só as imagens estáticas de cada insert, com consistência de personagem e cenário.",
     "gasta": True,  "auto": False},

    {"id": "img_ok",     "n": 7,  "nome": "Aprovação das imagens",
     "resumo": "Aprovar, rejeitar ou regerar cada imagem individualmente.",
     "gasta": False, "auto": False, "por_item": True, "portao_duro": True},

    {"id": "animacao",   "n": 8,  "nome": "Animação dos B-rolls",
     "resumo": "As imagens aprovadas viram vídeo, no modelo mais adequado a cada plano.",
     "gasta": True,  "auto": False},

    {"id": "vid_ok",     "n": 9,  "nome": "Aprovação dos vídeos",
     "resumo": "Cada b-roll animado passa por aprovação antes da montagem.",
     "gasta": False, "auto": False, "por_item": True, "portao_duro": True},

    {"id": "acabamento", "n": 10, "nome": "Letterings, voz e legendas",
     "resumo": "Gerados só depois do visual aprovado, preservando a copy validada.",
     "gasta": True,  "auto": False},

    {"id": "montagem",   "n": 11, "nome": "Montagem no Premiere",
     "resumo": "Importa, posiciona via Tools PRO, muda o áudio dos b-rolls, aplica punch-in, organiza trilhas e marcadores.",
     "gasta": False, "auto": False},

    {"id": "qc",         "n": 12, "nome": "Controle de qualidade",
     "resumo": "Confere o final quadro a quadro. A exportação só libera com a aprovação final.",
     "gasta": False, "auto": False, "portao_duro": True},
]

POR_ID = {e["id"]: e for e in ETAPAS}
ORDEM = [e["id"] for e in ETAPAS]


class Bloqueado(RuntimeError):
    """O portão recusou. A mensagem vai inteira para a tela — é ela que ensina
    o usuário por que não avançou, e evita o chamado de suporte."""


# ---------------------------------------------------------------- estado

def novo():
    return {
        "versao": 2,
        "etapa_atual": "analise",
        "etapas": {e["id"]: {"status": PENDENTE, "dados": {}, "atualizado": None}
                   for e in ETAPAS},
        "aprovacoes": [],
    }


def _agora():
    return time.time()


def situacao(est, eid):
    return (est.get("etapas") or {}).get(eid) or {"status": PENDENTE, "dados": {}}


def aprovada(est, eid):
    """Aprovação EXPLÍCITA — não confundir com concluída."""
    return any(a["etapa"] == eid and a["acao"] == "aprovou"
               for a in est.get("aprovacoes", []))


def anterior(eid):
    i = ORDEM.index(eid)
    return ORDEM[i - 1] if i > 0 else None


def pode_iniciar(est, eid):
    """A pergunta que o servidor faz antes de QUALQUER chamada paga.

    Devolve (True, "") ou (False, motivo). O motivo é escrito para o usuário
    ler, não para o log."""
    etapa = POR_ID.get(eid)
    if not etapa:
        return False, "Etapa desconhecida."

    st = situacao(est, eid)["status"]
    if st == CONCLUIDO:
        return False, "Esta etapa já foi concluída."
    if st == GERANDO:
        return False, "Esta etapa já está rodando."

    ant = anterior(eid)
    if ant is None:
        return True, ""

    ant_st = situacao(est, ant)["status"]
    ant_nome = POR_ID[ant]["nome"]

    # TRAVA 1 — ordem
    if ant_st != CONCLUIDO:
        return False, ("A etapa %d (%s) ainda está %s. As etapas rodam em ordem."
                       % (POR_ID[ant]["n"], ant_nome, ROTULO.get(ant_st, ant_st)))

    # TRAVA 2 — aprovação explícita antes de gastar
    if etapa.get("gasta") and not aprovada(est, ant):
        return False, ("“%s” gasta crédito. Aprove a etapa %d (%s) antes — "
                       "essa é a trava que evita gerar b-roll no ponto errado."
                       % (etapa["nome"], POR_ID[ant]["n"], ant_nome))

    # portão duro: mesmo sem gastar, não passa sem aprovação registrada
    if POR_ID[ant].get("portao_duro") and not aprovada(est, ant):
        return False, ("A etapa %d (%s) é um portão: precisa da sua aprovação "
                       "para liberar o que vem depois." % (POR_ID[ant]["n"], ant_nome))

    return True, ""


def exigir(est, eid):
    ok, motivo = pode_iniciar(est, eid)
    if not ok:
        raise Bloqueado(motivo)
    return True


# ---------------------------------------------------------------- transições

def marcar(est, eid, status, dados=None):
    if eid not in POR_ID:
        raise Bloqueado("Etapa desconhecida: " + str(eid))
    e = est["etapas"].setdefault(eid, {"status": PENDENTE, "dados": {}})
    e["status"] = status
    e["atualizado"] = _agora()
    if dados is not None:
        e["dados"] = dados
    if status in (GERANDO, AGUARDANDO):
        est["etapa_atual"] = eid
    return est


def iniciar(est, eid):
    exigir(est, eid)
    return marcar(est, eid, GERANDO)


def entregar(est, eid, dados=None):
    """A etapa terminou de produzir. NUNCA pula para concluído: para em
    'aguardando aprovação', porque quem conclui é o usuário."""
    return marcar(est, eid, AGUARDANDO, dados)


def aprovar(est, eid, quem, nota=""):
    st = situacao(est, eid)["status"]
    if st not in (AGUARDANDO, REJEITADO):
        raise Bloqueado("Só dá para aprovar uma etapa que está aguardando aprovação. "
                        "Esta está %s." % ROTULO.get(st, st))
    est["aprovacoes"].append({"etapa": eid, "acao": "aprovou", "quem": quem,
                              "quando": _agora(), "nota": nota})
    marcar(est, eid, CONCLUIDO)
    prox = proxima(est)
    est["etapa_atual"] = prox or eid
    return est


def rejeitar(est, eid, quem, nota=""):
    est["aprovacoes"].append({"etapa": eid, "acao": "rejeitou", "quem": quem,
                              "quando": _agora(), "nota": nota})
    marcar(est, eid, REJEITADO)
    est["etapa_atual"] = eid
    return est


def reabrir(est, eid, quem, nota=""):
    """Volta uma etapa já concluída e DERRUBA tudo depois dela.

    Sem isso o app mentiria: mudar a marcação com b-roll já gerado deixaria
    imagens aprovadas que não correspondem mais ao plano. Caro e silencioso —
    o pior tipo de erro."""
    i = ORDEM.index(eid)
    derrubadas = []
    for outro in ORDEM[i:]:
        if situacao(est, outro)["status"] != PENDENTE:
            derrubadas.append(outro)
        marcar(est, outro, PENDENTE, dados={} if outro != eid else None)
    est["aprovacoes"] = [a for a in est["aprovacoes"] if a["etapa"] not in ORDEM[i:]]
    est["aprovacoes"].append({"etapa": eid, "acao": "reabriu", "quem": quem,
                              "quando": _agora(), "nota": nota,
                              "derrubou": derrubadas})
    est["etapa_atual"] = eid
    return est


def proxima(est):
    for eid in ORDEM:
        if situacao(est, eid)["status"] != CONCLUIDO:
            return eid
    return None


# ---------------------------------------------------------------- por item

def itens(est, eid):
    return situacao(est, eid)["dados"].get("itens", [])


def julgar_item(est, eid, item_id, acao, quem, nota=""):
    """Aprovar / rejeitar / pedir nova versão de UMA imagem ou vídeo."""
    if acao not in ("aprovou", "rejeitou", "regerar"):
        raise Bloqueado("Ação inválida: " + str(acao))
    dados = situacao(est, eid)["dados"]
    achou = False
    for it in dados.get("itens", []):
        if it.get("id") == item_id:
            it["julgamento"] = acao
            it["nota"] = nota
            it["julgado_em"] = _agora()
            achou = True
    if not achou:
        raise Bloqueado("Item não encontrado: " + str(item_id))
    est["aprovacoes"].append({"etapa": eid, "acao": acao, "item": item_id,
                              "quem": quem, "quando": _agora(), "nota": nota})
    marcar(est, eid, situacao(est, eid)["status"], dados)
    return est


def saldo_itens(est, eid):
    its = itens(est, eid)
    conta = {"total": len(its), "aprovados": 0, "rejeitados": 0,
             "regerar": 0, "pendentes": 0}
    for it in its:
        j = it.get("julgamento")
        if j == "aprovou":
            conta["aprovados"] += 1
        elif j == "rejeitados" or j == "rejeitou":
            conta["rejeitados"] += 1
        elif j == "regerar":
            conta["regerar"] += 1
        else:
            conta["pendentes"] += 1
    return conta


def aprovados(est, eid):
    """Só o que passou segue para a etapa seguinte. É a regra do 'somente os
    materiais aprovados poderão seguir para animação'."""
    return [it for it in itens(est, eid) if it.get("julgamento") == "aprovou"]


# ---------------------------------------------------------------- painel

def painel(est):
    """O que a tela desenha: cada etapa com status, se pode rodar e por quê não."""
    saida = []
    for e in ETAPAS:
        st = situacao(est, e["id"])
        ok, motivo = pode_iniciar(est, e["id"])
        item = {
            "id": e["id"], "n": e["n"], "nome": e["nome"], "resumo": e["resumo"],
            "gasta": e.get("gasta", False),
            "por_item": e.get("por_item", False),
            "portao": e.get("portao_duro", False),
            "status": st["status"],
            "rotulo": ROTULO.get(st["status"], st["status"]),
            "atualizado": st.get("atualizado"),
            "pode": ok, "bloqueio": motivo,
            "aprovada": aprovada(est, e["id"]),
        }
        if e.get("por_item"):
            item["saldo"] = saldo_itens(est, e["id"])
        saida.append(item)
    return {
        "etapas": saida,
        "atual": est.get("etapa_atual"),
        "aprovacoes": list(reversed(est.get("aprovacoes", [])))[:40],
        "concluidas": sum(1 for e in ETAPAS
                          if situacao(est, e["id"])["status"] == CONCLUIDO),
        "total": len(ETAPAS),
    }
