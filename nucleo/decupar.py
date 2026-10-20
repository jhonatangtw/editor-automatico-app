"""
Decupagem — a fala vira timestamps por palavra.

Por que palavra e não frase: o insert precisa entrar NA palavra que o justifica.
"tive que trocar o guarda-roupa" só vale como beat se soubermos onde "guarda-roupa"
começa. Timestamp por frase erra por segundos, e segundo é uma eternidade num 9:16.

Whisper roda local — o material não sobe para lugar nenhum. É promessa de produto,
não detalhe técnico: o aluno edita VSL de cliente aqui dentro.

⚠️ Não forçar idioma. O body pode estar em inglês (voz americana é a convenção da
casa) com a copy em PT-BR no documento. Forçar PT-BR transcreve inglês fonético.
"""

import json
import os
import subprocess

from . import projetos, so


def disponivel():
    from shutil import which
    return which("whisper") is not None


def _ruido(linha):
    """Aviso técnico em inglês que o Whisper sempre imprime no Mac (FP16 na
    CPU) — não diz nada ao aluno e parece erro."""
    b = linha.lower()
    return "fp16 is not supported" in b or "warnings.warn(" in b


def _motivo(saida):
    """O erro certo: ambiente do Whisper quebrado não é culpa do áudio."""
    b = (saida or "").lower()
    if "modulenotfounderror" in b or "no module named" in b or "importerror" in b:
        return ("O Whisper está instalado mas quebrado. Vá em Ambiente e clique em "
                "Reparar no Whisper.")
    return "O Whisper falhou. Confira se o arquivo tem áudio."


def rodar(pid, modelo="medium", ao_vivo=None):
    """Gera transcricao.json com uma entrada por palavra."""
    p = projetos.ler(pid)
    video = p["plano"]["fonte"]["body"]
    saida_dir = projetos.caminho(pid, "cache")
    os.makedirs(saida_dir, exist_ok=True)

    cmd = ["whisper", video, "--model", modelo, "--word_timestamps", "True",
           "--output_format", "json", "--output_dir", saida_dir, "--verbose", "False"]

    proc = so.popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1)
    saida = []
    for linha in proc.stdout:
        saida.append(linha)
        if ao_vivo and not _ruido(linha):
            ao_vivo(linha.rstrip())
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(_motivo("".join(saida[-40:])))

    base = os.path.splitext(os.path.basename(video))[0]
    bruto = os.path.join(saida_dir, base + ".json")
    with open(bruto, encoding="utf-8") as f:
        d = json.load(f)

    palavras = []
    for seg in d.get("segments", []):
        for w in seg.get("words", []) or []:
            texto = (w.get("word") or "").strip()
            if texto:
                palavras.append({"t": round(float(w.get("start", 0)), 3),
                                 "fim": round(float(w.get("end", 0)), 3),
                                 "p": texto})

    destino = projetos.caminho(pid, "transcricao.json")
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"idioma": d.get("language"), "palavras": palavras},
                  f, ensure_ascii=False)
    os.replace(tmp, destino)
    projetos.marcar_etapa(pid, "plano")
    return {"palavras": len(palavras), "idioma": d.get("language")}


def ler(pid):
    try:
        with open(projetos.caminho(pid, "transcricao.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def frase_em(pid, inicio, fim):
    """A fala que cai nesse intervalo — é o que justifica o beat na revisão."""
    t = ler(pid)
    if not t:
        return ""
    return " ".join(w["p"] for w in t["palavras"]
                    if w["t"] >= inicio - 0.15 and w["t"] <= fim + 0.15)
