#!/usr/bin/env python3
"""Monta hyperframes/up1-MarcaE/index.html — Upsell #1 MarcaE (4:3 1440x1080, 25 fps).

Fonte da verdade: este arquivo + alinhamentos da ElevenLabs (ia/voz/...) + ativos em assets/.
Edite AQUI e rode de novo; nunca edite o index.html à mão.

    python3 edicao/build.py A        # versão de preço A (B, C)

B-roll de IA: o build procura, para cada cena, broll/ia/final/<cena>_*.mp4 (vídeo pronto),
depois broll/ia/img/<cena>_*.png (still com push) e, sem nada, usa um placeholder com o nº da cena.
Basta o arquivo cair na pasta e rodar o build de novo.
"""
import json, os, re, sys, glob, html, subprocess, shutil

J = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(J, "hyperframes", "up1-MarcaE")
A = os.path.join(P, "assets")
VER = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
assert VER in "ABC"
FPS = 25
TEAL, YEL = "#004C5B", "#FBD643"

PRECO = {"A": ("15", "139"), "B": ("16", "149"), "C": ("17", "159")}[VER]

# ---------------------------------------------------------------- utilidades
def r(x): return round(x + 1e-9, 3)
def q(x): return round(round(x * FPS) / FPS, 3)  # trava no quadro

def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout.strip())

def norm(w): return re.sub(r"[^a-z0-9$%']", "", w.lower().replace("’", "'"))

def palavras(alin):
    d = json.load(open(alin))
    ch, s, e = d["characters"], d["character_start_times_seconds"], d["character_end_times_seconds"]
    out, cur = [], None
    for i, c in enumerate(ch):
        if c.isspace():
            cur = None; continue
        if cur is None:
            cur = {"w": "", "s": s[i], "e": e[i]}; out.append(cur)
        cur["w"] += c; cur["e"] = e[i]
        if c == "—" and i + 1 < len(ch) and not ch[i + 1].isspace():
            cur = None  # "joints—so" vira dois tokens; o travessão fica com a 1ª palavra
    return out

# ---------------------------------------------------------------- sequência
SUS = lambda b: ("S", b, f"assets/susan/{b}.mp4", os.path.join(J, "ia", "voz", "susan_blocos", f"{b}_alin.json"))
DEP = lambda d, v="v1": ("D", d, f"assets/dep/{d}.mp4", os.path.join(J, "ia", "voz", "depoentes_tts", f"{d}_{v}_alin.json"))
SEQ = [SUS("S01"), SUS("S02"), SUS("S03"), DEP("D01_MARK"), DEP("D02_ELAINE"), DEP("D03_ROBERT"),
       SUS("S04"), SUS("S05"), DEP("D04_MARGARET"), SUS("S06"), SUS("S07"), SUS(f"PRECO_{VER}"), SUS("S08"),
       DEP("D05_FRANK"), DEP("D06_NANCY", "v2"), DEP("D07_GEORGE"), SUS("S09"),
       DEP("D08_CAROL"), DEP("D09_WILLIAM"), DEP("D10_LINDA")]
NOMES = {"D01_MARK": ("Mark Sullivan", 71), "D02_ELAINE": ("Elaine Parker", 68), "D03_ROBERT": ("Robert Hayes", 72),
         "D04_MARGARET": ("Margaret Collins", 82), "D05_FRANK": ("Frank", 64), "D06_NANCY": ("Nancy", 72),
         "D07_GEORGE": ("George", 74), "D08_CAROL": ("Carol", 67), "D09_WILLIAM": ("William", 74), "D10_LINDA": ("Linda", 69)}
CTA_FIXA = {"D08_CAROL", "D09_WILLIAM", "D10_LINDA"}
ACENO = 0.0    # usuário (22/10): abre direto no "Hello" do S01
ENDCARD = 4.0  # card final depois da Linda

def montar_seq():
    t = ACENO
    segs = []
    for i, (k, bid, src, alin) in enumerate(SEQ):
        ws = palavras(alin)
        fdur = dur(os.path.join(P, src))
        nxt = SEQ[i + 1][0] if i + 1 < len(SEQ) else None
        cauda = 0.35 if (k == "S" and nxt == "S") else 0.55
        d = q(min(fdur, ws[-1]["e"] + cauda))
        segs.append({"k": k, "id": bid, "src": src, "s": q(t), "d": d, "w": [dict(x, s=x["s"] + q(t), e=x["e"] + q(t)) for x in ws]})
        t = q(t) + d
    return segs, q(t)

SEGS, FIM_FALA = montar_seq()
FIM = q(FIM_FALA + ENDCARD)
BY = {s["id"].replace(f"PRECO_{VER}", "PRECO"): s for s in SEGS}

def achar(bid, frase, depois=0.0):
    """tempo absoluto do início da 1ª palavra da frase dentro do bloco."""
    ws = BY[bid]["w"]; alvo = [norm(x) for x in frase.split()]
    for i in range(len(ws) - len(alvo) + 1):
        if ws[i]["s"] < depois: continue
        if all(norm(ws[i + j]["w"]) == alvo[j] for j in range(len(alvo))):
            return ws[i]["s"]
    raise SystemExit(f"frase não achada em {bid}: {frase!r}")

def fim_frase(bid, frase):
    ws = BY[bid]["w"]; alvo = [norm(x) for x in frase.split()]
    for i in range(len(ws) - len(alvo) + 1):
        if all(norm(ws[i + j]["w"]) == alvo[j] for j in range(len(alvo))):
            return ws[i + len(alvo) - 1]["e"]
    raise SystemExit(f"frase não achada em {bid}: {frase!r}")

def fim_bloco(bid): s = BY[bid]; return s["s"] + s["d"]

# ---------------------------------------------------------------- b-roll (cena por cena da referência)
# (cena, bloco, frase de entrada, fim) — fim: "frase" do mesmo bloco, ("BLOCO", "frase") ou None = fim do bloco
# fonte: mf:<arq> (acervo MarcaB) · tt:<arq> (TikTok) · ia:<cena> (IA, com fallback) · especiais
BROLL = [
    ("02", "S01", "Head of Customer Success", "Before we ship", "ia:02"),
    ("03", "S01", "Before we ship your order", "I wanted to personally", "ia:03"),
    ("05", "S01", "to take care of your joints", "When getting out of bed", "mf:T01_hug"),
    ("06", "S01", "When getting out of bed", "when you can stand up", "ia:06"),
    ("07", "S01", "when you can stand up", "without using both hands", "tt:07_senior_standing_up_from_chair"),
    ("08", "S01", "without using both hands", "when you can climb", "tt:08_stand_up_without_hands"),
    ("09", "S01", "when you can climb stairs", "and when life is back", "ia:09"),
    ("10", "S01", "and when life is back", "you'll understand why", "mf:T05_meadow"),
    ("11", "S01", "you'll understand why", "people love MarcaE", "mf:T06_garden"),
    ("12", "S01", "people love MarcaE", ("S02", "With MarcaE"), "mf:T07_bee"),
    ("13", "S02", "With MarcaE", "you're nourishing the joints", "ia:13"),
    ("14", "S02", "you're nourishing the joints", "to get out of bed", "ia:14"),
    ("15", "S02", "to get out of bed", "walk through the grocery", "tt:15_elderly_man_climbing_stairs"),
    ("16", "S02", "walk through the grocery", "and do the little", "ia:16"),
    ("17", "S02", "and do the little", "carrying groceries", "tt:17_senior_woman_getting_out_of_car"),
    ("18", "S02", "carrying groceries", "or bending down", "ia:18"),
    ("19", "S02", "or bending down", "Now, before you start", "ia:19"),
    ("21", "S02", "Because after thousands", "that some of them", "mf:T11_convertible_5s"),
    ("22", "S02", "that some of them", None, "mf:T12_car_exit_5s"),
    ("24", "S03", "However, many people reported", "and even their daily", "mf:T13_door_greet"),
    ("25", "S03", "and even their daily", None, "mf:T14_sofa_grandson"),
    ("29", "S04", "After hearing messages", "I had to find out", "mosaico"),
    ("31", "S04", "What I found honestly", "You see", "ia:31"),
    ("32", "S04", "You see", "they TRIPLED the dose", "ia:32"),
    ("33", "S04", "they TRIPLED the dose", "Taking MarcaE three times", "split"),
    ("35", "S04", "because it delivers the key", "when your body absorbs", "ia:35"),
    ("36", "S04", "when your body absorbs", None, "mf:I08_digestion"),
    ("37", "S05", "Day by day", "repair years of damage", "ia:37"),
    ("38", "S05", "repair years of damage", "so the bones stop", "ia:38"),
    ("39", "S05", "so the bones stop", "That's when moving", "ia:39"),
    ("41", "S05", "You stand up, walk", "And because MarcaE", "ia:41"),
    ("43", "S05", "honestly, it's no different", "Listen to what Margaret", "mf:I10_tea"),
    ("47", "S06", "When you take MarcaE", "your supply will run", "ia:47"),
    ("49", "S06", "Especially now", "On top of that", "ia:49"),
    ("50", "S06", "On top of that", "the next shipment", "mf:P_B04_supplier"),
    ("51", "S06", "the next shipment", "We can't rush", "mf:T19_ship"),
    ("52", "S06", "We can't rush", "your treatment will stop", "mf:P_B06_seedlings"),
    ("53", "S06", "your treatment will stop", None, "ia:53"),
    ("55", "S07", "knowing a father", "Here's what we can", "mf:T20_car_couple"),
    ("57", "S07", "Since your order is already", "the main costs", "tt:57_taping_shipping_box"),
    ("58a", "S07", "the main costs", "Adding a few extra", "tt:58a_capsule_filling"),
    ("58b", "S07", "Adding a few extra", "So we agreed", "tt:58b_capsule_filling_machine"),
    ("60", "S07", "We want to make sure", "can have one of the best", "mf:T23_flowers"),
    ("61", "S07", "can have one of the best", None, "mf:T24_pier"),
    ("63", "PRECO", "fast joint-restoring kit", None, "kit"),
    ("65", "S08", "because we're adding", "before your order leaves", "ia:65"),
    ("66", "S08", "before your order leaves", "Rest assured", "ia66|tt:66_loading_boxes_delivery_van"),
    ("70", "S08", "As soon as your MarcaE", "just take it with", "ia:70"),
    ("71", "S08", "just take it with", "Here's what other people", "ia:71"),
    ("72", "S08", "Here's what other people", None, "ia:72"),
    ("E1", "S09", "Are you ready to stop", "holding the railing", "ia:E1"),
    ("E2", "S09", "holding the railing", "and sitting out", "tt:E2_holding_stair_railing"),
    ("E3", "S09", "and sitting out", "and finally play", "ia:E3"),
    ("E4", "S09", "and finally play", "walk beside the people", "tt:E4_grandma_pushing_swing"),
    ("E5", "S09", "walk beside the people", "and enjoy the life", "tt:E5_senior_couple_walking"),
    ("E6", "S09", "and enjoy the life", "Go ahead and click", "tt:E6_elderly_couple_laughing"),
]
IA_NOME = {}
try:
    for x in json.load(open(os.path.join(J, "broll", "ia", "prompts_broll.json"))):
        IA_NOME[x["cena"]] = x["nome"].replace("_", " ")
except Exception:
    pass
IA_NOME.setdefault("70", "segundo take do unboxing (mesma mulher da cena 03)")

IA_CFG = {  # janelas limpas (05_ativos.md): rótulo derrete depois
    "13": {"t": 1.8}, "63": {"t": 3.0}, "09": {"t": 2.0}, "70": {"still": True},
    "72": {"vid": True, "vf": "crop=1440:1080:120:0"},
}

VID_REPROVADO = {"63"}  # Kling da 63 reprovado (frascos mudam): fica o still nb com push

def ia_fonte(cena):
    """vídeo pronto > still > placeholder. Vídeo/still são conformados para assets/ia/."""
    os.makedirs(os.path.join(A, "ia"), exist_ok=True)
    cfg = IA_CFG.get(cena, {})
    vnb = [] if cena in VID_REPROVADO else sorted(glob.glob(os.path.join(J, "broll", "ia", "final", f"{cena}_*_nb.mp4")))   # 1) vídeo Nano Banana
    inb = sorted(glob.glob(os.path.join(J, "broll", "ia", "img", f"{cena}_*_nb.png")))     # 2) still Nano Banana (push)
    ves = sorted(glob.glob(os.path.join(J, "broll", "ia", "final", f"{cena}_*_escala.mp4")))
    ve = vnb or ([] if inb else ves)
    ie = inb or sorted(glob.glob(os.path.join(J, "broll", "ia", "img", f"{cena}_*_escala.png")))
    if ve:   # regerado com o frasco em escala: usa inteiro, sem as janelas antigas
        nb = ve[-1].endswith("_nb.mp4")
        cfg = {"13": {"t": 2.0 if nb else 3.0}, "70": {"t": 3.0}}.get(cena, {})  # 13: frasco gira depois (nb 0–2 s, escala 0–3 s)
        if cena in ("33a", "33b", "33c"):        # painéis soltos 480x1080 -> painel do split (476x1080)
            cfg = {"vf": "scale=476:1080:force_original_aspect_ratio=increase,crop=476:1080"}
        v = ve
    elif ie:  # still em escala chegou antes do vídeo: still com push
        cfg = {"still": True}
        v = []
    else:
        pasta = "vid" if cfg.get("vid") else "final"
        v = sorted(glob.glob(os.path.join(J, "broll", "ia", pasta, f"{cena}_*.mp4")))
    if v and not cfg.get("still"):
        out = os.path.join(A, "ia", f"{cena}.mp4")
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(v[-1]):
            vf = cfg.get("vf", "scale=1440:1080:force_original_aspect_ratio=increase,crop=1440:1080")
            tt = ["-t", str(cfg["t"])] if "t" in cfg else []
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v[-1]] + tt + ["-an", "-vf",
                            f"{vf},setsar=1,fps=25,eq=contrast=1.02:saturation=0.95",
                            "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out])
        return ("video", f"assets/ia/{cena}.mp4")
    im = ie or sorted(glob.glob(os.path.join(J, "broll", "ia", "img", f"{cena}_*.png")))
    if im:
        out = os.path.join(A, "ia", f"{cena}.jpg")
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(im[-1]):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", im[-1], "-vf",
                            "scale=1440:1080:force_original_aspect_ratio=increase,crop=1440:1080", "-q:v", "2", out])
        return ("still", f"assets/ia/{cena}.jpg")
    return ("ph", None)

def ultimo_quadro(src):
    """último quadro do trecho usado, para continuar o push sem loop quando a frase é maior que o plano."""
    out = os.path.join(P, src[:-4] + "_fim.jpg")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(os.path.join(P, src)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.08", "-i", os.path.join(P, src), "-frames:v", "1", "-q:v", "2", out])
    return src[:-4] + "_fim.jpg"

# ---------------------------------------------------------------- gráficos (frase de entrada / saída)
def janelas():
    g = {}
    g["kit"] = (achar("PRECO", "fast joint-restoring kit"), fim_bloco("PRECO"))
    g["preco_num"] = achar("PRECO", f"${PRECO[0]}")
    g["garantia"] = (achar("S08", "Rest assured"), achar("S08", "If you're not 100%"))
    g["contato"] = (achar("S08", "simply call or email"), fim_frase("S08", "No questions asked.") + 0.35)
    g["botao"] = (achar("S08", "click the button below."), achar("S08", "As soon as your"))
    g["amarelo"] = (achar("S09", "Go ahead and click"), fim_bloco("S09"))
    g["cta_fixa"] = (BY["D08_CAROL"]["s"], FIM_FALA)
    g["endcard"] = (FIM_FALA, FIM)
    g["punch_turn"] = achar("S09", "Now it's your turn")
    return g

G = janelas()

# ---------------------------------------------------------------- legenda (texto da copy = texto do alinhamento)
QUEBRA = re.compile(r"[.,!?;:…—]$")

MAXC = 80  # ~2 linhas de legenda a 48 px
CONECT = {"and", "but", "so", "because", "when", "that", "without", "or", "before", "after", "until", "than",
          "while", "which", "who", "if", "since", "then", "like", "where", "even"}

FIMP = re.compile(r"([.,!?;:…]['\"’”]?|—)$")  # fim de oração (aceita aspas de fechamento)

def txt_g(g): return " ".join(y["w"] for y in g)

def dividir_oracao(o):
    if len(txt_g(o)) <= MAXC: return [o]
    alvo, melhor = len(txt_g(o)) / 2, None
    for i in range(2, len(o) - 1):  # quebra ANTES da palavra i
        w = re.sub(r"[^a-z']", "", o[i]["w"].lower())
        traco = o[i - 1]["w"].endswith(("—", "-")) or o[i]["w"] in ("—", "-")
        esq, dir_ = len(txt_g(o[:i])), len(txt_g(o[i:]))
        pena = abs(esq - alvo) + (0 if (w in CONECT or traco) else 400) - (o[i]["s"] - o[i - 1]["e"]) * 60
        if o[i]["w"] in ("—", "-"): pena += 1000  # travessão fica com a palavra de antes
        if min(esq, dir_) < 0.30 * (esq + dir_): pena += 500  # corte desequilibrado ("We want to make sure you / or…")
        if melhor is None or pena < melhor[0]: melhor = (pena, i)
    i = melhor[1]
    return dividir_oracao(o[:i]) + dividir_oracao(o[i:])

def grupos():
    out = []
    for s in SEGS:
        if s["id"] in CTA_FIXA:
            continue  # sem legenda sob a CTA fixa
        # legenda por FRASE (pedido do usuário, 23/10: "sem quebra de frase"): corta só em pontuação;
        # oração longa (> MAXC caracteres, ~2 linhas) divide antes de conectivo, o mais perto do meio
        oracoes, g = [], []
        for x in s["w"]:
            g.append(x)
            if FIMP.search(x["w"]): oracoes.append(g); g = []
        if g: oracoes.append(g)
        # oração curta (≤ 2 palavras, ex. "Look,", "You see…") cola na seguinte da mesma frase, se couber
        junt = []
        for o in oracoes:
            if junt and len(junt[-1]) <= 3 and not re.search(r"[.!?]['\"’”]?$", junt[-1][-1]["w"]):
                junt[-1] = junt[-1] + o
            else:
                junt.append(o)
        # junta orações seguidas da MESMA frase enquanto couber em 2 linhas (mostra o pensamento inteiro)
        frase = []
        for o in junt:
            if frase and not re.search(r"[.!?…][\'\"’”]?$", frase[-1][-1]["w"]) and len(txt_g(frase[-1] + o)) <= MAXC:
                frase[-1] = frase[-1] + o
            else:
                frase.append(o)
        for o in frase:
            out.extend(dividir_oracao(o))
    res = []
    for i, g in enumerate(out):
        a = max(0.0, g[0]["s"] - 0.04)
        b = g[-1]["e"] + 0.3
        if i + 1 < len(out): b = min(b + 0.35, out[i + 1][0]["s"] - 0.04)
        res.append((q(a), q(max(b, a + 0.2)), " ".join(x["w"] for x in g).replace("\n", " ")))
    return res

# ---------------------------------------------------------------- montagem

# ---------------------------------------------------------------- frasco oficial composto (tamanho real)
# O IA Creator entrega broll/ia/fundos/<cena>_fundo.png (cena SEM frasco) + composicao.json.
# Aqui o mockup oficial (PNG alfa) entra por cima, proporção intacta, com sombra de contato,
# sombra projetada contra a luz e um leve "wrap" de cor. Coordenadas do json no espaço do fundo
# (px, ou fração 0–1). Chaves aceitas (com apelidos): x|x_centro|cx, y_base|base_y|y, altura|altura_px|h,
# mockup|png|arquivo ou frascos|n_frascos, luz|luz_dir|direcao_luz (esq/dir), sombra (0–1), espelhar.
MOCKS = {1: "1-MarcaE.png", 2: "2-MarcaE.png", 3: "3-MarcaE.png", 4: "4-MarcaE.png", 6: "6-MarcaE.png", 9: "9-MarcaE.png", 12: "12-MarcaE.png"}
FUNDOS = os.path.join(J, "broll", "ia", "fundos")

def _cfg_comp():
    """medidas da régua real (edicao/composicao_frasco.json) têm prioridade; depois o json do IA Creator."""
    d = {}
    for f in [os.path.join(FUNDOS, "composicao.json"), os.path.join(J, "edicao", "composicao_frasco.json")]:
        if not os.path.exists(f): continue
        x = json.load(open(f))
        if isinstance(x, dict) and "cenas" in x: x = x["cenas"]
        if isinstance(x, list): x = {str(i.get("cena")): i for i in x}
        d.update({str(k): v for k, v in x.items() if not str(k).startswith("_")})
    return d

def _pega(c, *ks, default=None):
    for k in ks:
        if k in c and c[k] is not None: return c[k]
    return default

def _mock_recortado(nome):
    """PNG do mockup recortado no alfa + silhueta preta (para a sombra). Devolve caminhos e tamanho."""
    from PIL import Image
    os.makedirs(os.path.join(A, "comp"), exist_ok=True)
    base = os.path.splitext(nome)[0]
    out, sil = os.path.join(A, "comp", base + "_rec.png"), os.path.join(A, "comp", base + "_sombra.png")
    if not os.path.exists(out):
        im = Image.open(os.path.join(J, "ia", "mockups", nome)).convert("RGBA")
        im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
        im.save(out)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A")); sh.save(sil)
    from PIL import Image as I2
    w, h = I2.open(out).size
    return f"assets/comp/{base}_rec.png", f"assets/comp/{base}_sombra.png", w, h

COMPOR = False  # usuário (22/10): composição do mockup "bem fake" -> desligada; frasco vem da própria cena de IA

def compor(cena, box=(1440, 1080)):
    if not COMPOR: return None
    cfg = _cfg_comp().get(str(cena))
    fundo = sorted(glob.glob(os.path.join(FUNDOS, f"{cena}_fundo.*")))
    if not cfg or not fundo: return None
    from PIL import Image
    W0, H0 = Image.open(fundo[0]).size
    bw, bh = box
    z = cfg.get("zoom")  # {"cx","cy","s"}: recorte do fundo (px do fundo)
    zs = float(z["s"]) if z else 1.0
    sc = max(bw / W0, bh / H0) * zs
    zcx, zcy = (float(z["cx"]), float(z["cy"])) if z else (W0 / 2, H0 / 2)
    ox, oy = zcx * sc - bw / 2, zcy * sc - bh / 2
    ox = min(max(ox, 0), W0 * sc - bw); oy = min(max(oy, 0), H0 * sc - bh)
    os.makedirs(os.path.join(A, "comp"), exist_ok=True)
    tag = f"{cena}_{bw}"
    fj = os.path.join(A, "comp", f"{tag}_fundo.jpg")
    if not os.path.exists(fj) or os.path.getmtime(fj) < max(os.path.getmtime(fundo[0]), os.path.getmtime(os.path.join(J, "edicao", "composicao_frasco.json"))):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", fundo[0], "-vf",
                        f"scale={round(W0 * sc)}:{round(H0 * sc)}:flags=lanczos,crop={bw}:{bh}:{round(ox)}:{round(oy)}", "-q:v", "2", fj])
    itens = cfg.get("itens") or [cfg]
    luz = str(_pega(cfg, "luz", "luz_dir", "direcao_luz", default="dir")).lower()
    sentido = -1 if luz.startswith(("d", "r")) else 1
    tint = str(_pega(cfg, "tom", default="rgba(255,236,210,.10)"))
    partes = [f'<img class="cfundo" src="assets/comp/{tag}_fundo.jpg">']
    for it in sorted(itens, key=lambda i: float(_pega(i, "y_base", default=0))):
        x = float(_pega(it, "x")) * sc - ox
        yb = float(_pega(it, "y_base")) * sc - oy
        hpx = float(_pega(it, "altura")) * sc
        nome = os.path.basename(str(_pega(it, "mockup", default=MOCKS.get(int(_pega(it, "frascos", default=1)), "1-MarcaE.png"))))
        rec, sil, mw, mh = _mock_recortado(nome)
        wpx = mw * hpx / mh
        rot = float(_pega(it, "rot", default=0))
        blur = float(_pega(it, "blur", default=0))
        forca = float(_pega(it, "sombra", default=_pega(cfg, "sombra", default=0.42)))
        fb = f" blur({r(blur)}px)" if blur else ""
        if abs(rot) == 90:  # deitado: ocupa hpx de largura e wpx de altura
            cx, cy = x, yb - wpx / 2
            L, T = cx - wpx / 2, cy - hpx / 2
            partes.append(f'<div class="ccont" style="left:{r(x - hpx * .55)}px; top:{r(yb - wpx * .12)}px; width:{r(hpx * 1.1)}px; height:{r(wpx * .24)}px;"></div>')
            tr = f" transform:rotate({rot:g}deg);"
        else:
            L, T = x - wpx / 2, yb - hpx
            partes.append(f'<div class="csomb" style="left:{r(L)}px; top:{r(T)}px; width:{r(wpx)}px; height:{r(hpx)}px; transform:skewX({35 * sentido}deg) scaleY(.32); opacity:{r(forca)};"><img src="{sil}"></div>')
            partes.append(f'<div class="ccont" style="left:{r(L - wpx * .06)}px; top:{r(yb - hpx * .045)}px; width:{r(wpx * 1.12)}px; height:{r(hpx * .09)}px;"></div>')
            tr = ""
        partes.append(f'<div class="cfr" style="left:{r(L)}px; top:{r(T)}px; width:{r(wpx)}px; height:{r(hpx)}px;{tr} filter:drop-shadow(0 2px 2px rgba(0,0,0,.25)) saturate(.96) contrast(1.02){fb};">'
                      f'<img src="{rec}"><i style="background:linear-gradient({90 if sentido < 0 else 270}deg, {tint}, rgba(0,0,0,0) 55%); -webkit-mask-image:url({rec}); mask-image:url({rec});"></i></div>')
    return "".join(partes)

ESTICADOS = []
COMPOSTOS = []
LUZES = []
# onde a luz entra: as emendas que bugaram (58a→58b) + algumas viradas de bloco (entra/sai depoimento)
LUZ = [("seg", "D01_MARK"), ("seg", "S04"), ("seg", "D04_MARGARET"), ("seg", "S06"), ("br", "58b"),
       ("seg", "D05_FRANK"), ("seg", "S09"), ("hold", "09"), ("hold", "63")]
HOLD = {}

def montar():
    clips, js, sfx = [], [], []
    def S(t, f, v, d=None):
        sfx.append((q(t), f, v, d))

    # --- câmera: aceno + blocos da Susan e depoentes (trilha 0, com áudio)
    clips.append('<div id="cam"><div id="cam-in" data-layout-allow-overflow>')
    if ACENO > 0:
        clips.append(f'<video id="v-aceno" class="clip" src="assets/susan/ACENO.mp4" muted playsinline data-start="0" data-duration="{q(ACENO)}" data-track-index="0"></video>')
    for s in SEGS:
        vid = "v-" + s["id"].lower()
        clips.append(f'<video id="{vid}" class="clip" src="{s["src"]}" playsinline data-start="{s["s"]}" data-duration="{s["d"]}" '
                     f'data-track-index="0" data-has-audio="true" data-volume="1"></video>')
    clips.append('</div></div>')

    # --- b-roll: tempos
    itens = []
    for cena, bid, ent, fim, fonte in BROLL:
        a = achar(bid, ent)
        if fim is None: b = fim_bloco(bid)
        elif isinstance(fim, tuple): b = achar(fim[0], fim[1])
        else: b = achar(bid, fim, a + 0.01)
        itens.append([cena, q(a - 0.08), q(b - 0.08), fonte])
    # emenda: b-roll seguido de outro (vão < 0,9 s) encosta no próximo; o próximo entra por cima com crossfade
    XF = 0.0  # usuário: crossfade mostrava fantasma -> corte seco (como a referência)
    for i in range(len(itens) - 1):
        if itens[i + 1][1] - itens[i][2] < 0.9:
            itens[i][2] = itens[i + 1][1]
    cobertura = []
    for i, (cena, a, b, fonte) in enumerate(itens):
        seguido = i + 1 < len(itens) and abs(itens[i + 1][1] - b) < 0.01
        precedido = i > 0 and abs(itens[i - 1][2] - a) < 0.01
        fim_clip = q(b + 0.12) if seguido else b   # o de baixo segura 3 quadros sob o próximo (sem buraco)
        d = r(fim_clip - a)
        WU = 0.08 if a >= 0.08 else 0.0            # aquecimento: o vídeo começa 2 quadros antes, escondido
        cobertura.append((a, b))
        wid = f"br{cena}"
        trk = 1 + (i % 2)
        S(a - 0.05, "whoosh2" if precedido else "whoosh", 0.06 if precedido else 0.09, 1.0)
        tipo, src = ("ph", None)
        if fonte.startswith("mf:"): tipo, src = "video", f"assets/mf/{fonte[3:]}.mp4"
        elif fonte.startswith("tt:"): tipo, src = "video", f"assets/tt/{fonte[3:]}.mp4"
        elif fonte.startswith("ia66|"):
            g66 = sorted(glob.glob(os.path.join(J, "broll", "ia", "final", "66a_warehouse*.mp4")))
            if g66:  # 66a corredor (a 66b tem uniforme marrom que lembra UPS)
                tipo, src = ia_fonte("66a")
            else:
                tipo, src = "video", f"assets/tt/{fonte.split('|')[1][3:]}.mp4"
        elif fonte.startswith("ia:"): tipo, src = ia_fonte(fonte[3:])
        else: tipo = fonte
        if False and tipo == "split":  # Samurai: usar os painéis + nossos rótulos, não o split montado
            tipo, src = ia_fonte("33"); SPLIT_VIDEO = True
        else:
            SPLIT_VIDEO = False
        cc = "63" if tipo == "kit" else (fonte[3:] if fonte.startswith("ia:") else None)
        comp = compor(cc) if cc else None
        if comp:
            tipo = "comp"
        elif tipo == "kit":
            t2, s2 = ia_fonte("63")
            if t2 == "video": tipo, src = "video", s2
        inner = f'<div class="brw" id="{wid}">'
        if tipo == "video":
            sd = dur(os.path.join(P, src)) - 0.04
            rate = 1.0 if sd >= d else max(0.8, round(sd / d - 0.005, 3))
            ratt = f' data-playback-rate="{rate}"' if rate < 1 else ""
            dv = d if sd / rate >= d else q(sd / rate)
            cauda = ""
            if dv < d:  # frase maior que o plano limpo: segura o último quadro com o mesmo push (sem loop)
                fq = ultimo_quadro(src)
                cauda = f'<div id="cf{cena}" class="clip full" data-start="{r(a + dv - 0.04)}" data-duration="{r(d - dv + 0.04)}" data-track-index="{trk + 2}"><img src="{fq}"></div>'
                ESTICADOS.append((cena, round(d, 2), round(sd, 2), rate)); HOLD[cena] = r(a + dv - 0.04)
            labs = ""
            if SPLIT_VIDEO:  # rótulos do split por cima do vídeo já montado (3 painéis de 480)
                for k, (rot, ico) in enumerate([("BREAKFAST", "sunrise"), ("LUNCH", "sun"), ("DINNER", "moon")]):
                    labs += f'<div class="plab sv p{k}" style="left:{k * 480}px; width:480px;">{ICONE[ico]}<span>{rot}</span></div>'
                    js.append(f'tl.fromTo("#{wid} .sv.p{k}", {{y:24, opacity:0}}, {{y:0, opacity:1, duration:0.4, ease:"power3.out"}}, {r(a + 0.25 + k * 0.16)});')
                    S(a + 0.25 + k * 0.16, "click", 0.10, 0.35)
            clips.append(inner + f'<div class="kb" data-layout-allow-overflow><video id="vb{cena}" class="clip" src="{src}" muted playsinline data-start="{r(a - WU)}" data-duration="{r(dv + WU)}" data-media-start="0" data-track-index="{trk}"{ratt}></video>{cauda}</div>{labs}</div>')
        elif tipo == "still":
            clips.append(inner + f'<div id="cb{cena}" class="clip full" data-start="{a}" data-duration="{d}" data-track-index="{trk}"><div class="kb" data-layout-allow-overflow><img src="{src}"></div></div></div>')
        elif tipo == "comp":
            clips.append(inner + f'<div id="cb{cena}" class="clip full" data-start="{a}" data-duration="{d}" data-track-index="{trk}"><div class="kb" data-layout-allow-overflow>{comp}</div></div></div>')
            COMPOSTOS.append(cena)
        elif tipo == "mosaico":
            clips.append(inner + f'<div class="kb" data-layout-allow-overflow><video id="vb{cena}" class="clip" src="assets/img/mosaico.mp4" muted playsinline data-start="{r(a - WU)}" data-duration="{r(d + WU)}" data-media-start="0" data-track-index="{trk}"></video></div></div>')
            S(a + 0.1, "pop", 0.12, 0.6)
        elif tipo == "split":
            pans = []
            for k, (sub, rot, ico) in enumerate([("33a", "BREAKFAST", "sunrise"), ("33b", "LUNCH", "sun"), ("33c", "DINNER", "moon")]):
                t2, s2 = ia_fonte(sub)
                cp = compor(sub, (476, 1080))
                if cp:
                    m = cp; COMPOSTOS.append(sub)
                elif t2 == "video":
                    m = f'<video id="vb{sub}" class="clip" src="{s2}" muted playsinline data-start="{r(a - WU)}" data-duration="{r(d + WU)}" data-media-start="0" data-track-index="{trk}"></video>'
                elif t2 == "still":
                    m = f'<img class="pimg" src="{s2}">'
                else:
                    m = f'<div class="ph mini" data-layout-ignore><b>{sub}</b><span>{html.escape(IA_NOME.get(sub, ""))}</span></div>'
                pans.append(f'<div class="pan p{k}"><div class="pan-in">{m}</div><div class="plab">{ICONE[ico]}<span>{rot}</span></div></div>')
                js.append(f'tl.fromTo("#{wid} .p{k} .pan-in", {{yPercent:8, opacity:0}}, {{yPercent:0, opacity:1, duration:0.45, ease:"power3.out"}}, {r(a + k * 0.16)});')
                js.append(f'tl.fromTo("#{wid} .p{k} .plab", {{y:24, opacity:0}}, {{y:0, opacity:1, duration:0.4, ease:"power3.out"}}, {r(a + 0.25 + k * 0.16)});')
                S(a + 0.25 + k * 0.16, "click", 0.10, 0.35)
            clips.append(inner + f'<div id="cb{cena}" class="full split">{"".join(pans)}</div></div>')
        elif tipo == "kit":
            t2, s2 = ia_fonte("63")
            fundo = (f'<div class="kb" data-layout-allow-overflow><video id="vb63" class="clip" src="{s2}" muted playsinline data-start="{a}" data-duration="{d}" data-media-start="0" data-track-index="{trk}"></video></div>' if t2 == "video"
                     else f'<div id="cb63" class="clip full kitbg" data-start="{a}" data-duration="{d}" data-track-index="{trk}"><div class="kb" data-layout-allow-overflow>'
                          + (f'<img src="{s2}">' if t2 == "still" else '<img class="kit9" src="assets/img/kit9.png">') + '</div></div>')
            clips.append(inner + fundo + '</div>')
        else:  # placeholder
            clips.append(inner + f'<div id="cb{cena}" class="clip full" data-start="{a}" data-duration="{d}" data-track-index="{trk}"><div class="kb" data-layout-allow-overflow><div class="ph" data-layout-ignore><b>CENA {cena}</b><span>{html.escape(IA_NOME.get(cena, ""))}</span><i>B-ROLL IA PENDENTE</i></div></div></div></div>')
        # entrada: crossfade curto (7 quadros) por cima do anterior; push lento contínuo 1,00 → 1,05
        js.append(f'tl.set("#{wid}", {{opacity:1}}, {a});')
        js.append(f'tl.set("#{wid}", {{opacity:0}}, {fim_clip});')
        if tipo != "split":
            js.append(f'tl.fromTo("#{wid} .kb", {{scale:1.0}}, {{scale:1.05, duration:{d}, ease:"none"}}, {a});')

    # --- punch-in alternado da Susan (corte seco), só onde ela está na tela
    def coberto(t): return any(a - 0.01 <= t < b for a, b in cobertura)
    sus = [s for s in SEGS if s["k"] == "S"]
    escala, ult = 1.0, -10
    for s in sus:
        frases = [s["w"][0]["s"]] + [x["s"] for i, x in enumerate(s["w"][1:], 1) if QUEBRA.search(s["w"][i - 1]["w"])]
        pontos = sorted(set([q(s["s"])] + [q(b) for a, b in cobertura if s["s"] < b < s["s"] + s["d"]] + [q(f - 0.04) for f in frases]))
        for t in pontos:
            if coberto(t + 0.05): continue
            volta = any(abs(t - b) < 0.02 for a, b in cobertura) or abs(t - s["s"]) < 0.02
            if not volta and t - ult < 3.6: continue
            if G["garantia"][0] - 0.1 <= t < G["contato"][1]: continue
            escala = 1.08 if escala == 1.0 else 1.0
            js.append(f'tl.set("#cam-in", {{scale:{escala}}}, {t});'); ult = t
    js.append(f'tl.set("#cam-in", {{scale:1.0}}, {q(G["garantia"][0] - 0.04)});')
    js.append(f'tl.set("#cam-in", {{scale:1.08}}, {q(G["punch_turn"] - 0.04)});')
    # depoentes: deriva lenta 1,00 → 1,03 (um plano por depoimento)
    for s in SEGS:
        if s["k"] == "D":
            js.append(f'tl.fromTo("#cam-in", {{scale:1.0}}, {{scale:1.03, duration:{s["d"]}, ease:"none", immediateRender:false}}, {s["s"]});')

    # --- tarja do depoente
    for s in SEGS:
        if s["k"] != "D": continue
        nome, idade = NOMES[s["id"]]
        a = q(s["s"] + 0.5); d = 5.4
        alto = " alto" if s["id"] in CTA_FIXA else ""
        clips.append(f'<div id="tj-{s["id"]}" class="clip tarja{alto}" data-start="{a}" data-duration="{d}" data-track-index="4">'
                     f'<div class="tj-in"><div class="tj-nome"><i></i>{html.escape(nome)}</div><div class="tj-age"><small data-layout-ignore>AGE</small><b>{idade}</b></div></div></div>')
        js.append(f'tl.fromTo("#tj-{s["id"]} .tj-in", {{clipPath:"inset(0% 100% 0% 0%)", x:-30}}, {{clipPath:"inset(0% 0% 0% 0%)", x:0, duration:0.45, ease:"power3.out"}}, {a});')
        js.append(f'tl.to("#tj-{s["id"]} .tj-in", {{clipPath:"inset(0% 100% 0% 0%)", duration:0.35, ease:"power2.in"}}, {r(a + d - 0.38)});')
        S(a, "click", 0.18, 0.35)

    # --- preço (card sobre o kit)
    a, b = G["kit"]; n = q(G["preco_num"] - 0.06)
    clips.append(f'<div id="g-preco" class="clip gpreco" data-start="{n}" data-duration="{r(b - n)}" data-track-index="5"><div class="pc-in">'
                 f'<div class="pc-num"><sup>$</sup>{PRECO[0]}</div><div class="pc-per">PER BOTTLE</div><div class="pc-line"></div><div class="pc-tot">${PRECO[1]} TOTAL</div></div></div>')
    clips.append(f'<div id="g-kitlab" class="clip kitlab" data-start="{q(a)}" data-duration="{r(b - a)}" data-track-index="5"><div class="kl-in">FAST JOINT-RESTORING KIT<span>9 BOTTLES</span></div></div>')
    js.append(f'tl.fromTo("#g-kitlab .kl-in", {{y:30, opacity:0}}, {{y:0, opacity:1, duration:0.5, ease:"power3.out"}}, {q(a + 0.1)});')
    js.append(f'tl.fromTo("#g-preco .pc-in", {{x:80, opacity:0, scale:0.94}}, {{x:0, opacity:1, scale:1, duration:0.5, ease:"power3.out"}}, {n});')
    js.append(f'tl.fromTo("#g-preco .pc-num", {{scale:0.7}}, {{scale:1, duration:0.45, ease:"back.out(2)"}}, {r(n + 0.12)});')
    S(n, "pop", 0.16, 0.6); S(n + 0.12, "cash", 0.16, 1.8)

    # --- garantia: Susan desfocada + card; riser antes
    a, b = G["garantia"]
    js.append(f'tl.fromTo("#cam-in", {{filter:"blur(0px) brightness(1)"}}, {{filter:"blur(16px) brightness(0.5)", duration:0.4, ease:"power2.out"}}, {q(a)});')
    js.append(f'tl.to("#cam-in", {{filter:"blur(0px) brightness(1)", duration:0.12}}, {q(b - 0.06)});')
    # selo oficial "1 YEAR MONEY-BACK GUARANTEE" (arte do usuário, 23/10) no lugar do texto
    clips.append(f'<div id="g-gar" class="clip ggar" data-start="{q(a)}" data-duration="{r(b - a)}" data-track-index="5">'
                 f'<img class="gg-selo" src="assets/graf/selo_garantia_1year.png" width="680" height="680" alt=""></div>')
    js.append(f'tl.fromTo("#g-gar .gg-selo", {{scale:0.55, rotation:-12, opacity:0}}, {{scale:1, rotation:0, opacity:1, duration:0.6, ease:"back.out(1.8)"}}, {r(a + 0.12)});')
    js.append(f'tl.to("#g-gar .gg-selo", {{scale:1.04, duration:{r(max(0.5, b - a - 0.9))}, ease:"sine.inOut"}}, {r(a + 0.75)});')
    S(a - 2.3, "riser", 0.12, 2.58); S(a + 0.15, "ding", 0.14, 2.2)
    # flash branco de 2 quadros na saída da garantia
    clips.append(f'<div id="g-flash" class="clip flash" data-start="{q(b - 0.04)}" data-duration="0.16" data-track-index="7"><div class="fl-in"></div></div>')
    js.append(f'tl.fromTo("#g-flash .fl-in", {{opacity:0.9}}, {{opacity:0, duration:0.14, ease:"power2.out"}}, {q(b - 0.04)});')

    # --- contato
    a, b = G["contato"]
    clips.append(f'<div id="g-cont" class="clip gcont" data-start="{q(a)}" data-duration="{r(b - a)}" data-track-index="5">'
                 f'<div class="ct ct1"><span class="ic">{ICONE["fone"]}</span><b>+1 (323) 372-2586</b></div>'
                 f'<div class="ct ct2"><span class="ic">{ICONE["mail"]}</span><b>support@MarcaE.com</b></div></div>')
    js.append(f'tl.fromTo("#g-cont .ct1", {{x:-560}}, {{x:0, duration:0.5, ease:"power3.out"}}, {q(a)});')
    js.append(f'tl.fromTo("#g-cont .ct2", {{x:-560}}, {{x:0, duration:0.5, ease:"power3.out"}}, {q(a + 0.14)});')
    js.append(f'tl.to("#g-cont .ct", {{x:-560, duration:0.35, ease:"power2.in", stagger:0.08}}, {r(b - 0.45)});')
    S(a, "click", 0.16, 0.35); S(a + 0.14, "click", 0.14, 0.35)

    # --- botão laranja ADD & CONTINUE
    a, b = G["botao"]
    clips.append(f'<div id="g-bt" class="clip gbt gbt-alto" data-start="{q(a)}" data-duration="{r(b - a)}" data-track-index="5"><div class="bt-in laranja">ADD &amp; CONTINUE <em>›</em></div></div>')
    js.append(f'tl.fromTo("#g-bt .bt-in", {{scale:0.6, opacity:0}}, {{scale:1, opacity:1, duration:0.4, ease:"back.out(2)"}}, {q(a)});')
    npul = max(1, int((b - a - 0.6) / 0.9))
    js.append(f'tl.to("#g-bt .bt-in", {{scale:1.05, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:{npul * 2 - 1}}}, {r(a + 0.5)});')
    S(a, "pop", 0.16, 0.6)

    # --- botão amarelo GET TRIPLE-DOSE (Susan na tela)
    a, b = G["amarelo"]
    clips.append(f'<div id="g-am" class="clip gbt gbt-alto" data-start="{q(a)}" data-duration="{r(b - a)}" data-track-index="5"><img class="bt-in bt-img" src="assets/graf/botao_get_triple_dose_alpha.png" width="640" height="113" alt="GET TRIPLE-DOSE"></div>')
    js.append(f'tl.fromTo("#g-am .bt-in", {{scale:0.6, opacity:0}}, {{scale:1, opacity:1, duration:0.4, ease:"back.out(2)"}}, {q(a)});')
    npul = max(1, int((b - a - 0.6) / 0.9))
    js.append(f'tl.to("#g-am .bt-in", {{scale:1.05, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:{npul * 2 - 1}}}, {r(a + 0.5)});')
    S(a, "pop", 0.16, 0.6)

    # --- CTA fixa por cima dos 3 últimos depoimentos
    a, b = G["cta_fixa"]
    clips.append(f'<div id="g-cta" class="clip gcta" data-start="{q(a)}" data-duration="{r(b - a)}" data-track-index="6"><img class="cta-in" src="assets/img/CTA_fixa_{VER}.png"></div>')
    js.append(f'tl.fromTo("#g-cta .cta-in", {{y:60, opacity:0}}, {{y:0, opacity:1, duration:0.7, ease:"power3.out"}}, {q(a + 0.3)});')
    S(a + 0.3, "whoosh", 0.08, 1.0)

    # --- card final
    a, b = G["endcard"]
    clips.append(f'<div id="g-end" class="clip gend" data-start="{q(a)}" data-duration="{r(b - a)}" data-track-index="7"><div class="end-in">'
                 f'<img class="end-kit" src="assets/img/kit3.png"><div class="end-t1">CLICK THE BUTTON BELOW</div>'
                 f'<div class="end-t2"><i></i>TO GET YOUR<i></i></div><div class="end-t3">TRIPLE-DOSE TREATMENT</div><div class="end-seta">{ICONE["seta"]}</div></div></div>')
    js.append(f'tl.fromTo("#g-end .end-in", {{opacity:0}}, {{opacity:1, duration:0.4}}, {q(a)});')
    js.append(f'tl.fromTo("#g-end .end-kit", {{y:-40, scale:0.92}}, {{y:0, scale:1, duration:0.7, ease:"power3.out"}}, {q(a)});')
    for k, cl in enumerate(["end-t1", "end-t2", "end-t3"]):
        js.append(f'tl.fromTo("#g-end .{cl}", {{y:30, opacity:0}}, {{y:0, opacity:1, duration:0.45, ease:"power3.out"}}, {r(a + 0.3 + k * 0.12)});')
    js.append(f'tl.fromTo("#g-end .end-seta", {{y:-20, opacity:0}}, {{y:0, opacity:1, duration:0.4, ease:"back.out(2)"}}, {r(a + 0.7)});')
    js.append(f'tl.to("#g-end .end-seta", {{y:14, duration:0.42, ease:"sine.inOut", yoyo:true, repeat:5}}, {r(a + 1.1)});')
    S(a, "whoosh", 0.10, 1.0); S(a + 0.35, "ding", 0.12, 2.2)

    # --- legenda
    for k, (a, b, txt) in enumerate(grupos()):
        if G["garantia"][0] - 0.2 <= (float(a) + float(b)) / 2 < G["garantia"][1]:
            continue  # sem legenda sob o card de garantia (pedido do usuário, 23/10)
        clips.append(f'<div id="cap{k}" class="clip cap" data-start="{a}" data-duration="{r(b - a)}" data-track-index="8"><div class="cap-in">{html.escape(txt)}</div></div>')

    # --- grão uniforme
    ng = int(FIM / 0.16) + 1
    js.append(f'tl.fromTo(".grao", {{backgroundPosition:"0px 0px"}}, {{backgroundPosition:"-5760px 0px", duration:0.16, ease:"steps(4)", repeat:{ng}}}, 0);')

    # --- light leak (Baú: _Burning Light Transition 4/5), pico no corte, screen a 60 %, shimmer leve
    for k, (tipo_l, nome_l) in enumerate(LUZ):
        if tipo_l == "hold" and nome_l not in HOLD: continue
        t = BY[nome_l]["s"] if tipo_l == "seg" else (HOLD[nome_l] if tipo_l == "hold" else next(x[1] for x in itens if x[0] == nome_l))
        a0 = q(t - 0.28)
        src = f"assets/luz/leak{4 if k % 2 == 0 else 5}_{k}.mp4"
        if not os.path.exists(os.path.join(P, src)):
            shutil.copy(os.path.join(A, "luz", f"leak{4 if k % 2 == 0 else 5}.mp4"), os.path.join(P, src))
        clips.append(f'<div class="luz" id="lz{k}"><video id="vlz{k}" class="clip" src="{src}" muted playsinline data-start="{a0}" data-duration="0.56" data-track-index="9"></video></div>')
        S(t - 0.25, "whoosh2", 0.05, 1.0)
        LUZES.append((nome_l, round(t, 2)))

    # --- áudio: trilha ~20 dB abaixo da voz sob a fala (−30 dB sumiu: "faltou fundo musical", 23/10); sobe ~8 dB no card final
    MV, MF = 0.39, 0.98
    ap = [{"t": 0, "v": 0.0}, {"t": 0.8, "v": MV}, {"t": r(FIM_FALA - 0.3), "v": MV}, {"t": r(FIM_FALA + 0.5), "v": MF},
          {"t": r(FIM - 1.4), "v": MF}, {"t": r(FIM), "v": 0.0}]
    auto = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": ap}]})
    clips.append(f"<audio id=\"trilha\" src=\"assets/music/bed.m4a\" data-start=\"0\" data-duration=\"{FIM}\" data-track-index=\"10\" data-volume=\"1\" data-automation='{auto}'></audio>")
    sfx.sort()
    for k, (t, f, v, d) in enumerate(sfx):
        if t < 0: continue
        dd = d or 1.0
        dd = min(dd, r(FIM - t))
        clips.append(f'<audio id="sfx{k}" src="assets/sfx/{f}.mp3" data-start="{t}" data-duration="{dd}" data-track-index="{11 + k % 4}" data-volume="{v}"></audio>')

    return clips, js, len(sfx), len(grupos())

ICONE = {
    "sunrise": '<svg viewBox="0 0 48 48"><path d="M8 34h32M14 34a10 10 0 0 1 20 0M24 12v6M10 20l4 4M38 20l-4 4" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>',
    "sun": '<svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="8" fill="none" stroke="#fff" stroke-width="3"/><path d="M24 6v5M24 37v5M6 24h5M37 24h5M11 11l3.5 3.5M33.5 33.5L37 37M37 11l-3.5 3.5M14.5 33.5L11 37" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>',
    "moon": '<svg viewBox="0 0 48 48"><path d="M30 8a16 16 0 1 0 10 26A13 13 0 0 1 30 8z" fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round"/></svg>',
    "fone": '<svg viewBox="0 0 48 48"><path d="M14 6l6 10-4 4c2 5 7 10 12 12l4-4 10 6-3 8C22 41 7 26 6 9z" fill="#fff"/></svg>',
    "mail": '<svg viewBox="0 0 48 48"><rect x="6" y="11" width="36" height="26" rx="3" fill="none" stroke="#fff" stroke-width="3"/><path d="M7 13l17 13 17-13" fill="none" stroke="#fff" stroke-width="3"/></svg>',
    "seta": '<svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="29" fill="none" stroke="#004C5B" stroke-width="4"/><path d="M32 18v26M21 34l11 11 11-11" fill="none" stroke="#004C5B" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}

CSS = f"""
@font-face {{ font-family:"Montserrat"; src:url("assets/fonts/Montserrat-VF.ttf"); font-weight:100 900; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1440px; height:1080px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:100%; height:100%; overflow:hidden; background:#000; font-family:"Montserrat"; }}
#cam {{ position:absolute; inset:0; overflow:hidden; z-index:1; }}
#cam-in {{ position:absolute; inset:0; transform-origin:50% 38%; }}
#cam video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.brw {{ position:absolute; inset:0; overflow:hidden; z-index:2; opacity:0; }}
.brw .kb {{ position:absolute; inset:0; }}
.brw video, .brw img, .brw .full {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.ph {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:18px;
  background:repeating-linear-gradient(135deg, #0b3b45 0 40px, #0e4652 40px 80px); color:#fff; text-align:center; }}
.ph b {{ font-size:120px; font-weight:800; letter-spacing:-2px; }}
.ph span {{ font-size:34px; font-weight:600; opacity:.85; max-width:1100px; }}
.ph i {{ font-style:normal; font-size:24px; font-weight:700; letter-spacing:.3em; color:{YEL}; }}
.ph.mini b {{ font-size:64px; }} .ph.mini span {{ font-size:20px; max-width:420px; }}
.split {{ background:#fff; }}
.split .pan {{ position:absolute; top:0; bottom:0; width:476px; overflow:hidden; }}
.split .p0 {{ left:0; }} .split .p1 {{ left:482px; }} .split .p2 {{ left:964px; }}
.split .pan-in {{ position:absolute; inset:0; }}
.split .pan-in video, .split .pan-in img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.plab.sv {{ position:absolute; bottom:250px; display:flex; flex-direction:column; align-items:center; gap:8px; color:#fff; font-size:28px; font-weight:700; letter-spacing:.3em; text-shadow:0 2px 12px rgba(0,0,0,.6); z-index:3; }}
.plab.sv svg {{ width:46px; height:46px; }}
.split .plab {{ position:absolute; left:0; right:0; bottom:250px; display:flex; flex-direction:column; align-items:center; gap:8px; color:#fff;
  font-size:28px; font-weight:700; letter-spacing:.3em; text-shadow:0 2px 12px rgba(0,0,0,.6); }}
.split .plab svg {{ width:46px; height:46px; filter:drop-shadow(0 2px 6px rgba(0,0,0,.5)); }}
.kitbg {{ background:radial-gradient(ellipse at 40% 45%, #ffffff 0%, #eef2f1 45%, #cfdcda 100%); }}
.kitbg .kit9 {{ position:absolute; left:40px; top:150px; width:900px; height:auto; object-fit:contain; filter:drop-shadow(0 30px 40px rgba(0,40,50,.28)); }}
.kitlab {{ position:absolute; left:90px; top:120px; z-index:6; }}
.kl-in {{ color:{TEAL}; font-size:40px; font-weight:800; letter-spacing:.02em; background:rgba(255,255,255,.9); padding:16px 26px 18px; border-radius:16px; box-shadow:0 12px 30px rgba(0,0,0,.18); }}
.kl-in span {{ display:block; font-size:28px; font-weight:700; letter-spacing:.34em; color:#2f6f7a; margin-top:6px; }}
.gpreco {{ position:absolute; right:70px; top:250px; z-index:6; }}
.pc-in {{ width:440px; background:{TEAL}; border:5px solid {YEL}; border-radius:28px; padding:26px 34px 30px; text-align:center;
  box-shadow:0 24px 60px rgba(0,30,40,.35); }}
.pc-num {{ color:{YEL}; font-size:200px; font-weight:900; line-height:.95; letter-spacing:-6px; }}
.pc-num sup {{ font-size:110px; vertical-align:top; position:relative; top:14px; margin-right:4px; }}
.pc-per {{ color:#fff; font-size:44px; font-weight:800; letter-spacing:.02em; margin-top:6px; }}
.pc-line {{ height:4px; background:#fff; margin:14px 10px 12px; }}
.pc-tot {{ color:#fff; font-size:36px; font-weight:600; }}
.ggar {{ position:absolute; inset:0; z-index:6; display:flex; align-items:center; justify-content:center; }}
.gg-in {{ text-align:center; color:#fff; text-shadow:0 6px 30px rgba(0,0,0,.45); }}
.gg-100 {{ font-size:170px; font-weight:900; line-height:1; letter-spacing:-4px; }}
.gg-mb {{ font-size:84px; font-weight:800; line-height:1.05; }}
.gg-g {{ font-size:40px; font-weight:600; letter-spacing:.42em; margin-top:10px; }}
.gg-y {{ display:inline-block; margin-top:28px; font-size:24px; font-weight:800; letter-spacing:.18em; color:{TEAL}; background:{YEL}; padding:10px 26px; border-radius:40px; text-shadow:none; }}
.cfundo {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.csomb {{ position:absolute; transform-origin:50% 100%; filter:blur(10px); }}
.csomb img, .cfr img {{ position:absolute; inset:0; width:100%; height:100%; }}
.ccont {{ position:absolute; border-radius:50%; background:radial-gradient(ellipse at center, rgba(0,0,0,.55) 0%, rgba(0,0,0,.25) 45%, rgba(0,0,0,0) 72%); filter:blur(3px); }}
.cfr {{ position:absolute; }}
.cfr i {{ position:absolute; inset:0; mix-blend-mode:soft-light; -webkit-mask-size:100% 100%; mask-size:100% 100%; }}
.luz {{ position:absolute; inset:0; z-index:8; pointer-events:none; mix-blend-mode:screen; opacity:.6; }}
.luz video {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.flash {{ position:absolute; inset:0; z-index:9; }}
.fl-in {{ position:absolute; inset:0; background:#fff; opacity:0; }}
.gcont {{ position:absolute; left:0; top:580px; z-index:6; }}
.ct {{ display:flex; align-items:center; height:86px; margin-bottom:16px; padding-right:40px; border-radius:0 14px 14px 0; box-shadow:0 12px 30px rgba(0,0,0,.25); }}
.ct .ic {{ width:86px; height:86px; display:flex; align-items:center; justify-content:center; background:#00353f; margin-right:22px; }}
.ct .ic svg {{ width:42px; height:42px; }}
.ct1 {{ background:{TEAL}; color:#fff; font-size:50px; font-weight:800; width:620px; }}
.ct2 {{ background:#fff; color:{TEAL}; font-size:34px; font-weight:700; width:560px; }}
.gbt {{ position:absolute; left:0; right:0; top:782px; z-index:6; display:flex; justify-content:center; }}
.bt-in {{ font-size:38px; font-weight:800; letter-spacing:.01em; padding:22px 58px; border-radius:60px; box-shadow:0 16px 40px rgba(0,0,0,.35); }}
.bt-in em {{ font-style:normal; margin-left:10px; }}
.gbt-alto {{ top:690px; }}  /* acima da legenda de 2 linhas */
.bt-img {{ width:640px; height:113px; object-fit:contain; padding:0; border-radius:0; box-shadow:none; filter:drop-shadow(0 14px 28px rgba(0,0,0,.4)); }}
.gg-selo {{ position:absolute; left:50%; top:50%; width:680px; height:680px; margin:-370px 0 0 -340px; filter:drop-shadow(0 20px 40px rgba(0,0,0,.45)); }}
.laranja {{ color:#fff; background:linear-gradient(180deg, #F26A1B, #E8531A); }}
.amarelo {{ color:{TEAL}; background:{YEL}; border:4px solid #fff; font-weight:900; }}
.gcta {{ position:absolute; inset:0; z-index:6; }}
.gcta img {{ position:absolute; inset:0; width:100%; height:100%; }}
.gend {{ position:absolute; inset:0; z-index:8; }}
.end-in {{ position:absolute; inset:0; background:radial-gradient(ellipse at 50% 35%, #ffffff 0%, #eef3f2 55%, #d6e3e1 100%); display:flex; flex-direction:column; align-items:center; }}
.end-kit {{ width:760px; height:auto; margin-top:40px; filter:drop-shadow(0 26px 34px rgba(0,40,50,.25)); }}
.end-t1 {{ color:#0d2b31; font-size:66px; font-weight:900; margin-top:18px; letter-spacing:-1px; }}
.end-t2 {{ display:flex; align-items:center; gap:18px; color:#41656b; font-size:28px; font-weight:700; letter-spacing:.3em; margin-top:8px; }}
.end-t2 i {{ display:block; width:90px; height:2px; background:#41656b; }}
.end-t3 {{ color:#fff; background:{TEAL}; font-size:46px; font-weight:800; padding:12px 40px; border-radius:16px; margin-top:16px; }}
.end-seta {{ margin-top:20px; width:72px; height:72px; }}
.end-seta svg {{ width:72px; height:72px; }}
.tarja {{ position:absolute; left:0; top:790px; z-index:5; }}
.tarja.alto {{ top:610px; }}
.tj-in {{ display:flex; align-items:stretch; height:84px; }}
.tj-nome {{ display:flex; align-items:center; background:{TEAL}; color:#fff; font-size:38px; font-weight:600; padding:0 30px 0 36px; position:relative; }}
.tj-nome i {{ position:absolute; left:16px; top:18px; bottom:18px; width:4px; background:#fff; }}
.tj-age {{ display:flex; flex-direction:column; align-items:center; justify-content:center; background:#fff; width:84px; }}
.tj-age small {{ font-size:13px; font-weight:700; letter-spacing:.2em; color:#7c8b8e; }}
.tj-age b {{ font-size:42px; font-weight:800; color:{TEAL}; line-height:1; }}
.cap {{ position:absolute; left:120px; right:120px; bottom:108px; z-index:7; display:flex; justify-content:center; }}
.cap-in {{ text-wrap:balance; max-width:1180px; background:rgba(0,0,0,.5); color:#fff; font-size:48px; font-weight:700; line-height:1.2; text-align:center;
  padding:12px 22px 14px; border-radius:10px; }}
.vinheta {{ position:absolute; inset:0; z-index:9; pointer-events:none; background:radial-gradient(ellipse at center, rgba(0,0,0,0) 62%, rgba(0,0,0,.26) 100%); }}
.grao {{ position:absolute; inset:0; z-index:9; pointer-events:none; opacity:.07; mix-blend-mode:overlay;
  background-image:url("assets/img/grao.png"); background-size:5760px 1080px; background-repeat:no-repeat; }}
"""

def preparar_imagens():
    img = os.path.join(A, "img"); os.makedirs(img, exist_ok=True)
    for v in "ABC":
        dst = os.path.join(img, f"CTA_fixa_{v}.png")
        if not os.path.exists(dst):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(J, "edicao", "ref_graficos", f"CTA_fixa_{v}.png"), "-vf", "scale=1440:1080", dst])
    for src, dst in [("9-MarcaE.png", "kit9.png"), ("3-MarcaE.png", "kit3.png")]:
        if not os.path.exists(os.path.join(img, dst)):
            shutil.copy(os.path.join(J, "ia", "mockups", src), os.path.join(img, dst))

def main():
    preparar_imagens()
    clips, js, nsfx, ncap = montar()
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1440, height=1080" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{FIM}" data-width="1440" data-height="1080" data-fps="{FPS}">
{chr(10).join(clips)}
<div class="vinheta"></div>
<div class="grao"></div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
    open(os.path.join(P, "index.html"), "w").write(doc)
    # relatório
    ia = [(c, ia_fonte(f[3:])[0]) for c, _, _, _, f in BROLL if f.startswith("ia:")]
    ia += [(s, ia_fonte(s)[0]) for s in ("33a", "33b", "33c", "63")]
    falta = [c for c, t in ia if t == "ph"]; still = [c for c, t in ia if t == "still"]
    rel = {"versao": VER, "duracao": FIM, "fala": FIM_FALA, "b_roll": len(BROLL), "legendas": ncap, "sfx": nsfx,
           "ia_placeholder": falta, "ia_still": still, "esticados": ESTICADOS, "compostos": COMPOSTOS, "luzes": LUZES,
           "segmentos": [(s["id"], s["s"], s["d"]) for s in SEGS], "janelas": {k: v for k, v in G.items()}}
    json.dump(rel, open(os.path.join(J, "edicao", f"build_{VER}.json"), "w"), indent=1, ensure_ascii=False)
    print(f"versão {VER} · {FIM:.2f}s ({int(FIM//60)}:{FIM%60:04.1f}) · {len(BROLL)} b-rolls · {ncap} legendas · {nsfx} SFX")
    print("IA placeholder:", " ".join(falta) or "—"); print("IA still:", " ".join(still) or "—"); print("esticados (cena, frase, plano, rate):", ESTICADOS); print("compostos:", COMPOSTOS); print("luzes:", LUZES)

if __name__ == "__main__":
    main()
