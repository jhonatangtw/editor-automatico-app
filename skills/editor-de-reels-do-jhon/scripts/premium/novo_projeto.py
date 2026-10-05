#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cria a pasta do projeto premium (HyperFrames) a partir do CORTE que o aluno exportou.

    python3 scripts/premium/novo_projeto.py --corte "Render/meu-corte.mp4" --pasta "Edicao premium" \
        [--telas "minhas-telas/"] [--musica "trilha.mp3"] [--marca marca.json] [--ini 0 --fim 15]

- o corte é só LIDO: nunca é alterado, movido ou renomeado;
- gera assets/video/fala.mp4 (proxy 1440x2560, 30 fps, Rec.709 — cobre punch-in
  de até 116 % em 1080 sem ampliar a imagem) e assets/audio/voz.wav (voz intacta);
- copia as telas/gravações do aluno para assets/telas (vídeo vira 30 fps com
  keyframe a cada quadro-segundo, para o render buscar o quadro certo);
- --ini/--fim fazem um trecho (teste rápido) sem tocar no corte inteiro.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
from comum import TEMPLATES, exigir, info_video, sair  # noqa: E402

VERSAO_HF = os.environ.get("HYPERFRAMES_VERSAO", "0.8.134")


def comando_hf():
    """O atalho do Editor Automático (versão fixa, Node certo) ou o npx."""
    pasta = os.environ.get("EDITOR_HF_BIN") or os.path.join(os.path.expanduser("~"), ".editorblackbelt", "bin")
    for n in ("hyperframes", "hyperframes.cmd"):
        a = os.path.join(pasta, n)
        if os.path.isfile(a):
            return '"%s"' % a
    return "npx --yes hyperframes@%s" % VERSAO_HF


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sair("falhou: %s\n%s" % (" ".join(cmd[:6]), r.stderr[-600:]))


def nome_limpo(n):
    base, ext = os.path.splitext(n)
    from comum import norm
    return (norm(base).replace(" ", "-") or "tela") + ext.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corte", required=True, help="o vídeo que o aluno exportou do Premiere (Rec.709)")
    ap.add_argument("--pasta", required=True)
    ap.add_argument("--telas", help="pasta com prints/gravações de tela do PRÓPRIO aluno")
    ap.add_argument("--musica", help="trilha com licença de uso (opcional)")
    ap.add_argument("--marca", help="marca.json próprio (padrão: Editor Black Belt)")
    ap.add_argument("--ini", type=float)
    ap.add_argument("--fim", type=float)
    a = ap.parse_args()
    exigir("ffmpeg")
    P = os.path.abspath(a.pasta)
    corte = os.path.abspath(a.corte)
    if os.path.dirname(corte) == P:
        sair("use uma pasta de projeto separada da pasta onde está o corte")
    inf = info_video(corte)
    if inf["hdr"]:
        sair("o corte está em HDR (%s). Exporte do Premiere em Rec.709 (fase 3 + 4) — senão a cor sai lavada." % inf["hdr"].upper())
    if inf["largura"] > inf["altura"]:
        print("! o corte é horizontal: vou preencher 9:16 cortando as laterais (cover).")
    for d in ("assets/video", "assets/audio", "assets/telas", "assets/sfx", "assets/fonts", "assets/musica", "compositions", "renders", "qc", "transcricao"):
        os.makedirs(os.path.join(P, d), exist_ok=True)
    corte_args = []
    if a.ini is not None:
        corte_args += ["-ss", "%.3f" % a.ini]
    if a.fim is not None:
        corte_args += ["-t", "%.3f" % (a.fim - (a.ini or 0))]
    print("proxy de vídeo 1440x2560 30 fps…", flush=True)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + corte_args + ["-i", corte, "-an",
         "-vf", "fps=30,scale=1440:2560:force_original_aspect_ratio=increase:flags=lanczos,crop=1440:2560,format=yuv420p",
         "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-x264-params", "keyint=30",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart",
         os.path.join(P, "assets/video/fala.mp4")])
    print("voz original (sem mexer)…", flush=True)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + corte_args + ["-i", corte, "-vn", "-c:a", "pcm_s24le", "-ar", "48000",
         os.path.join(P, "assets/audio/voz.wav")])
    if a.telas:
        for n in sorted(os.listdir(a.telas)):
            src = os.path.join(a.telas, n)
            if n.startswith(".") or not os.path.isfile(src):
                continue
            dst = os.path.join(P, "assets/telas", nome_limpo(n))
            ext = n.lower().rsplit(".", 1)[-1]
            if ext in ("png", "jpg", "jpeg", "webp"):
                shutil.copy2(src, dst)
            elif ext in ("mp4", "mov", "m4v", "webm"):
                dst = os.path.splitext(dst)[0] + ".mp4"
                run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-an", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                     "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst])
            else:
                continue
            print("  tela:", os.path.relpath(dst, P))
    if a.musica:
        dst = os.path.join(P, "assets/musica", nome_limpo(os.path.basename(a.musica)))
        shutil.copy2(a.musica, dst)
        print("  música:", os.path.relpath(dst, P), "(confira a licença de uso!)")
    if a.marca:
        shutil.copy2(a.marca, os.path.join(P, "marca.json"))
    nome = re.sub(r"[^a-z0-9-]+", "-", os.path.basename(P).lower()).strip("-") or "reels"
    open(os.path.join(P, "hyperframes.json"), "w").write('{\n  "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",\n'
                                                         '  "paths": { "blocks": "compositions", "components": "compositions/components", "assets": "assets" },\n'
                                                         '  "media": { "autoProxy": true }\n}\n')
    open(os.path.join(P, "meta.json"), "w").write('{"id": "%s", "name": "%s"}\n' % (nome, os.path.basename(P)))
    hf = comando_hf()
    pacote = {"name": nome, "private": True, "type": "module",
              "scripts": {"dev": hf + " preview", "check": hf + " check", "render": hf + " render"}}
    open(os.path.join(P, "package.json"), "w").write(json.dumps(pacote, ensure_ascii=False, indent=2) + "\n")
    if not os.path.exists(os.path.join(P, "roteiro.json")):
        shutil.copy2(os.path.join(TEMPLATES, "roteiro-exemplo.json"), os.path.join(P, "roteiro-exemplo.json"))
    print("ok -> %s\nPróximo: transcrever assets/audio/voz.wav, revisar a transcrição e escrever roteiro.json." % P)


if __name__ == "__main__":
    main()
