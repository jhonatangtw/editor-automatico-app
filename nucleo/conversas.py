"""
Registro de conversas — o que o Histórico lista.

O erro anterior: o Histórico listava PROJETOS. Mas conversar não exige projeto —
dá para abrir o app e falar sem criar nada. Essas conversas iam todas para um
arquivo único (`conversa-atual.json`), sobrescrevendo umas às outras e sem
aparecer em lugar nenhum. Trabalho feito, invisível.

Agora a conversa é a unidade. Cada uma tem pasta própria, título tirado da
primeira coisa que o usuário disse, e pode ou não estar ligada a um projeto de
trabalho. A sessão do Claude mora junto — é o que permite reabrir e continuar
com o contexto inteiro.
"""

import json
import os
import time
import uuid

RAIZ = os.path.expanduser("~/Documents/Editor Automático/Conversas")
ATUAL = os.path.expanduser("~/Documents/Editor Automático/conversa-atual.json")
SESSAO_ANTIGA = os.path.expanduser("~/Documents/Editor Automático/sessao-livre.txt")


def dir_conversa(cid):
    return os.path.join(RAIZ, cid)


def caminho(cid, nome):
    return os.path.join(dir_conversa(cid), nome)


def _gravar(destino, dados):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)
    os.replace(tmp, destino)


def _ler(caminho_):
    try:
        with open(caminho_, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def criar(titulo=None, projeto=None):
    cid = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
    _gravar(caminho(cid, "meta.json"), {
        "id": cid, "titulo": titulo or "Nova conversa",
        "criada": time.time(), "atualizada": time.time(), "projeto": projeto})
    _gravar(caminho(cid, "conversa.json"), [])
    return cid


def meta(cid):
    return _ler(caminho(cid, "meta.json")) or {"id": cid, "titulo": cid}


def gravar_meta(cid, **campos):
    m = meta(cid)
    m.update(campos)
    m["atualizada"] = time.time()
    _gravar(caminho(cid, "meta.json"), m)
    return m


def _titulo_de(msgs):
    """A primeira fala do usuário vira o nome. É como ele vai reconhecer depois —
    'Nova conversa' repetido dez vezes não ajuda ninguém."""
    for m in msgs:
        if m.get("role") == "user" and (m.get("content") or "").strip():
            t = " ".join(str(m["content"]).split())
            return t[:60] + ("…" if len(t) > 60 else "")
    return "Nova conversa"


def mensagens(cid):
    return _ler(caminho(cid, "conversa.json")) or []


def gravar_mensagens(cid, msgs):
    _gravar(caminho(cid, "conversa.json"), msgs[-200:])
    m = meta(cid)
    novo_titulo = _titulo_de(msgs)
    gravar_meta(cid, titulo=novo_titulo if m.get("titulo") in (None, "Nova conversa")
                else m["titulo"])


def listar():
    """Todas as conversas, mais recentes primeiro."""
    _migrar()
    saida = []
    if not os.path.isdir(RAIZ):
        return saida
    for cid in os.listdir(RAIZ):
        if not os.path.isdir(dir_conversa(cid)):
            continue
        m = meta(cid)
        msgs = mensagens(cid)
        if not msgs:
            continue
        ferr = sum(1 for x in msgs for _ in (x.get("passos") or []))
        saida.append({
            "id": cid,
            "titulo": m.get("titulo") or _titulo_de(msgs),
            "quando": m.get("atualizada") or m.get("criada") or 0,
            "mensagens": len([x for x in msgs if x.get("role") in ("user", "assistant")]),
            "passos": ferr,
            "projeto": m.get("projeto"),
        })
    saida.sort(key=lambda x: x["quando"], reverse=True)
    return saida


def apagar(cid):
    import shutil
    d = dir_conversa(cid)
    if os.path.isdir(d):
        shutil.rmtree(d)
    return True


def _migrar():
    """Traz a conversa solta antiga para o formato novo.

    Sem isso o usuário abriria o Histórico consertado e continuaria sem ver o
    que já tinha conversado — o defeito pareceria não ter sido resolvido."""
    msgs = _ler(ATUAL)
    if not msgs:
        return
    cid = criar(_titulo_de(msgs))
    _gravar(caminho(cid, "conversa.json"), msgs)
    sid = None
    try:
        with open(SESSAO_ANTIGA, encoding="utf-8") as f:
            sid = f.read().strip()
    except Exception:
        pass
    if sid:
        with open(caminho(cid, "sessao.txt"), "w", encoding="utf-8") as f:
            f.write(sid)
    for velho in (ATUAL, SESSAO_ANTIGA):
        try:
            os.remove(velho)
        except Exception:
            pass
