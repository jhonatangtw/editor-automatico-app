#!/usr/bin/env python3
"""Prepara os ativos do Upsell #1 MarcaE para o HyperFrames (4:3 1440x1080, 25 fps).

Tudo sai em hyperframes/up1-MarcaE/assets/. Idempotente: pula o que já existe
(apague o arquivo de saída para refazer). Rodar: python3 edicao/prep_up1.py [grupo...]
grupos: sfx music susan dep mf tt mosaic grain
"""
import os, sys, subprocess, json
from concurrent.futures import ThreadPoolExecutor

J = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(J, "hyperframes", "up1-MarcaE", "assets")
RAW = os.path.join(A, "raw")
SCR = os.path.join(J, "broll", "acervo")  # cópia LOCAL do b-roll de acervo (nunca o scratchpad)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print("ERRO", " ".join(cmd)[:200], r.stderr[-600:])
    return r

def ff(args, out):
    if os.path.exists(out):
        return
    run(["ffmpeg", "-v", "error", "-y"] + args + [out])
    print("ok", os.path.relpath(out, A))

V264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-r", "25"]
AAC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
GRADE_AV = "eq=contrast=1.03:saturation=0.97:gamma=0.99"
GRADE_MF = "eq=contrast=1.02:saturation=0.90:gamma=1.0"
GRADE_TT = "eq=contrast=1.04:saturation=0.95:brightness=0.005"

# ---------------- SFX ----------------
SFX = {  # nome: (arquivo do Baú, início, duração)
    "whoosh": ("clean-fast-swooshaiff-14784.mp3", 0.0, 0.98),
    "whoosh2": ("Golden swoosh.mp3", 0.0, 1.27),
    "pop": ("ES_Suction Pop 5 - SFX Producer.mp3", 0.0, 0.6),
    "click": ("Mouse Click Sound Effect.mp3", None, 0.35),
    "ding": ("Ding.mp3", 0.0, 2.2),
    "cash": ("Cash Register.mp3", 0.0, 1.8),
    "riser": ("woosh-building-109596.mp3", 0.0, 2.58),
}

def onset(path):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=n=-40dB:d=0.02", "-f", "null", "-"])
    for l in r.stderr.splitlines():
        if "silence_end" in l:
            return max(0.0, float(l.split("silence_end:")[1].split("|")[0]) - 0.01)
    return 0.0

def sfx():
    os.makedirs(os.path.join(A, "sfx"), exist_ok=True)
    for nome, (src, ini, dur) in SFX.items():
        p = os.path.join(RAW, src)
        if ini is None:
            ini = onset(p)
        tmp = os.path.join(A, "sfx", nome + "_t.wav")
        out = os.path.join(A, "sfx", nome + ".mp3")
        if os.path.exists(out):
            continue
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(ini), "-t", str(dur), "-i", p, "-ac", "2", "-ar", "48000",
             "-af", f"afade=t=out:st={max(0, dur - 0.12)}:d=0.12", tmp])
        # pico em -3 dBFS para os volumes do build serem comparáveis
        r = run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "volumedetect", "-f", "null", "-"])
        mx = [l for l in r.stderr.splitlines() if "max_volume" in l]
        g = -3.0 - float(mx[0].split(":")[1].split()[0]) if mx else 0
        run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"volume={g}dB", "-c:a", "libmp3lame", "-b:a", "192k", out])
        os.remove(tmp)
        print("ok sfx", nome, f"{g:+.1f} dB")

# ---------------- trilha ----------------
MUSICA = [
    "🙏 Música de fundo para vídeos de esperança, hope music! [9d7pQ0ODAgU].mp3",
    "2.Inspiring Cellos_mp3.mp3",
    "Documentary.mp3",
    "The Cello.mp3",
    "🙏 Música de fundo para vídeos de esperança, hope music! [9d7pQ0ODAgU].mp3",
]

def music():
    out = os.path.join(A, "music", "bed.m4a")
    if os.path.exists(out):
        return
    os.makedirs(os.path.join(A, "music"), exist_ok=True)
    ins, flt = [], []
    for i, m in enumerate(MUSICA):
        ins += ["-i", os.path.join(RAW, m)]
    # cada faixa normalizada separadamente, depois cadeia de crossfades de 3 s
    for i in range(len(MUSICA)):
        flt.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-36:TP=-9:LRA=9[m{i}]")
    cur = "m0"
    for i in range(1, len(MUSICA)):
        flt.append(f"[{cur}][m{i}]acrossfade=d=3:c1=tri:c2=tri[x{i}]")
        cur = f"x{i}"
    flt.append(f"[{cur}]atrim=0:760,afade=t=in:st=0:d=1.5[o]")
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(flt), "-map", "[o]", "-c:a", "aac", "-b:a", "192k", out])
    print("ok music bed")

# ---------------- Susan / depoentes ----------------
SUSAN = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "PRECO_A", "PRECO_B", "PRECO_C", "S08", "S09"]
DEP = ["D01_MARK", "D02_ELAINE", "D03_ROBERT", "D04_MARGARET", "D05_FRANK", "D06_NANCY", "D07_GEORGE",
       "D08_CAROL", "D09_WILLIAM", "D10_LINDA"]

def jobs_av():
    js = []
    for s in SUSAN:
        src = os.path.join(J, "ia", "susan", "blocos", f"SUSAN_{s}_v1.mp4")
        js.append((["-i", src, "-vf", f"crop=1440:1080:240:0,{GRADE_AV}"] + V264 + AAC, os.path.join(A, "susan", f"{s}.mp4")))
    src = os.path.join(J, "ia", "susan", "SUSAN_ACENO_kling_v1.mp4")
    js.append((["-ss", "0.9", "-i", src, "-an", "-vf", f"crop=1440:1080:240:0,{GRADE_AV},fps=25"] + V264, os.path.join(A, "susan", "ACENO.mp4")))
    for d in DEP:
        src = os.path.join(J, "ia", "depoentes", "video", f"{d}_avatar_v1.mp4")
        js.append((["-i", src, "-vf", f"crop=1440:1080:240:0,{GRADE_AV}"] + V264 + AAC, os.path.join(A, "dep", f"{d}.mp4")))
    return js

# ---------------- acervo MarcaB (1:1 -> 4:3) ----------------
MF = {  # arquivo: y do recorte 1080x810 dentro do 1080x1080
    "T01_hug": 60, "T05_meadow": 135, "T06_garden": 110, "T07_bee": 135, "T11_convertible_5s": 135,
    "T12_car_exit_5s": 120, "T13_door_greet": 135, "T14_sofa_grandson": 100, "I08_digestion": 135,
    "I10_tea": 100, "P_B04_supplier": 90, "T19_ship": 135, "P_B06_seedlings": 150, "T20_car_couple": 90,
    "T23_flowers": 90, "T24_pier": 135,
}

def jobs_mf():
    return [(["-i", os.path.join(SCR, f + ".mp4"), "-an", "-vf",
              f"crop=1080:810:0:{y},scale=1440:1080:flags=lanczos,setsar=1,{GRADE_MF}"] + V264,
             os.path.join(A, "mf", f + ".mp4")) for f, y in MF.items()]

def jobs_tt():
    d = os.path.join(J, "broll", "tiktok", "final")
    return [(["-i", os.path.join(d, f), "-an", "-vf", f"fps=25,{GRADE_TT}"] + V264, os.path.join(A, "tt", f))
            for f in sorted(os.listdir(d)) if f.endswith(".mp4")]

# ---------------- mosaico 3x3 dos depoentes ----------------
MOS = [("D01_MARK", 9), ("D02_ELAINE", 14), ("D03_ROBERT", 6), ("D04_MARGARET", 12), ("D05_FRANK", 3),
       ("D06_NANCY", 20), ("D07_GEORGE", 26), ("D08_CAROL", 16), ("D10_LINDA", 22)]

def mosaic():
    out = os.path.join(A, "img", "mosaico.mp4")
    if os.path.exists(out):
        return
    ins, flt = [], []
    for i, (d, t) in enumerate(MOS):
        ins += ["-ss", str(t), "-t", "4.5", "-i", os.path.join(J, "ia", "depoentes", "video", f"{d}_avatar_v1.mp4")]
        flt.append(f"[{i}:v]crop=1440:1080:240:0,scale=472:354,setsar=1,fps=25,{GRADE_AV}[v{i}]")
    lay = "|".join(f"{(i % 3) * 484}_{(i // 3) * 363}" for i in range(9))
    flt.append("".join(f"[v{i}]" for i in range(9)) + f"xstack=inputs=9:layout={lay}:fill=white[g]")
    flt.append("[g]pad=1440:1080:(ow-iw)/2:(oh-ih)/2:color=white[o]")
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(flt), "-map", "[o]", "-an"] + V264 + [out])
    print("ok mosaico")

# ---------------- grão (4 quadros num sprite) ----------------
def grain():
    out = os.path.join(A, "img", "grao.png")
    if os.path.exists(out):
        return
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x808080:s=720x540:d=0.2:r=20",
         "-vf", "noise=alls=26:allf=t,format=gray,tile=4x1", "-frames:v", "1", out])
    print("ok grao")

def paralelo(js, n=4):
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(lambda j: ff(*j), js))

if __name__ == "__main__":
    g = sys.argv[1:] or ["sfx", "music", "grain", "mosaic", "mf", "tt", "susan", "dep"]
    for d in ["susan", "dep", "mf", "tt", "img", "sfx", "music"]:
        os.makedirs(os.path.join(A, d), exist_ok=True)
    if "sfx" in g: sfx()
    if "music" in g: music()
    if "grain" in g: grain()
    if "mosaic" in g: mosaic()
    if "mf" in g: paralelo(jobs_mf())
    if "tt" in g: paralelo(jobs_tt())
    if "susan" in g or "dep" in g:
        js = jobs_av()
        if "susan" not in g: js = [j for j in js if "/dep/" in j[1]]
        if "dep" not in g: js = [j for j in js if "/dep/" not in j[1]]
        paralelo(js, 3)
