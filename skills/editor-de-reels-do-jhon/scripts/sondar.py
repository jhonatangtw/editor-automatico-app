#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lê o bruto (ou o corte) e diz o que ele é antes de qualquer edição.

    python3 scripts/sondar.py "bruto.MOV"

Aponta: vertical/horizontal, rotação de celular, fps, HDR (HLG/PQ do iPhone),
duração e o que isso muda nas próximas fases. Não altera o arquivo.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comum import info_video  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
i = info_video(sys.argv[1])
print(json.dumps(i, ensure_ascii=False, indent=1))
print()
vert = i["altura"] > i["largura"]
print("- formato:", "VERTICAL" if vert else "HORIZONTAL", "%dx%d" % (i["largura"], i["altura"]),
      "(rotação de celular %d° — o Premiere e o ffmpeg já desviram)" % i["rotacao"] if i["rotacao"] else "")
if i["hdr"]:
    print("- COR: HDR %s (iPhone/celular). No Premiere a sequência vai herdar Rec.2100 e o Reels fica claro/lavado." % i["hdr"].upper())
    print("  -> Fase 3: espaço de trabalho Rec.709 + tone map automático (scripts/premiere/montar.py cor).")
    print("  -> Prévias pelo ffmpeg usam só uma aproximação (eq); a cor que vale é a do Premiere.")
else:
    print("- cor: SDR (%s) — nada a converter." % (i["transfer"] or "sem etiqueta"))
if i["fps"] > 31:
    print("- %.2f fps: o Reels final sai em 30 fps; a edição premium usa um proxy 30 fps." % i["fps"])
if not i["audio"]:
    print("- ATENÇÃO: sem trilha de áudio — não dá pra decupar pela fala.")
print("- duração: %.1f s" % i["duracao"])
