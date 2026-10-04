"""
As skills que viajam dentro do app, e como elas chegam na máquina do editor.

O problema: o Claude Code lê as skills de `~/.claude/skills` (e o Codex, de
`~/.codex/skills`). Na máquina de quem ESCREVEU as skills isso está cheio; na
do editor está vazio. Então o mesmo app, com a mesma IA, respondia com um
repertório completamente diferente dependendo de quem abria — sem aviso.

O app leva um retrato LIMPO das skills (`skills/`, gerado por
`./sincronizar-skills.sh` + `limpar-skills.py`) e as instala nas pastas da IA.

Versão e posse, por skill instalada — o arquivo `.editor-automatico.json` que
o app deixa dentro da pasta guarda o hash do que ELE instalou:

  * não existe a pasta              -> instala;
  * marca do app e conteúdo intacto -> é nossa: atualiza sozinha quando o
                                       retrato muda (idempotente: igual = nada);
  * conteúdo mexido depois          -> é do aluno agora: NÃO toca;
  * pasta sem marca                 -> não é nossa (na máquina do autor as
                                       instaladas são a FONTE): NÃO toca, a menos
                                       que seja idêntica ao retrato.

Trocar uma cópia do aluno só com pedido explícito (`substituir=True`), e mesmo
assim a anterior vai para `~/.editorblackbelt/skills-anteriores/` — FORA da
pasta de skills. Guardar ao lado, como antes, deixava duas skills com o mesmo
nome visíveis para o Claude.
"""

import hashlib
import json
import os
import shutil
import sys
import time

DESTINO = os.path.expanduser("~/.claude/skills")
DESTINO_CODEX = os.path.expanduser("~/.codex/skills")
BACKUP = os.path.expanduser("~/.editorblackbelt/skills-anteriores")
MARCA = ".editor-automatico.json"
IGNORAR = {"__pycache__", ".DS_Store", MARCA}


def _raiz():
    aqui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for base in (aqui, getattr(sys, "_MEIPASS", None),
                 os.path.dirname(sys.executable)):
        if base and os.path.isdir(os.path.join(base, "skills")):
            return os.path.join(base, "skills")
    return os.path.join(aqui, "skills")


def embutidas():
    r = _raiz()
    try:
        return sorted(n for n in os.listdir(r)
                      if os.path.isdir(os.path.join(r, n)))
    except OSError:
        return []


def hash_pasta(pasta):
    """Hash do conteúdo de uma skill: caminho relativo + bytes de cada arquivo.
    Ignora o que o uso cria sozinho (__pycache__, .DS_Store) e a nossa marca —
    senão rodar um script da skill já a faria parecer "mexida"."""
    h = hashlib.sha256()
    for raiz, subs, arqs in os.walk(pasta):
        subs[:] = sorted(s for s in subs if s not in IGNORAR)
        for a in sorted(arqs):
            if a in IGNORAR or a.endswith(".pyc"):
                continue
            p = os.path.join(raiz, a)
            h.update(os.path.relpath(p, pasta).replace(os.sep, "/").encode("utf-8") + b"\0")
            with open(p, "rb") as f:
                h.update(f.read())
            h.update(b"\0")
    return h.hexdigest()[:16]


def destinos():
    """Para onde instalar. Claude sempre; Codex quando ele existe nesta máquina
    (pasta de configuração ou o comando no PATH) — o Codex lê o mesmo formato
    de skill (pasta com SKILL.md) em ~/.codex/skills."""
    d = [("claude", DESTINO)]
    if os.path.isdir(os.path.dirname(DESTINO_CODEX)) or shutil.which("codex"):
        d.append(("codex", DESTINO_CODEX))
    return d


def _marca(alvo):
    try:
        with open(os.path.join(alvo, MARCA), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _versao_app():
    try:
        from . import atualizacao
        return atualizacao.local().get("version")
    except Exception:
        return None


def situacao(nome, destino=DESTINO, hash_retrato=None):
    """faltando · em_dia · desatualizada (nossa, pode atualizar) ·
    do_usuario (mexida ou de outra origem: não tocamos)."""
    alvo = os.path.join(destino, nome)
    if not os.path.isdir(alvo):
        return "faltando"
    hr = hash_retrato or hash_pasta(os.path.join(_raiz(), nome))
    atual = hash_pasta(alvo)
    if atual == hr:
        return "em_dia"
    m = _marca(alvo)
    if m and m.get("hash") == atual:
        return "desatualizada"
    return "do_usuario"


def _titulo(pasta):
    """A primeira linha útil do SKILL.md — é o que a tela mostra.

    ⚠️ Metade das skills escreve a descrição em YAML DOBRADO (`description: >-`
    e o texto nas linhas seguintes, indentado). Ler só a linha do `description:`
    devolvia o literal `>-` — e era isso que aparecia na tela, para 5 das 13.
    """
    try:
        with open(os.path.join(pasta, "SKILL.md"), encoding="utf-8") as f:
            linhas = f.read().splitlines()
    except OSError:
        return ""

    for i, linha in enumerate(linhas):
        l = linha.strip()
        if l.startswith("description:"):
            resto = l.split(":", 1)[1].strip()
            if resto and resto[0] not in ">|":
                return resto.strip('"').strip("'")[:110]
            texto = []
            for seguinte in linhas[i + 1:]:
                if not seguinte.strip():
                    break
                if not seguinte[:1].isspace():
                    break
                texto.append(seguinte.strip())
            if texto:
                return " ".join(texto)[:110]
        if l.startswith("# "):
            return l[2:].strip()[:110]
    return ""


def estado():
    r = _raiz()
    itens = []
    for nome in embutidas():
        hr = hash_pasta(os.path.join(r, nome))
        st = situacao(nome, DESTINO, hr)
        itens.append({
            "nome": nome,
            "instalada": st != "faltando",
            "situacao": st,
            "descricao": _titulo(os.path.join(r, nome)),
        })
    faltam = [i["nome"] for i in itens if i["situacao"] == "faltando"]
    atualizar = [i["nome"] for i in itens if i["situacao"] == "desatualizada"]
    return {"skills": itens, "faltam": faltam, "atualizar": atualizar,
            "do_usuario": [i["nome"] for i in itens if i["situacao"] == "do_usuario"],
            "destino": DESTINO, "destinos": [d for _, d in destinos()],
            "total": len(itens), "instaladas": len(itens) - len(faltam)}


def _copiar(origem, alvo, hash_retrato):
    tmp = alvo + ".instalando"
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(origem, tmp, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc"))
    with open(os.path.join(tmp, MARCA), "w", encoding="utf-8") as f:
        json.dump({"hash": hash_retrato, "app": _versao_app(),
                   "instalado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "aviso": "Instalada pelo Editor Automático. Se você editar esta skill, "
                            "o app deixa de atualizá-la sozinho."}, f, ensure_ascii=False, indent=1)
    shutil.rmtree(alvo, ignore_errors=True)
    os.replace(tmp, alvo)


def _guardar(alvo, quem):
    os.makedirs(os.path.join(BACKUP, quem), exist_ok=True)
    destino = os.path.join(BACKUP, quem, os.path.basename(alvo) + "-" + time.strftime("%Y%m%d-%H%M%S"))
    base, n = destino, 1
    while os.path.exists(destino):
        n += 1
        destino = "%s~%d" % (base, n)
    shutil.move(alvo, destino)
    return destino


def instalar(substituir=False, ao_vivo=None):
    """Instala o que falta e atualiza o que é nosso. Devolve o que fez, item a item.

    Rodar duas vezes seguidas não muda nada na segunda (idempotente)."""
    diz = ao_vivo or (lambda _: None)
    r = _raiz()
    if not embutidas():
        raise RuntimeError("Este app não trouxe skills. Reinstale — elas vêm junto.")

    feitos = []
    for quem, destino in destinos():
        os.makedirs(destino, exist_ok=True)
        for nome in embutidas():
            origem, alvo = os.path.join(r, nome), os.path.join(destino, nome)
            hr = hash_pasta(origem)
            st = situacao(nome, destino, hr)
            item = {"skill": nome, "para": quem}
            if st == "em_dia":
                if not _marca(alvo):          # idêntica ao retrato: passa a ser nossa
                    _copiar(origem, alvo, hr)
                item["acao"] = "já estava em dia"
            elif st == "faltando":
                diz("instalando %s (%s)" % (nome, quem))
                _copiar(origem, alvo, hr)
                item["acao"] = "instalada"
            elif st == "desatualizada":
                diz("atualizando %s (%s)" % (nome, quem))
                _copiar(origem, alvo, hr)
                item["acao"] = "atualizada"
            elif substituir:
                velha = _guardar(alvo, quem)
                diz("trocando %s (%s) — a sua ficou guardada" % (nome, quem))
                _copiar(origem, alvo, hr)
                item.update(acao="substituída", anterior=velha)
            else:
                item["acao"] = "mantida (cópia sua)"
            feitos.append(item)

    novas = [f for f in feitos if f["acao"] in ("instalada", "atualizada", "substituída")]
    mantidas = [f for f in feitos if f["acao"].startswith("mantida")]
    partes = []
    if novas:
        partes.append("%d skill(s) instalada(s) ou atualizada(s). A IA passa a usá-las "
                      "na próxima mensagem." % len(novas))
    else:
        partes.append("Todas as skills do app já estavam em dia.")
    if mantidas:
        partes.append("%d foram mantidas porque você mexeu nelas — use Reinstalar para "
                      "trocar (a sua fica guardada em %s)." % (len(mantidas), BACKUP))
    return {"ok": True, "feitos": feitos, "novas": len(novas), "mantidas": len(mantidas),
            "destino": DESTINO, "destinos": [d for _, d in destinos()], "msg": " ".join(partes)}


def sincronizado():
    try:
        with open(os.path.join(_raiz(), "FONTE.json"), encoding="utf-8") as f:
            return json.load(f).get("sincronizado")
    except Exception:
        return None
