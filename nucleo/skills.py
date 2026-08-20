"""
As skills que viajam dentro do app, e como elas chegam na máquina do editor.

O problema: o Claude Code lê as skills de `~/.claude/skills`. Na máquina de quem
ESCREVEU as skills isso está cheio; na do editor está vazio. Então o mesmo app,
com o mesmo Claude, respondia com um repertório completamente diferente
dependendo de quem abria — e sem nenhum aviso.

O app leva um retrato das skills de produção de criativo (`skills/`, gerado por
`./sincronizar-skills.sh`) e as instala na pasta do Claude do usuário.

⚠️ **Nunca escreve por cima de uma skill que já existe.** Na máquina do autor as
skills instaladas são a FONTE — o retrato é sempre mais velho. Sobrescrever ali
seria apagar o original com uma cópia desatualizada. Só instala o que falta; a
troca de uma skill existente exige pedido explícito, e mesmo assim guarda a
anterior ao lado.
"""

import json
import os
import shutil
import sys
import time

DESTINO = os.path.expanduser("~/.claude/skills")


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


def _titulo(pasta):
    """A primeira linha útil do SKILL.md — é o que a tela mostra."""
    try:
        with open(os.path.join(pasta, "SKILL.md"), encoding="utf-8") as f:
            for linha in f:
                l = linha.strip()
                if l.startswith("description:"):
                    return l.split(":", 1)[1].strip().strip('"')[:110]
                if l.startswith("# "):
                    return l[2:].strip()[:110]
    except OSError:
        pass
    return ""


def estado():
    r = _raiz()
    itens = []
    for nome in embutidas():
        alvo = os.path.join(DESTINO, nome)
        itens.append({
            "nome": nome,
            "instalada": os.path.isdir(alvo),
            "descricao": _titulo(os.path.join(r, nome)),
        })
    faltam = [i["nome"] for i in itens if not i["instalada"]]
    return {"skills": itens, "faltam": faltam, "destino": DESTINO,
            "total": len(itens), "instaladas": len(itens) - len(faltam)}


def instalar(substituir=False, ao_vivo=None):
    """Põe na pasta do Claude o que falta. Devolve o que fez, item a item."""
    diz = ao_vivo or (lambda _: None)
    r = _raiz()
    if not embutidas():
        raise RuntimeError("Este app não trouxe skills. Reinstale — elas vêm junto.")

    os.makedirs(DESTINO, exist_ok=True)
    feitos = []
    for nome in embutidas():
        origem, alvo = os.path.join(r, nome), os.path.join(DESTINO, nome)
        if os.path.isdir(alvo) and not substituir:
            feitos.append({"skill": nome, "acao": "já existia"})
            continue
        if os.path.isdir(alvo):
            # guarda a anterior: skill do usuário pode ter mudanças dele
            velha = alvo + ".anterior-" + time.strftime("%Y%m%d-%H%M%S")
            shutil.move(alvo, velha)
            feitos.append({"skill": nome, "acao": "substituída",
                           "anterior": os.path.basename(velha)})
        else:
            feitos.append({"skill": nome, "acao": "instalada"})
        diz("instalando " + nome)
        shutil.copytree(origem, alvo)

    novas = [f for f in feitos if f["acao"] != "já existia"]
    return {"ok": True, "feitos": feitos, "novas": len(novas),
            "destino": DESTINO,
            "msg": ("%d skill(s) instalada(s) em %s. O Claude passa a usá-las na "
                    "próxima mensagem." % (len(novas), DESTINO)) if novas
                   else "Todas as skills do app já estavam instaladas."}


def sincronizado():
    try:
        with open(os.path.join(_raiz(), "FONTE.json"), encoding="utf-8") as f:
            return json.load(f).get("sincronizado")
    except Exception:
        return None
