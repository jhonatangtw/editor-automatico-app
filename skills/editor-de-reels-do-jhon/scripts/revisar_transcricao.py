#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corrige a transcrição SEM perder os tempos (o Whisper erra nome próprio e gíria).

    python3 scripts/revisar_transcricao.py transcricao.json \
        --troca "estar no zero=editar do zero" \
        --troca "Hoje é ele de vocês, tá não é?@4.5=Hoje ela é de vocês. Tá no ar." \
        --inaudivel "Lá ele@30.5"

--troca "ERRADO[@tempo]=CERTO"  troca a sequência de palavras (comparação sem acento
         e sem pontuação); @tempo escolhe a ocorrência mais perto daquele segundo.
         Os tempos do trecho são redistribuídos pelo tamanho das palavras novas.
--inaudivel "TRECHO[@tempo]"     marca palavras que não devem virar legenda.
--listar                         mostra palavra@tempo para conferir.
Guarda o original em transcricao.orig.json na primeira vez. Sempre confira
de ouvido nomes de marca, produto e termos técnicos — é isso que vai na tela.
"""
import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comum import gravar_json, ler_json, norm, sair  # noqa: E402


def achar(W, seq, perto):
    alvo = [norm(x) for x in seq.split() if norm(x)]
    n = len(alvo)
    cands = [i for i in range(len(W) - n + 1) if [norm(w["w"]) for w in W[i:i + n]] == alvo]
    if not cands:
        sair("não achei '%s' na transcrição (use --listar para ver as palavras)" % seq)
    if perto is not None:
        return min(cands, key=lambda i: abs(W[i]["s"] - perto)), n
    if len(cands) > 1:
        print("! '%s' aparece %d vezes; troquei a primeira (use @tempo para escolher)" % (seq, len(cands)))
    return cands[0], n


def sep(arg):
    a, _, b = arg.partition("=")
    a, _, t = a.partition("@")
    return a.strip(), (float(t.replace(",", ".")) if t else None), b.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcricao")
    ap.add_argument("--troca", action="append", default=[])
    ap.add_argument("--inaudivel", action="append", default=[])
    ap.add_argument("--listar", action="store_true")
    a = ap.parse_args()
    d = ler_json(a.transcricao)
    W = d["palavras"]
    if a.listar:
        print(" ".join("%s@%.2f" % (w["w"], w["s"]) for w in W))
        return
    orig = os.path.splitext(a.transcricao)[0] + ".orig.json"
    if not os.path.exists(orig):
        shutil.copy2(a.transcricao, orig)
    for t in a.troca:
        errado, perto, certo = sep(t)
        if not certo:
            sair("--troca precisa de ERRADO=CERTO")
        i, n = achar(W, errado, perto)
        s, e = W[i]["s"], W[i + n - 1]["e"]
        novas = certo.split()
        pesos = [max(1, len(norm(x))) for x in novas]
        tot, acc, out = float(sum(pesos)), 0.0, []
        for x, p in zip(novas, pesos):
            ws = s + (e - s) * acc / tot
            acc += p
            out.append({"w": x, "s": round(ws, 2), "e": round(s + (e - s) * acc / tot, 2)})
        W[i:i + n] = out
        print("trocado %.2f–%.2f: '%s' -> '%s'" % (s, e, errado, certo))
    for t in a.inaudivel:
        trecho, _, tt = t.partition("@")
        i, n = achar(W, trecho, float(tt) if tt else None)
        for w in W[i:i + n]:
            w["inaudivel"] = True
        print("sem legenda: '%s' em %.2f" % (trecho, W[i]["s"]))
    d["palavras"] = W
    d["revisado"] = True
    gravar_json(a.transcricao, d)
    txt = os.path.splitext(a.transcricao)[0] + ".txt"
    linhas, cur, ini = [], [], None
    for w in W:
        ini = w["s"] if ini is None else ini
        cur.append(w["w"])
        if w["w"][-1:] in ".!?":
            linhas.append("[%6.2f] %s" % (ini, " ".join(cur))); cur, ini = [], None
    if cur:
        linhas.append("[%6.2f] %s" % (ini, " ".join(cur)))
    open(txt, "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    print("ok ->", a.transcricao)


if __name__ == "__main__":
    main()
