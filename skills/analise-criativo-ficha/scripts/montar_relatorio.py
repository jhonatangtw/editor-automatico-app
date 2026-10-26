#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
montar_relatorio.py  —  Gera o relatório combinado de criativo (padrão PONTE).

Junta 3 camadas num único HTML auto-contido, por criativo:
  1) QA técnico   (checks automáticos vindos do _QA/dados.json)
  2) Detalhamento (card AD-por-AD: visual + edição + transcrição + pontos de atenção)
  3) PONTE        (análise estratégica de conversão: nota por letra + matriz de teste)

O QA (camada 1) é 100% automático. As camadas 2 e 3 dependem de JULGAMENTO
(ler o mosaico, avaliar a copy) — por isso vêm de um "análise.json" que o Claude
preenche por criativo. Este script só faz o templating consistente.

USO:
  python3 montar_relatorio.py --qa "<pasta>/_QA" --analise analise.json -o "<pasta>"

FORMATO do analise.json (lista, um objeto por criativo — a chave `name` casa com o _QA):
[
  {
    "name": "AD10_H1",
    "badge": "AD10 H1",
    "produto": "Sonnus — gummies naturais p/ dormir (nutra EN/US)",
    "one_line": "Criadora loira, filmada em casa; b-roll de melatonina, frasco azul, laudos...",
    "resumo_edicao": "Talking-head no ângulo '...'. Alterna ... Fecha com ...",
    "transcricao": "It is impossible to take this melatonin...",
    "ficha": {  # OPCIONAL (criativo/AD): espelha o meta do .docx ADS -> renderiza no rodapé
      "tipo": "...", "plataforma": "...", "nicho": "...", "formato": "...", "tom": "...",
      "consciencia": "...", "sofisticacao": "...", "angulo": "...", "framework": "...",
      "mup": "...", "mus": "...", "publico": "...", "deeper": "...",
      "flow": {"hook": "...", "corpo": "...", "close": "..."}
    },  # -> "Ficha Técnica do Anúncio" + "Mapa de Fluxo Persuasivo"
    "ficha_vsl": {  # OPCIONAL (VSL, com --tipo vsl): espelha o meta do .docx VSL
      "vsl_name": "...", "product_type": "...", "date": "...", "formato_lead": "...",
      "tom": "...", "foco": "...", "mup": "...", "mus": "...",
      "nome_chiclete_problema": "...", "nome_chiclete_solucao": "...",
      "personagens": [{"nome": "...", "tipo": "...", "funcao_curta": "..."}],
      "ingredientes_hero": ["..."], "superestruturas": ["..."], "lead_variants": 1,
      "flow_summary": {"lead": "...", "storytelling": "...", "tese": "...", "fechamento": "..."}
    },  # -> "Ficha Técnica da VSL" + "Personagens Principais" + "Mapa de Fluxo da VSL"
    "atencao": [
      {"sev": "orange", "texto": "Duração 2:08 (>120s) — longo pra tráfego frio."},
      {"sev": "yellow", "texto": "Mecanismo afirmado sem nomear ingrediente."},
      {"sev": "plain",  "texto": "Mesma criadora/roteiro dos demais ADs da série."}
    ],
    "ponte": {
      "O": {"nota": 4, "veredito": "Dor cirúrgica; falta rastrear origem",
            "pontos": [{"tipo":"good","txt":"Dor sensorial (3h, café, filhos)"},
                       {"tipo":"bad","txt":"Origem do hook não rastreada"}]},
      "P": {"nota": 4, "veredito": "...", "pontos": [...]},
      "T": {"nota": 3, "veredito": "...", "pontos": [...]},
      "N": {"nota": 4, "veredito": "...", "pontos": [...]},
      "E": {"nota": 2, "veredito": "...", "pontos": [...]},
      "global": 3.4,
      "acoes": ["Reescrever CTA com oferta+garantia+urgência", "...", "..."],
      "matriz": [
        {"eixo":"Hook","de":"O","testar":"H2 descoberta pela filha · H3 choque do exame"},
        {"eixo":"CTA/oferta","de":"P","testar":"+ desconto · + garantia · + urgência"}
      ]
    }
  }
]

Campos ausentes são tolerados (a seção correspondente é omitida). Se o analise.json
não existir, o script gera só a camada de QA técnico.
"""
import argparse, base64, html, json, os, sys

# -------- helpers --------
LETRAS = {
    "O": ("Orgânico decupado", "Combustível"),
    "P": ("Persuasão", "Esqueleto"),
    "T": ("Traduzir mecanismo", "Diferencial"),
    "N": ("Native creator", "Embalagem"),
    "E": ("Experimentação", "Motor"),
}
SEV_DOT = {"red": "&#128308;", "orange": "&#128992;", "yellow": "&#128993;", "plain": "&#9899;"}

def esc(s):
    return html.escape(str(s), quote=False) if s is not None else ""

def fmt_dur(sec):
    sec = int(round(sec or 0)); return f"{sec//60}:{sec%60:02d}"

def nota_classe(n):
    try: n = float(n)
    except Exception: return "s3"
    return "s4" if n >= 4 else ("s3" if n >= 3 else "s2")

def data_uri(path):
    if not path or not os.path.isfile(path): return ""
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "jpeg"
    if ext == "jpg": ext = "jpeg"
    with open(path, "rb") as f:
        return f"data:image/{ext};base64," + base64.b64encode(f.read()).decode()

def load_qa(qa_dir):
    """Devolve dict name -> record (do dados.json) e caminhos de mosaico/transcrição."""
    dados = {}
    p = os.path.join(qa_dir, "dados.json")
    if os.path.isfile(p):
        for r in json.load(open(p, encoding="utf-8")):
            dados[r.get("name", "")] = r
    return dados

def read_transcript(qa_dir, name):
    p = os.path.join(qa_dir, "transcripts", name + ".txt")
    if os.path.isfile(p):
        # remove timestamps [..] no começo de cada linha, junta em parágrafo
        import re
        txt = open(p, encoding="utf-8").read()
        txt = re.sub(r"^\[[^\]]*\]\s*", "", txt, flags=re.M)
        return " ".join(l.strip() for l in txt.splitlines() if l.strip())
    return ""

# -------- render de um card --------
FICHA_LABELS = [
    ("tipo", "Tipo de criativo"), ("plataforma", "Plataforma"), ("nicho", "Nicho / Subnicho"),
    ("formato", "Formato dominante"), ("tom", "Tom"), ("consciencia", "Nível de consciência"),
    ("sofisticacao", "Sofisticação"), ("angulo", "Ângulo dominante"), ("framework", "Framework"),
    ("mup", "MUP (vilão)"), ("mus", "MUS (solução)"), ("publico", "Público / postura"),
    ("deeper", "Deeper Core"),
]

def render_ficha(fi):
    """Ficha Técnica do Anúncio + Mapa de Fluxo Persuasivo (mesmos campos do meta do .docx ADS)."""
    if not fi:
        return ""
    rows = ""
    for k, lbl in FICHA_LABELS:
        v = fi.get(k)
        if v:
            rows += f'<tr><td class="k">{esc(lbl)}</td><td class="v">{esc_rich(v)}</td></tr>'
    out = f'<h4>Ficha Técnica do Anúncio</h4><table class="ficha">{rows}</table>' if rows else ""
    fl = fi.get("flow") or {}
    if fl.get("hook") or fl.get("corpo") or fl.get("close"):
        out += ('<h4>Mapa de Fluxo Persuasivo</h4><div class="fluxo">'
                f'<div class="fx hk"><div class="fxh">Hook</div><div class="fxt">{esc_rich(fl.get("hook",""))}</div></div>'
                f'<div class="fx bd"><div class="fxh">Corpo</div><div class="fxt">{esc_rich(fl.get("corpo",""))}</div></div>'
                f'<div class="fx cl"><div class="fxh">Close / CTA</div><div class="fxt">{esc_rich(fl.get("close",""))}</div></div>'
                '</div>')
    return out

def render_ficha_vsl(fi):
    """Ficha Técnica da VSL + Personagens Principais + Mapa de Fluxo da VSL (campos do meta do .docx VSL)."""
    if not fi:
        return ""
    def row(lbl, val):
        return f'<tr><td class="k">{esc(lbl)}</td><td class="v">{esc_rich(val)}</td></tr>' if val else ""
    prod = " — ".join(x for x in [fi.get("vsl_name"), fi.get("product_type")] if x)
    rows = row("VSL / Produto", prod) + row("Data", fi.get("date"))
    rows += row("Formato da Lead", fi.get("formato_lead")) + row("Tom", fi.get("tom")) + row("Foco", fi.get("foco"))
    rows += row("MUP (problema)", fi.get("mup")) + row("MUS (solução)", fi.get("mus"))
    rows += row("Nome chiclete — problema", fi.get("nome_chiclete_problema"))
    rows += row("Nome chiclete — solução", fi.get("nome_chiclete_solucao"))
    if fi.get("ingredientes_hero"): rows += row("Ingredientes hero", ", ".join(fi["ingredientes_hero"]))
    if fi.get("superestruturas"): rows += row("Superestruturas", ", ".join(fi["superestruturas"]))
    if fi.get("lead_variants") is not None: rows += row("Variantes de lead", str(fi["lead_variants"]))
    out = f'<h4>Ficha Técnica da VSL</h4><table class="ficha">{rows}</table>' if rows else ""
    pers = fi.get("personagens") or []
    if pers:
        prows = "".join(
            f'<tr><td><b>{esc(p.get("nome",""))}</b></td><td>{esc(p.get("tipo",""))}</td><td>{esc_rich(p.get("funcao_curta",""))}</td></tr>'
            for p in pers)
        out += f'<h4>Personagens Principais</h4><table><tr><th>Personagem</th><th>Tipo</th><th>Função</th></tr>{prows}</table>'
    fl = fi.get("flow_summary") or {}
    if any(fl.get(k) for k in ("lead", "storytelling", "tese", "fechamento")):
        out += ('<h4>Mapa de Fluxo da VSL</h4><div class="fluxo f4">'
                f'<div class="fx hk"><div class="fxh">Lead</div><div class="fxt">{esc_rich(fl.get("lead",""))}</div></div>'
                f'<div class="fx bd"><div class="fxh">Storytelling</div><div class="fxt">{esc_rich(fl.get("storytelling",""))}</div></div>'
                f'<div class="fx gd"><div class="fxh">Tese</div><div class="fxt">{esc_rich(fl.get("tese",""))}</div></div>'
                f'<div class="fx cl"><div class="fxh">Fechamento</div><div class="fxt">{esc_rich(fl.get("fechamento",""))}</div></div>'
                '</div>')
    return out

def render_card(a, qa, qa_dir, show_ponte=True, tipo="ad"):
    _arco = "arco completo da VSL" if tipo == "vsl" else "arco completo do AD"
    name = a.get("name", "")
    rec = qa.get(name, {})
    info = rec.get("info", {})
    dur = fmt_dur(info.get("dur", 0)) if info else a.get("duracao", "—")
    res = f'{info.get("w","?")}&times;{info.get("h","?")}' if info else a.get("resolucao", "—")
    fps = info.get("fps", a.get("fps", "—"))
    audio = "sim" if info.get("audio", True) else "não"
    flags = rec.get("flags", [])

    mosaic = a.get("mosaic_path") or os.path.join(qa_dir, "montage", name + ".jpg")
    mosaic_uri = data_uri(mosaic)
    transcript = a.get("transcricao") or read_transcript(qa_dir, name)

    # ---- QA técnico chips ----
    if flags:
        chips = "".join(
            f'<span class="chip {f["sev"]}">{esc(f.get("code",""))}: {esc(f.get("msg",""))}</span>'
            for f in flags)
        qa_line = chips
    else:
        qa_line = '<span class="chip ok">Sem apontes técnicos — pronto pra subir</span>'

    # ---- pontos de atenção ----
    at = ""
    for it in a.get("atencao", []):
        dot = SEV_DOT.get(it.get("sev", "yellow"), SEV_DOT["yellow"])
        cls = "plain" if it.get("sev") == "plain" else ""
        at += f'<li class="{cls}"><span class="dot">{dot}</span>{esc_rich(it.get("texto",""))}</li>'

    # ---- Ficha Técnica + Mapa de Fluxo (do meta do .docx) ----
    ficha_html = render_ficha_vsl(a.get("ficha_vsl")) if tipo == "vsl" else render_ficha(a.get("ficha"))

    # ---- PONTE (opcional) ----
    ponte_html = render_ponte(a.get("ponte")) if show_ponte else ""

    return f"""
    <div class="card">
      <div class="head">
        <div class="badge">{esc(a.get("badge", name))}</div>
        <div class="desc">{esc_rich(a.get("one_line",""))}
          {f'<span class="prod">— {esc(a.get("produto"))}</span>' if a.get("produto") else ''}</div>
      </div>
      <div class="grid">
        <div class="mosaic">
          {f'<img src="{mosaic_uri}" alt="mosaico {esc(name)}">' if mosaic_uri else '<div class="nomosaic">mosaico indisponível</div>'}
          <div class="cap">Referência visual — frames amostrados com timestamp ({_arco})</div>
        </div>
        <div class="col">
          <div class="meta"><b>Duração:</b> {dur} &nbsp;&middot;&nbsp; <b>Resolução:</b> {res} &nbsp;&middot;&nbsp; <b>FPS:</b> {esc(fps)} &nbsp;&middot;&nbsp; <b>Áudio:</b> {audio}</div>

          <h4>QA técnico <span class="lbl">automático</span></h4>
          <div class="qa">{qa_line}</div>

          {f'<h4>Resumo da edição</h4><div class="prose">{esc_rich(a.get("resumo_edicao"))}</div>' if a.get("resumo_edicao") else ''}

          {f'<h4>Transcrição de áudio <span class="lbl">palavra por palavra</span></h4><div class="trans">{esc_rich(transcript)}</div>' if transcript else ''}

          {f'<h4>Pontos de atenção</h4><ul class="pts">{at}</ul>' if at else ''}

          {ficha_html}

          {ponte_html}
        </div>
      </div>
    </div>"""

def esc_rich(s):
    """Escapa mas preserva **negrito** -> <b> e 'aspas'."""
    if not s: return ""
    s = html.escape(str(s), quote=False)
    import re
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = s.replace("\n\n", "<br><br>").replace("\n", "<br>")
    return s

def render_ponte(p):
    if not p: return ""
    rows = ""
    for L in ["O", "P", "T", "N", "E"]:
        d = p.get(L)
        if not d: continue
        nome, camada = LETRAS[L]
        cls = nota_classe(d.get("nota"))
        rows += (f'<tr><td><span class="letter">{L}</span> — {esc(nome)}</td>'
                 f'<td>{esc(camada)}</td>'
                 f'<td class="score {cls}">{esc(d.get("nota","—"))}/5</td>'
                 f'<td>{esc_rich(d.get("veredito",""))}</td></tr>')
    # cards por letra (opcional — só se tiver pontos)
    cards = ""
    for L in ["O", "P", "T", "N", "E"]:
        d = p.get(L)
        if not d or not d.get("pontos"): continue
        nome, _ = LETRAS[L]
        lis = ""
        for pt in d.get("pontos", []):
            mark = "good" if pt.get("tipo") == "good" else "bad"
            lis += f'<li class="{mark}">{esc_rich(pt.get("txt",""))}</li>'
        cards += (f'<div class="lcard"><b><span class="letter">{L}</span> {esc(nome)} '
                  f'<span class="chip mini {nota_classe(d.get("nota"))}">{esc(d.get("nota","—"))}/5</span></b>'
                  f'<ul class="lu">{lis}</ul></div>')
    # matriz
    matriz = ""
    if p.get("matriz"):
        mr = "".join(f'<tr><td>{esc(m.get("eixo",""))}</td><td class="from">{esc(m.get("de",""))}</td>'
                     f'<td>{esc_rich(m.get("testar",""))}</td></tr>' for m in p["matriz"])
        matriz = (f'<h5>Matriz de experimentação (letra E)</h5>'
                  f'<table class="mtx"><tr><th>Eixo</th><th>Vem de</th><th>Testar</th></tr>{mr}</table>')
    acoes = ""
    if p.get("acoes"):
        acoes = "<h5>Ações que mais movem o ponteiro</h5><ol class='act'>" + \
                "".join(f"<li>{esc_rich(x)}</li>" for x in p["acoes"]) + "</ol>"
    glob = ""
    if p.get("global") is not None:
        gval = str(p["global"]).replace(".", ",")  # decimal pt-BR
        glob = (f'<div class="global"><div class="big">{esc(gval)}<small>/5</small>'
                f'<span class="gl">Nota global PONTE</span></div></div>')
    return (f'<h4>Análise PONTE <span class="lbl">estratégia de conversão</span></h4>'
            f'<table class="ptable"><tr><th>Letra</th><th>Camada</th><th class="score">Nota</th><th>Veredito</th></tr>{rows}</table>'
            f'{cards}{matriz}{acoes}{glob}')

# -------- documento --------
CSS = """
* { box-sizing:border-box; }
:root{
  --bg:#0a0a12; --card:rgba(255,255,255,.035); --card-brd:rgba(255,255,255,.08);
  --ink:#ececf5; --mut:#9a9ab8; --mut2:#7a7a98; --line:rgba(255,255,255,.07);
  --acc:#818cf8; --acc2:#a78bfa; --grad:linear-gradient(135deg,#6366f1,#8b5cf6);
  --ok:#34d399; --warn:#fbbf24; --crit:#fb7185; --gold:#fcd34d;
}
html{ -webkit-text-size-adjust:100%; }
body { margin:0; background:var(--bg); color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",Inter,"Helvetica Neue",Arial,sans-serif;
  font-size:14px; line-height:1.6; padding:40px 22px 64px; letter-spacing:.1px;
  background-image:radial-gradient(60vw 42vw at 12% -6%, rgba(99,102,241,.20), transparent 60%),
    radial-gradient(52vw 40vw at 102% -2%, rgba(139,92,246,.15), transparent 55%);
  background-attachment:fixed; background-repeat:no-repeat; }
.wrap { max-width:1120px; margin:0 auto; }
.top { padding-bottom:22px; margin-bottom:26px; border-bottom:1px solid var(--line); }
.kicker { font-size:11px; letter-spacing:2.4px; color:var(--mut); text-transform:uppercase; font-weight:700; margin-bottom:11px; display:flex; align-items:center; gap:9px; }
.kicker::before{ content:""; width:24px; height:3px; border-radius:3px; background:var(--grad); }
.title { font-size:30px; font-weight:800; letter-spacing:-.02em; margin:0 0 6px; line-height:1.15;
  background:linear-gradient(120deg,#ffffff 28%,#c4b5fd); -webkit-background-clip:text; background-clip:text; color:transparent; }
.top .meta2 { color:var(--mut); font-size:12.5px; }
.card { background:var(--card); border:1px solid var(--card-brd); border-radius:22px; padding:26px; margin-bottom:26px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 24px 60px -34px rgba(0,0,0,.95); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); }
.head { display:flex; align-items:flex-start; gap:16px; margin-bottom:20px; }
.badge { background:var(--grad); color:#fff; font-weight:800; font-size:15px; padding:9px 15px; border-radius:12px; white-space:nowrap; box-shadow:0 10px 26px -10px rgba(129,140,248,.75); letter-spacing:.2px; }
.desc { color:#cfcfe2; padding-top:5px; } .desc .prod { color:var(--mut2); }
.grid { display:grid; grid-template-columns:300px 1fr; gap:26px; align-items:start; }
.mosaic img { width:100%; border-radius:14px; display:block; border:1px solid var(--line); box-shadow:0 20px 44px -26px rgba(0,0,0,.95); }
.mosaic .nomosaic { color:var(--mut2); padding:44px 0; text-align:center; border:1px dashed rgba(255,255,255,.14); border-radius:14px; }
.mosaic .cap { text-align:center; color:var(--mut2); font-size:11px; margin-top:10px; }
.meta { background:rgba(255,255,255,.03); border:1px solid var(--line); border-radius:12px; padding:12px 16px; font-size:13px; margin-bottom:6px; } .meta b { color:#fff; }
h4 { color:var(--ink); font-size:11.5px; letter-spacing:1.3px; text-transform:uppercase; margin:26px 0 11px; font-weight:700; display:flex; align-items:center; gap:9px; }
h4::before{ content:""; width:6px; height:6px; border-radius:50%; background:var(--grad); box-shadow:0 0 10px 1px rgba(129,140,248,.6); }
h4 .lbl { color:var(--mut2); font-weight:400; letter-spacing:0; text-transform:none; font-size:11px; }
h5 { color:#c9c9e2; font-size:12px; text-transform:uppercase; letter-spacing:.6px; margin:16px 0 6px; }
.prose { color:#d6d6ea; } .prose b, .trans b { color:#fff; }
.trans { background:rgba(255,255,255,.025); border:1px solid var(--line); border-left:3px solid var(--gold); border-radius:12px; padding:15px 18px; color:#cfcfe4; font-size:13px; }
.qa .chip { display:inline-block; font-size:12px; font-weight:600; padding:5px 12px; border-radius:999px; margin:2px 5px 2px 0; border:1px solid transparent; }
.chip.ok { background:rgba(52,211,153,.12); color:#4ade80; border-color:rgba(52,211,153,.26); }
.chip.aten { background:rgba(251,191,36,.12); color:#fbbf24; border-color:rgba(251,191,36,.26); }
.chip.crit { background:rgba(251,113,133,.12); color:#fb7185; border-color:rgba(251,113,133,.26); }
.pts { list-style:none; padding:0; margin:0; }
.pts li { padding:8px 0 8px 28px; position:relative; color:#d6d6ea; border-bottom:1px solid rgba(255,255,255,.05); } .pts li:last-child{ border:0; } .pts li b { color:#fff; }
.pts .plain { color:#9a9ab5; font-style:italic; } .dot { position:absolute; left:0; top:9px; font-size:12px; }
table { width:100%; border-collapse:collapse; margin:8px 0; }
th,td { text-align:left; padding:9px 11px; border-bottom:1px solid var(--line); vertical-align:top; font-size:13px; }
th { color:var(--acc); font-size:10.5px; text-transform:uppercase; letter-spacing:.5px; font-weight:700; }
tbody tr:hover td, table tr:hover td { background:rgba(255,255,255,.02); }
.letter { font-weight:800; color:var(--acc); } .score { text-align:center; font-weight:800; white-space:nowrap; }
.s4 { color:#34d399; } .s3 { color:#fbbf24; } .s2 { color:#fb7185; }
.lcard { background:rgba(255,255,255,.03); border:1px solid var(--line); border-left:3px solid var(--acc); border-radius:10px; padding:10px 14px; margin:8px 0; }
.lu { margin:5px 0 2px; padding-left:18px; } .lu li { margin:3px 0; color:#d6d6ea; }
.lu .good::marker { content:"✓ "; color:#34d399; } .lu .bad::marker { content:"✗ "; color:#fb7185; }
.chip.mini { font-size:11px; padding:1px 9px; border-radius:999px; margin-left:6px; }
.chip.mini.s4 { background:rgba(52,211,153,.15); } .chip.mini.s3 { background:rgba(251,191,36,.15); } .chip.mini.s2 { background:rgba(251,113,133,.15); }
.mtx .from { color:var(--acc); font-weight:700; text-align:center; }
.act { margin:4px 0; padding-left:20px; } .act li { margin:5px 0; color:#eaeaf5; }
.global { background:var(--grad); border-radius:14px; padding:16px 20px; margin-top:18px; box-shadow:0 22px 46px -24px rgba(129,140,248,.65); }
.global .big { font-size:30px; font-weight:800; color:#fff; } .global small { font-size:15px; opacity:.85; } .global .gl { font-size:14px; font-weight:600; margin-left:12px; }
.foot { text-align:center; color:var(--mut2); font-size:11px; margin-top:16px; }
.ficha { width:100%; border-collapse:separate; border-spacing:0; margin:4px 0 6px; background:rgba(255,255,255,.02); border:1px solid var(--line); border-radius:14px; overflow:hidden; }
.ficha td { border-bottom:1px solid var(--line); padding:9px 14px; font-size:12.5px; vertical-align:top; }
.ficha tr:last-child td { border-bottom:0; }
.ficha td.k { color:var(--acc); width:32%; font-size:10.5px; text-transform:uppercase; letter-spacing:.5px; font-weight:700; background:rgba(255,255,255,.02); }
.ficha td.v { color:#d6d6ea; } .ficha td.v b { color:#fff; }
.ficha tr:hover td { background:rgba(129,140,248,.06); }
.fluxo { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:8px 0; }
.fluxo.f4 { grid-template-columns:repeat(4,1fr); }
.fx { border-radius:14px; padding:14px; background:rgba(255,255,255,.03); border:1px solid var(--line); position:relative; overflow:hidden; }
.fx::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; }
.fx .fxh { font-weight:800; font-size:11px; letter-spacing:.7px; text-transform:uppercase; margin-bottom:7px; }
.fx.hk::before { background:linear-gradient(90deg,#34d399,transparent); } .fx.hk .fxh { color:#34d399; }
.fx.bd::before { background:linear-gradient(90deg,#fbbf24,transparent); } .fx.bd .fxh { color:#fbbf24; }
.fx.gd::before { background:linear-gradient(90deg,#fcd34d,transparent); } .fx.gd .fxh { color:#fcd34d; }
.fx.cl::before { background:linear-gradient(90deg,#fb7185,transparent); } .fx.cl .fxh { color:#fb7185; }
.fx .fxt { color:#c7c7de; font-size:12px; line-height:1.5; }
@media(max-width:820px){ .grid{ grid-template-columns:1fr; } }
@media(max-width:640px){ body{ padding:26px 14px; } .title{ font-size:24px; } .fluxo,.fluxo.f4{ grid-template-columns:1fr; } .head{ flex-direction:column; } }
"""

def build_doc(analises, qa, qa_dir, projeto, show_ponte=True, tipo="ad"):
    cards = "".join(render_card(a, qa, qa_dir, show_ponte, tipo) for a in analises)
    n = len(analises)
    is_vsl = (tipo == "vsl")
    detalhe = "Detalhamento da VSL" if is_vsl else "Detalhamento AD por AD"
    titulo  = "Análise de VSL" if is_vsl else "Análise de criativos"
    unidade = ("VSL" if n == 1 else "VSLs") if is_vsl else "criativo(s)"
    kicker = f"{detalhe} · Método PONTE" if show_ponte else detalhe
    sub = ("QA técnico automático + detalhamento editorial + análise PONTE de conversão"
           if show_ponte else "QA técnico automático + detalhamento editorial")
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>{titulo} — {esc(projeto)}</title><style>{CSS}</style></head>
<body><div class="wrap">
  <div class="top">
    <div class="kicker">{kicker}</div>
    <div class="title">{titulo} — {esc(projeto)}</div>
    <div class="meta2">{n} {unidade} · {sub}</div>
  </div>
  {cards}
  <div class="foot">Gerado pela skill analise-criativo-ficha · QA (conferir.py) + montar_relatorio.py</div>
</div></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", required=True, help="pasta _QA gerada pelo conferir.py")
    ap.add_argument("--analise", default=None, help="analise.json (preenchido pelo Claude)")
    ap.add_argument("-o", "--out", required=True, help="pasta ou arquivo .html de saída")
    ap.add_argument("--projeto", default=None)
    ap.add_argument("--sem-ponte", dest="sem_ponte", action="store_true",
                    help="não renderizar a seção 'Análise PONTE' no HTML (mantém QA + detalhamento)")
    ap.add_argument("--tipo", choices=["ad", "vsl"], default="ad",
                    help="ad (padrão) usa rótulos de criativo; vsl troca para 'Análise de VSL'")
    args = ap.parse_args()

    qa = load_qa(args.qa)
    projeto = args.projeto or os.path.basename(os.path.dirname(os.path.abspath(args.qa))) or "criativos"

    if args.analise and os.path.isfile(args.analise):
        analises = json.load(open(args.analise, encoding="utf-8"))
        if isinstance(analises, dict):
            analises = [analises]
    else:
        # fallback: só QA técnico, um card mínimo por vídeo detectado
        analises = [{"name": n, "badge": n} for n in qa]
        if not analises:
            print("ERRO: sem analise.json e sem dados de QA. Rode conferir.py antes.", file=sys.stderr)
            sys.exit(1)

    out = args.out
    if os.path.isdir(out) or not out.lower().endswith(".html"):
        os.makedirs(out, exist_ok=True)
        _pref = "Analise VSL" if args.tipo == "vsl" else "Analise Criativos"
        out = os.path.join(out, f"{_pref} - {projeto}.html")

    open(out, "w", encoding="utf-8").write(build_doc(analises, qa, args.qa, projeto, show_ponte=not args.sem_ponte, tipo=args.tipo))
    print("Relatório gerado:", out)

if __name__ == "__main__":
    main()
