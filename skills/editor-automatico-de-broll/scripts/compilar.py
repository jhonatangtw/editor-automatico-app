#!/usr/bin/env python3
"""
Compila PLANO + ESTILO nos artefatos de execução.

    python3 compilar.py --plano plano.json --estilo alta-densidade --out .

Entra:
  plano.json   — o QUE o criativo diz (beats: insert, lettering, copy, punch manual)
  estilo       — COMO ele é acabado (densidade, escala de punch, legenda, marcador)

Sai:
  edicao.json      — contrato do montar.py (punch contíguo, inserts, overlays)
  marcadores.json  — contrato do pr_marcadores_criar (Tools PRO), já com cor e cobertura
  resumo no stdout — densidade medida vs alvo do estilo, e o que falta

A regra que justifica a separação: o mesmo plano tem que render em qualquer estilo.
Nada de acabamento (escala de punch, cor de marcador, template de legenda) mora no plano,
e nada de conteúdo (fala, intenção, arquivo de b-roll) mora no estilo.
"""
import argparse, json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_ESTILOS = os.path.join(os.path.dirname(AQUI), "estilos")

TIPOS = {"insert", "lettering", "copy", "punch"}


def carregar_estilo(ref):
    caminho = ref if os.path.isfile(ref) else os.path.join(DIR_ESTILOS, f"{ref}.json")
    if not os.path.isfile(caminho):
        disponiveis = sorted(f[:-5] for f in os.listdir(DIR_ESTILOS) if f.endswith(".json"))
        sys.exit(f"ERRO: estilo '{ref}' não existe. Disponíveis: {', '.join(disponiveis)}")
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def validar(plano, avisos):
    dur = float(plano["fonte"]["duracao"])
    beats = plano.get("beats", [])
    for b in beats:
        if b["tipo"] not in TIPOS:
            sys.exit(f"ERRO: beat {b.get('id')} tem tipo '{b['tipo']}'; use um de {sorted(TIPOS)}")
        if b["fim"] <= b["inicio"]:
            sys.exit(f"ERRO: beat {b.get('id')} termina antes de começar ({b['inicio']}→{b['fim']})")
        if b["fim"] > dur + 0.05:
            sys.exit(f"ERRO: beat {b.get('id')} passa da duração do body ({b['fim']} > {dur})")

    inserts = sorted([b for b in beats if b["tipo"] == "insert"], key=lambda b: b["inicio"])
    for a, c in zip(inserts, inserts[1:]):
        if c["inicio"] < a["fim"] - 1e-6:
            sys.exit(f"ERRO: inserts {a.get('id')} e {c.get('id')} se sobrepõem — "
                     f"{a['fim']} > {c['inicio']}")

    sem_midia = [b.get("id") for b in inserts if not b.get("midia")]
    if sem_midia:
        avisos.append(f"{len(sem_midia)} insert(s) sem mídia — falta gerar: {', '.join(sem_midia)}")
    faltando = [b.get("midia") for b in inserts
                if b.get("midia") and not os.path.isfile(
                    os.path.join(os.path.dirname(plano["_caminho"]), b["midia"]))]
    if faltando:
        avisos.append(f"{len(faltando)} arquivo(s) de b-roll não encontrado(s) no disco: "
                      f"{', '.join(faltando)}")
    return inserts


def calcular_punch(plano, estilo, inserts, avisos):
    """Punch é derivado do estilo, não do plano — salvo beats tipo 'punch' (override manual)."""
    dur = float(plano["fonte"]["duracao"])
    cfg = estilo["punch"]
    escalas = cfg.get("escalas") or []

    manuais = [b for b in plano.get("beats", []) if b["tipo"] == "punch"]
    janelas = [(b["inicio"], b["fim"], float(b.get("escala") or (escalas[0] if escalas else 1.1)))
               for b in manuais]

    if escalas and cfg.get("duracao_seg"):
        dmin, dmax = cfg["duracao_seg"]
        alvo = (dmin + dmax) / 2.0
        margem = float(cfg.get("margem_do_insert_seg") or 0)
        proibido = [(b["inicio"] - margem, b["fim"] + margem) for b in inserts] if \
            cfg.get("evitar_sobre_insert") else []
        proibido += [(i, f) for i, f, _ in janelas]

        def livre(ini, fim):
            return all(fim <= a or ini >= b for a, b in proibido)

        passo = float(cfg.get("intervalo_minimo_seg") or 12.0)
        t = passo
        n = len(janelas)
        while t + alvo < dur:
            if livre(t, t + alvo):
                janelas.append((round(t, 2), round(t + alvo, 2), escalas[n % len(escalas)]))
                n += 1
                t += passo + alvo
            else:
                t += 1.0

    janelas.sort()
    for a, c in zip(janelas, janelas[1:]):
        if c[0] < a[1] - 1e-6:
            avisos.append(f"punch sobreposto em {a[1]:.2f}s — revisar")

    # segmentos contíguos cobrindo 0..dur, que é o contrato do montar.py
    segs, cursor = [], 0.0
    for ini, fim, esc in janelas:
        if ini > cursor + 1e-6:
            segs.append([round(cursor, 2), round(ini, 2), 1.00])
        segs.append([round(ini, 2), round(fim, 2), round(esc, 2)])
        cursor = fim
    if cursor < dur - 1e-6:
        segs.append([round(cursor, 2), round(dur, 2), 1.00])
    if not segs:
        segs = [[0.0, round(dur, 2), 1.00]]
    segs[0][0] = 0.0
    segs[-1][1] = round(dur, 2)
    return segs, janelas


def montar_marcadores(plano, estilo, inserts):
    """Vermelho é cama de imagem: estica até o próximo. Azul e roxo colam na fala."""
    dur = float(plano["fonte"]["duracao"])
    cores = estilo["marcadores"]
    itens = []

    if inserts:
        inicios = [b["inicio"] for b in inserts]
        if estilo["insert"].get("abre_em_zero"):
            inicios[0] = 0.0
        for idx, b in enumerate(inserts):
            fim = inicios[idx + 1] if idx + 1 < len(inicios) else dur
            itens.append({
                "_ordem": inicios[idx], "tipo": "B-ROLL", "cor": cores["B-ROLL"],
                "inicio": round(inicios[idx], 2), "duracao": round(fim - inicios[idx], 2),
                "descricao": b.get("intencao") or b.get("id"),
                "comentario": _comentario(b),
            })

    for b in plano.get("beats", []):
        if b["tipo"] == "lettering":
            itens.append({"_ordem": b["inicio"], "tipo": "LETTERING", "cor": cores["LETTERING"],
                          "inicio": round(b["inicio"], 2),
                          "duracao": round(b["fim"] - b["inicio"], 2),
                          "descricao": (b.get("texto") or "").replace("\n", " / "),
                          "comentario": _comentario(b)})
        elif b["tipo"] == "copy":
            itens.append({"_ordem": b["inicio"], "tipo": "COPY", "cor": cores["COPY"],
                          "inicio": round(b["inicio"], 2),
                          "duracao": round(b["fim"] - b["inicio"], 2),
                          "descricao": b.get("nota") or b.get("id"),
                          "comentario": _comentario(b)})

    itens.sort(key=lambda m: m["_ordem"])
    for i, m in enumerate(itens, 1):
        m["nome"] = f"{i:02d} - {m['tipo']} - {m['descricao']}"
        del m["_ordem"], m["descricao"]
    return itens


def _comentario(b):
    partes = []
    if b.get("fala"):
        partes.append(f'"{b["fala"]}"')
    if b.get("intencao"):
        partes.append(b["intencao"])
    if b.get("nota"):
        partes.append(b["nota"])
    return " — ".join(partes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plano", required=True)
    ap.add_argument("--estilo", help="sobrescreve o estilo declarado no plano")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    with open(args.plano, encoding="utf-8") as f:
        plano = json.load(f)
    plano["_caminho"] = os.path.abspath(args.plano)

    estilo = carregar_estilo(args.estilo or plano.get("estilo") or "alta-densidade")
    avisos = []
    inserts = validar(plano, avisos)
    punch, janelas_punch = calcular_punch(plano, estilo, inserts, avisos)
    marcadores = montar_marcadores(plano, estilo, inserts)

    fonte, dur = plano["fonte"], float(plano["fonte"]["duracao"])
    edicao = {
        "body": fonte["body"],
        "duracao": dur,
        "largura": fonte.get("largura", 1080),
        "altura": fonte.get("altura", 1920),
        "saida": plano.get("saida", f"{plano.get('job', 'SAIDA')}_9x16.mp4"),
        "legenda": plano.get("legenda"),
        "punch": punch,
        "inserts": [{"arquivo": b["midia"], "inicio": b["inicio"], "fim": b["fim"]}
                    for b in inserts if b.get("midia")],
        "overlays": plano.get("overlays", []),
        "flash": estilo["corte"].get("flash"),
        "sfx": estilo["corte"].get("sfx"),
    }

    os.makedirs(args.out, exist_ok=True)
    p_ed = os.path.join(args.out, "edicao.json")
    p_mk = os.path.join(args.out, "marcadores.json")
    with open(p_ed, "w", encoding="utf-8") as f:
        json.dump(edicao, f, ensure_ascii=False, indent=2)
    with open(p_mk, "w", encoding="utf-8") as f:
        json.dump(marcadores, f, ensure_ascii=False, indent=2)

    n_punch = len([s for s in punch if s[2] > 1.0])
    cortes = 2 * len(edicao["inserts"]) + 2 * n_punch
    cobertura = sum(b["fim"] - b["inicio"] for b in inserts) / dur if dur else 0

    print(f"plano  : {plano.get('job', '?')}  ({dur:.1f}s)")
    print(f"estilo : {estilo['nome']}")
    print(f"inserts: {len(inserts)}  ({len(edicao['inserts'])} com mídia)  "
          f"cobertura {cobertura*100:.0f}%  [alvo {estilo['insert']['cobertura_alvo']*100:.0f}%]")
    print(f"punch  : {n_punch}")
    alvo = estilo["corte"].get("alvo_segundos_por_corte")
    if cortes:
        s = dur / cortes
        faixa = f"  [alvo {alvo[0]}–{alvo[1]}s]" if alvo else ""
        print(f"ritmo  : {cortes} cortes, 1 a cada {s:.1f}s{faixa}")
        if alvo and s > alvo[1]:
            avisos.append(f"subcortado para o estilo: 1 corte a cada {s:.1f}s, "
                          f"o alvo é {alvo[0]}–{alvo[1]}s")
    elif alvo:
        avisos.append("nenhum corte — o estilo pede densidade alta")
    print(f"marcad.: {len(marcadores)}")
    print(f"\nescrito: {p_ed}\n         {p_mk}")
    if avisos:
        print("\nAVISOS:")
        for a in avisos:
            print(f"  ! {a}")


if __name__ == "__main__":
    main()
