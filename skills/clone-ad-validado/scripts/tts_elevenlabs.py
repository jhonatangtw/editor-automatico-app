#!/usr/bin/env python3
"""Gera a locução no ElevenLabs COM o tempo de cada palavra.

    export ELEVENLABS_API_KEY="..."      # a chave vem do ambiente, nunca do código nem do chat
    python3 tts_elevenlabs.py VOICE_ID "Texto da fala." voz/cand_a.mp3
    python3 tts_elevenlabs.py VOICE_ID --arquivo copy.txt voz/voz_nova.mp3 [modelo]

Grava o .mp3 e, ao lado, um .json com {"alignment": ..., "words": [{text, start, end}]}.
O JSON é o que vira legenda e encaixe — guarde os dois JUNTOS, na pasta do job.

⚠️ TTS não é idempotente: gerar de novo o mesmo texto, com a mesma voz e os
mesmos ajustes, devolve durações diferentes. Regerou o áudio? Regere tudo o
que foi calculado em cima do JSON antigo (encaixe, legenda).

Isto GASTA crédito do ElevenLabs: rode só depois de o usuário aprovar.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request


def main(a):
    if len(a) < 3:
        sys.exit(__doc__)
    chave = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not chave:
        sys.exit("Defina ELEVENLABS_API_KEY no ambiente (a mesma chave da aba Contas do Editor Automático).")
    voz = a[0]
    if a[1] == "--arquivo":
        texto = open(a[2], encoding="utf-8").read().strip()
        resto = a[3:]
    else:
        texto, resto = a[1], a[2:]
    saida = resto[0]
    modelo = resto[1] if len(resto) > 1 else "eleven_multilingual_v2"
    corpo = {"text": texto, "model_id": modelo,
             "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}}
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps?output_format=mp3_44100_128" % voz,
        data=json.dumps(corpo).encode(), headers={"xi-api-key": chave, "Content-Type": "application/json"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        sys.exit("HTTP %s: %s" % (e.code, e.read()[:300].decode("utf-8", "replace")))
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    with open(saida, "wb") as f:
        f.write(base64.b64decode(d["audio_base64"]))
    al = d["alignment"]
    palavras, cur, ini, fim_ant = [], "", None, None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur:
                palavras.append({"text": cur, "start": ini, "end": fim_ant})
                cur = ""
            continue
        if not cur:
            ini = s
        cur += ch
        fim_ant = e
    if cur:
        palavras.append({"text": cur, "start": ini, "end": fim_ant})
    with open(os.path.splitext(saida)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump({"alignment": al, "words": palavras}, f, ensure_ascii=False, indent=1)
    print("%s  %.2f s  %d palavras" % (saida, palavras[-1]["end"] if palavras else 0, len(palavras)))


if __name__ == "__main__":
    main(sys.argv[1:])
