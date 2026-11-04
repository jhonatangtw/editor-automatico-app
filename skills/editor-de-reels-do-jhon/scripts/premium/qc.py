#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle de qualidade do Reels renderizado (roda sozinho no fim do renderizar.sh).

    python3 scripts/premium/qc.py "renders/X - premium.mp4" [--pasta PROJETO]

Confere e grava em qc/:
- formato: 1080x1920, 30 fps, H.264, áudio presente;
- loudness: -14 LUFS (±1) e true peak <= -1 dBTP;
- "lapso": trechos parados >= 0,25 s (freezedetect) — num Reels com punch-in e
  deriva constante, quadro congelado é defeito, não respiro;
- quadro preto;
- folha de contato com a ZONA SEGURA do Reels desenhada (vermelho = área que a
  interface do Instagram cobre): nada de texto importante dentro do vermelho.
Não altera o vídeo.
"""
import argparse
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from comum import info_video  # noqa: E402


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-nostdin"] + args, capture_output=True, text=True).stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--pasta")
    a = ap.parse_args()
    qc = os.path.join(a.pasta or os.path.dirname(os.path.abspath(a.video)), "qc")
    os.makedirs(qc, exist_ok=True)
    i = info_video(a.video)
    falhas, rel = [], {"arquivo": os.path.basename(a.video), "info": i}
    if (i["largura"], i["altura"]) != (1080, 1920):
        falhas.append("tamanho %dx%d (Reels = 1080x1920)" % (i["largura"], i["altura"]))
    if abs(i["fps"] - 30) > 0.05:
        falhas.append("%.2f fps (esperado 30)" % i["fps"])
    if not i["audio"]:
        falhas.append("sem áudio")
    e = ff(["-i", a.video, "-af", "ebur128=peak=true", "-f", "null", "-"])
    s = e[e.rfind("Summary"):]
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", s)[-1]) if i["audio"] else None
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", s)[-1]) if i["audio"] else None
    rel.update(lufs=lufs, true_peak=tp)
    if lufs is not None and abs(lufs + 14) > 1.0:
        falhas.append("loudness %.1f LUFS (alvo -14)" % lufs)
    if tp is not None and tp > -1.0:
        falhas.append("true peak %.1f dBTP (máx -1)" % tp)
    e = ff(["-i", a.video, "-vf", "freezedetect=n=0.0005:d=0.25", "-an", "-f", "null", "-"])
    ini = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", e)]
    dur = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", e)]
    lapsos = [[round(x, 2), round(d, 2)] for x, d in zip(ini, dur)]
    rel["lapsos"] = lapsos
    if lapsos:
        falhas.append("%d trecho(s) parado(s) >= 0,25 s: %s" % (len(lapsos), ", ".join("%.2f s (%.2f s)" % (x, d) for x, d in lapsos[:6])))
    e = ff(["-i", a.video, "-vf", "blackdetect=d=0.1:pix_th=0.06", "-an", "-f", "null", "-"])
    pretos = re.findall(r"black_start:([\d.]+)", e)
    rel["pretos"] = pretos
    if pretos:
        falhas.append("quadro preto em %s s" % ", ".join(pretos[:5]))
    # folha de contato com a zona segura (sem drawtext: só caixas)
    n = 12
    passo = max(0.5, i["duracao"] / n)
    caixa = ("drawbox=x=0:y=0:w=1080:h=192:color=red@0.28:t=fill,"
             "drawbox=x=0:y=1536:w=1080:h=384:color=red@0.28:t=fill,"
             "drawbox=x=960:y=900:w=120:h=636:color=red@0.28:t=fill")
    folha = os.path.join(qc, "folha-zona-segura.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf",
                    "fps=1/%.3f,%s,scale=270:480,tile=6x2" % (passo, caixa), "-frames:v", "1", "-update", "1", folha])
    rel["folha"] = folha
    rel["falhas"] = falhas
    json.dump(rel, open(os.path.join(qc, "qc.json"), "w"), ensure_ascii=False, indent=1)
    print("QC %s" % os.path.basename(a.video))
    print("  %dx%d · %.2f fps · %.2f s · %s LUFS · TP %s dBTP" % (i["largura"], i["altura"], i["fps"], i["duracao"], lufs, tp))
    print("  folha com zona segura:", folha, "(OLHE: texto não pode cair no vermelho)")
    if falhas:
        print("  REPROVADO em:")
        for f in falhas:
            print("   - " + f)
        sys.exit(1)
    print("  aprovado (formato, loudness, sem lapso, sem preto)")


if __name__ == "__main__":
    main()
