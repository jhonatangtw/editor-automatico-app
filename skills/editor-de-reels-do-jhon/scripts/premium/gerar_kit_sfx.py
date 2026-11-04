#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera um kit de SFX neutro, SINTETIZADO no ffmpeg (sem licença de terceiros).

    python3 scripts/premium/gerar_kit_sfx.py PASTA_DO_PROJETO/assets/sfx

Cria whoosh, whoosh-soft, impact-soft, tick, shimmer, success-chime, riser e
swell-out (.mp3). Servem para o vídeo funcionar já na primeira rodada; se você
tem um kit próprio com licença, ponha os arquivos com ESSES nomes na pasta
(ou mude os nomes em sfx-cues.json). Não sobrescreve o que já existe, a não ser com --forcar.
"""
import os
import subprocess
import sys

KIT = {
    # ruído filtrado com varredura de frequência: "passou"
    "whoosh": "anoisesrc=d=0.55:c=pink:a=0.9,highpass=f=300,lowpass=f=5000,"
              "afade=t=in:d=0.22:curve=exp,afade=t=out:st=0.25:d=0.3:curve=exp,volume=0.9",
    "whoosh-soft": "anoisesrc=d=0.45:c=pink:a=0.6,highpass=f=500,lowpass=f=3200,"
                   "afade=t=in:d=0.18:curve=exp,afade=t=out:st=0.2:d=0.25,volume=0.7",
    # baque grave curto
    "impact-soft": "sine=f=58:d=0.6,volume=1.6,afade=t=out:st=0.03:d=0.55:curve=exp[a];"
                   "anoisesrc=d=0.12:c=brown:a=0.8,lowpass=f=900,afade=t=out:d=0.12[b];[a][b]amix=inputs=2:normalize=0",
    # clique de interface
    "tick": "sine=f=2400:d=0.05,afade=t=out:d=0.05:curve=exp,volume=0.5",
    # brilho: três senoides agudas
    "shimmer": "sine=f=2637:d=0.9,volume=0.25[a];sine=f=3520:d=0.9,volume=0.18[b];sine=f=4186:d=0.9,volume=0.12[c];"
               "[a][b][c]amix=inputs=3:normalize=0,tremolo=f=14:d=0.5,afade=t=in:d=0.04,afade=t=out:st=0.2:d=0.7",
    # "deu certo": duas notas
    "success-chime": "sine=f=1046.5:d=0.7,afade=t=out:st=0.05:d=0.6,volume=0.5[a];"
                     "sine=f=1568:d=0.7,adelay=110|110,afade=t=out:st=0.15:d=0.55,volume=0.45[b];[a][b]amix=inputs=2:normalize=0",
    # subida de tensão (1,8 s) que termina na batida
    "riser": "anoisesrc=d=1.8:c=white:a=0.5,highpass=f=800,lowpass=f=7000,afade=t=in:d=1.7:curve=qsin,"
             "afade=t=out:st=1.72:d=0.08,volume=0.6",
    # fecho do vídeo
    "swell-out": "anoisesrc=d=0.8:c=pink:a=0.5,lowpass=f=2500,afade=t=in:d=0.3,afade=t=out:st=0.35:d=0.45,volume=0.6",
}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = sys.argv[1]
    forcar = "--forcar" in sys.argv
    os.makedirs(out, exist_ok=True)
    for nome, grafo in KIT.items():
        dst = os.path.join(out, nome + ".mp3")
        if os.path.exists(dst) and not forcar:
            print("  já existe:", nome)
            continue
        fc = grafo if "[" in grafo else None
        cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y"]
        if fc:
            cmd += ["-filter_complex", fc + ",aformat=sample_rates=48000:channel_layouts=stereo"]
        else:
            cmd += ["-f", "lavfi", "-i", grafo + ",aformat=sample_rates=48000:channel_layouts=stereo"]
        cmd += ["-c:a", "libmp3lame", "-b:a", "192k", dst]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            sys.exit("x %s: %s" % (nome, r.stderr[-300:]))
        print("  ok:", nome)


if __name__ == "__main__":
    main()
