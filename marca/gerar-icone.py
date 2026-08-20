#!/usr/bin/env python3
"""
Desenha o ícone do app: uma faixa preta amarrada, sobre o dourado da marca.

Por que preto SOBRE dourado, e não o contrário: no Dock e na barra de tarefas o
ícone aparece em cima de fundos claros e escuros que não escolhemos. Ícone
predominantemente preto vira um borrão sem forma no escuro. O dourado dá o
recorte, e a faixa preta é a figura — reconhecível a 32 px, que é o tamanho em
que ele vai ser visto de verdade.

    python3 marca/gerar-icone.py     → marca/icone.png, .icns e .ico
"""
import os
import struct
import subprocess

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
L = 1024
OURO_CLARO = (226, 190, 96)
OURO = (198, 158, 62)
OURO_ESCURO = (150, 116, 36)
PRETO = (11, 12, 14)
PRETO_2 = (26, 28, 32)


def fundo(img):
    """Quadrado arredondado com leve degradê — plano, mas não chapado."""
    d = ImageDraw.Draw(img)
    for y in range(L):
        t = y / L
        c = tuple(int(OURO_CLARO[i] + (OURO_ESCURO[i] - OURO_CLARO[i]) * t)
                  for i in range(3))
        d.line([(0, y), (L, y)], fill=c)
    # máscara de canto arredondado no padrão da Apple (~22% do lado)
    mascara = Image.new("L", (L, L), 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, L - 1, L - 1],
                                              radius=int(L * 0.225), fill=255)
    saida = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    saida.paste(img, (0, 0), mascara)
    return saida


def _peca(tam, cor, raio, angulo, corte=0):
    """Desenha um retângulo arredondado numa camada própria e gira.

    Girar é o que separa "faixa amarrada" de "banquinho": ponta de faixa cai
    torta, e o nó fica levemente inclinado. Sem isso a primeira versão do ícone
    ficou parecendo um móvel de três pernas."""
    lar, alt = tam
    folga = int(max(lar, alt) * 0.9)
    camada = Image.new("RGBA", (lar + folga, alt + folga), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    x0, y0 = folga // 2, folga // 2
    d.rounded_rectangle([x0, y0, x0 + lar, y0 + alt], radius=raio, fill=cor)
    if corte:
        # ponta cortada na diagonal, como faixa de verdade
        d.polygon([(x0, y0 + alt), (x0 + lar, y0 + alt),
                   (x0 + lar, y0 + alt - corte)], fill=(0, 0, 0, 0))
    return camada.rotate(angulo, resample=Image.BICUBIC, expand=False)


def faixa(img):
    meio = L // 2
    cintura = int(L * 0.44)          # a faixa fica acima do centro: sobra para as pontas
    alt = int(L * 0.145)

    # --- pontas penduradas, ATRÁS do nó
    for lado, ang in ((-1, 7), (1, -7)):
        larg, comp = int(L * 0.076), int(L * 0.265)
        peca = _peca((larg, comp), PRETO, int(L * 0.014), ang, corte=int(L * 0.055))
        x = meio + lado * int(L * 0.078) - peca.width // 2
        y = cintura + int(alt * 0.15) - peca.height // 2 + comp // 2
        img.alpha_composite(peca, (x, y))

    # --- a faixa em volta do corpo
    d = ImageDraw.Draw(img)
    y0 = cintura - alt // 2
    d.rectangle([-10, y0, L + 10, y0 + alt], fill=PRETO)
    d.rectangle([-10, y0, L + 10, y0 + int(alt * 0.15)], fill=PRETO_2)

    # --- o nó: largo e inclinado, por cima de tudo
    nl, na = int(L * 0.265), int(alt * 1.42)
    no = _peca((nl, na), PRETO, int(L * 0.026), -6)
    img.alpha_composite(no, (meio - no.width // 2, cintura - no.height // 2))

    # --- o vinco dourado do nó: é ele que faz a forma existir a 32 px
    d = ImageDraw.Draw(img)
    larg_linha = max(4, int(L * 0.017))
    dy = int(L * 0.016)
    d.line([(meio - int(nl * 0.42), cintura + dy + int(L * 0.012)),
            (meio + int(nl * 0.42), cintura + dy - int(L * 0.020))],
           fill=OURO, width=larg_linha)
    return img


def png():
    img = fundo(Image.new("RGB", (L, L), OURO)).convert("RGBA")
    img = faixa(img)
    alvo = os.path.join(AQUI, "icone.png")
    img.save(alvo)
    return alvo, img


def icns(img):
    """iconutil é o caminho nativo do macOS — e o único que a Apple garante."""
    pasta = os.path.join(AQUI, "icone.iconset")
    os.makedirs(pasta, exist_ok=True)
    for tam in (16, 32, 128, 256, 512):
        img.resize((tam, tam), Image.LANCZOS).save(
            os.path.join(pasta, "icon_%dx%d.png" % (tam, tam)))
        img.resize((tam * 2, tam * 2), Image.LANCZOS).save(
            os.path.join(pasta, "icon_%dx%d@2x.png" % (tam, tam)))
    alvo = os.path.join(AQUI, "icone.icns")
    subprocess.run(["iconutil", "-c", "icns", pasta, "-o", alvo], check=True)
    return alvo


def ico(img):
    """ICO com PNG dentro (Vista+). O Pillow escreve; só cuidamos dos tamanhos
    que o Windows realmente usa."""
    alvo = os.path.join(AQUI, "icone.ico")
    img.save(alvo, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                          (64, 64), (128, 128), (256, 256)])
    return alvo


if __name__ == "__main__":
    caminho, img = png()
    print("png :", caminho)
    print("icns:", icns(img))
    print("ico :", ico(img))
