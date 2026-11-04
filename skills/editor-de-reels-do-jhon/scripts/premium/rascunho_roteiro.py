#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Primeiro rascunho do roteiro.json a partir da transcrição revisada.

    python3 scripts/premium/rascunho_roteiro.py PASTA_DO_PROJETO [--cta "Link|na bio"] [--forcar]

Faz o esqueleto que JÁ RENDERIZA: cenas de ~6–9 s cortadas no fim de frase,
lettering de 1–3 palavras por linha ancorado na palavra falada ("palavra@tempo"),
a 2ª linha de cada batida em destaque, tudo em tela cheia. Depois o Claude e o
aluno trocam o que importa: o gancho, o "hit" dourado, as telas reais, o cartão
de aprovação e o CTA. Não sobrescreve roteiro.json existente sem --forcar.
"""
import argparse
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from comum import duracao, gravar_json, ler_json, norm  # noqa: E402

FRACAS = {"a", "o", "e", "de", "do", "da", "no", "na", "em", "um", "uma", "pra", "que", "ou", "se", "com", "por", "os", "as", "é", "e"}


def ancora(w):
    return "%s@%.2f" % (w["w"].strip(".,!?;:\"'"), w["s"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--cta", help='texto do fecho em 2 linhas, ex.: "Link|na bio" (vira cena final em PiP)')
    ap.add_argument("--forcar", action="store_true")
    a = ap.parse_args()
    P = os.path.abspath(a.pasta)
    alvo = os.path.join(P, "roteiro.json")
    if os.path.exists(alvo) and not a.forcar:
        sys.exit("roteiro.json já existe (use --forcar para refazer)")
    W = [w for w in ler_json(os.path.join(P, "transcricao.json"))["palavras"] if not w.get("inaudivel")]
    DUR = duracao(os.path.join(P, "assets", "video", "fala.mp4"))
    frases, cur = [], []
    for w in W:
        cur.append(w)
        if w["w"][-1:] in ".!?":
            frases.append(cur); cur = []
    if cur:
        frases.append(cur)

    def batidas(fr):
        out, i = [], 0
        while i < len(fr):
            n = min(6, len(fr) - i)
            if len(fr) - i - n in (1, 2):      # não deixar sobra de 1–2 palavras
                n = max(3, (len(fr) - i + 1) // 2)
            while n > 2 and i + n < len(fr) and norm(fr[i + n - 1]["w"]) in FRACAS:
                n -= 1                            # a batida não termina em "no", "de", "é"…
            out.append(fr[i:i + n]); i += n
        return out

    cenas, beats, ini = [], [], 0.0
    for fi, fr in enumerate(frases):
        for b in batidas(fr):
            meio = (len(b) + 1) // 2
            while 1 < meio < len(b) and norm(b[meio - 1]["w"]) in FRACAS:
                meio -= 1        # a linha não termina em palavra fraca
            l1, l2 = b[:meio], b[meio:]
            linhas = [{"texto": " ".join(x["w"].strip(",;:") for x in l1), "em": ancora(l1[0]) if l1[0]["s"] > 0.05 else 0}]
            if l2:
                linhas.append({"texto": " ".join(x["w"].strip(",;:") for x in l2), "em": ancora(l2[0]), "destaque": True})
            else:
                linhas[0]["destaque"] = True
            beats.append(linhas)
        fim_frase = fr[-1]["e"]
        prox = frases[fi + 1][0]["s"] if fi + 1 < len(frases) else DUR
        if fim_frase - ini >= 6.0 or fi + 1 == len(frases):
            cenas.append({"id": "gancho" if not cenas else "cena-%d" % (len(cenas) + 1), "ini": round(ini, 2),
                          "beats": [{"linhas": L} for L in beats]})
            beats, ini = [], max(fim_frase, prox - 0.15)
    layout = [[0, "cheio"]]
    if a.cta:
        l = (a.cta.split("|") + [""])[:2]
        t = max(0.0, DUR - 4.0)
        cenas.append({"id": "cta", "ini": round(t, 2), "visual": {"tipo": "cta", "linhas": l, "pilula": "Link na bio"}})
        layout.append([round(t, 2), "pip"])
        if cenas[-2]["ini"] >= t:
            cenas.pop(-2)
    gravar_json(alvo, {"_leia": "rascunho automático — ajuste com o aluno (ver references/roteiro.md)", "layout": layout,
                       "punch_ins": "auto", "musica": None, "cenas": cenas})
    print("ok -> %s (%d cenas, %d batidas)" % (alvo, len(cenas), sum(len(c.get("beats", [])) for c in cenas)))


if __name__ == "__main__":
    main()
