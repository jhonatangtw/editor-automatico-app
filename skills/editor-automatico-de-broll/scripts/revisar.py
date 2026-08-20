#!/usr/bin/env python3
"""
Imprime o PLANO para aprovação — antes de gerar b-roll e antes de escrever no Premiere.

    python3 revisar.py --plano plano.json
    python3 revisar.py --plano plano.json --estilo talking-head-puro

É o portão do pipeline: sai com código 1 se houver bloqueio (mídia faltando, beat
inválido, vão longo demais para o estilo). Serve para o usuário bater o olho e dizer
"pode ir" — que é a etapa que faltava entre decupar e executar.

Não escreve nada. Só lê e mostra.
"""
import argparse, json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from compilar import carregar_estilo  # noqa: E402

SIMBOLO = {"insert": "▓", "punch": "▒", "lettering": "T", "copy": "!"}
LARGURA = 68


def tc(s):
    return f"{int(s // 60):d}:{s % 60:05.2f}"


def regua(dur, beats):
    linha = ["·"] * LARGURA
    for b in beats:
        i = int(b["inicio"] / dur * LARGURA)
        f = max(i + 1, int(b["fim"] / dur * LARGURA))
        for x in range(i, min(f, LARGURA)):
            linha[x] = SIMBOLO.get(b["tipo"], "?")
    return "".join(linha)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plano", required=True)
    ap.add_argument("--estilo")
    args = ap.parse_args()

    with open(args.plano, encoding="utf-8") as f:
        plano = json.load(f)
    base = os.path.dirname(os.path.abspath(args.plano))
    estilo = carregar_estilo(args.estilo or plano.get("estilo") or "alta-densidade")

    dur = float(plano["fonte"]["duracao"])
    beats = sorted(plano.get("beats", []), key=lambda b: b["inicio"])
    inserts = [b for b in beats if b["tipo"] == "insert"]
    bloqueios, alertas = [], []

    print(f"\n  {plano.get('job', '?')}   {dur:.1f}s   estilo: {estilo['nome']}")
    print(f"  {plano['fonte']['body']}\n")
    print("  " + regua(dur, beats))
    print(f"  0{' ' * (LARGURA - 8)}{dur:.0f}s")
    print(f"  ▓ insert   T lettering   ! copy\n")

    for b in beats:
        marca = " "
        if b["tipo"] == "insert":
            if not b.get("midia"):
                marca = "○"
                bloqueios.append(f'{b.get("id")}: sem mídia — falta gerar')
            elif not os.path.isfile(os.path.join(base, b["midia"])):
                marca = "×"
                bloqueios.append(f'{b.get("id")}: arquivo não existe — {b["midia"]}')
            else:
                marca = "●"
        if b["tipo"] == "copy":
            marca = "!"
            alertas.append(f'{b.get("id")} em {tc(b["inicio"])}: {b.get("nota")}')

        rotulo = (b.get("intencao") or b.get("texto", "").replace("\n", " / ")
                  or b.get("nota") or "")
        print(f"  {marca} {tc(b['inicio'])} → {tc(b['fim'])}  "
              f"{b['tipo']:<9} {rotulo[:44]}")
        if b.get("fala"):
            print(f'              "{b["fala"][:60]}"')

    # vão sem nenhuma troca de imagem — é onde o plano fica parado
    cobertura = sum(b["fim"] - b["inicio"] for b in inserts)
    marcos = [0.0] + [x for b in inserts for x in (b["inicio"], b["fim"])] + [dur]
    maior_vao, onde = 0.0, 0.0
    for a, c in zip(marcos, marcos[1:]):
        if c - a > maior_vao:
            maior_vao, onde = c - a, a

    # cadência na mesma unidade que o Captions usa: 1 troca de imagem a cada N segundos
    trocas = 2 * len(inserts)
    cadencia = dur / trocas if trocas else None

    print(f"\n  cobertura de b-roll : {cobertura / dur * 100:.0f}%  "
          f"[alvo {estilo['insert']['cobertura_alvo'] * 100:.0f}%]")
    print(f"  maior vão sem troca : {maior_vao:.1f}s  a partir de {tc(onde)}")
    if cadencia:
        print(f"  cadência (só insert): 1 a cada {cadencia:.1f}s")
    print(f"  referência Ignite   : 1 a cada 5.0s · b-roll em 67% dos shots"
          f"   (medido no Captions, 15 shots / 74.5s)")

    alvo = estilo["corte"].get("alvo_segundos_por_corte")
    if alvo and maior_vao > alvo[1] * 4:
        alertas.append(f"vão de {maior_vao:.0f}s sem nenhuma troca de imagem "
                       f"(a partir de {tc(onde)}) — o punch do estilo cobre, mas confira")
    if alvo and cobertura / dur < estilo["insert"]["cobertura_alvo"] * 0.6:
        alertas.append(f"cobertura de b-roll bem abaixo do estilo "
                       f"({cobertura / dur * 100:.0f}% contra {estilo['insert']['cobertura_alvo'] * 100:.0f}%)")
    if len([b for b in beats if b["tipo"] == "lettering"]) > estilo["lettering"]["maximo"]:
        alertas.append(f"mais lettering que o estilo permite "
                       f"(máximo {estilo['lettering']['maximo']}) — vira videoclipe e rouba a legenda")

    if alertas:
        print("\n  ALERTAS")
        for a in alertas:
            print(f"    ~ {a}")
    if bloqueios:
        print("\n  BLOQUEIOS")
        for b in bloqueios:
            print(f"    ! {b}")
        print("\n  Plano NÃO está pronto para montar.\n")
        sys.exit(1)

    print("\n  Plano fechado. Pode compilar:")
    print(f"    python3 compilar.py --plano {args.plano} --out .\n")


if __name__ == "__main__":
    main()
