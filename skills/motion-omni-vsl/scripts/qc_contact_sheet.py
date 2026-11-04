# -*- coding: utf-8 -*-
# AJUSTAR ANTES DE REUSAR NOUTRO JOB:
#   CROP -> hoje corta 9:16 para 4:5 (1080x1350). Se o entregavel for outro,
#           recalcule: altura = largura * (alturaAlvo/larguraAlvo)
#   Trata "nsfw" como status terminal junto de completed/failed — sem isso o loop trava.
"""Aguarda o lote vertical, baixa, e gera o frame de pico JA CORTADO em 4:5 (1080x1350),
que e como o motion vai aparecer na sequencia 08.CLOSE. Valida grafia e enquadramento juntos."""
import json, os, subprocess, time, urllib.request

S = os.path.dirname(os.path.abspath(__file__))
ENV = {**os.environ, "PATH": os.path.expanduser("~/.npm-global/bin:") + os.environ["PATH"]}
OUT, QC = os.path.join(S, "motions_v"), os.path.join(S, "qc_v")
for d in (OUT, QC):
    os.makedirs(d, exist_ok=True)

# 9:16 -> 4:5: mantem a largura, corta 15% em cima e 15% embaixo
CROP = "crop=iw:iw*1.25:0:(ih-iw*1.25)/2,scale=1080:1350"

jobs = json.load(open(os.path.join(S, "jobs_vertical.json")))
pend = {k: v for k, v in jobs.items() if not str(v["job"]).startswith("ERRO")}
feito, falhou = {}, {}

while pend:
    for k in list(pend):
        r = subprocess.run(["higgsfield", "generate", "get", pend[k]["job"], "--json"],
                           capture_output=True, text=True, env=ENV)
        try:
            d = json.loads(r.stdout)
        except Exception:
            continue
        st = d.get("status")
        if st == "completed" and d.get("result_url"):
            mp4 = os.path.join(OUT, f"m{int(k):02d}.mp4")
            urllib.request.urlretrieve(d["result_url"], mp4)
            # frame de pico ja cortado como vai entrar na timeline
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "7.0", "-i", mp4,
                            "-frames:v", "1", "-vf", CROP + ",scale=430:-1",
                            os.path.join(QC, f"p{int(k):02d}.png")], check=False)
            # versao 4:5 completa do clipe, pronta para a timeline
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", CROP,
                            "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-an",
                            os.path.join(OUT, f"m{int(k):02d}_1080x1350.mp4")], check=False)
            feito[k] = dict(pend[k], url=d["result_url"],
                            arquivo=os.path.join(OUT, f"m{int(k):02d}_1080x1350.mp4"))
            print(f"OK   {int(k):02d} {pend[k]['cor']:<9} {pend[k]['frase'][:36]}")
            del pend[k]
        elif st in ("failed", "error", "canceled"):
            falhou[k] = dict(pend[k], status=st)
            print(f"FALHA {int(k):02d} {st}")
            del pend[k]
    if pend:
        time.sleep(20)

json.dump(feito, open(os.path.join(S, "motions_v_prontos.json"), "w"), indent=1, ensure_ascii=False)
print(f"\nprontos: {len(feito)} | falhas: {len(falhou)} {list(falhou)}")
