# -*- coding: utf-8 -*-
"""Sinaliza colagem, letterbox e rotacao nas imagens geradas.

    python3 qc_colagem.py /pasta/com/pngs

Falso positivo conhecido: desenho sobre papel (a borda do papel vira "emenda").
Olhe os sinalizados antes de refazer.
"""
import sys, os, glob
import numpy as np
from PIL import Image

def analisar(caminho):
    a = np.asarray(Image.open(caminho).convert("L").resize((256, 455))).astype(float)
    H = a.shape[0]
    d = np.abs(np.diff(a, axis=0)).mean(1)
    z = (d - np.median(d)) / (d.std() + 1e-6)
    costuras = [i for i in range(int(H * .10), int(H * .90)) if z[i] > 7.5]
    # agrupar costuras vizinhas
    grupos = []
    for i in costuras:
        if grupos and i - grupos[-1] < 8: continue
        grupos.append(i)
    linhas = a.mean(1)
    barra_topo = (linhas[:int(H * .06)] < 45).mean() > .7
    barra_base = (linhas[int(H * .94):] < 45).mean() > .7
    return grupos, barra_topo, barra_base

if __name__ == "__main__":
    pasta = sys.argv[1]
    susp = []
    arqs = sorted(glob.glob(os.path.join(pasta, "*.png")))
    for p in arqs:
        g, t, b = analisar(p)
        if g or t or b:
            k = os.path.basename(p)[:-4]
            susp.append(k)
            marca = []
            if g: marca.append(f"{len(g)+1} paineis?")
            if t: marca.append("barra topo")
            if b: marca.append("barra base")
            print(f"  {k:14s} {', '.join(marca)}")
    print(f"\nsuspeitos: {len(susp)} de {len(arqs)}")
    if susp: print(" ".join(susp))
