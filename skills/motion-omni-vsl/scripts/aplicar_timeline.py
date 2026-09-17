# -*- coding: utf-8 -*-
# AJUSTAR ANTES DE REUSAR NOUTRO JOB:
#   DEST -> pasta 4.Motion do projeto
#   SEQ  -> nome exato da sequencia ativa
#   V2   -> trilha base 0 (V1=0, V2=1)
#   FIM_RESOLVE = 8.8 -> fim do beat RESOLVE, define a regra de entrada no clipe
"""Copia os motions para a pasta do projeto, importa e coloca na V2 da 08.CLOSE."""
import json, os, re, shutil, sys, unicodedata, urllib.request

S = os.path.dirname(os.path.abspath(__file__))
TOK = json.load(open(os.path.expanduser("~/.editor-black-belt/mcp-ppro.json")))["token"]
SEQ = "08.CLOSE"
V2 = 1                      # trilha base 0: V1=0, V2=1
FIM_RESOLVE = 8.8
# A pasta 4.Motion do projeto. Vem da variavel MOTION_DEST justamente porque
# MUDA A CADA JOB: caminho cravado aqui escreveria os motions no projeto errado,
# e num computador que nao seja o do autor nem existe.
#   export MOTION_DEST="/.../<projeto>/4.Motion/08 Close"
DEST = os.environ.get("MOTION_DEST", "").rstrip("/")
if not DEST:
    sys.exit("ABORTADO: defina MOTION_DEST com a pasta 4.Motion deste projeto.\n"
             '  export MOTION_DEST="/caminho/do/projeto/4.Motion/08 Close"')


def call(name, args=None):
    req = urllib.request.Request(
        "http://127.0.0.1:7842/mcp",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": name, "arguments": args or {}}}).encode(),
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream",
                 "Authorization": "Bearer " + TOK})
    txt = json.load(urllib.request.urlopen(req, timeout=300))["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"ok": False, "texto_cru": txt}


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:38]


def main():
    simular = "--simular" in sys.argv
    info = call("pr_marcadores_info")
    if info.get("name") != SEQ:
        print(f"ABORTADO: sequencia ativa e {info.get('name')!r}, esperava {SEQ!r}")
        return
    marc = sorted(call("pr_marcadores_listar").get("itens", []), key=lambda m: m.get("tempo", 0))
    prontos = json.load(open(os.path.join(S, "motions_v_prontos.json")))

    os.makedirs(DEST, exist_ok=True)
    clipes, pulados = [], []
    for k in sorted(prontos, key=int):
        n = int(k)
        v = prontos[k]
        alvo = next((m for m in marc if m.get("nome", "").startswith(f"{n:02d} ")), None)
        if not alvo:
            pulados.append((n, "sem marcador")); continue
        d = alvo.get("duracao") or 0
        if d <= 0:
            pulados.append((n, "marcador de ponto (pre-roll do Host)")); continue
        entrada = round(max(0.0, FIM_RESOLVE - d), 2)
        saida = round(min(10.0, entrada + d), 2)
        nome = f"08-MO-{n:02d}_{slug(v['frase'])}.mp4"
        destino = os.path.join(DEST, nome)
        if not simular and not os.path.exists(destino):
            shutil.copy2(v["arquivo"], destino)
        clipes.append(dict(n=n, cor=v["cor"], frase=v["frase"], nome=nome, caminho=destino,
                           tempo=round(alvo["tempo"], 2), dur=round(d, 2),
                           entrada=entrada, saida=saida,
                           sobra=round(max(0.0, d - (saida - entrada)), 2)))

    print(f"{'#':>3} {'cor':<9} {'TL':>8} {'dur':>6} {'in':>5} {'out':>5}  arquivo")
    for c in clipes:
        print(f"{c['n']:>3} {c['cor']:<9} {c['tempo']:>8.2f} {c['dur']:>6.2f} "
              f"{c['entrada']:>5.2f} {c['saida']:>5.2f}  {c['nome']}"
              + (f"   [motion cobre 10s de {c['dur']}s]" if c["sobra"] else ""))
    for n, m in pulados:
        print(f"{n:>3} -- pulado: {m}")
    if simular:
        print(f"\n[simulacao] {len(clipes)} clipes iriam para a V2")
        return

    imp = call("pr_midia_importar", {"arquivos": [c["caminho"] for c in clipes],
                                     "bin": "08 Close Motions"})
    print("\nimportar:", json.dumps(imp, ensure_ascii=False)[:300])

    r = call("pr_timeline_colocar", {
        "sequencia": SEQ,
        "clipes": [dict(nome=c["nome"], trilha=V2, tempo=c["tempo"],
                        entrada=c["entrada"], saida=c["saida"], modo="sobrescrever")
                   for c in clipes]})
    print("colocar:", json.dumps(r, ensure_ascii=False)[:600])
    json.dump(clipes, open(os.path.join(S, "aplicados.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
