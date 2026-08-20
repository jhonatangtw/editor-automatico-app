#!/usr/bin/env python3
"""
Gera o comando ffmpeg que monta o criativo: body com punch-ins + inserts de B-roll
+ overlay de legenda (+ opcionalmente flash e whoosh nos cortes).

  python3 montar.py --config edicao.json > build.sh && bash build.sh

Formato do edicao.json em references/config.md.

Cuidados embutidos (todos vieram de bug real):
  - setsar=1 em todo segmento, senao o concat quebra com SAR nao-quadrado
  - blend screen convertido para gbrp e de volta, senao o video inteiro fica magenta
  - camada de flash montada com tpad, nao com overlay+enable (que vaza o efeito)
"""
import argparse, json, sys


def build(c):
    body = c["body"]
    dur = float(c["duracao"])
    W, H = c.get("largura", 1080), c.get("altura", 1920)
    segs = c.get("punch", [])          # [[ini, fim, escala], ...] cobrindo 0..dur
    broll = c.get("inserts", [])       # [{arquivo, inicio, fim}, ...]
    legenda = c.get("legenda")         # .mov com alpha
    overlays = c.get("overlays", [])   # outros .mov com alpha (lettering etc), em ordem
    flash = c.get("flash")             # {arquivo, in, out, lead} ou null
    sfx = c.get("sfx")                 # {arquivo, lead, volume} ou null
    saida = c["saida"]

    if not segs:
        segs = [[0, dur, 1.0]]
    if abs(segs[0][0]) > 1e-6:
        sys.exit("ERRO: o primeiro segmento de punch precisa comecar em 0 (comeca em %s)" % segs[0][0])
    if abs(segs[-1][1] - dur) > 0.05:
        sys.exit("ERRO: o ultimo segmento de punch termina em %s, mas a duracao e %s"
                 % (segs[-1][1], dur))
    for i in range(len(segs) - 1):
        if abs(segs[i][1] - segs[i + 1][0]) > 1e-6:
            sys.exit("ERRO: buraco/sobreposicao no punch entre %s e %s — os segmentos precisam "
                     "ser contiguos, senao o concat perde ou duplica frames"
                     % (segs[i][1], segs[i + 1][0]))
        if segs[i][1] <= segs[i][0]:
            sys.exit("ERRO: segmento de punch invalido: %s" % segs[i])

    ins, f = [f'-i "{body}"'], []

    # --- body em segmentos, com punch-in por escala ---
    for i, (a, b, z) in enumerate(segs):
        if abs(z - 1.0) < 1e-6:
            f.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,setsar=1[s{i}]")
        else:
            w = 2 * round(W * z / 2); h = 2 * round(H * z / 2)
            f.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={w}:{h},"
                     f"crop={W}:{H}:{(w-W)//2}:{(h-H)//2},setsar=1[s{i}]")
    f.append("".join(f"[s{i}]" for i in range(len(segs))) +
             f"concat=n={len(segs)}:v=1:a=0[body]")

    # --- inserts de B-roll ---
    cur = "body"
    for j, b in enumerate(broll):
        idx = len(ins); ins.append(f'-i "{b["arquivo"]}"')
        st, en = float(b["inicio"]), float(b["fim"])
        f.append(f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                 f"setsar=1,setpts=PTS-STARTPTS+{st}/TB[b{j}]")
        f.append(f"[{cur}][b{j}]overlay=0:0:enable='between(t,{st},{en})'[v{j}]")
        cur = f"v{j}"

    cortes = [float(b["inicio"]) for b in broll]

    # --- flash nos cortes (opcional) ---
    if flash and cortes:
        fi, fo = float(flash.get("in", 0.20)), float(flash.get("out", 0.62))
        lead = float(flash.get("lead", 0.12))
        fdur = fo - fi
        idx = len(ins); ins.append(f'-i "{flash["arquivo"]}"')
        f.append(f"[{cur}]format=gbrp[mn0]")   # screen so e neutro com preto em RGB
        f.append(f"[{idx}:v]split={len(cortes)}" + "".join(f"[fs{k}]" for k in range(len(cortes))))
        cur = "mn0"
        for k, ct in enumerate(cortes):
            pre = round(ct - lead, 3); post = round(dur - pre - fdur, 3)
            if pre < 0 or post < 0:
                sys.exit(f"ERRO: flash do corte {ct}s cai fora do video")
            f.append(f"[fs{k}]trim={fi}:{fo},setpts=PTS-STARTPTS,scale={W}:{H},setsar=1,"
                     f"format=gbrp,tpad=start_duration={pre}:stop_duration={post}:color=black[fl{k}]")
            f.append(f"[{cur}][fl{k}]blend=all_mode=screen:shortest=1[mn{k+1}]")
            cur = f"mn{k+1}"
        f.append(f"[{cur}]format=yuv420p[vfx]")
        cur = "vfx"

    # --- overlays com alpha por cima de tudo (nunca antes do flash, senao estouram junto) ---
    # ordem: legenda primeiro, lettering depois — lettering e o elemento de destaque
    camadas = ([legenda] if legenda else []) + list(overlays)
    for n, cam in enumerate(camadas):
        idx = len(ins); ins.append(f'-i "{cam}"')
        alvo = "vout" if n == len(camadas) - 1 else f"ov{n}"
        f.append(f"[{cur}][{idx}:v]overlay=0:0[{alvo}]")
        cur = alvo
    if not camadas:
        f.append(f"[{cur}]null[vout]")

    # --- audio ---
    if sfx and cortes:
        idx = len(ins); ins.append(f'-i "{sfx["arquivo"]}"')
        lead = float(sfx.get("lead", 0.30)); vol = float(sfx.get("volume", 0.60))
        f.append(f"[{idx}:a]asplit={len(cortes)}" + "".join(f"[as{k}]" for k in range(len(cortes))))
        for k, ct in enumerate(cortes):
            d = int(max(0, ct - lead) * 1000)
            f.append(f"[as{k}]volume={vol},adelay={d}|{d}[sx{k}]")
        f.append("[0:a]" + "".join(f"[sx{k}]" for k in range(len(cortes))) +
                 f"amix=inputs={len(cortes)+1}:duration=first:normalize=0[aout]")
        amap = '-map "[aout]"'
    else:
        amap = "-map 0:a"

    return (f'ffmpeg -v error {" ".join(ins)} \\\n -filter_complex "{";".join(f)}" \\\n'
            f' -map "[vout]" {amap} -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \\\n'
            f' -c:a aac -b:a 192k -movflags +faststart -t {dur} "{saida}" -y')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    a = ap.parse_args()
    print(build(json.load(open(a.config))))
