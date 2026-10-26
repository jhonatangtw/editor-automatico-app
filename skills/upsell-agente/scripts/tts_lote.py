#!/usr/bin/env python3
"""TTS em lote na ElevenLabs (eleven_v4, com timestamps por caractere) para os blocos do upsell.
    python3 tts_lote.py <blocos.json> <pasta_saida> <voice_id_apresentador> [vozes_depoentes.json]
vozes_depoentes.json = {"D01": "<voice_id>", ...}. Saída: <id>.mp3 + <id>_alin.json (é o alinhamento que
o build usa para legenda e tempos — nunca o Whisper). Chave em ELEVENLABS_API_KEY (variável de ambiente; não imprimir).
Depois rode qc_tts.py e refaça só o que errar (troque o seed).
"""
import json, os, sys, base64, subprocess, urllib.request
from concurrent.futures import ThreadPoolExecutor

blocos, OUT, VAP = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
VDEP = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}
os.makedirs(OUT, exist_ok=True)
K = os.environ.get("ELEVENLABS_API_KEY") or ""
if not K:
    sys.exit("Defina ELEVENLABS_API_KEY (a mesma chave da aba Contas do Editor Automatico).")

def tts(b, seed=None):
    vid = VDEP.get(b["id"]) if b["tipo"] == "depoente" else VAP
    if not vid: return f'{b["id"]} SEM VOZ'
    st = (0.45, 0.8, 0.3) if b["tipo"] == "depoente" else (0.5, 0.8, 0.25)
    body = {"text": b["txt"], "model_id": "eleven_v4",
            "voice_settings": {"stability": st[0], "similarity_boost": st[1], "style": st[2], "use_speaker_boost": True}}
    if seed is not None: body["seed"] = seed
    r = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_128",
                               data=json.dumps(body).encode(), headers={"xi-api-key": K, "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(r, timeout=180))
    base = os.path.join(OUT, b["id"])
    open(base + ".mp3", "wb").write(base64.b64decode(d["audio_base64"]))
    json.dump(d["alignment"], open(base + "_alin.json", "w"))
    du = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", base + ".mp3"],
                        capture_output=True, text=True).stdout.strip()
    return f'{b["id"]} {du}s {len(b["txt"])} caracteres'

with ThreadPoolExecutor(4) as ex:
    for r in ex.map(tts, blocos): print(r)
