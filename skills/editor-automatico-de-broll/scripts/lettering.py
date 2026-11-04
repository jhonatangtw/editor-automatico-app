#!/usr/bin/env python3
"""
Lettering animado com glow -> overlay ProRes 4444 com alpha.

Reforca fala importante com tipografia grande, glow colorido e pop-in com overshoot.
Feito com PIL porque este ffmpeg nao tem drawtext/libass.

  python3 lettering.py --config lettering.json --out LETTERING.mov --dur 133.6

lettering.json:
[
  {"texto": "22 POUNDS\\nIN 12 DAYS", "inicio": 5.90, "fim": 8.10},
  {"texto": "100% NATURAL",           "inicio": 70.30, "fim": 72.30}
]

Cuidado de layout: y padrao 0.55 fica ACIMA da legenda (0.73) e ABAIXO do rosto,
que num enquadramento selfie 9:16 ocupa o terco superior. Mudar com criterio.
"""
import argparse, json, math, os, subprocess, tempfile

CANDIDATAS = [
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",          # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/ariblk.ttf",                                 # Windows
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",        # Linux
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def achar_fonte(preferida=None):
    """Fonte pesada pro lettering, com fallback por SO."""
    import os as _os
    for p in ([preferida] if preferida else []) + CANDIDATAS:
        if p and _os.path.exists(p):
            return p
    raise SystemExit("ERRO: nenhuma fonte encontrada. Passe --font com o caminho de uma .ttf bold.")


def ease_out(t):
    return 1 - (1 - t) ** 3


def estado(t, dur, t_in=0.18, t_settle=0.10, t_out=0.25):
    """Retorna (escala, opacidade) no instante t do lettering."""
    if t < t_in:                                    # pop com overshoot
        p = ease_out(t / t_in)
        return 0.75 + p * (1.06 - 0.75), min(1.0, p * 1.3)
    if t < t_in + t_settle:                         # assenta
        p = ease_out((t - t_in) / t_settle)
        return 1.06 - p * 0.06, 1.0
    if t > dur - t_out:                             # sai crescendo e sumindo
        p = (t - (dur - t_out)) / t_out
        return 1.0 + p * 0.08, max(0.0, 1.0 - p)
    return 1.0, 1.0


def render(cfg, saida, dur, W, H, font_path, size, y_frac, fps,
           cor_texto, cor_glow, glow_raio, glow_forca):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    f = ImageFont.truetype(font_path, size)
    tmp = tempfile.mkdtemp(prefix="lett_")
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(os.path.join(tmp, "blank.png"))

    linhas_concat, cursor, n_frames = [], 0.0, 0

    for idx, item in enumerate(sorted(cfg, key=lambda x: x["inicio"])):
        st, en = float(item["inicio"]), float(item["fim"])
        if st < cursor - 1e-6:
            raise SystemExit("ERRO: lettering %d comeca antes do anterior terminar" % idx)
        texto, d = item["texto"], en - st
        linhas = texto.split("\\n") if "\\n" in texto else texto.split("\n")

        if st > cursor + 1e-6:
            linhas_concat += ["file '%s/blank.png'" % tmp, "duration %.3f" % (st - cursor)]

        # canvas base do texto, em tamanho natural (escala aplicada depois)
        probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
        lh = int(size * 1.15)
        tw = int(max(probe.textlength(l, font=f) for l in linhas))
        th = lh * len(linhas)
        pad = glow_raio * 4
        base = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        db = ImageDraw.Draw(base)
        yy = pad
        for l in linhas:
            db.text(((base.width - db.textlength(l, font=f)) / 2, yy), l, font=f, fill=cor_texto)
            yy += lh

        # halo = copia borrada, tingida
        alpha = base.split()[3]
        halo = Image.new("RGBA", base.size, cor_glow)
        halo.putalpha(alpha.filter(ImageFilter.GaussianBlur(glow_raio)))

        nf = max(1, int(round(d * fps)))
        for k in range(nf):
            t = k / fps
            esc, op = estado(t, d)
            # pulso sutil no glow, pra nao ficar chapado
            pulso = 0.85 + 0.15 * math.sin(t * 6.0)
            frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            nw, nh = max(1, int(base.width * esc)), max(1, int(base.height * esc))
            g = halo.resize((nw, nh), Image.LANCZOS)
            b = base.resize((nw, nh), Image.LANCZOS)
            ga = g.split()[3].point(lambda v: int(v * glow_forca * pulso * op))
            g.putalpha(ga)
            ba = b.split()[3].point(lambda v: int(v * op))
            b.putalpha(ba)
            x0, y0 = (W - nw) // 2, int(H * y_frac) - nh // 2
            frame.alpha_composite(g, (x0, y0))
            frame.alpha_composite(b, (x0, y0))
            p = os.path.join(tmp, "l%02d_%04d.png" % (idx, k))
            frame.save(p)
            linhas_concat += ["file '%s'" % p, "duration %.4f" % (1.0 / fps)]
            n_frames += 1
        cursor = st + nf / fps

    if cursor < dur:
        linhas_concat += ["file '%s/blank.png'" % tmp, "duration %.3f" % (dur - cursor)]
    linhas_concat.append("file '%s/blank.png'" % tmp)

    lista = os.path.join(tmp, "concat.txt")
    open(lista, "w").write("\n".join(linhas_concat))
    subprocess.run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista,
        "-vf", "fps=%d,format=yuva444p10le" % fps,
        "-c:v", "prores_ks", "-profile:v", "4444", "-t", str(dur), saida, "-y"
    ], check=True)
    return len(cfg), n_frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--w", type=int, default=1080)
    ap.add_argument("--h", type=int, default=1920)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--size", type=int, default=96)
    ap.add_argument("--y", type=float, default=0.55)
    ap.add_argument("--font", default=None, help="caminho de uma .ttf bold; autodetecta se omitido")
    ap.add_argument("--glow", default="156,204,101", help="R,G,B do glow (padrao verde matcha)")
    ap.add_argument("--raio", type=int, default=22)
    ap.add_argument("--forca", type=float, default=0.95)
    a = ap.parse_args()

    glow = tuple(int(x) for x in a.glow.split(",")) + (255,)
    n, fr = render(json.load(open(a.config)), a.out, a.dur, a.w, a.h, achar_fonte(a.font),
                   a.size, a.y, a.fps, (255, 255, 255, 255), glow, a.raio, a.forca)
    print("lettering: %s (%d blocos, %d frames animados)" % (a.out, n, fr))


if __name__ == "__main__":
    main()
