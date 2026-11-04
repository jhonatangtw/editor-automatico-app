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


def _pastas():
    """Toda skill do retrato. `_agentes/` não é skill: são os manifestos."""
    r = _raiz()
    try:
        return sorted(n for n in os.listdir(r)
                      if os.path.isdir(os.path.join(r, n)) and not n.startswith("_"))
    except OSError:
        return []


def embutidas():
    """As do botão geral. As EXCLUSIVAS de um agente só chegam pelo cartão dele —
    quem não quer o agente não recebe a agência inteira na lista do Claude."""
    so_de_agente = {s for a in agentes() for s in a.get("exclusivas", [])}
    return [n for n in _pastas() if n not in so_de_agente]


# ---------------------------------------------------------------- agentes
# Um agente é um PACOTE: as skills de que ele precisa (algumas já são do botão
# geral, outras só dele) + os subagentes que ele despacha, que o Claude Code lê
# de ~/.claude/agents. O manifesto mora em skills/_agentes/<id>/agente.json.

DESTINO_AGENTES = os.path.expanduser("~/.claude/agents")
REGISTRO_AGENTES = os.path.expanduser("~/.editorblackbelt/subagentes.json")


def agentes():
    base = os.path.join(_raiz(), "_agentes")
    try:
        ids = sorted(os.listdir(base))
    except OSError:
        return []
    out = []
    for i in ids:
        try:
            with open(os.path.join(base, i, "agente.json"), encoding="utf-8") as f:
                out.append(json.load(f))
        except (OSError, ValueError):
            continue
    return out


def _agente(id_):
    for a in agentes():
        if a.get("id") == id_:
            return a
    raise KeyError("Este app não traz o agente '%s'." % id_)


def _hash_arquivo(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _registro():
    try:
        with open(REGISTRO_AGENTES, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _situacao_sub(id_, nome, reg=None):
    """Mesma regra de posse das skills, com o hash guardado FORA do arquivo
    (um .md de subagente não tem onde levar marca): o que o app instalou e
    ninguém mexeu atualiza sozinho; o que foi mexido é do aluno."""
    origem = os.path.join(_raiz(), "_agentes", id_, "agents", nome + ".md")
    alvo = os.path.join(DESTINO_AGENTES, nome + ".md")
    if not os.path.isfile(alvo):
        return "faltando"
    atual, hr = _hash_arquivo(alvo), _hash_arquivo(origem)
    if atual == hr:
        return "em_dia"
    if (reg if reg is not None else _registro()).get(nome) == atual:
        return "desatualizada"
    return "do_usuario"


def estado_agentes():
    reg = _registro()
    r = _raiz()
    out = []
    for a in agentes():
        sk = [{"nome": n, "situacao": situacao(n, DESTINO, hash_pasta(os.path.join(r, n)))
               if os.path.isdir(os.path.join(r, n)) else "ausente_no_app"} for n in a.get("skills", [])]
        sub = [{"nome": n, "situacao": _situacao_sub(a["id"], n, reg)} for n in a.get("subagentes", [])]
        itens = sk + sub
        out.append({
            "id": a["id"], "nome": a.get("nome", a["id"]), "descricao": a.get("descricao", ""),
            "chamar": a.get("chamar", ""), "skills": sk, "subagentes": sub,
            "faltam": [i["nome"] for i in itens if i["situacao"] == "faltando"],
            "atualizar": [i["nome"] for i in itens if i["situacao"] == "desatualizada"],
            "do_usuario": [i["nome"] for i in itens if i["situacao"] == "do_usuario"],
            "instalado": not any(i["situacao"] == "faltando" for i in itens),
        })
    return {"agentes": out}


def instalar_agente(id_, substituir=False, ao_vivo=None):
    """Instala o agente inteiro: as skills dele (no Claude e no Codex, igual ao
    botão geral) e os subagentes (só Claude — o Codex não tem subagente)."""
    diz = ao_vivo or (lambda _: None)
    a = _agente(id_)
    r = _raiz()
    faltam_no_app = [n for n in a.get("skills", []) if not os.path.isdir(os.path.join(r, n))]
    if faltam_no_app:
        raise RuntimeError("Este app veio sem parte do agente (%s). Reinstale o app."
                           % ", ".join(faltam_no_app))
    feitos = _instalar_nomes(a["skills"], substituir, diz)

    os.makedirs(DESTINO_AGENTES, exist_ok=True)
    reg = _registro()
    for nome in a.get("subagentes", []):
        origem = os.path.join(r, "_agentes", id_, "agents", nome + ".md")
        alvo = os.path.join(DESTINO_AGENTES, nome + ".md")
        st = _situacao_sub(id_, nome, reg)
        item = {"subagente": nome, "para": "claude"}
        if st == "em_dia":
            item["acao"] = "já estava em dia"
        elif st in ("faltando", "desatualizada") or substituir:
            if st == "do_usuario":
                os.makedirs(os.path.join(BACKUP, "agents"), exist_ok=True)
                item["anterior"] = os.path.join(BACKUP, "agents", "%s-%s.md"
                                                % (nome, time.strftime("%Y%m%d-%H%M%S")))
                shutil.move(alvo, item["anterior"])
            diz("instalando o subagente %s" % nome)
            shutil.copyfile(origem, alvo + ".instalando")
            os.replace(alvo + ".instalando", alvo)
            item["acao"] = {"faltando": "instalada", "desatualizada": "atualizada"}.get(st, "substituída")
        else:
            item["acao"] = "mantida (cópia sua)"
        if item["acao"] != "mantida (cópia sua)":
            reg[nome] = _hash_arquivo(alvo)
        feitos.append(item)
    os.makedirs(os.path.dirname(REGISTRO_AGENTES), exist_ok=True)
    with open(REGISTRO_AGENTES, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=1)

    novas = [f for f in feitos if f["acao"] in ("instalada", "atualizada", "substituída")]
    mantidas = [f for f in feitos if f["acao"].startswith("mantida")]
    msg = ("%s instalado: %d item(ns) novos ou atualizados." % (a.get("nome", id_), len(novas))
           if novas else "%s já estava instalado e em dia." % a.get("nome", id_))
    if novas and any("subagente" in f for f in novas):
        msg += " Feche e reabra o Claude Code para os subagentes aparecerem."
    if mantidas:
        msg += " %d mantidos porque você mexeu neles — use Reinstalar para trocar." % len(mantidas)
    if a.get("chamar"):
        msg += " Para começar, digite %s na conversa." % a["chamar"]
    return {"ok": True, "feitos": feitos, "novas": len(novas), "mantidas": len(mantidas), "msg": msg}


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


def _instalar_nomes(nomes, substituir, diz):
    r = _raiz()
    feitos = []
    for quem, destino in destinos():
        os.makedirs(destino, exist_ok=True)
        for nome in nomes:
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

    return feitos


def instalar(substituir=False, ao_vivo=None):
    """Instala o que falta e atualiza o que é nosso. Devolve o que fez, item a item.

    Rodar duas vezes seguidas não muda nada na segunda (idempotente)."""
    diz = ao_vivo or (lambda _: None)
    r = _raiz()
    if not embutidas():
        raise RuntimeError("Este app não trouxe skills. Reinstale — elas vêm junto.")

    feitos = _instalar_nomes(embutidas(), substituir, diz)

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
