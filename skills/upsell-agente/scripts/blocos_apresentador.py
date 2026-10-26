#!/usr/bin/env python3
"""Divide a copy marcada em blocos para TTS + Avatar IV.
A copy (copy.md) usa marcadores [APRESENTADOR], [NOME SOBRENOME, IDADE] e [PREÇO A]/[PREÇO B]/[PREÇO C]
no início de cada fala (ver references/RECEITA.md § copy.md). O texto vem depois de uma linha '---'.

    python3 blocos_apresentador.py <copy.md> <saida.json> [palavras_por_bloco=85]

- Falas do apresentador entre depoimentos viram blocos S01..Snn de ~85 palavras, sempre fechando em fim de frase
  (bloco longo no Avatar IV deriva; ~30–40 s por bloco é o ponto bom).
- Cada [PREÇO x] vira um bloco próprio PRECO_x (só a 1ª linha depois do marcador; o resto volta para o apresentador).
- Depoimentos viram D01..Dnn com nome/idade.
"""
import re, json, sys

src, out = sys.argv[1], sys.argv[2]
ALVO = int(sys.argv[3]) if len(sys.argv) > 3 else 85
t = open(src).read().split("---", 1)[1].replace("’", "'")
blocos = re.findall(r"\[([^\]]+)\]([^\[]*)", t)

seq = []
for q, txt in blocos:
    txt = txt.strip()
    if q.upper().startswith("PREÇO") or q.upper().startswith("PRECO"):
        v = q.split()[-1].upper()
        linhas = txt.split("\n", 1)
        seq.append(("PRECO_" + v, linhas[0].strip()))
        if len(linhas) > 1 and linhas[1].strip(): seq.append(("AP", linhas[1].strip()))
    elif "," in q and re.search(r"\d+\s*$", q):  # depoente "NOME, 71"
        seq.append(("DEP:" + q.strip(), txt))
    else:
        seq.append(("AP", txt))

res, cur, ns, nd = [], None, 0, 0
def fecha_ap(texto):
    global ns
    frases = re.split(r"(?<=[.?!…])\s+", texto.strip()); buf = []
    partes = []
    for f in frases:
        buf.append(f)
        if len(" ".join(buf).split()) >= ALVO: partes.append(" ".join(buf)); buf = []
    if buf:
        if partes and len(" ".join(buf).split()) < 30: partes[-1] += " " + " ".join(buf)
        else: partes.append(" ".join(buf))
    for p in partes:
        ns += 1; res.append({"id": f"S{ns:02d}", "tipo": "apresentador", "txt": p, "palavras": len(p.split())})

for k, txt in seq:
    if k == "AP":
        cur = (cur + " " + txt) if cur else txt; continue
    if cur: fecha_ap(cur); cur = None
    if k.startswith("PRECO_"):
        res.append({"id": k, "tipo": "preco", "txt": txt, "palavras": len(txt.split())})
    else:
        nd += 1; nome, idade = k[4:].rsplit(",", 1)
        res.append({"id": f"D{nd:02d}", "tipo": "depoente", "nome": nome.strip().title(), "idade": int(idade),
                    "txt": txt.strip().strip('"“”'), "palavras": len(txt.split())})
if cur: fecha_ap(cur)
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
for b in res: print(f'{b["id"]:9s} {b["palavras"]:4d} palavras ~{b["palavras"] / 2.5:4.0f}s  {b["txt"][:60]}')
