#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decupagem: acha TODOS os takes de cada frase do roteiro, recomenda um e
monta o plano de corte com borda por energia e margem de "corte suave".

    python3 scripts/decupar.py --video BRUTO.MOV --transcricao transcricao.json \
        --roteiro roteiro.txt --saida decupagem/ \
        [--antes 0.40 --depois 0.30] [--escolha "2:3,5:6"] [--sem "4"]

roteiro.txt: uma frase por linha, na ordem do vídeo. Linha com "(opcional)"
no fim vira peça opcional. Linhas vazias e "#comentário" são ignoradas.
Sem roteiro (--roteiro omitido), cada fala do bruto vira um take e takes
parecidos em sequência são agrupados como a mesma frase.

Grava na pasta de saída:
  takes.json        todas as frases com todos os takes (para o Premiere)
  plano-corte.json  um take por frase, na ordem (o corte v1)
  mapa-takes.md     o mapa para o ALUNO decidir (recomendado, alertas, falas fora do roteiro)

Nada é cortado aqui: o bruto não é tocado. As escolhas são do aluno —
--escolha "FRASE:TAKE" troca a recomendação; --sem "FRASE" tira a frase.
"""
import argparse
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comum import gravar_json, info_video, ler_json, limiar_auto, nivel_voz, norm, pcm16k, rms_db, sair, tokens, trechos_de_fala  # noqa: E402


def ler_roteiro(p):
    frases = []
    for L in open(p, encoding="utf-8"):
        L = L.strip()
        if not L or L.startswith("#"):
            continue
        opc = L.lower().endswith("(opcional)")
        if opc:
            L = L[: -len("(opcional)")].strip()
        frases.append({"texto": L, "opcional": opc})
    return frases


def candidatos(frase, palavras, minimo=0.5):
    """Janelas de palavras parecidas com a frase.

    Nota da janela = 70 % cobertura do roteiro + 30 % precisão. Depois a janela é
    completada para trás/para frente com as palavras coladas (mesmo fôlego) que
    faltam no começo/fim — o Whisper costuma errar justamente a 1ª palavra do take.
    """
    alvo = tokens(frase)
    n = len(alvo)
    if not n:
        return []
    W = [norm(w["w"]) for w in palavras]
    conj = set(alvo)
    achados = []
    for i, w in enumerate(W):
        if w not in conj:
            continue
        melhor = None
        for L in range(max(1, int(n * 0.5)), int(n * 1.6) + 2):
            j = i + L
            if j > len(W):
                break
            sm = difflib.SequenceMatcher(None, alvo, W[i:j], autojunk=False)
            bl = [x for x in sm.get_matching_blocks() if x.size]
            m = sum(x.size for x in bl)
            if not m:
                continue
            nota = 0.7 * m / n + 0.3 * m / L
            if melhor is None or nota > melhor[0] + 1e-9:
                # o que falta no começo/fim do roteiro, descontando palavras da janela antes/depois do 1º/último acerto
                cab = max(0, bl[0].a - bl[0].b)
                cauda = max(0, (n - (bl[-1].a + bl[-1].size)) - (L - (bl[-1].b + bl[-1].size)))
                melhor = (nota, i, j, cab, cauda, m / float(n))
        if melhor and melhor[5] >= minimo:
            achados.append(melhor)
    achados.sort(key=lambda x: -x[0])
    final = []
    for c in achados:  # sem sobreposição: fica a melhor
        if any(not (c[2] <= f[1] or c[1] >= f[2]) for f in final):
            continue
        final.append(c)
    out = []
    for nota, i, j, cab, cauda, cob in sorted(final, key=lambda x: x[1]):
        k = 0
        while k < cab and i > 0 and palavras[i]["s"] - palavras[i - 1]["e"] < 0.35:
            i -= 1; k += 1
        cab -= k
        k = 0
        while k < cauda and j < len(palavras) and palavras[j]["s"] - palavras[j - 1]["e"] < 0.35:
            j += 1; k += 1
        cauda -= k
        out.append((round(nota, 3), i, j, cab, cauda, cob))
    return out


def borda_energia(fala, s, e):
    """Ajusta [s,e] (tempos do Whisper) às bordas reais da voz."""
    dentro = [x for x in fala if x[1] > s - 0.6 and x[0] < e + 0.6]
    if not dentro:
        return s, e
    ini = min(x[0] for x in dentro if x[1] > s - 0.6)
    fim = max(x[1] for x in dentro if x[0] < e + 0.6)
    # não puxar fala de outra frase: limitar o quanto a borda anda
    ini = max(ini, s - 0.6)
    fim = min(fim, e + 0.6)
    return round(ini, 2), round(fim, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="bruto (só leitura)")
    ap.add_argument("--transcricao", required=True, help="saída do transcrever.py sobre o BRUTO")
    ap.add_argument("--roteiro")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--antes", type=float, default=0.40)
    ap.add_argument("--depois", type=float, default=0.30)
    ap.add_argument("--escolha", default="", help='ex.: "2:3,5:6" = frase 2 usa o take 3')
    ap.add_argument("--sem", default="", help='frases a tirar do corte, ex.: "4,8"')
    ap.add_argument("--similaridade", type=float, default=0.5)
    ap.add_argument("--sem-verificar", action="store_true", help="pula a reconferência take a take (mais rápido, menos seguro)")
    ap.add_argument("--modelo", default="medium")
    ap.add_argument("--limiar", type=float, help="dBFS da voz (padrão: automático, relativo à voz)")
    a = ap.parse_args()

    T = ler_json(a.transcricao)
    P = T["palavras"]
    if not P:
        sair("transcrição vazia")
    inf = info_video(a.video)
    total = inf["duracao"]
    y = pcm16k(a.video)
    r = rms_db(y)
    lim = a.limiar if a.limiar is not None else limiar_auto(r)
    print("limiar da voz: %.1f dBFS" % lim)
    fala = trechos_de_fala(r, lim, juntar=0.25, minimo=0.08)

    frases = []
    usados = set()
    if a.roteiro:
        roteiro = ler_roteiro(a.roteiro)
        for n, fr in enumerate(roteiro, 1):
            cs = candidatos(fr["texto"], P, a.similaridade)
            takes = []
            for k, (rat, i, j, cab, cauda, cob) in enumerate(cs, 1):
                s, e = P[i]["s"], P[j - 1]["e"]
                usados.update(range(i, j))
                takes.append({"take": k, "fala_ini": s, "fala_fim": e, "texto": " ".join(w["w"] for w in P[i:j]),
                              "similaridade": rat, "cobertura": round(cob, 2), "_cab": cab, "_cauda": cauda})
            frases.append({"frase": n, "texto": fr["texto"], "opcional": fr["opcional"], "takes": takes})
    else:
        grupos = []
        for t in T["trechos"]:
            if not t["palavras"]:
                continue
            tk = {"fala_ini": t["palavras"][0]["s"], "fala_fim": t["palavras"][-1]["e"], "texto": t["texto"], "similaridade": 1.0}
            if grupos and difflib.SequenceMatcher(None, tokens(grupos[-1]["texto"]), tokens(t["texto"])).ratio() >= 0.5:
                grupos[-1]["takes"].append(tk)
            else:
                grupos.append({"texto": t["texto"], "opcional": False, "takes": [tk]})
        for n, g in enumerate(grupos, 1):
            for k, tk in enumerate(g["takes"], 1):
                tk["take"] = k
            g["frase"] = n
            frases.append(g)

    # bordas por energia, pausas internas, nível e nota de cada take
    for fr in frases:
        for tk in fr["takes"]:
            s, e = tk["fala_ini"], tk["fala_fim"]
            al = []
            nv, frac = nivel_voz(r, s, e, lim)
            if frac < 0.45 and e - s > 0.8:
                # tempo do Whisper desalinhado (comum em trecho com silêncio no meio):
                # procura, perto, o bloco de voz com duração parecida
                blocos = []
                for x in fala:
                    if blocos and x[0] - blocos[-1][1] < 0.6:
                        blocos[-1][1] = x[1]
                    else:
                        blocos.append([x[0], x[1]])
                perto = [bk for bk in blocos if abs(bk[0] - s) < 8]
                if perto:
                    bk = min(perto, key=lambda bk: abs((bk[1] - bk[0]) - (e - s)) + 0.3 * abs(bk[0] - s))
                    nv2, frac2 = nivel_voz(r, bk[0], bk[1], lim)
                    if frac2 > frac:
                        s, e = bk[0], bk[1]
                        al.append("tempo realinhado pela energia (o Whisper errou o tempo) — confira na prévia")
            s, e = borda_energia(fala, s, e)
            tk["fala_ini"], tk["fala_fim"] = s, e
            tk["nivel_db"], tk["voz_frac"] = nivel_voz(r, s, e, lim)
            ws = [w for w in P if w["s"] >= s - 0.05 and w["e"] <= e + 0.05]
            gaps = [ws[k + 1]["s"] - ws[k]["e"] for k in range(len(ws) - 1)]
            sil = [x for x in zip(fala, fala[1:]) if x[0][1] > s and x[1][0] < e]
            gap_e = max([b2[0] - a2[1] for a2, b2 in sil] or [0])
            tk["maior_pausa"] = round(max(gaps + [gap_e]), 2) if (gaps or sil) else 0.0
            tk["completo"] = tk.get("_cab", 0) <= 1 and tk.get("_cauda", 0) <= 1 and tk.get("cobertura", 1) >= 0.75
            if tk["maior_pausa"] > 1.0:
                al.append("pausa de %.1f s no meio" % tk["maior_pausa"])
            if not tk["completo"]:
                al.append("incompleto: falta começo ou fim da frase")
            if tk["similaridade"] < 0.7:
                al.append("texto diferente do roteiro (improviso ou Whisper errou — ouça)")
            tk["alertas"] = al
            tk.pop("_cab", None); tk.pop("_cauda", None)
        if fr["takes"]:
            niveis = [t["nivel_db"] for t in fr["takes"]]
            lo, hi = min(niveis), max(niveis)
            for t in fr["takes"]:
                nv = 0 if hi == lo else (t["nivel_db"] - lo) / (hi - lo)
                t["nota"] = round(60 * t["similaridade"] + 20 * t["completo"] + 10 * (t["maior_pausa"] <= 0.8) + 10 * nv, 1)
            # empate técnico: o take mais tardio costuma ser o "já pegou o jeito"
            rec = max(fr["takes"], key=lambda t: (round(t["nota"] / 3), t["fala_ini"]))
            fr["recomendado"] = rec["take"]
        # reconferência: transcreve de novo SÓ a janela de cada take (passada curta = tempo confiável)
    if a.roteiro and not a.sem_verificar:
        try:
            import whisper
            mdl = whisper.load_model(a.modelo)
        except Exception as ex:  # noqa: BLE001
            mdl = None
            print("! sem Whisper para reconferir (%s) — confira os takes de ouvido" % ex)
        blocos = []
        for x in fala:
            if blocos and x[0] - blocos[-1][1] < 0.6:
                blocos[-1][1] = x[1]
            else:
                blocos.append([x[0], x[1]])

        def ouvir(s0, e0):
            seg = y[int(max(0, s0 - 0.25) * 16000):int((e0 + 0.25) * 16000)]
            res = mdl.transcribe(seg, language="pt", temperature=0, condition_on_previous_text=False, fp16=False)
            return res["text"].strip()
        for fr in frases if mdl else []:
            alvo = tokens(fr["texto"])
            for tk in fr["takes"]:
                txt = ouvir(tk["fala_ini"], tk["fala_fim"])
                sim = difflib.SequenceMatcher(None, alvo, tokens(txt)).ratio()
                tk["reconferido"] = txt
                if sim >= 0.5:
                    continue
                # o tempo estava errado: procura por perto o bloco de voz que diz a frase
                melhor = None
                for bk in blocos:
                    if abs(bk[0] - tk["fala_ini"]) > 10 or bk[1] - bk[0] < 0.4:
                        continue
                    t2 = ouvir(bk[0], bk[1])
                    s2 = difflib.SequenceMatcher(None, alvo, tokens(t2)).ratio()
                    if melhor is None or s2 > melhor[0]:
                        melhor = (s2, bk, t2)
                if melhor and melhor[0] >= 0.5:
                    tk["fala_ini"], tk["fala_fim"] = round(melhor[1][0], 2), round(melhor[1][1], 2)
                    tk["reconferido"] = melhor[2]
                    tk["nivel_db"], tk["voz_frac"] = nivel_voz(r, tk["fala_ini"], tk["fala_fim"], lim)
                    tk["alertas"].append("TEMPO CORRIGIDO na reconferência (a passada longa errou o lugar)")
                else:
                    tk["alertas"].append("na reconferência a janela diz '%s' — ouça antes de usar" % txt[:60])

    # possível falso começo: take curto seguido de outro da mesma frase em < 3 s
        for t1, t2 in zip(fr["takes"], fr["takes"][1:]):
            if t2["fala_ini"] - t1["fala_fim"] < 3.0 and t1["fala_fim"] - t1["fala_ini"] < 0.7 * (t2["fala_fim"] - t2["fala_ini"]):
                t1["alertas"].append("provável falso começo (logo depois vem outro take) — reconfira com transcrever.py --ini/--fim")

    # margens de corte suave, sem invadir a fala vizinha
    # (só palavras contam como "fala vizinha": respiração e ruído de sala podem ficar na margem)
    todos = sorted([(w["s"], w["e"]) for w in P])
    for fr in frases:
        for t in fr["takes"]:
            antes = [b for x, b in todos if b <= t["fala_ini"] - 0.01]
            depois = [x for x, b in todos if x >= t["fala_fim"] + 0.01]
            pa = max(antes) if antes else 0.0
            nb = min(depois) if depois else total
            t["entrada"] = round(max(t["fala_ini"] - a.antes, (pa + t["fala_ini"]) / 2 if t["fala_ini"] - pa < 2 * a.antes else 0, 0), 2)
            t["saida"] = round(min(t["fala_fim"] + a.depois, (t["fala_fim"] + nb) / 2 if nb - t["fala_fim"] < 2 * a.depois else total, total), 2)

    esc = dict(x.split(":") for x in a.escolha.split(",") if ":" in x)
    sem = {x.strip() for x in a.sem.split(",") if x.strip()}
    pecas, pos, faltando = [], 0.0, []
    for fr in frases:
        if str(fr["frase"]) in sem:
            continue
        if not fr["takes"]:
            faltando.append(fr)
            continue
        k = int(esc.get(str(fr["frase"]), fr.get("recomendado", 1)))
        t = next((x for x in fr["takes"] if x["take"] == k), None)
        if not t:
            sair("frase %s não tem take %s" % (fr["frase"], k))
        d = round(t["saida"] - t["entrada"], 2)
        pecas.append({"nome": "%02d_%s" % (fr["frase"], "_".join(tokens(fr["texto"])[:4])), "frase": fr["frase"], "take": k,
                      "entrada": t["entrada"], "saida": t["saida"], "dur": d, "texto": t["texto"],
                      "opcional": fr["opcional"], "pos_na_saida": round(pos, 2)})
        pos += d

    # fala que não casou com nenhuma frase (improviso, ensaio, comentário)
    fora = []
    for t in T["trechos"]:
        ws = [w for w in t["palavras"] if P.index(w) not in usados] if a.roteiro else []
        if len(ws) >= 3:
            fora.append({"ini": ws[0]["s"], "fim": ws[-1]["e"], "texto": " ".join(w["w"] for w in ws)})

    os.makedirs(a.saida, exist_ok=True)
    gravar_json(os.path.join(a.saida, "takes.json"), {"fonte": os.path.basename(a.video), "duracao": total, "frases": frases})
    gravar_json(os.path.join(a.saida, "plano-corte.json"), {
        "fonte": os.path.basename(a.video),
        "observacao": "tempos em segundos no bruto. Margens: %.2f s antes da 1ª fala, %.2f s depois da última (corte suave), sem invadir fala vizinha." % (a.antes, a.depois),
        "pedacos": pecas, "duracao_total": round(pos, 2),
        "duracao_sem_opcionais": round(pos - sum(p["dur"] for p in pecas if p["opcional"]), 2)})

    L = ["# Mapa de takes — %s" % os.path.basename(a.video), "",
         "Bruto: %.1f s. Tempos em segundos no bruto. Borda = energia da voz; margem %.2f s antes / %.2f s depois." % (total, a.antes, a.depois),
         "Recomendado = mais parecido com o roteiro, completo, sem pausa longa e com a voz mais firme. **Quem decide é você.**", ""]
    for fr in frases:
        L.append("## %d. %s%s — %d take(s)" % (fr["frase"], fr["texto"], " (opcional)" if fr["opcional"] else "", len(fr["takes"])))
        if not fr["takes"]:
            L.append("- NÃO ACHEI esta frase gravada. Confira de ouvido ou regrave.")
        for t in fr["takes"]:
            rec = " **RECOMENDADO**" if t["take"] == fr.get("recomendado") else ""
            al = (" — ⚠ " + "; ".join(t["alertas"])) if t["alertas"] else ""
            L.append("- T%d %.2f–%.2f (%.1f s, %.0f dB, nota %.0f)%s: \"%s\"%s" % (
                t["take"], t["fala_ini"], t["fala_fim"], t["fala_fim"] - t["fala_ini"], t["nivel_db"], t["nota"], rec, t["texto"], al))
        tops = sorted(fr["takes"], key=lambda t: -t.get("nota", 0))[:2]
        if len(tops) == 2 and abs(tops[0]["nota"] - tops[1]["nota"]) <= 5:
            L.append("- ↔ empate técnico entre T%d e T%d: OUÇA os dois (entonação, final enrolado e falso começo o script não percebe)." % (tops[0]["take"], tops[1]["take"]))
        L.append("")
    if fora:
        L += ["## Falas fora do roteiro (improviso/ensaio)", ""]
        L += ["- %.2f–%.2f \"%s\"" % (f["ini"], f["fim"], f["texto"]) for f in fora]
        L.append("")
    L += ["## Plano de corte", "", "| # | frase/take | entrada | saída | dur | texto |", "|---|---|---|---|---|---|"]
    L += ["| %d | %d/T%d%s | %.2f | %.2f | %.2f | %s |" % (k + 1, p["frase"], p["take"], " (opc)" if p["opcional"] else "", p["entrada"], p["saida"], p["dur"], p["texto"]) for k, p in enumerate(pecas)]
    L += ["", "Duração: %.2f s (sem opcionais: %.2f s)." % (pos, pos - sum(p["dur"] for p in pecas if p["opcional"]))]
    if faltando:
        L.append("Frases sem take: " + ", ".join(str(f["frase"]) for f in faltando))
    open(os.path.join(a.saida, "mapa-takes.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[-len(pecas) - 6:]))
    print("ok ->", a.saida)


if __name__ == "__main__":
    main()
