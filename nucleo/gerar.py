"""
Geração — o que gasta crédito.

Este é o único módulo do app que consome saldo. Todo caminho até aqui passou
pelo portão do `pipeline.py`; aqui o cuidado é outro: gastar o mínimo e não
perder o que já foi pago.

Disciplinas que vieram de erro real, não de precaução:

  --wait SEMPRE com --wait-timeout 50m --wait-interval 20s. Sob concorrência o
  CLI desiste antes do servidor e o job aparece como falha SEM TER FALHADO — o
  crédito já saiu e o app geraria de novo.

  generate_audio: false no Seedance. B-roll com áudio de IA briga com a voz do
  avatar na montagem, e não dá pra separar depois.

  Âncora de personagem em TODA cena, via --image-references. O nano_banana
  deriva para fotorrealismo e troca o rosto entre planos quando a consistência
  depende só da descrição no prompt.

  `generate cost` NÃO gasta. É por isso que a tela de aprovação mostra preço
  antes: aprovar às cegas é o que faz o aluno queimar saldo.
"""

import json
import os
import re
import subprocess

from . import projetos

ESPERA = ["--wait", "--wait-timeout", "50m", "--wait-interval", "20s"]

# ---------------------------------------------------------------- motores
#
# O usuário ESCOLHE o motor. A automação sugere, não impõe — a diferença entre
# o mais barato e o mais caro é ~3x, e num lote de 10 inserts isso é a conta do
# mês. Custos medidos ao vivo com `generate cost` (que não gasta) em 17/08/2026;
# `custo_vivo()` reconsulta antes de cada aprovação, porque preço muda.

MOTORES_IMAGEM = [
    {"id": "nano_banana_2_lite", "nome": "Nano Banana 2 Lite", "credito": 1,
     "ancora": True,  "nota": "mais barato que segura âncora — bom para lote grande"},
    {"id": "seedream_v4_5",      "nome": "Seedream 4.5",       "credito": 1,
     "ancora": True,  "nota": "alternativa de mesmo preço, estética diferente"},
    {"id": "flux_2",             "nome": "Flux 2",             "credito": 1,
     "ancora": True,  "nota": "bom em cena e ambiente"},
    {"id": "nano_banana_flash",  "nome": "Nano Banana Flash",  "credito": 1.5,
     "ancora": True,  "nota": "mais rápido"},
    {"id": "nano_banana_pro",    "nome": "Nano Banana Pro",    "credito": 2,
     "ancora": True,  "nota": "segura melhor o rosto entre cenas — o padrão da casa",
     "padrao": True},
    {"id": "gpt_image_2",        "nome": "GPT Image 2",        "credito": 7,
     "ancora": True,  "nota": "caro; só quando precisa de texto legível na imagem"},
]

# `duracoes` = lista fechada que o motor aceita; `minimo` = piso quando é livre.
# Medido com `generate cost` em 17/08/2026 — cada um tem uma regra diferente, e
# pedir duração inválida derruba a geração DEPOIS do portão, com crédito em risco.
MOTORES_VIDEO = [
    {"id": "kling3_0_turbo",    "nome": "Kling 3.0 Turbo",  "credito": 7.5,
     "ref": False, "fim": False, "duracoes": [], "minimo": 3,
     "nota": "mais barato para animar uma imagem só", "padrao": True},
    {"id": "kling3_0",          "nome": "Kling 3.0",        "credito": 10,
     "ref": False, "fim": False, "duracoes": [], "minimo": 3,
     "nota": "sem o corte de preço do turbo"},
    {"id": "kling2_6",          "nome": "Kling 2.6",        "credito": 10,
     "ref": False, "fim": False, "duracoes": [5, 10], "minimo": 5,
     "nota": "geração anterior; só 5s ou 10s"},
    {"id": "seedance_2_0_mini", "nome": "Seedance 2.0 Mini", "credito": 12.5,
     "ref": True,  "fim": True,  "duracoes": [], "minimo": 4,
     "nota": "aceita âncora por metade do preço do Seedance cheio; mínimo 4s"},
    {"id": "wan2_6",            "nome": "Wan 2.6",          "credito": 13,
     "ref": False, "fim": False, "duracoes": [5, 10, 15], "minimo": 5,
     "nota": "movimento mais solto; só 5s, 10s ou 15s"},
    {"id": "seedance_2_0",      "nome": "Seedance 2.0",     "credito": 22.5,
     "ref": True,  "fim": True,  "duracoes": [], "minimo": 4,
     "nota": "melhor consistência com âncora — 3x o Kling Turbo; mínimo 4s"},
    {"id": "minimax_hailuo",    "nome": "MiniMax Hailuo",   "credito": None,
     "ref": False, "fim": True,  "duracoes": [6, 10], "minimo": 6, "custo_com_imagem": True,
     "nota": "transição início→fim; só 6s ou 10s. O preço dele só sai junto da "
             "imagem — a API recusa orçar sem ela."},
]

POR_MOTOR = {m["id"]: m for m in MOTORES_IMAGEM + MOTORES_VIDEO}
MODELO_IMAGEM = "nano_banana_pro"   # padrão; sempre sobrescrevível


class Falhou(RuntimeError):
    pass


def _cli(args, timeout=3600):
    try:
        r = subprocess.run(["higgsfield"] + args, capture_output=True,
                           text=True, timeout=timeout)
    except FileNotFoundError:
        raise Falhou("O CLI do Higgsfield não está instalado nesta máquina.")
    except subprocess.TimeoutExpired:
        raise Falhou("A geração passou do tempo. O crédito pode ter saído — confira "
                     "em `higgsfield generate list` antes de gerar de novo.")
    if r.returncode != 0:
        raise Falhou((r.stderr or r.stdout or "").strip()[:400])
    return r.stdout


def _json_cli(args, timeout=3600):
    saida = _cli(args + ["--json"], timeout)
    try:
        return json.loads(saida)
    except Exception:
        # o CLI às vezes imprime linha de progresso antes do JSON
        m = re.search(r"[\[{].*[\]}]", saida, re.S)
        if not m:
            raise Falhou("Resposta ilegível do Higgsfield: " + saida[:200])
        return json.loads(m.group(0))


# ---------------------------------------------------------------- custo

def custo(job_type, **params):
    """Preflight. NÃO gasta — é o número que a tela de aprovação mostra."""
    args = ["generate", "cost", job_type]
    for k, v in params.items():
        if v is not None:
            args += ["--" + k.replace("_", "-"), str(v)]
    try:
        d = _json_cli(args, timeout=90)
        return float(d.get("credits") or 0)
    except Falhou:
        return None


def saldo():
    try:
        d = _json_cli(["account", "status"], timeout=60)
        return float(d.get("credits") or 0)
    except Falhou:
        return None


def orcamento(pid, corpo_motor_img=None, corpo_motor_vid=None):
    """Quanto custa gerar o que falta — antes de gastar nada."""
    p = projetos.ler(pid)
    faltam = [b for b in p["plano"].get("beats", [])
              if b.get("tipo") == "insert" and not b.get("midia")]
    m_img = corpo_motor_img or MODELO_IMAGEM
    m_vid = corpo_motor_vid or "kling3_0_turbo"
    img = custo_vivo(m_img) or 0
    vid = custo_vivo(m_vid, duration=5) or 0
    total = len(faltam) * (img + vid)
    s = saldo()
    return {
        "inserts": len(faltam),
        "motor_imagem": m_img,
        "motor_video": m_vid,
        "custo_imagem": img,
        "custo_video": vid,
        "total": round(total, 1),
        "saldo": s,
        "sobra": round(s - total, 1) if s is not None else None,
        "suficiente": (s is None) or (s >= total),
    }


# ---------------------------------------------------------------- escolha

def ajustar_duracao(motor, dur):
    """A duração que ESTE motor aceita, mais próxima do beat.

    Beat de 3s com Seedance vira 4s, com Wan vira 5s. Sem este ajuste a chamada
    volta erro depois do portão — e o usuário já tinha aprovado o gasto."""
    cfg = POR_MOTOR.get(motor) or {}
    dur = max(1, round(dur or 5))
    if cfg.get("duracoes"):
        return min(cfg["duracoes"], key=lambda x: abs(x - dur))
    return max(cfg.get("minimo", 3), min(10, dur))


def sugerir_video(beat, tem_ancora):
    """A SUGESTÃO — o mais barato que atende o que ESTE plano exige.

    Seedance custa 3x o Kling Turbo. Só vale quando a cena precisa de âncora de
    personagem junto da imagem inicial; caso contrário é dinheiro no lixo."""
    bruto = (beat.get("fim", 0) - beat.get("inicio", 0)) or 5
    if beat.get("imagem_fim"):
        return "minimax_hailuo", ajustar_duracao("minimax_hailuo", bruto)
    if tem_ancora:
        m = "seedance_2_0_mini"     # metade do Seedance cheio e aceita âncora
    else:
        m = "kling3_0_turbo"
    return m, ajustar_duracao(m, bruto)


def opcoes_video(beat, tem_ancora, quantos=1):
    """Todos os motores viáveis para este beat, com custo — a lista que a tela
    mostra para o usuário trocar. Marca a sugestão, mas não decide por ele."""
    sug, _ = sugerir_video(beat, tem_ancora)
    bruto = (beat.get("fim", 0) - beat.get("inicio", 0)) or 5
    saida = []
    for m in MOTORES_VIDEO:
        if tem_ancora and not m["ref"] and m["id"] == sug:
            pass
        if beat.get("imagem_fim") and not m["fim"]:
            continue
        d = ajustar_duracao(m["id"], bruto)
        c = custo_vivo(m["id"], duration=d)
        saida.append({
            "id": m["id"], "nome": m["nome"], "nota": m["nota"],
            "duracao": d, "credito": c,
            "preco_na_hora": m.get("custo_com_imagem", False),
            "total": round((c or 0) * quantos, 1) if c else None,
            "aceita_ancora": m["ref"],
            "sugerido": m["id"] == sug,
            "perde_ancora": tem_ancora and not m["ref"],
        })
    return sorted(saida, key=lambda x: (x["credito"] is None, x["credito"] or 0))


def opcoes_imagem(quantos=1):
    saida = []
    for m in MOTORES_IMAGEM:
        c = custo_vivo(m["id"])
        saida.append({"id": m["id"], "nome": m["nome"], "nota": m["nota"],
                      "credito": c, "total": round((c or 0) * quantos, 1) if c else None,
                      "sugerido": m.get("padrao", False)})
    return sorted(saida, key=lambda x: (x["credito"] is None, x["credito"] or 0))


_cache_custo = {}


def custo_vivo(job_type, **params):
    """Custo real, com cache por sessão — `generate cost` é uma chamada de rede
    e a tela pede o catálogo inteiro de uma vez."""
    chave = (job_type, tuple(sorted(params.items())))
    if chave not in _cache_custo:
        _cache_custo[chave] = custo(job_type, prompt="x", **params)
    return _cache_custo[chave]


# ---------------------------------------------------------------- etapa 5

def avatares(pid, corpo, log=None):
    """Opções de personagem para o usuário escolher ANTES de qualquer b-roll.

    Gera poucas e baratas de propósito: 3 imagens a 2 créditos. A escolha aqui
    vira a âncora de todas as cenas seguintes — errar aqui contamina o lote."""
    desc = (corpo.get("descricao") or "").strip()
    if not desc:
        raise Falhou("Descreva o personagem: idade, tipo físico, roupa, cenário.")
    quantas = int(corpo.get("quantas") or 3)
    motor = corpo.get("motor") or MODELO_IMAGEM
    if motor not in POR_MOTOR:
        raise Falhou("Motor desconhecido: " + str(motor))
    pasta = projetos.caminho(pid, "avatar")
    os.makedirs(pasta, exist_ok=True)

    variacoes = [
        "retrato de corpo inteiro, luz natural de janela, ambiente doméstico",
        "plano médio, luz suave frontal, fundo neutro",
        "plano americano, luz lateral quente, cenário de cozinha",
    ][:quantas]

    itens = []
    for i, v in enumerate(variacoes, 1):
        prompt = "%s. %s. Enquadramento vertical 9:16, aparência natural, sem texto na imagem." % (desc, v)
        log and log("gerando avatar %d/%d…" % (i, len(variacoes)))
        d = _json_cli(["generate", "create", motor,
                       "--prompt", prompt, "--aspect-ratio", "9:16"] + ESPERA)
        url = _extrair_url(d)
        alvo = os.path.join(pasta, "avatar_%d.png" % i)
        _baixar(url, alvo)
        itens.append({"id": "AV%d" % i, "arquivo": alvo, "url": url,
                      "variacao": v, "prompt": prompt})

    return {"itens": itens, "descricao": desc, "motor": motor,
            "custo_gasto": round(len(itens) * (custo_vivo(motor) or 0), 1),
            "nota": "Escolha um. Ele vira a âncora de personagem de todas as cenas."}


# ---------------------------------------------------------------- etapa 6

def imagens(pid, corpo, log=None):
    """Uma imagem estática por insert, com a MESMA âncora de personagem.

    Estático primeiro de propósito: imagem custa 2 créditos, vídeo custa 7,5+.
    Reprovar uma imagem custa 2; reprovar um vídeo custa o vídeo inteiro."""
    p = projetos.ler(pid)
    ancora = corpo.get("ancora")
    motor = corpo.get("motor") or MODELO_IMAGEM
    if motor not in POR_MOTOR:
        raise Falhou("Motor desconhecido: " + str(motor))
    if ancora and not os.path.isfile(ancora):
        raise Falhou("A imagem-âncora escolhida não está no disco: " + ancora)

    faltam = [b for b in p["plano"].get("beats", [])
              if b.get("tipo") == "insert" and not b.get("midia")]
    if not faltam:
        raise Falhou("Nenhum insert pendente de mídia.")

    pasta = projetos.caminho(pid, "broll")
    os.makedirs(pasta, exist_ok=True)

    itens = []
    for i, b in enumerate(faltam, 1):
        intencao = (b.get("intencao") or "").strip() or "cena de apoio"
        # A âncora entra por --image-references, NÃO redescrita no prompt.
        # Repetir a descrição do personagem no texto é o que faz o modelo
        # derivar para fotorrealismo e trocar o rosto entre planos.
        prompt = "%s. Enquadramento vertical 9:16, sem texto na imagem." % intencao
        args = ["generate", "create", motor, "--prompt", prompt,
                "--aspect-ratio", "9:16"]
        if ancora:
            args += ["--image-references", ancora]
        log and log("imagem %d/%d — %s" % (i, len(faltam), b.get("id")))
        d = _json_cli(args + ESPERA)
        url = _extrair_url(d)
        alvo = os.path.join(pasta, "%s.png" % b.get("id"))
        _baixar(url, alvo)
        itens.append({"id": b.get("id"), "arquivo": alvo, "url": url,
                      "intencao": intencao, "fala": b.get("fala", ""),
                      "inicio": b.get("inicio"), "fim": b.get("fim")})

    return {"itens": itens, "ancora": ancora, "motor": motor,
            "custo_gasto": round(len(itens) * (custo_vivo(motor) or 0), 1)}


# ---------------------------------------------------------------- etapa 8

def animar(pid, corpo, aprovadas, log=None):
    """Só as imagens APROVADAS viram vídeo. A lista vem do pipeline, não daqui —
    é o motor que garante que reprovada não passa."""
    if not aprovadas:
        raise Falhou("Nenhuma imagem aprovada. Aprove ao menos uma na etapa 7.")

    p = projetos.ler(pid)
    beats = {b.get("id"): b for b in p["plano"].get("beats", [])}
    ancora = corpo.get("ancora")
    pasta = projetos.caminho(pid, "broll")

    itens = []
    forcado = corpo.get("motor")
    if forcado and forcado not in POR_MOTOR:
        raise Falhou("Motor desconhecido: " + str(forcado))

    for i, it in enumerate(aprovadas, 1):
        b = beats.get(it["id"], {})
        sug, dur = sugerir_video(b, bool(ancora))
        modelo = forcado or sug
        cfg = POR_MOTOR[modelo]
        dur = ajustar_duracao(modelo, (b.get("fim", 0) - b.get("inicio", 0)) or 5)
        porque = ("você escolheu" if forcado else cfg["nota"])
        prompt = (it.get("intencao") or "movimento sutil de câmera").strip()
        args = ["generate", "create", modelo, "--prompt", prompt,
                "--duration", str(dur), "--start-image", it["arquivo"]]
        if cfg["ref"] and ancora:
            args += ["--image-references", ancora]
        if modelo.startswith("seedance"):
            # b-roll com áudio de IA briga com a voz do avatar e não separa depois
            # b-roll com áudio de IA briga com a voz do avatar e não separa depois
            args += ["--generate-audio", "false"]
        if modelo != "minimax_hailuo":
            args += ["--aspect-ratio", "9:16"]

        log and log("animando %d/%d — %s em %s" % (i, len(aprovadas), it["id"], modelo))
        d = _json_cli(args + ESPERA)
        url = _extrair_url(d)
        alvo = os.path.join(pasta, "%s.mp4" % it["id"])
        _baixar(url, alvo)
        itens.append({"id": it["id"], "arquivo": alvo, "url": url,
                      "modelo": modelo, "duracao": dur, "porque": porque,
                      "custo": custo_vivo(modelo, duration=dur)})

    return {"itens": itens,
            "custo_gasto": round(sum(x["custo"] or 0 for x in itens), 1)}


# ---------------------------------------------------------------- util

def _extrair_url(d):
    """O CLI muda o formato entre modelos; procura a primeira URL de mídia."""
    achadas = []

    def anda(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, str) and v.startswith("http") and re.search(
                        r"\.(png|jpe?g|webp|mp4|mov)(\?|$)", v, re.I):
                    achadas.append(v)
                else:
                    anda(v)
        elif isinstance(x, list):
            for v in x:
                anda(v)
    anda(d)
    if not achadas:
        raise Falhou("A geração terminou mas não veio arquivo. Confira em "
                     "`higgsfield generate list` — o crédito pode ter saído.")
    return achadas[0]


def _baixar(url, destino):
    import urllib.request
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tmp = destino + ".parte"
    req = urllib.request.Request(url, headers={"User-Agent": "EditorAutomatico/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
        while True:
            pedaco = r.read(65536)
            if not pedaco:
                break
            f.write(pedaco)
    os.replace(tmp, destino)
    return destino
