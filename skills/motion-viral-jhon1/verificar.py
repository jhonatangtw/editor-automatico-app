#!/usr/bin/env python3
"""Verificação de instalação da MOTION-VIRAL-JHON1. Rode antes do primeiro projeto."""
import os, shutil, subprocess, sys
from pathlib import Path

S = Path(__file__).resolve().parent
G, R, Y, Z = "\033[32m", "\033[31m", "\033[33m", "\033[0m"
faltas = []
def ok(m):    print(f"  {G}ok{Z}    {m}")
def erro(m):  print(f"  {R}FALTA{Z} {m}"); faltas.append(m)
def aviso(m): print(f"  {Y}aviso{Z} {m}")

print(f"MOTION-VIRAL-JHON1 — verificação\n  skill em {S}")

print("\npython")
(ok if sys.version_info >= (3, 9) else erro)(f"python {sys.version_info.major}.{sys.version_info.minor}")

print("\nbibliotecas")
for mod, nome in (("PIL", "Pillow"), ("numpy", "numpy"), ("cv2", "opencv-python")):
    try:
        __import__(mod); ok(nome)
    except Exception as e:
        erro(f"{nome} ({e.__class__.__name__})")
try:
    __import__("faster_whisper"); ok("faster-whisper")
except Exception:
    erro("faster-whisper — sem ela não há transcript por palavra, e sem transcript não há motion ancorado")

print("\nferramentas")
for b in ("ffmpeg", "ffprobe"):
    p = shutil.which(b)
    ok(f"{b}  {p}") if p else erro(b)
p = shutil.which("yt-dlp")
ok(f"yt-dlp  {p}") if p else aviso("yt-dlp ausente — só faz falta para baixar vídeo de referência")
p = shutil.which("higgsfield")
ok(f"higgsfield  {p}") if p else aviso("higgsfield CLI ausente — só faz falta para gerar asset novo")

print("\nafter effects")
apps = sorted(Path("/Applications").glob("Adobe After Effects *"))
if apps:
    ok(f"{apps[-1].name}")
    ae = apps[-1] / "aerender"
    ok(f"aerender  {ae}") if ae.exists() else erro("aerender não encontrado dentro do app")
    rodando = subprocess.run(["pgrep", "-f", "Adobe After Effects"], capture_output=True).returncode == 0
    (ok if rodando else aviso)("AE rodando" if rodando else "AE fechado — a skill escreve no projeto ABERTO pelo usuário")
else:
    erro("After Effects não encontrado em /Applications")

print("\nkit que viaja com a skill")
fontes = sorted((S / "fontes").glob("*.ttf"))
(ok if len(fontes) >= 10 else erro)(f"{len(fontes)} fontes em fontes/ (esperado 10)")
inst = Path.home() / "Library/Fonts"
faltando = [f.name for f in fontes if not (inst / f.name).exists()]
if faltando:
    aviso(f"{len(faltando)} fonte(s) não instaladas no sistema: cp fontes/*.ttf ~/Library/Fonts/")
else:
    ok("fontes instaladas em ~/Library/Fonts")
for f in ("lib/ae_lib.jsx", "lib/ae_podcast.jsx", "lib/render.sh", "lib/rodar.sh", "lib/voz_jhon.sh", "lib/conferir_voz.py",
          "lib/conferir_render.py", "lib/recortar_gradiente.py", "IDENTIDADE.md",
          "references/armadilhas-extendscript.md", "references/voz-e-legenda.md",
          "references/transicoes-e-fundo.md", "references/prompts-asset.md", "references/formato-podcast-split.md",
          "exemplo/01_setup.jsx", "exemplo/02_cena_cutaway.jsx", "exemplo/03_podcast_body.jsx", "exemplo/04_dopa_lettering.jsx"):
    (ok if (S / f).exists() else erro)(f)
for f in ("lib/rodar.sh", "lib/voz_jhon.sh", "lib/render.sh"):
    p = S / f
    if p.exists() and not os.access(p, os.X_OK):
        erro(f"{f} sem permissão de execução (chmod +x)")

print("\nbiblioteca")
src = (S / "lib/ae_lib.jsx").read_text()
n = src.count("function ")
(ok if n >= 60 else erro)(f"ae_lib.jsx com {n} funções")
for fn in ("premiumBG", "sweep", "dashedCircle", "drawIn", "blockIn", "placeInMain", "report", "frame"):
    (ok if f"function {fn}(" in src else erro)(f"ae_lib.jsx: {fn}()")
(ok if "SCRATCH" not in src else erro)("ae_lib.jsx sem caminho fixo de sessão")
src2 = (S / "lib/ae_podcast.jsx").read_text() if (S / "lib/ae_podcast.jsx").exists() else ""
n2 = src2.count("function ")
(ok if n2 >= 30 else erro)(f"ae_podcast.jsx com {n2} funções")
for fn in ("cardPhoto", "split", "reenquadrar", "fundoSobCartao", "legendasCaixa", "legendasPremium", "camera3D", "cenaDopa", "cenaEditorial", "revelaLetras"):
    (ok if f"function {fn}(" in src2 else erro)(f"ae_podcast.jsx: {fn}()")

print("\nvoz")
env = Path.home() / ".config/hw-creative/.env"
if env.exists():
    chave = "ELEVENLABS_API_KEY" in env.read_text()
    (ok if chave else erro)(f"ELEVENLABS_API_KEY em {env}")
else:
    erro(f"{env} não existe — sem ela a troca de voz não roda")

print()
if faltas:
    print(f"{R}{len(faltas)} item(ns) faltando.{Z} Resolva antes de começar."); sys.exit(1)
print(f"{G}Pronto para rodar.{Z}")
