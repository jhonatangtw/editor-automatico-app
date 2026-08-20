"""
Ponte com a skill — a regra de edição mora lá, não aqui.

`compilar.py` da skill `editor-automatico-de-broll` é a ÚNICA implementação de
punch, cadência, marcador e validação. Este arquivo importa aquele; não copia.
Copiar criaria duas regras que discordam, e a divergência só apareceria num job
real, tarde demais.

Duas armadilhas de importar um script de linha de comando dentro de um servidor:

  1. `carregar_estilo()` chama `sys.exit()` quando o estilo não existe. Num CLI
     isso é educado; aqui derrubaria o app inteiro por causa de um nome digitado
     errado. Todo ponto de entrada abaixo captura SystemExit.
  2. O módulo tem estado global de caminho (DIR_ESTILOS). Carregamos uma vez e
     reusamos, em vez de reimportar por requisição.
"""

import importlib.util
import json
import os
import subprocess
import sys

SKILL = os.path.expanduser("~/.claude/skills/editor-automatico-de-broll")
SCRIPTS = os.path.join(SKILL, "scripts")
ESTILOS = os.path.join(SKILL, "estilos")

_cache = {}


class SemSkill(RuntimeError):
    pass


class RegraRecusou(RuntimeError):
    """A skill disse não. A mensagem é dela, não nossa — repassar sem enfeitar."""


def instalada():
    return os.path.isfile(os.path.join(SCRIPTS, "compilar.py"))


def _modulo(nome):
    if nome in _cache:
        return _cache[nome]
    caminho = os.path.join(SCRIPTS, nome + ".py")
    if not os.path.isfile(caminho):
        raise SemSkill(
            "A skill 'editor-automatico-de-broll' não está instalada nesta máquina. "
            "Ela é a regra de edição — sem ela o app não sabe onde entra o punch."
        )
    spec = importlib.util.spec_from_file_location("skill_" + nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    _cache[nome] = mod
    return mod


def estilos():
    """Os tokens de acabamento disponíveis, com a descrição que a skill deu."""
    saida = []
    if not os.path.isdir(ESTILOS):
        return saida
    for f in sorted(os.listdir(ESTILOS)):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(ESTILOS, f), encoding="utf-8") as fh:
                d = json.load(fh)
            saida.append({
                "id": d.get("nome") or f[:-5],
                "descricao": d.get("descricao", ""),
                "origem": d.get("origem", ""),
                "cobertura_alvo": (d.get("insert") or {}).get("cobertura_alvo"),
                "cadencia": (d.get("corte") or {}).get("alvo_segundos_por_corte"),
            })
        except Exception:
            continue
    return saida


def _protegido(fn, *a, **kw):
    """Roda algo da skill sem deixar um sys.exit derrubar o app."""
    try:
        return fn(*a, **kw)
    except SystemExit as e:
        raise RegraRecusou(str(e) or "A regra recusou sem explicar.") from None


def compilar(plano, estilo_id=None, caminho_plano=None):
    """plano + estilo -> edicao.json + marcadores.json, pela regra da skill.

    `caminho_plano` não é enfeite: a skill resolve o b-roll de cada insert
    RELATIVO à pasta do plano, e sem ele o primeiro beat com mídia derruba a
    compilação com KeyError('_caminho') — só não aparecia antes porque nenhum
    beat tinha mídia ainda."""
    c = _modulo("compilar")
    plano = dict(plano)
    if caminho_plano:
        plano["_caminho"] = os.path.abspath(caminho_plano)
    plano.setdefault("_caminho", os.path.abspath(caminho_plano or "plano.json"))
    estilo = _protegido(c.carregar_estilo, estilo_id or plano.get("estilo") or "alta-densidade")

    avisos = []
    inserts = _protegido(c.validar, plano, avisos)
    punch, _ = _protegido(c.calcular_punch, plano, estilo, inserts, avisos)
    marcadores = _protegido(c.montar_marcadores, plano, estilo, inserts)

    fonte = plano["fonte"]
    edicao = {
        "body": fonte["body"],
        "duracao": float(fonte["duracao"]),
        "largura": fonte.get("largura") or 1080,
        "altura": fonte.get("altura") or 1920,
        "saida": plano.get("saida") or "final.mp4",
        "legenda": plano.get("legenda"),
        "punch": punch,
        "inserts": [{"arquivo": b["midia"], "inicio": b["inicio"], "fim": b["fim"]}
                    for b in inserts if b.get("midia")],
        "flash": estilo["corte"].get("flash"),
        "sfx": estilo["corte"].get("sfx"),
    }
    return {"edicao": edicao, "marcadores": marcadores,
            "avisos": avisos, "estilo": estilo}


def revisar(caminho_plano, estilo_id=None):
    """O PORTÃO. Roda o revisar.py como processo — a saída dele é desenhada pra
    humano ler, e a régua de texto é exatamente o que queremos mostrar na tela.
    Código de saída 1 = tem bloqueio, não pode montar."""
    if not instalada():
        raise SemSkill("A skill não está instalada.")
    cmd = [sys.executable, os.path.join(SCRIPTS, "revisar.py"), "--plano", caminho_plano]
    if estilo_id:
        cmd += ["--estilo", estilo_id]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return {"liberado": r.returncode == 0,
            "texto": (r.stdout or "") + (r.stderr or "")}


def build_ffmpeg(caminho_edicao, cwd):
    """montar.py cospe o comando ffmpeg; quem executa é o chamador, para poder
    mostrar progresso e cancelar."""
    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "montar.py"), "--config", caminho_edicao],
        capture_output=True, text=True, cwd=cwd, timeout=120)
    if r.returncode != 0:
        raise RegraRecusou((r.stderr or r.stdout or "").strip())
    return r.stdout
