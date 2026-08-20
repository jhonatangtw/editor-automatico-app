"""
Etapa 12 — controle de qualidade.

Duas provas diferentes, e as duas importam:

  1. **A timeline**, lida de volta do Premiere. Responde "o que foi montado é o
     que foi planejado?" — insert que não entrou, b-roll fora da fala, marcador
     que sumiu, trilha muda por engano.
  2. **O arquivo exportado**, quando existir. Responde "o que saiu presta?" —
     formato, quadro preto, silêncio, duração.

Por que não uma só: a timeline pode estar perfeita e o export sair errado
(sequência errada, preset errado), e o arquivo pode estar bonito e não ser o
job (export de ontem parado na pasta). Cada uma pega o que a outra não vê.

Roda 100% local. Nenhum crédito, nenhuma chamada de plataforma — QC que custa
dinheiro é QC que o aluno pula.
"""

import json
import os
import re
import subprocess

from . import adobe, projetos

TOLERANCIA = 0.20      # segundos de folga entre o beat e o clipe na timeline
VIDEO_EXT = (".mp4", ".mov", ".m4v")


class Falhou(RuntimeError):
    pass


def _achado(sev, o_que, detalhe="", onde=None):
    return {"severidade": sev, "o_que": o_que, "detalhe": detalhe, "onde": onde}


# ---------------------------------------------------------------- a timeline

def auditar_timeline(pid, trilha_apoio=2):
    """Compara o que está na sequência ativa com o que o plano pediu."""
    tl = adobe.timeline()
    p = projetos.ler(pid)
    plano = p["plano"]
    dur = float(plano["fonte"].get("duracao") or 0)
    beats = plano.get("beats", [])
    inserts = sorted([b for b in beats if b.get("tipo") == "insert"],
                     key=lambda b: b.get("inicio", 0))

    video = tl.get("video") or []
    audio = tl.get("audio") or []
    apoio = video[trilha_apoio - 1]["clipes"] if len(video) >= trilha_apoio else []
    body = video[0]["clipes"] if video else []

    achados = []
    if not body:
        achados.append(_achado("grave", "A V1 está vazia",
                               "Sem body na V1 não há o que conferir — o vídeo montado "
                               "não existe nesta sequência."))

    # cada insert planejado tem clipe cobrindo?
    cobertos, descobertos = [], []
    for b in inserts:
        ini, fim = b.get("inicio", 0), b.get("fim", 0)
        casa = None
        for c in apoio:
            if c["entra"] <= ini + TOLERANCIA and c["sai"] >= fim - TOLERANCIA:
                casa = c
                break
        if casa:
            cobertos.append({"id": b.get("id"), "clipe": casa["nome"],
                             "entra": casa["entra"], "sai": casa["sai"]})
        else:
            parcial = next((c for c in apoio
                            if c["sai"] > ini + 0.05 and c["entra"] < fim - 0.05), None)
            descobertos.append({"id": b.get("id"), "inicio": ini, "fim": fim,
                                "parcial": bool(parcial)})
            achados.append(_achado(
                "grave" if not parcial else "atencao",
                "Insert %s %s" % (b.get("id"), "sem b-roll na timeline" if not parcial
                                  else "coberto só em parte"),
                b.get("fala") or b.get("intencao") or "", round(ini, 2)))

    # b-roll na timeline que ninguém planejou — costuma ser sobra de montagem anterior
    for c in apoio:
        if not any(abs(c["entra"] - b.get("inicio", 0)) < 0.5 for b in inserts):
            achados.append(_achado("atencao", "Clipe de apoio fora do plano",
                                   c["nome"], round(c["entra"], 2)))

    # trilhas mudas: a do body muda é o erro que passa despercebido até o export
    for t in video[:1] + audio[:1]:
        if t.get("mudo"):
            achados.append(_achado("grave", "Trilha %s está MUDA" % t.get("nome"),
                                   "O export sai sem ela."))

    # marcadores
    marcadores = tl.get("marcadores") or []
    do_app = [m for m in marcadores if str(m.get("comentario") or "").startswith("EA:")]
    if inserts and not marcadores:
        achados.append(_achado("atencao", "Nenhum marcador na sequência",
                               "A montagem escreve marcador para cada b-roll e lettering."))

    # vãos: trecho longo sem nenhum apoio, o sintoma de criativo parado
    ordenados = sorted(apoio, key=lambda c: c["entra"])
    vaos, cursor = [], 0.0
    for c in ordenados:
        if c["entra"] - cursor > 0.05:
            vaos.append([round(cursor, 2), round(c["entra"], 2)])
        cursor = max(cursor, c["sai"])
    if dur - cursor > 0.05:
        vaos.append([round(cursor, 2), round(dur, 2)])
    maior = max(([v[1] - v[0] for v in vaos] or [0]))

    coberto_seg = sum(c["sai"] - c["entra"] for c in ordenados)
    cobertura = round(coberto_seg / dur * 100, 1) if dur else 0

    return {
        "sequencia": tl.get("sequencia"),
        "duracao_sequencia": tl.get("duracao"),
        "duracao_body": dur,
        "trilhas": {"video": len(video), "audio": len(audio),
                    "mudas": tl["resumo"]["trilhas_mudas"]},
        "clipes_apoio": len(apoio),
        "inserts_planejados": len(inserts),
        "inserts_cobertos": len(cobertos),
        "descobertos": descobertos,
        "cobertura": cobertura,
        "vaos": vaos[:12],
        "maior_vao": round(maior, 2),
        "marcadores": {"total": len(marcadores), "do_app": len(do_app)},
        "achados": achados,
    }


# ---------------------------------------------------------------- o arquivo

def _ffprobe(caminho):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", caminho],
        capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        raise Falhou("O ffprobe não leu esse arquivo: %s" % os.path.basename(caminho))
    return json.loads(r.stdout)


def _varredura(caminho, ao_vivo=None):
    """Quadro preto e silêncio numa passada só de ffmpeg — decodificar duas
    vezes um export de 1080x1920 é o dobro do tempo por nada."""
    cmd = ["ffmpeg", "-v", "info", "-i", caminho,
           "-vf", "blackdetect=d=0.12:pic_th=0.98:pix_th=0.10",
           "-af", "silencedetect=n=-38dB:d=1.0",
           "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    saida = r.stderr or ""
    pretos = [{"inicio": round(float(a), 2), "fim": round(float(b), 2)}
              for a, b in re.findall(
                  r"black_start:([\d.]+) black_end:([\d.]+)", saida)]
    silencios = []
    ini = None
    for m in re.finditer(r"silence_(start|end): (-?[\d.]+)", saida):
        if m.group(1) == "start":
            ini = float(m.group(2))
        elif ini is not None:
            silencios.append({"inicio": round(ini, 2), "fim": round(float(m.group(2)), 2)})
            ini = None
    return pretos, silencios


def _mosaico(caminho, destino, duracao):
    """20 quadros numa folha. É o que deixa reprovar por olho em 5 segundos —
    sem legenda queimada, porque o ffmpeg desta máquina não tem drawtext."""
    if duracao <= 0:
        return None
    passo = max(duracao / 20.0, 0.4)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", caminho,
         "-vf", "fps=1/%.3f,scale=200:-1,tile=5x4" % passo,
         "-frames:v", "1", destino],
        capture_output=True, text=True, timeout=600)
    return destino if r.returncode == 0 and os.path.isfile(destino) else None


def auditar_arquivo(pid, caminho, ao_vivo=None):
    p = projetos.ler(pid)
    f = p["plano"]["fonte"]
    esperado = float(f.get("duracao") or 0)

    d = _ffprobe(caminho)
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        raise Falhou("Esse arquivo não tem trilha de vídeo.")
    larg, alt = int(v.get("width") or 0), int(v.get("height") or 0)
    dur = round(float((d.get("format") or {}).get("duration") or 0), 2)
    num, _, den = (v.get("r_frame_rate") or "30/1").partition("/")
    fps = round(float(num) / float(den or 1), 3)

    achados = []
    razao = (larg / alt) if alt else 0
    if not (0.5 < razao < 0.62):
        achados.append(_achado("atencao", "O export não está em 9:16",
                               "%d×%d — o padrão da casa para criativo é vertical." % (larg, alt)))
    if alt < 1080:
        achados.append(_achado("atencao", "Resolução abaixo de 1080 na vertical",
                               "%d×%d" % (larg, alt)))
    if not a:
        achados.append(_achado("grave", "O arquivo exportado não tem áudio", ""))
    else:
        # áudio que acaba antes do vídeo não vira silêncio detectável: a trilha
        # simplesmente TERMINA, e o silencedetect não tem o que ouvir. Só a
        # comparação de duração pega esse — e é erro comum de export.
        dur_a = float(a.get("duration") or (d.get("format") or {}).get("duration") or 0)
        if dur and dur_a and dur - dur_a > 0.5:
            achados.append(_achado("grave", "O áudio acaba antes do vídeo",
                                   "áudio %.2fs × vídeo %.2fs — os últimos %.2fs saem mudos"
                                   % (dur_a, dur, dur - dur_a)))
    if esperado and abs(dur - esperado) > 1.0:
        achados.append(_achado(
            "grave" if abs(dur - esperado) > 3 else "atencao",
            "A duração não bate com o body",
            "export %.2fs × body %.2fs" % (dur, esperado)))

    ao_vivo and ao_vivo("varrendo quadro preto e silêncio…")
    pretos, silencios = _varredura(caminho, ao_vivo)
    for b in pretos:
        fim_do_video = b["fim"] >= dur - 0.3
        achados.append(_achado("atencao" if fim_do_video else "grave",
                               "Quadro preto de %.2fs" % (b["fim"] - b["inicio"]),
                               "no fim do vídeo" if fim_do_video else "no meio do vídeo",
                               b["inicio"]))
    for s in silencios:
        if s["fim"] - s["inicio"] >= 1.5:
            achados.append(_achado("atencao", "Silêncio de %.2fs" % (s["fim"] - s["inicio"]),
                                   "criativo parado nesse trecho", s["inicio"]))

    ao_vivo and ao_vivo("montando o mosaico de quadros…")
    mosaico = _mosaico(caminho, projetos.caminho(pid, "saida", "qc-mosaico.jpg"), dur)

    return {
        "arquivo": caminho,
        "geometria": "%d×%d · %s fps" % (larg, alt, fps),
        "duracao": dur,
        "duracao_esperada": esperado,
        "tem_audio": bool(a),
        "pretos": pretos, "silencios": silencios,
        "mosaico": mosaico,
        "achados": achados,
    }


def _export_provavel(pid):
    """Procura um export recente na pasta de saída. Nada de adivinhar fora dela:
    pegar o mp4 errado faz o QC aprovar um vídeo que não é o job."""
    d = projetos.caminho(pid, "saida")
    if not os.path.isdir(d):
        return None
    cands = [os.path.join(d, n) for n in os.listdir(d)
             if n.lower().endswith(VIDEO_EXT)]
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


# ---------------------------------------------------------------- etapa 12

def conferir(pid, corpo=None, log=None):
    corpo = corpo or {}
    diz = log or (lambda _: None)
    achados, saida = [], {"timeline": None, "arquivo": None}

    diz("lendo a timeline montada…")
    try:
        saida["timeline"] = auditar_timeline(pid, int(corpo.get("trilha") or 2))
        achados += saida["timeline"]["achados"]
    except Exception as e:
        achados.append(_achado(
            "atencao", "Não consegui conferir a timeline",
            "%s — abra o Premiere com o projeto e o painel do Tools PRO para "
            "esta parte do QC valer." % e))

    caminho = corpo.get("arquivo") or _export_provavel(pid)
    if caminho and os.path.isfile(os.path.expanduser(caminho)):
        diz("conferindo o arquivo exportado…")
        saida["arquivo"] = auditar_arquivo(pid, os.path.expanduser(caminho), diz)
        achados += saida["arquivo"]["achados"]
    else:
        achados.append(_achado(
            "atencao", "Sem arquivo exportado para conferir",
            "Exporte para a pasta “saida” do projeto e rode o QC de novo — a "
            "conferência do arquivo é a que pega erro de preset de export."))

    graves = [a for a in achados if a["severidade"] == "grave"]
    atencoes = [a for a in achados if a["severidade"] == "atencao"]

    if graves:
        veredito = ("%d problema(s) grave(s). Aprovar aqui libera a exportação — "
                    "não aprove sem resolver." % len(graves))
    elif atencoes:
        veredito = ("Nada grave. %d ponto(s) de atenção para você julgar." % len(atencoes))
    else:
        veredito = "Passou limpo: timeline e arquivo batem com o plano."

    return {
        "veredito": veredito,
        "graves": len(graves),
        "atencoes": len(atencoes),
        "achados": sorted(achados, key=lambda a: (a["severidade"] != "grave",
                                                  a.get("onde") or 0)),
        "timeline": saida["timeline"],
        "arquivo": saida["arquivo"],
        "liberado_pela_regra": not graves,
    }
