#!/usr/bin/env python3
"""
Fila de geracao no Higgsfield pelo CLI — imagens e videos, em lote, com retry.

Por que existe: gerar uma cena por vez leva ~5 min cada (43 cenas = 4 h). E
submeter tudo de uma vez estoura o teto da conta e metade falha CALADA — o erro
so aparece se voce imprimir o retorno do submit.

A fila resolve os dois: N workers, cada um submete → espera → pega a proxima.
Com backoff quando bate no `rate_limit_reached`.

    python3 gerar_lote.py --spec cenas.json --tipo imagem --out ./saida
    python3 gerar_lote.py --spec cenas.json --tipo video  --out ./saida --workers 4

Formato do `cenas.json` — uma lista de objetos:

    [{"id": "01",
      "prompt": "...",
      "refs": ["ancoras/sarah.png", "estilo.png"],   # imagem: image-references
      "duracao": 12,                                  # video: segundos (4..15)
      "start": "saida/cena01.png"}]                   # video: frame inicial

O indice de URLs é gravado com lock e relido antes de cada escrita — dois
processos gravando o mesmo JSON se sobrescrevem, e ja custou 7 URLs apagadas.
"""
import argparse, json, math, os, re, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

UUID = re.compile(r'"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"')
lock = threading.Lock()

# limites do Seedance, aprendidos na marra
DUR_MIN, DUR_MAX = 4, 15


def grava(indice, chave, url):
    with lock:
        d = json.load(open(indice)) if os.path.exists(indice) else {}
        d[chave] = url
        json.dump(d, open(indice, "w"), indent=1)


def lido(indice):
    return json.load(open(indice)) if os.path.exists(indice) else {}


def submete(cmd, chave, tentativas=10):
    """Devolve o job_id. Espera e tenta de novo quando bate no teto da conta."""
    for i in range(tentativas):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
            blob = (r.stdout or "") + (r.stderr or "")
            if "rate_limit_reached" in blob:
                time.sleep(45); continue
            m = UUID.search(blob)
            if m:
                return m.group(1)
            print(f"{chave} submit t{i+1}: {blob.strip()[-90:]}", flush=True)
            time.sleep(20)
        except subprocess.TimeoutExpired:
            time.sleep(20)
    return None


def espera(jid, chave):
    try:
        r = subprocess.run(["higgsfield", "generate", "wait", jid,
                            "--timeout", "25m", "--quiet"],
                           capture_output=True, text=True, timeout=1600)
        blob = (r.stdout or "") + (r.stderr or "")
        for linha in blob.strip().splitlines()[::-1]:
            if "cloudfront" in linha and "http" in linha:
                return linha.strip().split()[-1]
        # status nsfw / failed vem aqui — importa distinguir de erro de rede
        print(f"{chave} sem url: {blob.strip()[-90:]}", flush=True)
    except Exception as e:
        print(f"{chave} wait erro {e}", flush=True)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--tipo", required=True, choices=["imagem", "video"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4,
                    help="4 e o padrao: o teto da conta e 8 e e dividido com a equipe")
    ap.add_argument("--modelo", default=None)
    ap.add_argument("--resolucao", default=None)
    ap.add_argument("--aspect", default="9:16")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    indice = os.path.join(a.out, f"{a.tipo}_urls.json")
    cenas = json.load(open(a.spec))
    modelo = a.modelo or ("nano_banana_pro" if a.tipo == "imagem" else "seedance_2_0")
    resol = a.resolucao or ("2k" if a.tipo == "imagem" else "720p")

    def uma(c):
        chave = str(c["id"])
        if chave in lido(indice):
            return
        if a.tipo == "imagem":
            cmd = ["higgsfield", "generate", "create", modelo,
                   "--aspect_ratio", a.aspect, "--resolution", resol]
            for r in c.get("refs", []):
                if os.path.exists(r):
                    cmd += ["--image-references", r]
            cmd += ["--prompt", c["prompt"], "--json"]
            alvo = os.path.join(a.out, f"cena{chave}.png")
        else:
            start = c.get("start")
            if not start or not os.path.exists(start):
                print(f"{chave} SEM FRAME INICIAL", flush=True); return
            d = max(DUR_MIN, min(DUR_MAX, math.ceil(c.get("duracao", 5))))
            cmd = ["higgsfield", "generate", "create", modelo,
                   "--resolution", resol, "--aspect_ratio", a.aspect,
                   "--duration", str(d), "--generate_audio", "false",
                   "--mode", "fast", "--start-image", start,
                   "--prompt", c["prompt"], "--json"]
            alvo = os.path.join(a.out, f"v_cena{chave}.mp4")

        jid = submete(cmd, chave)
        if not jid:
            print(f"{chave} NAO SUBMETEU", flush=True); return
        url = espera(jid, chave)
        if not url:
            return
        grava(indice, chave, url)
        subprocess.run(["curl", "-sL", "-o", alvo, url])
        print(f"{chave} OK", flush=True)

    pendentes = [c for c in cenas if str(c["id"]) not in lido(indice)]
    print(f"fila: {len(pendentes)} {a.tipo}(s), {a.workers} simultaneos "
          f"[{modelo} {resol}]", flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(uma, pendentes))

    feito = lido(indice)
    falta = [str(c["id"]) for c in cenas if str(c["id"]) not in feito]
    print(f"\nFIM — {len(feito)}/{len(cenas)}", flush=True)
    if falta:
        print("faltando:", falta)
        print("Rodar de novo: a fila pula o que ja esta pronto.")


if __name__ == "__main__":
    main()
