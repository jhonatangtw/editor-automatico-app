#!/usr/bin/env python3
"""Monta o index.html do AD no HyperFrames — H1 + corpo, edição dinâmica (skill advalidado-weightloss).

COPIE para <JOB>/edicao/build.py. Fonte da verdade: palavras (edicao/palavras_h1.json e
palavras_corpo.json, Whisper medium com word_timestamps) + as listas abaixo. Edite AQUI e rode
de novo; nunca edite o index.html à mão (o Studio reformata o arquivo).

⚠️ As listas BROLL / PUNCH / LETTER / FLASH / SETA / SFX abaixo são o EXEMPLO REAL do AD de
referência (201 s). Troque pelos tempos do SEU AD, tirados das palavras da voz nova.

Projeto HyperFrames: <JOB>/hyperframes/<PROJETO> (export PROJETO=nome; padrão "ad").
Avatar: H1_avatar.mp4 e CORPO_avatar.mp4 na raiz do projeto. Ajuste H1_DUR e a duração do corpo.
"""
import json, os, re, html

J = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(J, "hyperframes", os.environ.get("PROJETO", "ad"))
CORPO_DUR = float(os.environ.get("CORPO_DUR", "196.48"))  # duração do vídeo do corpo (ffprobe)
H1_DUR = 4.68
FIM = 66.6  # 1º minuto: fecha em "the scale wouldn't budge."

# ---------- b-roll: (id, arquivo, início, fim, movimento) ----------
BROLL = [
    ("H1-01", "assets/broll/H1-01.jpg", 0.75, 2.75, "push"),
    ("H1-02", "assets/broll/H1-02.jpg", 3.20, 4.68, "punch"),
    ("BR01", "assets/broll/BR01.jpg", 10.65, 15.35, "push"),
    ("BR02", "assets/broll/BR02.jpg", 15.40, 29.70, "foto"),
    ("BR03", "assets/broll/BR03.jpg", 46.70, 50.80, "memoria"),
    ("BR04", "assets/broll/BR04.mp4", 59.85, 60.95, "video"),
    ("BR05", "assets/broll/BR05.mp4", 60.95, 61.75, "video"),
    ("BR06", "assets/broll/BR06.jpg", 61.75, 62.35, "punch"),
    ("BR07", "assets/broll/BR07.mp4", 62.35, 63.25, "video"),
    ("BR08", "assets/broll/BR08.mp4", 63.25, 64.25, "video"),
    ("BR09", "assets/broll/BR09.jpg", 64.25, 65.05, "punch"),
    ("BR10", "assets/broll/BR10.jpg", 65.05, FIM, "push"),
]

# ---------- punch-in no avatar: (t, escala, y%) ----------
PUNCH = [
    (0.0, 1.0, 0), (2.75, 1.12, 2), (4.68, 1.0, 0), (6.8, 1.1, 2), (7.5, 1.18, 3), (9.3, 1.28, 4),
    (29.7, 1.0, 0), (30.45, 1.42, 6), (31.6, 1.15, 3), (33.8, 1.0, 0), (35.4, 1.12, 2), (36.8, 1.0, 0),
    (39.4, 1.08, 1), (40.2, 1.16, 3), (40.75, 1.26, 4), (42.0, 1.0, 0), (43.7, 1.2, 3),
    (50.8, 1.0, 0), (52.3, 1.1, 2), (54.6, 1.0, 0), (56.0, 1.18, 3), (58.8, 1.06, 1),
]
DRIFT = [(43.7, 45.9, 1.28)]  # empurrão lento contínuo (momento emocional)

# ---------- lettering: (início, fim, texto, estilo) ----------
LETTER = [
    (4.15, 4.68, "THEY ZIPPED.", "amarelo"),
    (9.30, 10.60, "SACRIFICED EVERYTHING.", "vermelho"),
    (23.75, 24.30, "THE ARM.", "vermelho"),
    (24.30, 24.85, "THE BELLY.", "vermelho"),
    (24.85, 25.60, "THE DOUBLE CHIN.", "vermelho"),
    (28.75, 29.70, "HIDING NOTHING.", "caixa"),
    (31.60, 32.60, "I WISHED I HADN'T.", "branco"),
    (42.00, 43.30, "THE REAL VERSION.", "amarelo"),
    (56.20, 58.20, "+47 POUNDS", "gigante"),
    (65.40, FIM, "WOULDN'T BUDGE.", "vermelho"),
]
FLASH = [23.25, 28.75, 56.20]
DIM = [(31.55, 32.65)]  # escurece em "I wished I hadn't"

# ---------- SFX: (t, arquivo, volume, duração) ----------
SFX = [
    (0.75, "whoosh", .16, .9), (3.20, "whoosh", .14, .9), (4.15, "pop", .45, .6), (9.30, "boom", .22, 2.0),
    (10.65, "whoosh", .16, .9), (15.40, "whoosh", .14, .9), (16.15, "shutter", 1.0, .6),
    (23.25, "whoosh", .14, .9), (23.75, "pop", .4, .6), (24.30, "pop", .4, .6), (24.85, "pop", .4, .6),
    (28.75, "boom", .26, 2.0), (30.45, "whoosh", .2, .9), (42.0, "pop", .38, .6), (46.70, "whoosh", .14, .9),
    (56.20, "boom", .28, 2.0), (59.85, "pop", .22, .6), (60.95, "pop", .2, .6), (61.75, "pop", .2, .6),
    (62.35, "pop", .2, .6), (63.25, "pop", .2, .6), (64.25, "pop", .2, .6), (65.05, "pop", .22, .6),
    (65.40, "boom", .2, 1.2),
]

# ================= resto do AD (66.6 → fim) =================
FIM = round(H1_DUR + CORPO_DUR, 2)
BROLL[-1] = ("BR10", "assets/broll/BR10.jpg", 65.05, 66.6, "push")
BROLL += [
    ("BR11", "assets/broll/BR11.jpg", 76.30, 80.60, "push"),
    ("BR12", "assets/broll/BR12.jpg", 83.80, 88.55, "push"),
    ("BR13", "assets/broll/BR13.jpg", 88.55, 91.65, "push"),
    ("BR14", "assets/broll/BR14.jpg", 91.65, 94.40, "push"),
    ("BR15", "assets/broll/BR15.mp4", 94.40, 95.35, "video"),
    ("BR16", "assets/broll/BR16.jpg", 95.35, 96.60, "punch"),
    ("BR17", "assets/broll/BR17.mp4", 100.55, 101.20, "video"),
    ("BR18", "assets/broll/BR18.jpg", 101.20, 102.80, "punch"),
    ("BR19", "assets/broll/BR19.mp4", 102.80, 105.35, "video"),
    ("BR20", "assets/broll/BR20.jpg", 105.35, 107.95, "push"),
    ("BR21", "assets/broll/BR21.jpg", 107.95, 110.60, "push"),
    ("BR22", "assets/broll/BR22.mp4", 110.65, 112.35, "video"),
    ("BR23", "assets/broll/BR23.mp4", 112.35, 115.65, "video"),
    ("BR24", "assets/broll/BR24.mp4", 115.65, 116.45, "video"),
    ("BR25", "assets/broll/BR25.mp4", 116.45, 118.65, "video"),
    ("BR26", "assets/broll/BR26.jpg", 118.65, 121.30, "push"),
    ("BR27", "assets/broll/BR27.jpg", 121.30, 122.45, "punch"),
    ("BR28", "assets/broll/BR28.mp4", 122.45, 124.10, "video"),
    ("BR29", "assets/broll/BR29.jpg", 124.10, 127.55, "push"),
    ("BR30", "assets/broll/BR30.jpg", 127.55, 131.10, "push"),
    ("BR31", "assets/broll/BR31.mp4", 131.95, 135.05, "video"),
    ("BR32", "assets/broll/BR32.mp4", 135.05, 136.95, "video"),
    ("BR33", "assets/broll/BR33.mp4", 136.95, 139.95, "video"),
    ("BR34", "assets/broll/BR34.mp4", 139.95, 142.70, "video"),
    ("BR35", "assets/broll/BR35.jpg", 142.75, 144.50, "punch"),
    ("BR36", "assets/broll/BR36.jpg", 144.55, 147.45, "push"),
    ("BR37", "assets/broll/BR37.jpg", 147.45, 150.60, "push"),
    ("BR39", "assets/broll/BR39.jpg", 168.00, 174.20, "polaroid"),
    ("BR38", "assets/broll/BR38.jpg", 187.35, 191.60, "push"),
]
PUNCH += [
    (66.6, 1.0, 0), (68.8, 1.15, 3), (70.5, 1.25, 4), (72.1, 1.0, 0), (74.4, 1.2, 3),
    (80.6, 1.0, 0), (81.4, 1.1, 2), (82.8, 1.2, 3),
    (96.6, 1.0, 0), (97.6, 1.12, 2), (98.8, 1.24, 4), (99.5, 1.05, 1),
    (131.1, 1.0, 0), (131.4, 1.3, 5),
    (150.6, 1.0, 0), (151.7, 1.1, 2), (153.4, 1.2, 3), (154.8, 1.0, 0), (156.8, 1.15, 3), (158.0, 1.0, 0),
    (159.6, 1.22, 4), (160.9, 1.0, 0), (161.9, 1.1, 2), (162.9, 1.2, 3), (163.6, 1.28, 4), (165.0, 1.0, 0),
    (174.2, 1.0, 0), (175.0, 1.12, 2), (177.4, 1.0, 0), (177.9, 1.18, 3), (179.7, 1.26, 4),
    (181.4, 1.0, 0), (184.4, 1.12, 2), (185.7, 1.22, 3),
    (191.6, 1.0, 0), (192.0, 1.15, 3), (194.9, 1.0, 0), (195.4, 1.2, 3), (197.8, 1.08, 1), (198.4, 1.26, 4), (200.0, 1.0, 0),
]
DRIFT += [(74.4, 76.2, 1.3), (179.7, 181.2, 1.32)]
LETTER += [
    (68.80, 70.30, "THE GUILT.", "vermelho"),
    (74.40, 75.30, "LOST MYSELF.", "branco"),
    (83.80, 85.00, "AFTER 35", "amarelo"),
    (88.60, 90.90, "GLP-1 & GIP", "amarelo"),
    (93.40, 94.40, "STORED AS FAT.", "vermelho"),
    (101.60, 102.80, "$2,000 A MONTH", "vermelho"),
    (109.40, 110.60, "BACK DOUBLE.", "vermelho"),
    (110.70, 112.20, "ANOTHER WAY.", "amarelo"),
    (119.80, 121.20, "NATURALLY.", "amarelo"),
    (121.40, 122.40, "NO INJECTION.", "x"),
    (122.50, 123.30, "NO DIET.", "x"),
    (123.40, 124.10, "NO GYM.", "x"),
    (125.80, 127.50, "-54 POUNDS", "gigante"),
    (129.00, 131.00, "25 LBS IN 21 DAYS", "vermelho"),
    (135.70, 136.95, "ALTERED ON PURPOSE.", "caixa"),
    (141.10, 142.60, "FLOUR CAPSULES", "vermelho"),
    (144.80, 146.30, "THE ORIGINAL RECIPE", "amarelo"),
    (149.30, 150.60, "FREE · LIMITED TIME", "caixa"),
    (153.40, 154.60, "LESS THAN 3 WEEKS", "amarelo"),
    (156.80, 157.70, "ZIPPED UP.", "amarelo"),
    (159.60, 160.80, "“YOU LOOK DIFFERENT.”", "branco"),
    (163.20, 164.60, "THE GLOW.", "amarelo"),
    (179.70, 181.20, "FOUND HERSELF AGAIN.", "amarelo"),
    (185.70, 187.20, "FEEL GOOD IN HER OWN BODY.", "branco"),
    (189.30, 191.60, "BUTTON BELOW", "caixa"),
    (195.40, 197.40, "NEVER A LACK OF DISCIPLINE.", "vermelho"),
    (198.10, 199.60, "YOUR HORMONES JUST STOPPED.", "amarelo"),
    (200.00, FIM, "TAP LEARN MORE NOW", "caixa"),
]
FLASH += [83.8, 110.7, 121.4, 125.8, 144.6, 168.0, 187.35]
SETA = [(187.40, 191.60), (199.90, FIM)]  # seta do CTA
SFX += [
    (68.8, "boom", .2, 2.0), (74.4, "pop", .35, .6), (76.30, "whoosh", .14, .9), (76.60, "ding", .22, 1.5),
    (83.8, "whoosh", .14, .9), (88.55, "whoosh", .14, .9), (88.6, "pop", .35, .6), (93.4, "pop", .35, .6),
    (94.4, "pop", .18, .6), (95.35, "pop", .18, .6), (100.55, "pop", .18, .6), (101.6, "caixa", .28, 1.6),
    (102.8, "pop", .18, .6), (105.35, "whoosh", .12, .9), (108.0, "riser", .18, 2.7), (109.4, "boom", .2, 1.5),
    (110.65, "whoosh", .16, .9), (112.35, "whoosh", .12, .9), (115.65, "pop", .18, .6), (116.45, "pop", .18, .6),
    (118.65, "whoosh", .14, .9), (119.8, "pop", .32, .6), (121.4, "boom", .2, 1.0), (122.5, "boom", .18, .8),
    (123.4, "boom", .2, 1.2), (124.1, "whoosh", .14, .9), (125.8, "boom", .26, 2.0), (129.0, "pop", .32, .6),
    (131.4, "whoosh", .18, .9), (131.95, "whoosh", .14, .9), (135.05, "pop", .18, .6), (135.7, "boom", .22, 1.5),
    (136.95, "pop", .18, .6), (139.95, "pop", .18, .6), (141.1, "pop", .32, .6), (142.75, "pop", .18, .6),
    (144.55, "whoosh", .14, .9), (144.8, "pop", .32, .6), (147.45, "whoosh", .12, .9), (149.3, "pop", .32, .6),
    (153.4, "pop", .3, .6), (156.8, "pop", .3, .6), (159.6, "pop", .3, .6), (163.2, "pop", .3, .6),
    (166.2, "shutter", 1.0, .6), (168.0, "whoosh", .14, .9), (179.7, "pop", .3, .6), (185.7, "pop", .3, .6),
    (187.35, "whoosh", .16, .9), (189.7, "ding", .24, 1.8), (195.4, "boom", .22, 1.5), (198.1, "pop", .3, .6),
    (200.0, "ding", .2, 1.1),
]
CORRIGE = {"flower": "flour", "Monjaro": "Mounjaro"}

# ---------- legenda palavra por palavra ----------
def palavras():
    h = json.load(open(os.path.join(J, "edicao", "palavras_h1.json")))
    c = json.load(open(os.path.join(J, "edicao", "palavras_corpo.json")))
    w = [dict(x) for x in h] + [{"w": x["w"], "s": x["s"] + H1_DUR, "e": x["e"] + H1_DUR} for x in c]
    out = []
    for x in w:
        if x["s"] >= FIM: break
        if x["w"][:1] in "-," and out:  # "pre"+"-baby", "GLP"+"-1", "$2"+",000"
            out[-1]["w"] += x["w"]; out[-1]["e"] = x["e"]; continue
        nu = re.sub(r"[^\w']", "", x["w"])
        if nu in CORRIGE: x["w"] = x["w"].replace(nu, CORRIGE[nu])
        out.append(x)
    return out

def em_lettering(t):
    return any(a - 0.05 <= t < b for a, b, _, _ in LETTER)

def grupos(ws):
    gs, g = [], []
    for i, x in enumerate(ws):
        if em_lettering(x["s"]):
            if g: gs.append(g); g = []
            continue
        if g and (len(g) >= 3 or x["s"] - g[-1]["e"] > 0.3 or re.search(r"[.,!?]$", g[-1]["w"])):
            gs.append(g); g = []
        g.append(x)
    if g: gs.append(g)
    res = []
    for k, g in enumerate(gs):
        fim = g[-1]["e"] + 0.15
        if k + 1 < len(gs): fim = min(fim + 0.4, gs[k + 1][0]["s"])
        res.append({"s": round(g[0]["s"], 3), "e": round(min(fim, FIM), 3), "w": g})
    return res

def r(x): return round(x, 3)

def montar():
    ws = palavras(); gs = grupos(ws)
    clips, js = [], []
    # avatar
    clips.append(f'''<div id="cam"><div id="cam-in">
  <video id="av-h1" class="clip" src="H1_avatar.mp4" playsinline data-start="0" data-duration="{H1_DUR}" data-track-index="0" data-has-audio="true" data-volume="1"></video>
  <video id="av-corpo" class="clip" src="CORPO_avatar.mp4" playsinline data-start="{H1_DUR}" data-duration="{r(FIM - H1_DUR)}" data-track-index="0" data-has-audio="true" data-volume="1"></video>
</div></div>''')
    for t, s, y in PUNCH:
        js.append(f'tl.to("#cam-in", {{scale:{s}, yPercent:{y}, duration:0.16, ease:"power3.out"}}, {t});')
    for a, b, s in DRIFT:
        js.append(f'tl.to("#cam-in", {{scale:{s}, duration:{r(b - a - 0.2)}, ease:"none"}}, {r(a + 0.2)});')
    # b-roll
    for bid, src, a, b, mov in BROLL:
        d = r(b - a); cid = "b-" + bid
        if mov == "video":
            clips.append(f'<div class="brw" id="w-{bid}"><video id="{cid}" class="clip" src="{src}" muted playsinline data-start="{a}" data-duration="{d}" data-media-start="0" data-track-index="1"></video></div>')
            js.append(f'tl.fromTo("#w-{bid}", {{scale:1.12}}, {{scale:1.0, duration:{d}, ease:"power1.out"}}, {a});')
        elif mov == "foto":
            clips.append(f'''<div id="{cid}" class="clip broll" data-start="{a}" data-duration="{d}" data-track-index="1">
  <img class="bg" src="assets/broll/BR02_fundo.jpg"><div class="card"><img class="ph" src="assets/broll/BR02_card.jpg"></div><img class="full" src="{src}">
</div>''')
            js += [
                f'tl.fromTo("#{cid} .card", {{scale:0.6, rotation:-9, yPercent:12}}, {{scale:1, rotation:-3, yPercent:0, duration:0.35, ease:"back.out(1.6)"}}, {a});',
                f'tl.to("#{cid} .card", {{scale:1.06, rotation:-1.5, duration:5.5, ease:"none"}}, {r(a + 0.35)});',
                f'tl.fromTo("#{cid} .bg", {{scale:1.15}}, {{scale:1.3, duration:7.8, ease:"none"}}, {a});',
                f'tl.fromTo("#{cid} .full", {{opacity:0}}, {{opacity:1, duration:0.08}}, 23.25);',
                # zoom no que ela fala: braço, barriga, papada (s=2; x,y = -(p-centro)*s, travado na borda)
                f'tl.to("#{cid} .full", {{scale:2.0, x:-540, y:-380, duration:0.18, ease:"power3.out"}}, 23.75);',
                f'tl.to("#{cid} .full", {{scale:2.0, x:120, y:-900, duration:0.18, ease:"power3.out"}}, 24.30);',
                f'tl.to("#{cid} .full", {{scale:2.2, x:0, y:880, duration:0.18, ease:"power3.out"}}, 24.85);',
                f'tl.to("#{cid} .full", {{scale:1.0, x:0, y:0, duration:0.3, ease:"power2.inOut"}}, 25.60);',
                f'tl.to("#{cid} .full", {{scale:1.12, duration:2.7, ease:"none"}}, 25.95);',
                f'tl.to("#{cid} .full", {{scale:1.3, duration:0.18, ease:"power3.out"}}, 28.75);',
            ]
        elif mov == "polaroid":
            clips.append(f'''<div id="{cid}" class="clip broll quente" data-start="{a}" data-duration="{d}" data-track-index="1">
  <img class="bg" src="assets/broll/{bid}_fundo.jpg"><div class="card"><img class="ph" src="{src}"></div>
</div>''')
            js += [
                f'tl.fromTo("#{cid} .card", {{scale:0.6, rotation:8, yPercent:12}}, {{scale:1, rotation:2.5, yPercent:0, duration:0.4, ease:"back.out(1.6)"}}, {a});',
                f'tl.to("#{cid} .card", {{scale:1.16, rotation:0, duration:{r(d - 0.4)}, ease:"none"}}, {r(a + 0.4)});',
                f'tl.fromTo("#{cid} .bg", {{scale:1.15}}, {{scale:1.3, duration:{d}, ease:"none"}}, {a});',
            ]
        else:
            extra = ' memoria' if mov == "memoria" else ''
            clips.append(f'<div id="{cid}" class="clip broll{extra}" data-start="{a}" data-duration="{d}" data-track-index="1"><img class="kb" src="{src}"></div>')
            if mov == "punch":
                js.append(f'tl.fromTo("#{cid} .kb", {{scale:1.25}}, {{scale:1.05, duration:{min(d, .5)}, ease:"power3.out"}}, {a});')
            else:
                js.append(f'tl.fromTo("#{cid} .kb", {{scale:1.04, yPercent:1}}, {{scale:1.18, yPercent:-2, duration:{d}, ease:"none"}}, {a});')
    # escurecer
    for k, (a, b) in enumerate(DIM):
        clips.append(f'<div id="dim{k}" class="clip dim" data-start="{a}" data-duration="{r(b - a)}" data-track-index="4"><div class="dim-in"></div></div>')
        js.append(f'tl.fromTo("#dim{k} .dim-in", {{opacity:0}}, {{opacity:0.62, duration:0.15}}, {a});')
    # flash
    for k, t in enumerate(FLASH):
        clips.append(f'<div id="fl{k}" class="clip flash" data-start="{t}" data-duration="0.3" data-track-index="5"><div class="fl-in"></div></div>')
        js.append(f'tl.fromTo("#fl{k} .fl-in", {{opacity:0.85}}, {{opacity:0, duration:0.28, ease:"power2.out"}}, {t});')
    # lettering
    for k, (a, b, txt, est) in enumerate(LETTER):
        xis = '<div class="xis"><i></i><i></i></div>' if est == "x" else ''
        clips.append(f'<div id="lt{k}" class="clip lt {est}" data-start="{a}" data-duration="{r(b - a)}" data-track-index="2">{xis}<div class="lt-in">{html.escape(txt)}</div></div>')
        js.append(f'tl.fromTo("#lt{k} .lt-in", {{scale:1.7, opacity:0}}, {{scale:1, opacity:1, duration:0.16, ease:"back.out(2.2)"}}, {a});')
        if xis:
            js.append(f'tl.fromTo("#lt{k} .xis", {{scale:2.2, opacity:0, rotation:-20}}, {{scale:1, opacity:1, rotation:0, duration:0.18, ease:"back.out(2)"}}, {r(a + 0.05)});')
    # seta do CTA (pulsa para baixo)
    for k, (a, b) in enumerate(SETA):
        clips.append(f'<div id="seta{k}" class="clip seta" data-start="{a}" data-duration="{r(b - a)}" data-track-index="2"><div class="seta-in"><div class="haste"></div><div class="ponta"></div></div></div>')
        js.append(f'tl.fromTo("#seta{k} .seta-in", {{y:-60, opacity:0}}, {{y:0, opacity:1, duration:0.25, ease:"back.out(2)"}}, {a});')
        n = max(1, int((b - a - 0.3) / 0.5))
        js.append(f'tl.to("#seta{k} .seta-in", {{y:46, duration:0.25, ease:"sine.inOut", yoyo:true, repeat:{n * 2 - 1}}}, {r(a + 0.3)});')
    # legenda
    for k, g in enumerate(gs):
        spans = "".join(f'<span class="w" id="c{k}w{i}">{html.escape(x["w"])}</span> ' for i, x in enumerate(g["w"]))
        clips.append(f'<div id="cap{k}" class="clip cap" data-start="{g["s"]}" data-duration="{r(g["e"] - g["s"])}" data-track-index="3"><div class="cap-in">{spans.strip()}</div></div>')
        js.append(f'tl.fromTo("#cap{k} .cap-in", {{scale:0.82, opacity:0}}, {{scale:1, opacity:1, duration:0.1, ease:"back.out(2)"}}, {g["s"]});')
        for i, x in enumerate(g["w"]):
            js.append(f'tl.set("#c{k}w{i}", {{color:"#FFE14D", scale:1.12}}, {r(x["s"])});')
            if i + 1 < len(g["w"]):
                js.append(f'tl.set("#c{k}w{i}", {{color:"#FFFFFF", scale:1}}, {r(g["w"][i + 1]["s"])});')
    # sfx
    for k, (t, f, v, d) in enumerate(SFX):
        clips.append(f'<audio id="sfx{k}" src="assets/sfx/{f}.mp3" data-start="{t}" data-duration="{d}" data-track-index="{6 + k % 3}" data-volume="{v}"></audio>')

    doc = f'''<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face {{ font-family: "Montserrat XB"; src: url("assets/fonts/Montserrat-ExtraBold.otf"); }}
@font-face {{ font-family: "Anton"; src: url("assets/fonts/Anton-Regular.ttf"); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:100%; height:100%; overflow:hidden; background:#000; }}
#cam, .brw {{ position:absolute; inset:0; overflow:hidden; }}
#cam-in {{ position:absolute; inset:0; }}
#cam video, .brw video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.brw {{ z-index:2; }}
.broll {{ position:absolute; inset:0; overflow:hidden; z-index:2; background:#111; }}
.broll img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.broll .bg {{ }}
.broll .card {{ position:absolute; left:110px; top:330px; width:860px; height:1200px; background:#f6f3ec; padding:34px 34px 150px; box-shadow:0 30px 80px rgba(0,0,0,.55); }}
.broll .card .ph {{ position:relative; width:100%; height:100%; object-fit:cover; }}
.broll .full {{ opacity:0; }}
.memoria img {{ filter: sepia(.35) saturate(.8) contrast(1.06) brightness(1.04); }}
.memoria::after {{ content:""; position:absolute; inset:0; background:radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(40,20,0,.55) 100%); }}
.dim {{ position:absolute; inset:0; z-index:4; }}
.dim-in {{ position:absolute; inset:0; background:#000; opacity:0; }}
.flash {{ position:absolute; inset:0; z-index:9; }}
.fl-in {{ position:absolute; inset:0; background:#fff; opacity:0; }}
.vinheta {{ position:absolute; inset:0; z-index:3; pointer-events:none; background:radial-gradient(ellipse at center, rgba(0,0,0,0) 58%, rgba(0,0,0,.38) 100%); }}
.lt {{ position:absolute; left:60px; right:60px; top:880px; height:300px; z-index:6; display:flex; align-items:center; justify-content:center; }}
.lt-in {{ font-family:"Anton"; font-size:132px; line-height:1.0; text-align:center; letter-spacing:1px; color:#fff; paint-order:stroke fill; -webkit-text-stroke:10px #000; text-shadow:0 8px 30px rgba(0,0,0,.6); }}
.vermelho .lt-in {{ color:#FF2E2E; -webkit-text-stroke:10px #fff; text-shadow:0 0 28px rgba(255,46,46,.55), 0 10px 30px rgba(0,0,0,.6); }}
.amarelo .lt-in {{ color:#FFE14D; }}
.branco .lt-in {{ color:#fff; font-size:118px; }}
.caixa .lt-in {{ background:#FF2E2E; color:#fff; -webkit-text-stroke:0; padding:12px 34px 6px; border-radius:10px; }}
.gigante .lt-in {{ font-size:230px; color:#FF2E2E; -webkit-text-stroke:12px #fff; }}
.quente .card {{ transform-origin:50% 50%; }}
.quente .ph {{ filter: saturate(1.15) brightness(1.05) sepia(.12); }}
.x .lt-in {{ color:#fff; }}
.xis {{ position:absolute; left:50%; top:50%; width:520px; height:520px; margin:-260px 0 0 -260px; opacity:0; }}
.xis i {{ position:absolute; left:-30px; right:-30px; top:50%; height:46px; margin-top:-23px; background:#FF2E2E; border-radius:12px; box-shadow:0 0 30px rgba(255,46,46,.7); }}
.xis i:first-child {{ transform:rotate(45deg); }}
.xis i:last-child {{ transform:rotate(-45deg); }}
.seta {{ position:absolute; left:0; right:0; top:1460px; height:300px; z-index:8; display:flex; justify-content:center; }}
.seta-in {{ position:relative; width:160px; height:260px; filter: drop-shadow(0 0 18px #fff) drop-shadow(0 0 40px rgba(255,255,255,.7)); }}
.seta .haste {{ position:absolute; left:58px; top:0; width:44px; height:150px; background:#fff; border-radius:22px; }}
.seta .ponta {{ position:absolute; left:0; top:120px; width:0; height:0; border-left:80px solid transparent; border-right:80px solid transparent; border-top:120px solid #fff; }}
.cap {{ position:absolute; left:70px; right:70px; top:1250px; height:180px; z-index:7; display:flex; align-items:center; justify-content:center; }}
.cap-in {{ font-family:"Montserrat XB"; font-size:76px; line-height:1.12; text-align:center; color:#fff; paint-order:stroke fill; -webkit-text-stroke:9px #000; text-shadow:0 6px 18px rgba(0,0,0,.55); }}
.cap .w {{ display:inline-block; margin:0 .16em; transform-origin:50% 60%; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{FIM}" data-width="1080" data-height="1920">
{chr(10).join(clips)}
<div class="vinheta"></div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
    open(os.path.join(P, "index.html"), "w").write(doc)
    print(f"{len(BROLL)} b-rolls · {len(gs)} grupos de legenda · {len(LETTER)} letterings · {len(SFX)} SFX · {FIM}s")

if __name__ == "__main__":
    montar()
