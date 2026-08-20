"""
O que cada etapa FAZ. O `pipeline.py` decide se pode; aqui é o trabalho.

Toda função devolve os dados que a tela mostra para o usuário decidir. Nenhuma
delas conclui a própria etapa — entregam em "aguardando aprovação" e param.
Quem conclui é o humano, sempre.
"""

import difflib
import json
import os
import re
import unicodedata

from . import decupar, projetos, skill

# ---------------------------------------------------------------- 1. análise

COPY_EXT = (".txt", ".md", ".rtf", ".docx")
VIDEO_EXT = (".mp4", ".mov", ".m4v")


def _normal(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", t)


def _palavras(t):
    return [p for p in _normal(t).split() if p]


def analise(pid):
    """Identifica o que existe: projeto, arquivos, formato e a copy.

    O formato sai da geometria, não de um campo digitado — 1080x1920 é 9:16 e
    ponto. Palpite de humano aqui vira export no formato errado."""
    p = projetos.ler(pid)
    f = p["plano"]["fonte"]
    larg, alt = f.get("largura") or 0, f.get("altura") or 0
    razao = (larg / alt) if alt else 0

    if 0.5 < razao < 0.62:
        formato, ok_formato = "9:16 (vertical)", True
    elif 1.6 < razao < 1.85:
        formato, ok_formato = "16:9 (horizontal)", False
    elif 0.95 < razao < 1.05:
        formato, ok_formato = "1:1 (quadrado)", False
    else:
        formato, ok_formato = "%dx%d" % (larg, alt), False

    pasta = os.path.dirname(f["body"])
    achados = {"copy": [], "video": [], "audio": []}
    try:
        for nome in sorted(os.listdir(pasta)):
            baixo = nome.lower()
            cheio = os.path.join(pasta, nome)
            if not os.path.isfile(cheio):
                continue
            if baixo.endswith(COPY_EXT):
                achados["copy"].append(cheio)
            elif baixo.endswith(VIDEO_EXT) and cheio != f["body"]:
                achados["video"].append(cheio)
            elif baixo.endswith((".wav", ".mp3", ".m4a")):
                achados["audio"].append(cheio)
    except Exception:
        pass

    alertas = []
    if not ok_formato:
        alertas.append("O bruto está em %s. O padrão da casa para criativo é 9:16 — "
                       "confirme antes de seguir." % formato)
    if not achados["copy"]:
        alertas.append("Não achei arquivo de copy na pasta do body. Você pode colar "
                       "a copy na próxima etapa.")
    if f.get("duracao", 0) < 5:
        alertas.append("O body tem menos de 5 segundos. Confira se apontou o arquivo certo.")

    return {
        "projeto": p["plano"]["job"],
        "body": f["body"],
        "pasta": pasta,
        "formato": formato,
        "formato_ok": ok_formato,
        "geometria": "%d×%d · %s fps" % (larg, alt, f.get("fps")),
        "duracao": f.get("duracao"),
        "arquivos": achados,
        "alertas": alertas,
    }


# ------------------------------------------------------- 2. verificação da copy

def _ler_copy(caminho):
    if caminho.lower().endswith(".docx"):
        import zipfile
        with zipfile.ZipFile(caminho) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        return re.sub(r"<[^>]+>", " ", xml)
    with open(caminho, encoding="utf-8", errors="ignore") as f:
        return f.read()


def verificar_copy(pid, texto_copy=None, caminho_copy=None):
    """Compara a copy escrita com a fala REAL transcrita.

    Não é diff de texto por vaidade: é onde aparece a palavra que o avatar
    engoliu, a que ele pronunciou errado, a frase repetida por bug de geração
    e o trecho que sumiu. Cada um desses vira retrabalho se passar batido."""
    t = decupar.ler(pid)
    if not t:
        raise RuntimeError("Decupe a fala primeiro — sem transcrição não há o que comparar.")

    if texto_copy is None and caminho_copy:
        texto_copy = _ler_copy(caminho_copy)
    if not (texto_copy or "").strip():
        raise RuntimeError("Sem copy para comparar. Cole o texto ou aponte o arquivo.")

    falado_palavras = [w["p"] for w in t["palavras"]]
    a = _palavras(texto_copy)          # copy escrita
    b = _palavras(" ".join(falado_palavras))  # fala real

    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    divergencias = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        na, nb = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        # onde isso acontece na linha do tempo
        quando = t["palavras"][min(j1, len(t["palavras"]) - 1)]["t"] if t["palavras"] else 0
        if tag == "delete":
            divergencias.append({"tipo": "ausente", "copy": na, "falado": "",
                                 "t": quando, "grave": len(a[i1:i2]) > 2})
        elif tag == "insert":
            divergencias.append({"tipo": "sobra", "copy": "", "falado": nb,
                                 "t": quando, "grave": len(b[j1:j2]) > 3})
        else:
            divergencias.append({"tipo": "trocado", "copy": na, "falado": nb,
                                 "t": quando, "grave": abs(len(a[i1:i2]) - len(b[j1:j2])) > 2})

    # repetição: bug clássico de geração de avatar (o modelo repete o fim do bloco)
    repeticoes = []
    jan = 4
    for i in range(len(b) - jan * 2):
        if b[i:i + jan] == b[i + jan:i + jan * 2]:
            quando = t["palavras"][i]["t"] if i < len(t["palavras"]) else 0
            trecho = " ".join(b[i:i + jan])
            if not any(r["trecho"] == trecho for r in repeticoes):
                repeticoes.append({"trecho": trecho, "t": quando})

    cobertura = round(sm.ratio() * 100, 1)
    return {
        "cobertura": cobertura,
        "palavras_copy": len(a),
        "palavras_faladas": len(b),
        "idioma": t.get("idioma"),
        "divergencias": divergencias[:60],
        "graves": sum(1 for d in divergencias if d["grave"]),
        "repeticoes": repeticoes[:10],
        "copy": texto_copy,
        "veredito": ("A fala bate com a copy." if cobertura >= 95
                     else "Confira as divergências antes de seguir." if cobertura >= 80
                     else "A fala diverge muito da copy. Isso costuma ser bloco errado ou take antigo."),
    }


# ------------------------------------------------------- 3. marcação da timeline

CORES = {"insert": "vermelho", "lettering": "azul", "copy": "roxo"}


def marcar_timeline(pid):
    """Os marcadores que vão para o Premiere, na convenção da casa.

    A fala de cada marcador vem da transcrição, não da digitação: é ela que
    prova que o insert está na palavra que o justifica."""
    p = projetos.ler(pid)
    beats = p["plano"].get("beats", [])
    if not beats:
        raise RuntimeError("Nenhum beat no plano ainda. Marque os pontos antes.")

    itens = []
    for b in sorted(beats, key=lambda x: x.get("inicio", 0)):
        tipo = b.get("tipo", "insert")
        fala = b.get("fala") or decupar.frase_em(pid, b.get("inicio", 0), b.get("fim", 0))
        itens.append({
            "id": b.get("id"),
            "tipo": tipo,
            "cor": CORES.get(tipo, "roxo"),
            "inicio": b.get("inicio"),
            "fim": b.get("fim"),
            "intencao": b.get("intencao") or b.get("texto") or b.get("nota") or "",
            "fala": fala,
            "midia": b.get("midia"),
        })

    dur = p["plano"]["fonte"].get("duracao") or 1
    inserts = [i for i in itens if i["tipo"] == "insert"]
    cobertos = sum((i["fim"] - i["inicio"]) for i in inserts)
    return {
        "itens": itens,
        "duracao": dur,
        "cobertura": round(cobertos / dur * 100, 1),
        "por_cor": {"vermelho": len(inserts),
                    "azul": len([i for i in itens if i["tipo"] == "lettering"]),
                    "roxo": len([i for i in itens if i["tipo"] == "copy"])},
        "sem_fala": [i["id"] for i in inserts if not i["fala"]],
    }


# ------------------------------------------------------- 4. plano (o portão)

def mapa_do_plano(pid):
    """O mapa completo que o usuário revisa antes de qualquer geração.
    Roda o portão da skill — é a mesma medida do terminal, sem segunda regra."""
    p = projetos.ler(pid)
    caminho = projetos.caminho(pid, "plano.json")
    r = skill.revisar(caminho, p["plano"].get("estilo"))
    marc = marcar_timeline(pid)
    faltam = [i["id"] for i in marc["itens"]
              if i["tipo"] == "insert" and not i["midia"]]
    return {
        "portao": r["texto"],
        "liberado_pela_regra": r["liberado"],
        "estilo": p["plano"].get("estilo"),
        "marcadores": marc,
        "a_gerar": faltam,
        "custo_previsto": "%d imagem(ns) + %d animação(ões)" % (len(faltam), len(faltam)),
    }
