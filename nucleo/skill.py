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

import contextlib
import importlib.util
import io
import json
import os
import sys
import threading

# A regra é AUTORADA na skill. Mas a skill mora em `~/.claude/skills`, pasta que
# só existe em máquina de quem usa o Claude Code — ou seja, na do autor. Na
# máquina do editor o app parava na etapa 4 com "a skill não está instalada",
# depois de passar limpo pelas três primeiras. Por isso um RETRATO da regra
# viaja dentro do app (`regra/`, sincronizado por `sincronizar-regra.sh`).
#
# A ordem é deliberada: se a skill estiver instalada, é ELA que vale — quem
# está desenvolvendo a regra vê o efeito na hora, sem republicar o app.
SKILL_USUARIO = os.path.expanduser("~/.claude/skills/editor-automatico-de-broll")


def _raiz_embutida():
    aqui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base in (aqui, getattr(sys, "_MEIPASS", None),
                 os.path.dirname(sys.executable)):
        if base and os.path.isdir(os.path.join(base, "regra")):
            return os.path.join(base, "regra")
    return os.path.join(aqui, "regra")


def _base():
    if os.path.isfile(os.path.join(SKILL_USUARIO, "scripts", "compilar.py")):
        return SKILL_USUARIO, "skill instalada nesta máquina"
    return _raiz_embutida(), "regra que vem com o app"


def origem():
    base, rotulo = _base()
    d = {"pasta": base, "rotulo": rotulo,
         "da_skill": base == SKILL_USUARIO, "sincronizada": None}
    try:
        with open(os.path.join(_raiz_embutida(), "FONTE.json"), encoding="utf-8") as f:
            d["sincronizada"] = json.load(f).get("sincronizado")
    except Exception:
        pass
    return d


def _dir(qual):
    return os.path.join(_base()[0], qual)


_cache = {}
_trava = threading.Lock()


class SemSkill(RuntimeError):
    pass


class RegraRecusou(RuntimeError):
    """A skill disse não. A mensagem é dela, não nossa — repassar sem enfeitar."""


def instalada():
    """Agora é sempre verdade: a regra viaja com o app. Fica porque a tela
    pergunta, e porque uma instalação corrompida ainda pode responder não."""
    return os.path.isfile(os.path.join(_dir("scripts"), "compilar.py"))


def _modulo(nome):
    if nome in _cache:
        return _cache[nome]
    caminho = os.path.join(_dir("scripts"), nome + ".py")
    if not os.path.isfile(caminho):
        raise SemSkill(
            "A regra de edição não foi encontrada (%s). Reinstale o app — ela "
            "vem junto." % caminho)
    spec = importlib.util.spec_from_file_location("skill_" + nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    _cache[nome] = mod
    return mod


def estilos():
    """Os tokens de acabamento disponíveis, com a descrição que a skill deu."""
    saida = []
    pasta = _dir("estilos")
    if not os.path.isdir(pasta):
        return saida
    for f in sorted(os.listdir(pasta)):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(pasta, f), encoding="utf-8") as fh:
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
    """O PORTÃO. A régua de texto que ele imprime é exatamente o que a tela
    mostra. Código de saída 1 = tem bloqueio, não pode montar.

    ⚠️ Isto RODAVA como subprocesso, com `sys.executable`. No app empacotado
    `sys.executable` é o PRÓPRIO APP, não o Python: a etapa 4 abriria uma
    segunda janela do Editor Automático em vez de rodar a régua. Rodando em
    processo o problema deixa de existir.

    ⚠️ `redirect_stdout` é global ao processo, e o servidor atende em threads —
    daí a trava. Duas revisões ao mesmo tempo misturariam a saída."""
    mod = _modulo("revisar")
    argv = ["revisar.py", "--plano", caminho_plano]
    if estilo_id:
        argv += ["--estilo", estilo_id]

    buf, codigo = io.StringIO(), 0
    with _trava:
        velho_argv = sys.argv
        try:
            sys.argv = argv
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                try:
                    mod.main()
                except SystemExit as e:
                    codigo = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        finally:
            sys.argv = velho_argv
    return {"liberado": codigo == 0, "texto": buf.getvalue()}


def build_ffmpeg(caminho_edicao, cwd):
    """montar.py cospe o comando ffmpeg; quem executa é o chamador, para poder
    mostrar progresso e cancelar.

    ⚠️ Roda em processo pelo mesmo motivo do `revisar()`: com `sys.executable`
    o app EMPACOTADO chamaria a si mesmo em vez do Python."""
    mod = _modulo("montar")
    buf, codigo = io.StringIO(), 0
    with _trava:
        velho_argv, velho_cwd = sys.argv, os.getcwd()
        try:
            sys.argv = ["montar.py", "--config", caminho_edicao]
            os.chdir(cwd)
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                try:
                    mod.main()
                except SystemExit as e:
                    codigo = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        finally:
            sys.argv = velho_argv
            os.chdir(velho_cwd)
    if codigo != 0:
        raise RegraRecusou(buf.getvalue().strip())
    return buf.getvalue()
