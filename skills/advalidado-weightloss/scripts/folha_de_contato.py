#!/usr/bin/env python3
"""Folha de contato do b-roll: miniatura + id + tempo + fala. Sai em broll/folha_de_contato.jpg."""
import json, os, textwrap
from PIL import Image, ImageDraw, ImageFont
B = os.path.dirname(os.path.abspath(__file__)); plano = json.load(open(os.path.join(B, "plano.json")))
tk = set(json.load(open(os.path.join(B, "tiktok_escolhidos.json")))) if os.path.exists(os.path.join(B, "tiktok_escolhidos.json")) else set()
W, H, COLS, TXT = 300, 533, 8, 120
def fonte(t):
    for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try: return ImageFont.truetype(f, t)
        except OSError: pass
    return ImageFont.load_default()
F1, F2 = fonte(22), fonte(17)
linhas = -(-len(plano) // COLS)
folha = Image.new("RGB", (COLS * W, linhas * (H + TXT)), (18, 18, 22)); d = ImageDraw.Draw(folha)
for k, p in enumerate(plano):
    x, y = (k % COLS) * W, (k // COLS) * (H + TXT)
    org = p["id"] in tk
    f = os.path.join(B, "tiktok", "quadros", p["id"] + ".jpg") if org else os.path.join(B, "imagens", p["id"] + ".png")
    if os.path.exists(f):
        im = Image.open(f).convert("RGB"); im.thumbnail((W - 6, H - 6)); folha.paste(im, (x + 3, y + 3))
    else:
        d.rectangle([x + 3, y + 3, x + W - 3, y + H - 3], outline=(200, 60, 60), width=3); d.text((x + 20, y + H // 2), "FALTA", font=F1, fill=(200, 60, 60))
    d.rectangle([x + 8, y + 10, x + 92, y + 38], fill=(0, 160, 120) if org else (90, 70, 200)); d.text((x + 14, y + 13), "TIKTOK" if org else "IA", font=F1, fill=(255, 255, 255))
    d.text((x + 8, y + H + 4), f"{p['id']}  ·  {p['tempo']}s", font=F1, fill=(255, 190, 60))
    for i, l in enumerate(textwrap.wrap("“" + p["fala"] + "”", 33)[:4]):
        d.text((x + 8, y + H + 32 + i * 20), l, font=F2, fill=(230, 230, 235))
out = os.path.join(B, "folha_de_contato.jpg"); folha.save(out, quality=88); print(out, folha.size)
