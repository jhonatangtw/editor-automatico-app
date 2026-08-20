#!/usr/bin/env python3
"""
Confere o texto do SRT contra a copy oficial e corrige nome proprio / picote do Whisper.

O Whisper acerta o TIMING e erra o TEXTO. Nomes de marca sao os que mais escapam
(ja passou MOUNJARO -> "MANJARO" duas vezes num criativo so). Este script acha as
divergencias e opcionalmente aplica substituicoes, preservando o timing.

  # so listar as divergencias
  python3 conferir_legenda.py --srt legendas.srt --copy copy.txt

  # aplicar correcoes de termo
  python3 conferir_legenda.py --srt legendas.srt --copy copy.txt \
          --fix "MANJARO=MOUNJARO" --fix "100 %=100%" --aplicar
"""
import argparse, difflib, re, sys


def norm(s):
    s = re.sub(r"[^A-Za-z0-9%' ]", " ", s.upper())
    return [w for w in s.split() if w]


def parse_ts(t):
    h, m, rest = t.split(":"); s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = int(x % 60)
    ms = int(round((x - int(x)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def ler_srt(p):
    out = []
    for b in open(p).read().strip().split("\n\n"):
        L = b.strip().split("\n")
        if len(L) < 3:
            continue
        a, z = L[1].split(" --> ")
        out.append([parse_ts(a), parse_ts(z), " ".join(L[2:]).strip()])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--srt", required=True)
    ap.add_argument("--copy", required=True, help="txt com a copy oficial (a que foi GRAVADA)")
    ap.add_argument("--fix", action="append", default=[], help='"ERRADO=CERTO", repetivel')
    ap.add_argument("--aplicar", action="store_true", help="grava as correcoes no SRT")
    a = ap.parse_args()

    blocos = ler_srt(a.srt)
    doc = open(a.copy).read()

    D = norm(doc)
    C = norm(" ".join(b[2] for b in blocos))
    print("palavras na copy: %d | na legenda: %d\n" % (len(D), len(C)))

    div = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, D, C).get_opcodes():
        if tag != "equal":
            div += 1
            print("  %-8s copy=%-38s legenda=%s"
                  % (tag, " ".join(D[i1:i2])[:38] or "(nada)", " ".join(C[j1:j2])[:38] or "(nada)"))
    if not div:
        print("  nenhuma divergencia — legenda bate com a copy")

    if a.fix:
        n = 0
        for regra in a.fix:
            if "=" not in regra:
                sys.exit("ERRO: --fix precisa ser ERRADO=CERTO")
            err, cert = regra.split("=", 1)
            for b in blocos:
                if err in b[2]:
                    b[2] = b[2].replace(err, cert); n += 1
        print("\n%d substituicoes aplicadas" % n)

    # clampa sobreposicao sempre — barato e evita legenda piscando
    ov = 0
    for i in range(len(blocos) - 1):
        if blocos[i][1] > blocos[i + 1][0]:
            blocos[i][1] = blocos[i + 1][0]; ov += 1
    if ov:
        print("%d sobreposicoes corrigidas" % ov)

    if a.aplicar:
        open(a.srt, "w").write("\n".join(
            "%d\n%s --> %s\n%s\n" % (i, ts(x), ts(y), t)
            for i, (x, y, t) in enumerate(blocos, 1)))
        print("SRT reescrito: %s" % a.srt)
        print(">>> Regere o overlay: legendas.py --srt %s --overlay ... --dur ..." % a.srt)
    elif a.fix or ov:
        print("\n(nada foi gravado — rode de novo com --aplicar)")


if __name__ == "__main__":
    main()
