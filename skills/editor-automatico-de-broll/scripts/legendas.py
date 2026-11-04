#!/usr/bin/env python3
"""
Whisper JSON -> SRT em frases curtas -> overlay ProRes 4444 com alpha.

Pilula branca de canto arredondado, texto preto, estilo UGC.
Existe porque este ffmpeg nao tem libass/drawtext — a legenda e desenhada com PIL.

  python3 legendas.py --json body.json --out legendas.srt \
                      --overlay LEGENDAS.mov --dur 133.6

Para so regerar o overlay a partir de um SRT ja corrigido a mao:
  python3 legendas.py --srt legendas.srt --overlay LEGENDAS.mov --dur 133.6
"""
import argparse, json, os, re, subprocess, sys, tempfile

CANDIDATAS = [
    "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",   # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/ARLRDBD.TTF",                                # Windows (Arial Rounded)
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",        # Linux
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def achar_fonte(preferida=None):
    """Fonte bold arredondada, com fallback por SO. Sem isso o script quebra fora do mac."""
    import os as _os
    for p in ([preferida] if preferida else []) + CANDIDATAS:
        if p and _os.path.exists(p):
            return p
    raise SystemExit(
        "ERRO: nenhuma fonte encontrada. Passe --font com o caminho de uma .ttf bold.\n"
        "Testei: " + "\n  ".join(CANDIDATAS))


FONT_PADRAO = None  # resolvido em runtime por achar_fonte()


def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = int(x % 60)
    ms = int(round((x - int(x)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def parse_ts(t):
    h, m, rest = t.split(":"); s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def agrupar(words, teto=4, dur_min=0.45, caixa="original"):
    """Quebra sempre apos . ! ? ; apos virgula se ja tem corpo; teto de N palavras."""
    grupos, cur = [], []
    for st, en, t in words:
        cur.append((st, en, t))
        if re.search(r"[.!?]$", t):
            grupos.append(cur); cur = []
        elif re.search(r"[,;:]$", t) and len(cur) >= 2:
            grupos.append(cur); cur = []
        elif len(cur) >= teto:
            grupos.append(cur); cur = []
    if cur:
        grupos.append(cur)

    # junta orfaos de 1 palavra com o vizinho curto anterior
    merged = []
    for g in grupos:
        if len(g) == 1 and merged and len(merged[-1]) <= 3:
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)

    blocos = []
    for g in merged:
        txt = re.sub(r"\s+", " ", " ".join(w[2] for w in g).strip())
        if caixa == "alta":
            txt = txt.upper()
        st, en = g[0][0], g[-1][1]
        if en - st < dur_min:
            en = st + dur_min
        blocos.append([st, en, txt])

    # CRITICO: clampar sobreposicao, senao dois blocos aparecem juntos e pisca
    for i in range(len(blocos) - 1):
        if blocos[i][1] > blocos[i + 1][0]:
            blocos[i][1] = blocos[i + 1][0]
    return blocos


def ler_srt(p):
    out = []
    for b in open(p).read().strip().split("\n\n"):
        L = b.strip().split("\n")
        if len(L) < 3:
            continue
        a, z = L[1].split(" --> ")
        out.append([parse_ts(a), parse_ts(z), " ".join(L[2:]).strip()])
    return out


def escrever_srt(blocos, p):
    open(p, "w").write("\n".join(
        "%d\n%s --> %s\n%s\n" % (i, ts(a), ts(b), t)
        for i, (a, b, t) in enumerate(blocos, 1)))


def render_overlay(blocos, saida, dur, W, H, font_path, size, cy_frac, maxw, fps):
    from PIL import Image, ImageDraw, ImageFont
    PADX, PADY, RADIUS = 30, 18, 20
    CY = int(H * cy_frac)
    f = ImageFont.truetype(font_path, size)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))

    def wrap(txt):
        linhas, cur = [], ""
        for w in txt.split():
            t = (cur + " " + w).strip()
            if probe.textlength(t, font=f) <= maxw - 2 * PADX:
                cur = t
            else:
                if cur:
                    linhas.append(cur)
                cur = w
        if cur:
            linhas.append(cur)
        return linhas

    tmp = tempfile.mkdtemp(prefix="caps_")
    for i, (st, en, txt) in enumerate(blocos):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        linhas = wrap(txt); lh = size + 12
        bw = int(max(d.textlength(l, font=f) for l in linhas)) + 2 * PADX
        bh = lh * len(linhas) + 2 * PADY - 12
        x0, y0 = (W - bw) // 2, CY - bh // 2
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=RADIUS, fill=(255, 255, 255, 255))
        y = y0 + PADY - 4
        for l in linhas:
            d.text(((W - d.textlength(l, font=f)) // 2, y), l, font=f, fill=(0, 0, 0, 255))
            y += lh
        img.save(os.path.join(tmp, "c%04d.png" % i))
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(os.path.join(tmp, "blank.png"))

    linhas, t = [], 0.0
    for i, (st, en, _) in enumerate(blocos):
        if st > t + 0.001:
            linhas += ["file '%s/blank.png'" % tmp, "duration %.3f" % (st - t)]
        linhas += ["file '%s/c%04d.png'" % (tmp, i), "duration %.3f" % max(en - st, 0.05)]
        t = en
    if t < dur:
        linhas += ["file '%s/blank.png'" % tmp, "duration %.3f" % (dur - t)]
    linhas.append("file '%s/blank.png'" % tmp)
    lista = os.path.join(tmp, "concat.txt")
    open(lista, "w").write("\n".join(linhas))

    # fps= no -vf (nao -vsync, que conflita com -r); prores 4444 carrega o alpha
    subprocess.run([
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista,
        "-vf", "fps=%d,format=yuva444p10le" % fps,
        "-c:v", "prores_ks", "-profile:v", "4444", "-t", str(dur), saida, "-y"
    ], check=True)
    return len(blocos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="JSON do Whisper com word_timestamps")
    ap.add_argument("--srt", help="SRT ja existente (pula o agrupamento)")
    ap.add_argument("--out", help="caminho do SRT de saida")
    ap.add_argument("--overlay", help="caminho do .mov de saida")
    ap.add_argument("--dur", type=float, required=True, help="duracao do video em segundos")
    ap.add_argument("--w", type=int, default=1080)
    ap.add_argument("--h", type=int, default=1920)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--size", type=int, default=60)
    ap.add_argument("--y", type=float, default=0.73, help="centro vertical, fracao da altura")
    ap.add_argument("--maxw", type=int, default=900)
    ap.add_argument("--font", default=None, help="caminho de uma .ttf bold; autodetecta se omitido")
    ap.add_argument("--teto", type=int, default=4, help="max de palavras por bloco")
    ap.add_argument("--caixa", choices=["original", "alta"], default="original",
                    help="'original' preserva o caso da copy (padrao); 'alta' converte pra CAIXA ALTA")
    ap.add_argument("--mute", action="append", default=[],
                    help='"INI-FIM" em segundos: suprime a legenda nessa janela. '
                         'Usar nas janelas de lettering — senao o mesmo texto aparece 2x na tela.')
    a = ap.parse_args()

    if a.srt:
        blocos = ler_srt(a.srt)
    elif a.json:
        d = json.load(open(a.json))
        words = [(w["start"], w["end"], w["word"].strip())
                 for s in d["segments"] for w in s.get("words", []) if w["word"].strip()]
        if not words:
            sys.exit("ERRO: JSON sem word timestamps. Rode o whisper com --word_timestamps True")
        blocos = agrupar(words, teto=a.teto, caixa=a.caixa)
    else:
        sys.exit("ERRO: passe --json ou --srt")

    if a.out:
        escrever_srt(blocos, a.out)
        print("SRT: %s (%d blocos)" % (a.out, len(blocos)))

    # o SRT em disco fica completo; so o OVERLAY perde os blocos mudos
    if a.mute:
        janelas = []
        for m in a.mute:
            ini, fim = m.split("-")
            janelas.append((float(ini), float(fim)))
        antes = len(blocos)
        blocos = [b for b in blocos
                  if not any(b[0] < f and b[1] > i for i, f in janelas)]
        print("mute: %d blocos suprimidos no overlay (%d janelas de lettering)"
              % (antes - len(blocos), len(janelas)))

    if a.overlay:
        n = render_overlay(blocos, a.overlay, a.dur, a.w, a.h,
                           achar_fonte(a.font), a.size, a.y, a.maxw, a.fps)
        print("overlay: %s (%d legendas)" % (a.overlay, n))

    if a.out:
        print("\n>>> Agora rode conferir_legenda.py contra a copy ANTES de montar.")


if __name__ == "__main__":
    main()
