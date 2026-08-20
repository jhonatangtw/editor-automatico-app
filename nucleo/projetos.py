"""
Projeto em disco. Um job = uma pasta.

O plano é um ARQUIVO legível, não uma linha de banco. Isso é decisão de produto:
o aluno consegue abrir, versionar, mandar pro editor e editar fora do app. É a
diferença entre uma ferramenta e uma caixa-preta.

Gravação sempre por troca atômica — o app lê o plano em vários pontos e um JSON
pela metade perde o job inteiro.
"""

import json
import os
import shutil
import subprocess
import time
import unicodedata

from . import pipeline, so

RAIZ = os.path.expanduser("~/Documents/Editor Automático/Projetos")


def _id(nome):
    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    base = "".join(c if c.isalnum() else "-" for c in base).strip("-").lower()[:40]
    return (base or "projeto") + "-" + str(int(time.time()))[-6:]


def dir_projeto(pid):
    return os.path.join(RAIZ, pid)


def caminho(pid, *partes):
    return os.path.join(dir_projeto(pid), *partes)


def _gravar(destino, dados):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    os.replace(tmp, destino)


def sondar(video):
    """Dimensão, duração e fps pelo ffprobe. Sem isso o plano não tem régua."""
    r = so.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate:format=duration",
         "-of", "json", video],
        capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("Não consegui ler esse vídeo. Ele abre no player?")
    d = json.loads(r.stdout)
    s = (d.get("streams") or [{}])[0]
    num, _, den = (s.get("r_frame_rate") or "30/1").partition("/")
    try:
        fps = round(float(num) / float(den or 1), 3)
    except Exception:
        fps = 30.0
    return {
        "body": video,
        "largura": s.get("width") or 1080,
        "altura": s.get("height") or 1920,
        "duracao": round(float((d.get("format") or {}).get("duration") or 0), 2),
        "fps": fps,
    }


def criar(nome, video):
    fonte = sondar(video)
    pid = _id(nome)
    plano = {
        "versao": 1,
        "job": nome,
        "formato": "ugc-9x16",
        "estilo": "alta-densidade",
        "saida": "FINAL_9x16.mp4",
        "legenda": None,
        "fonte": fonte,
        "beats": [],
    }
    os.makedirs(caminho(pid, "broll"), exist_ok=True)
    os.makedirs(caminho(pid, "saida"), exist_ok=True)
    _gravar(caminho(pid, "plano.json"), plano)
    _gravar(caminho(pid, "app.json"), {
        "id": pid, "nome": nome, "criado": time.time()})
    _gravar(caminho(pid, "pipeline.json"), pipeline.novo())
    return ler(pid)


def estado_pipeline(pid):
    """O progresso das 12 etapas. Se o arquivo sumir, o projeto recomeça do
    zero em vez de quebrar — mas o plano em disco continua lá."""
    try:
        with open(caminho(pid, "pipeline.json"), encoding="utf-8") as f:
            est = json.load(f)
    except Exception:
        est = pipeline.novo()
    # projeto criado antes do motor existir
    if est.get("versao") != 2:
        est = pipeline.novo()
    return est


def gravar_pipeline(pid, est):
    _gravar(caminho(pid, "pipeline.json"), est)
    return est


def ler(pid):
    with open(caminho(pid, "plano.json"), encoding="utf-8") as f:
        plano = json.load(f)
    meta = {}
    try:
        with open(caminho(pid, "app.json"), encoding="utf-8") as f:
            meta = json.load(f)
    except Exception:
        pass
    return {"id": pid, "plano": plano, "meta": meta}


def gravar_plano(pid, plano):
    _gravar(caminho(pid, "plano.json"), plano)
    return ler(pid)


def marcar_etapa(pid, etapa):
    try:
        with open(caminho(pid, "app.json"), encoding="utf-8") as f:
            m = json.load(f)
    except Exception:
        m = {"id": pid}
    m["etapa"] = etapa
    _gravar(caminho(pid, "app.json"), m)


def listar():
    if not os.path.isdir(RAIZ):
        return []
    saida = []
    for pid in sorted(os.listdir(RAIZ), reverse=True):
        try:
            p = ler(pid)
        except Exception:
            continue
        pl = p["plano"]
        est = estado_pipeline(pid)
        pnl = pipeline.painel(est)
        inserts = [b for b in pl.get("beats", []) if b.get("tipo") == "insert"]
        saida.append({
            "id": pid,
            "nome": pl.get("job", pid),
            "duracao": pl["fonte"].get("duracao", 0),
            "estilo": pl.get("estilo"),
            "beats": len(pl.get("beats", [])),
            "inserts": len(inserts),
            "faltam_midia": len([b for b in inserts if not b.get("midia")]),
            "etapa": est.get("etapa_atual"),
            "concluidas": pnl["concluidas"],
            "total": pnl["total"],
            "status_atual": next((e["rotulo"] for e in pnl["etapas"]
                                  if e["id"] == est.get("etapa_atual")), ""),
        })
    return saida


def apagar(pid):
    d = dir_projeto(pid)
    if os.path.isdir(d):
        shutil.rmtree(d)
    return True
