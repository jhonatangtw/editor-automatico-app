#!/usr/bin/env python3
"""Encaixa a locução NOVA nos tempos da fala ORIGINAL.

Cada bloco da voz nova (palavras entre pausas maiores que --pausa) passa a
começar no instante em que a MESMA palavra começa no AD original. Se o bloco
não cabe até o próximo, é acelerado (atempo) até --tempo-max; nunca é
desacelerado. Resultado: a legenda, os cortes e as transições do original
continuam caindo na palavra certa.

    python3 encaixar_voz.py --original decupagem/whisper.json --nova voz/voz_nova.json \
        --audio voz/voz_nova.mp3 --fim 29.10 --saida voz/voz_clone.wav

--original: JSON do Whisper (segments[].words[]) ou {"words":[{text|word,start,end}]}
--nova:     JSON do tts_elevenlabs.py
Saída: o .wav encaixado + um .json com o tempo de cada palavra NO VÍDEO
(é ele que alimenta a legenda da montagem).

As duas listas precisam ter o MESMO número de palavras. Se não tiverem (o
Whisper inventa palavra no silêncio, escreve "going to" onde a copy diz
"gonna", número em dígito), o script grava `<original>.palavras.json` com as
palavras do original para você corrigir à mão — vale o que está na legenda
queimada / na copy — e para mostrando onde as listas divergem. Rode de novo
com --original apontando para o arquivo corrigido.
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys


def palavras(p):
    d = json.load(open(p, encoding="utf-8"))
    w = d["words"] if "words" in d else [x for s in d.get("segments", []) for x in s.get("words", [])]
    return [{"t": (x.get("text") or x.get("word") or "").strip(), "s": float(x["start"]), "e": float(x["end"])} for x in w]


def norm(t):
    return re.sub(r"[^a-z0-9']", "", t.lower())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original", required=True)
    ap.add_argument("--nova", required=True)
    ap.add_argument("--audio", required=True, help="áudio da voz nova (o .mp3 do TTS)")
    ap.add_argument("--fim", type=float, required=True, help="duração final, em s (fim do trecho clonado)")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--ate", type=float, default=None, help="ignora palavras do original depois deste tempo")
    ap.add_argument("--pausa", type=float, default=0.3, help="pausa que separa blocos na voz nova (s)")
    ap.add_argument("--tempo-max", type=float, default=1.15, help="aceleração máxima de um bloco")
    a = ap.parse_args()

    o = palavras(a.original)
    if a.ate is not None:
        o = [w for w in o if w["s"] < a.ate]
    n = palavras(a.nova)
    if len(o) != len(n):
        corr = os.path.splitext(a.original)[0] + ".palavras.json"
        json.dump({"words": [{"text": w["t"], "start": w["s"], "end": w["e"]} for w in o]},
                  open(corr, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("x original tem %d palavras, a voz nova tem %d. Onde divergem:" % (len(o), len(n)))
        sm = difflib.SequenceMatcher(a=[norm(w["t"]) for w in o], b=[norm(w["t"]) for w in n], autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op != "equal":
                print("  %-8s original[%d:%d] %s  ->  nova %s" % (
                    op, i1, i2, " ".join(w["t"] for w in o[i1:i2]) or "-", " ".join(w["t"] for w in n[j1:j2]) or "-"))
        print("Corrija as palavras do original em %s (apague a inventada, junte 'going to' em uma, etc.)" % corr)
        print("e rode de novo com --original %s" % corr)
        sys.exit(2)

    blocos, cur = [], [0]
    for k in range(1, len(n)):
        if n[k]["s"] - n[k - 1]["e"] > a.pausa:
            blocos.append(cur)
            cur = []
        cur.append(k)
    blocos.append(cur)

    plano, saida_w, fim_ant = [], [], -1.0
    for b, idx in enumerate(blocos):
        ini, fim = max(0.0, n[idx[0]]["s"] - 0.04), n[idx[-1]]["e"] + 0.06
        alvo = max(o[idx[0]]["s"], fim_ant + 0.05)
        lim = (o[blocos[b + 1][0]]["s"] if b + 1 < len(blocos) else a.fim) - 0.04
        dur = fim - ini
        tempo = min(max(1.0, dur / max(0.1, lim - alvo)), a.tempo_max)
        plano.append((ini, fim, alvo, tempo))
        fim_ant = alvo + dur / tempo
        for k in idx:
            saida_w.append({"text": n[k]["t"], "start": round(alvo + (n[k]["s"] - ini) / tempo, 3),
                            "end": round(alvo + (n[k]["e"] - ini) / tempo, 3)})
        aviso = "  <- não coube: passa %.2f s do próximo bloco" % (fim_ant - lim) if fim_ant > lim + 0.02 else ""
        print("bloco %2d  %-28s em %6.2f s  dur %4.2f  vaga %4.2f  tempo %.3f%s" % (
            b, (n[idx[0]]["t"] + ".." + n[idx[-1]]["t"])[:28], alvo, dur, lim - alvo, tempo, aviso))

    filt = []
    for k, (ini, fim, alvo, tempo) in enumerate(plano):
        d = (fim - ini) / tempo
        ms = int(round(alvo * 1000))
        filt.append("[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,atempo=%.4f,afade=t=in:d=0.02,"
                    "afade=t=out:st=%.3f:d=0.03,adelay=%d|%d[b%d]" % (ini, fim, tempo, max(0, d - 0.03), ms, ms, k))
    filt.append("".join("[b%d]" % k for k in range(len(plano))) +
                "amix=inputs=%d:normalize=0,apad,atrim=0:%.3f[out]" % (len(plano), a.fim))
    os.makedirs(os.path.dirname(os.path.abspath(a.saida)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.audio, "-filter_complex", ";".join(filt),
                    "-map", "[out]", "-ac", "1", "-ar", "48000", a.saida], check=True)
    json.dump({"words": saida_w}, open(os.path.splitext(a.saida)[0] + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("ok: %s  (%d palavras, última termina em %.2f s)" % (a.saida, len(saida_w), saida_w[-1]["end"]))


if __name__ == "__main__":
    main()
