#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transcrição com tempo por palavra, POR TRECHO DE FALA (nunca uma passada longa só).

    python3 scripts/transcrever.py VIDEO --saida transcricao.json \
        [--modelo medium] [--termos "Nome da Marca, Premiere, ChatGPT"] \
        [--ini 120 --fim 140]     # só uma janela (para reconferir um take)

Por que por trecho: numa passada longa o Whisper inventa palavras dentro do
silêncio e às vezes engole frases inteiras. Aqui o áudio é cortado onde há
energia de voz (RMS a cada 10 ms) e cada trecho é transcrito sozinho.

Saída (JSON):
  {"modelo", "limiar_db", "trechos": [{"a","b","texto","palavras":[...]}],
   "palavras": [{"w","s","e"}]}            # tempos em segundos no arquivo
e um .txt legível ao lado. Os tempos de palavra do Whisper deslocam até ~0,5 s:
o corte usa a borda por ENERGIA (decupar.py), não estes tempos.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comum import gravar_json, limiar_auto, pcm16k, rms_db, sair, trechos_de_fala  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Whisper por trecho de fala, com tempo por palavra")
    ap.add_argument("video")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--modelo", default="medium")
    ap.add_argument("--lingua", default="pt")
    ap.add_argument("--termos", default="", help="nomes próprios e termos para o Whisper acertar a grafia")
    ap.add_argument("--ini", type=float)
    ap.add_argument("--fim", type=float)
    ap.add_argument("--limiar", type=float, help="dBFS da fala (padrão: piso da sala + 10 dB)")
    ap.add_argument("--juntar", type=float, default=1.2, help="junta trechos separados por menos que isto (s)")
    a = ap.parse_args()
    try:
        import whisper
    except ImportError:
        sair("Whisper não instalado: pip3 install --user openai-whisper")

    ini = a.ini or 0.0
    y = pcm16k(a.video, a.ini, a.fim)
    if len(y) == 0:
        sair("não consegui ler o áudio de %s" % a.video)
    r = rms_db(y)
    lim = a.limiar if a.limiar is not None else limiar_auto(r)
    fala = trechos_de_fala(r, lim, juntar=0.3, minimo=0.15)
    blocos = []
    for s, e in fala:
        # junta falas próximas, mas não deixa um bloco passar de ~25 s (passada longa inventa/omite)
        if blocos and s - blocos[-1][1] < a.juntar and not (e - blocos[-1][0] > 25 and s - blocos[-1][1] > 0.2):
            blocos[-1][1] = e
        else:
            blocos.append([s, e])
    print("limiar %.1f dBFS · %d trechos de fala · modelo %s" % (lim, len(blocos), a.modelo), flush=True)
    m = whisper.load_model(a.modelo)
    total = len(y) / 16000.0
    out, todas = [], []
    for s, e in blocos:
        s0, e0 = max(0.0, s - 0.4), min(total, e + 0.4)
        seg = y[int(s0 * 16000):int(e0 * 16000)]
        res = m.transcribe(seg, language=a.lingua, word_timestamps=True, temperature=0,
                           condition_on_previous_text=False, no_speech_threshold=0.6,
                           initial_prompt=a.termos or None, fp16=False)
        ws = []
        for sg in res["segments"]:
            for w in sg.get("words", []):
                ws_, we_ = w["start"] + s0, w["end"] + s0
                # alucinação típica: palavra "falada" num pedaço sem energia de voz
                i0, i1 = int(ws_ * 100), max(int(ws_ * 100) + 1, int(we_ * 100))
                if r[i0:i1].size and r[i0:i1].max() < lim:
                    continue
                ws.append({"w": w["word"].strip(), "s": round(ws_ + ini, 2), "e": round(we_ + ini, 2)})
        txt = " ".join(w["w"] for w in ws)
        out.append({"a": round(s + ini, 2), "b": round(e + ini, 2), "texto": txt, "palavras": ws})
        todas += ws
        print("[%7.2f-%7.2f] %s" % (s + ini, e + ini, txt), flush=True)
        for w in ws:  # palavra longa demais numa fala corrida = trecho engolido
            if w["e"] - w["s"] > 1.5:
                print("   ! '%s' dura %.1f s — o Whisper pode ter engolido fala aqui; reconfira esta janela." % (w["w"], w["e"] - w["s"]))
    gravar_json(a.saida, {"modelo": "whisper %s (%s), por trecho de fala, word_timestamps" % (a.modelo, a.lingua),
                          "limiar_db": round(lim, 1), "trechos": out, "palavras": todas})
    txt = os.path.splitext(a.saida)[0] + ".txt"
    with open(txt, "w", encoding="utf-8") as f:
        for t in out:
            f.write("[%7.2f-%7.2f] %s\n" % (t["a"], t["b"], t["texto"]))
    print("ok ->", a.saida, "e", txt)


if __name__ == "__main__":
    main()
