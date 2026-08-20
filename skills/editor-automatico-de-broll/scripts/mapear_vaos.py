#!/usr/bin/env python3
"""
Mapeia o que FALTA de video numa timeline ja parcialmente editada.

Por que existe: nos tres ADs do LinfaFlow a primeira metade estava pronta e a
segunda estava vazia — 64% e 63% da timeline sem video nenhum. Descobrir isso
antes evita prometer "alguns espacos vazios" e entregar meio anuncio.

Entrada: o JSON de `pr_timeline_listar`.
Saida: a lista de vaos, e opcionalmente um esqueleto de marcadores em cenas
de no maximo 15 s ja casadas com a fala.

    python3 mapear_vaos.py --timeline tl.json --duracao 711.28
    python3 mapear_vaos.py --timeline tl.json --duracao 711.28 \
            --transcricao tl.json.whisper --esqueleto marcadores.json
"""
import argparse, json, sys

TETO = 15.0        # teto do Seedance
MINIMO = 0.3       # abaixo disso nao e vao, e arredondamento de frame


def mmss(x):
    return f"{int(x // 60):02d}:{x % 60:05.2f}"


def vaos_de(clipes, total):
    fim_anterior, out = 0.0, []
    for c in sorted(clipes, key=lambda x: x["inicio"]):
        if c["inicio"] - fim_anterior > MINIMO:
            out.append((fim_anterior, c["inicio"]))
        fim_anterior = max(fim_anterior, c["fim"])
    if total - fim_anterior > MINIMO:
        out.append((fim_anterior, total))
    return out


def cenas_do_vao(a, b, segmentos):
    """Corta o vao em cenas de ate 15 s, quebrando no fim de frase."""
    dentro = [s for s in segmentos if s["e"] > a and s["s"] < b]
    if not dentro:
        n = max(1, int((b - a) // TETO) + (1 if (b - a) % TETO else 0))
        passo = (b - a) / n
        return [(round(a + i * passo, 2), round(a + (i + 1) * passo, 2), "") for i in range(n)]
    cenas, ini, txt = [], max(a, dentro[0]["s"]), []
    for s in dentro:
        if txt and s["e"] - ini > TETO:
            cenas.append((round(ini, 2), round(s["s"], 2), " ".join(txt)))
            ini, txt = s["s"], []
        txt.append(s["t"].strip())
    if txt:
        cenas.append((round(ini, 2), round(min(b, dentro[-1]["e"]), 2), " ".join(txt)))

    # nenhuma cena pode passar do teto — parte no meio o que sobrou
    final = []
    for x, y, t in cenas:
        if y - x <= TETO:
            final.append((x, y, t)); continue
        n = int((y - x) // TETO) + (1 if (y - x) % TETO else 0)
        passo = (y - x) / n
        for i in range(n):
            final.append((round(x + i * passo, 2), round(x + (i + 1) * passo, 2),
                          t if i == 0 else ""))
    return final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--duracao", type=float, required=True, help="duracao da sequencia")
    ap.add_argument("--trilha", default="V1")
    ap.add_argument("--transcricao", default=None, help="JSON com segments[] {s,e,t}")
    ap.add_argument("--esqueleto", default=None, help="grava um marcadores.json de partida")
    a = ap.parse_args()

    d = json.load(open(a.timeline))
    clipes = []
    for t in d.get("video", []):
        if t.get("trilha") == a.trilha:
            clipes = t.get("itens", [])
    if not clipes:
        print(f"AVISO: {a.trilha} vazia — o anuncio inteiro esta sem video", file=sys.stderr)

    vs = vaos_de(clipes, a.duracao)
    total = sum(b - x for x, b in vs)
    print(f"{'de':>9} {'ate':>9} {'duracao':>9}")
    for x, b in vs:
        print(f"{mmss(x):>9} {mmss(b):>9} {b - x:8.2f}s")
    pct = total / a.duracao * 100 if a.duracao else 0
    print(f"\n{len(vs)} vaos | {total:.1f}s sem video de {a.duracao:.0f}s ({pct:.0f}%)")

    if not a.esqueleto:
        return

    segs = []
    if a.transcricao:
        tr = json.load(open(a.transcricao))
        segs = tr.get("segments", tr if isinstance(tr, list) else [])

    marc, n = [], 0
    for x, b in vs:
        for ini, fim, txt in cenas_do_vao(x, b, segs):
            if fim - ini < 0.5:
                continue
            n += 1
            marc.append({"tempo": ini, "duracao": round(fim - ini, 2), "cor": 1,
                         "nome": f"{n:02d} - CENA - (descrever)", "comentario": txt[:380]})
    json.dump(marc, open(a.esqueleto, "w"), ensure_ascii=False, indent=1)
    print(f"\nesqueleto: {a.esqueleto} ({len(marc)} marcadores, maior "
          f"{max((m['duracao'] for m in marc), default=0):.2f}s)")
    print("Os nomes vem como '(descrever)' de proposito — escrever cada um a partir da fala,")
    print("senao o editor recebe 47 marcadores identicos e nao sabe o que colocar.")


if __name__ == "__main__":
    main()
