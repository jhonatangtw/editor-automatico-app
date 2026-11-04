#!/usr/bin/env python3
"""Gera as imagens do plano.json no Higgsfield (GPT Image 2.5, 9:16, 2k).

Uso (dentro de <JOB>/broll, ao lado do plano.json):
    python3 gerar_broll.py --custo          # só mostra o custo de cada imagem, não gera nada
    python3 gerar_broll.py                  # gera todas que ainda não existem em imagens/
    python3 gerar_broll.py BR01 BR07        # gera (ou refaz) só essas

Cenas com "ref": true levam a foto da personagem (../avatar/H1_start.png) como referência.

Por que este jeito (cada item é uma lição paga):
  * envia SEM --wait e acompanha pelo `generate list`: com vários jobs juntos o --wait estoura
    o tempo e parece falha, mas o job foi criado e cobrado;
  * o --json do create devolve uma LISTA de ids, não um objeto;
  * baixa pelo `result_url` — o `min_result_url` é miniatura de ~600 px;
  * se o envio der erro, NÃO reenvie no escuro: confira `higgsfield generate list --image --json`.
"""
import json, os, shutil, subprocess, sys, time, urllib.request

B = os.path.dirname(os.path.abspath(__file__)) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plano.json")) else os.getcwd()
OUT = os.path.join(B, "imagens")
REF = os.environ.get("REF_PERSONAGEM") or os.path.join(B, "..", "avatar", "H1_start.png")
HF = shutil.which("higgsfield") or "higgsfield"
MODELO = os.environ.get("MODELO_IMAGEM", "gpt_image_2_5")
os.makedirs(OUT, exist_ok=True)


def hf(*args):
    r = subprocess.run([HF, *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout).strip()[-300:])
    return r.stdout


def base(p):
    a = ["--prompt", p["prompt"], "--aspect_ratio", "9:16", "--quality", "high", "--resolution", "2k"]
    if p.get("ref"):
        a += ["--image-references", REF]
    return a


def baixar(falta, minutos=45):
    """Acompanha os jobs {job_id: cena} pelo `generate list` e baixa o result_url."""
    for _ in range(int(minutos * 4)):
        if not falta:
            break
        time.sleep(15)
        for j in json.loads(hf("generate", "list", "--image", "--json", "--size", "50")):
            jid = j.get("id")
            if jid not in falta:
                continue
            st = (j.get("status") or "").lower()
            if j.get("result_url"):
                dest = os.path.join(OUT, falta.pop(jid) + ".png")
                urllib.request.urlretrieve(j["result_url"], dest)
                print("ok", os.path.basename(dest), flush=True)
            elif st in ("failed", "error", "nsfw", "canceled", "cancelled"):
                print("FALHOU", falta.pop(jid), st, flush=True)
    return falta


def main():
    plano = json.load(open(os.path.join(B, "plano.json")))
    pend_arq = os.path.join(OUT, "_pendentes.json")
    pend = json.load(open(pend_arq)) if os.path.exists(pend_arq) else {}
    if pend:  # job já pago numa rodada anterior: só baixa, nunca reenvia
        print("baixando", len(pend), "pendente(s) da rodada anterior")
        pend = baixar(pend, 10)

    so = [x for x in sys.argv[1:] if not x.startswith("--")]
    em_fila = set(pend.values())
    if so:
        alvo = [p for p in plano if p["id"] in so and p["id"] not in em_fila]
    else:
        alvo = [p for p in plano if p["id"] not in em_fila and not os.path.exists(os.path.join(OUT, p["id"] + ".png"))]
    if not alvo:
        json.dump(pend, open(pend_arq, "w")) if pend else (os.path.exists(pend_arq) and os.remove(pend_arq))
        print("nada novo a gerar"); return
    if any(p.get("ref") for p in alvo) and not os.path.exists(REF):
        sys.exit(f"x falta a foto da personagem: {REF}")

    if "--custo" in sys.argv:
        for p in alvo:
            print(p["id"], hf("generate", "cost", MODELO, *base(p)).strip().splitlines()[-1])
        return

    for p in alvo:
        try:
            pend[json.loads(hf("generate", "create", MODELO, *base(p), "--json"))[0]] = p["id"]
            json.dump(pend, open(pend_arq, "w"))   # grava ANTES de esperar: o job já foi cobrado
            print("enviado", p["id"], flush=True)
        except Exception as e:
            print("FALHOU NO ENVIO", p["id"], "-", e, "(confira o generate list antes de reenviar)", flush=True)
        time.sleep(4)

    pend = baixar(pend)
    if pend:
        json.dump(pend, open(pend_arq, "w"))
        for jid, pid in pend.items():
            print("AINDA NA FILA", pid, "- rode de novo: só baixa, não cobra outra vez")
    elif os.path.exists(pend_arq):
        os.remove(pend_arq)


if __name__ == "__main__":
    main()
