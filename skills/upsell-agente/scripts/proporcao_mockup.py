#!/usr/bin/env python3
"""Mede a proporção altura/largura do frasco no mockup oficial (PNG com alfa) — é a régua para aceitar
ou refazer cada still de IA com o produto (aceitar ±8%; MarcaE = 1,79).
    python3 proporcao_mockup.py <mockup_1_frasco.png>
No still gerado, meça o frasco mais frontal (bbox com tampa) e compare. Deitado/inclinado: compare
largura da tampa ÷ largura do corpo (MarcaE 0,82).
"""
import sys
from PIL import Image
import numpy as np

im = Image.open(sys.argv[1]).convert("RGBA")
a = np.asarray(im)[..., 3] > 20
x0, y0, x1, y1 = Image.fromarray(a.astype("uint8") * 255).getbbox()
w, h = x1 - x0, y1 - y0
print(f"bbox {w}x{h} px · altura/largura = {h / w:.2f}")
# largura da tampa (faixa do topo) vs corpo
linhas = [a[y, x0:x1].sum() for y in range(y0, y1)]
tampa = max(linhas[: max(1, len(linhas) // 5)]); corpo = max(linhas)
print(f"tampa/corpo = {tampa / corpo:.2f}")
