# -*- coding: utf-8 -*-
# AJUSTAR ANTES DE REUSAR NOUTRO JOB:
#   REF_*            -> mockups do produto deste job (ver ../assets)
#   PALETTE / STYLE  -> trocar o acento verde #3FB27A pela cor do produto
#   MOTIONS          -> a lista abaixo e a do CLOSE LeafTide; serve de exemplo real
#                       de como descrever cada beat por arquetipo
#   --aspect-ratio   -> 9:16 se o entregavel for vertical ou 4:5; 16:9 so se a
#                       sequencia for mesmo 16:9 (CONFIRA COM getSettings ANTES)
"""Gera os 24 motions restantes (vermelho + roxo) do close LeafTide no Omni Flash.

Blocos STYLE / TECHNICAL / PALETTE / CAMERA / AUDIO / DO NOT sao IDENTICOS em todos —
e o que faz o lote emendar como um sistema visual so (exigencia da skill blackbelt-omni).
Varia apenas: string exata, tipografia por linha, e TIMELINE.
"""
import json, os, subprocess, sys

S = os.path.dirname(os.path.abspath(__file__))
REF_KIT = os.path.join(S, "ref_kit_6.png")
REF_POTE = os.path.join(S, "ref_pote_solo.png")
REF_RHONDA = os.path.join(S, "rhonda.png")

# ---------------------------------------------------------------- blocos comuns
STYLE_PROD = ("STYLE: Premium direct-response motion graphics on a deep black void — a matte black stage "
  "with soft volumetric haze, the LeafTide jar lit as a hero object with a warm practical rim light behind "
  "it and a soft key from the left, floating glass cards with rounded corners and thin luminous green edges "
  "drifting in the lower third, off-white line graphics inside the cards, subtle film grain, shallow depth "
  "of field, everything rendered with the restraint of a high-end product film. Vertical portrait composition: the jar sits in the upper middle of the frame and the typography stacks directly beneath it, both centred.")

STYLE_AVATAR = ("STYLE: Premium direct-response motion graphics on a deep black void — a mature woman with long "
  "wavy brown hair, wearing a plain black fitted long-sleeve top and no jewelry, stands centred in the "
  "frame in a matte black studio with soft volumetric haze, a warm practical rim light behind her and a soft key "
  "from the left, her silhouette clean against the dark. Large off-white typography stacks in the space above her head. "
  "A single glass panel with thin luminous green edges sits behind the type. Subtle film grain, shallow depth of "
  "field, the restraint of a high-end brand film. Vertical portrait composition: she is framed from the chest up in the lower half of the frame, and the typography stacks above her head in the upper middle, centred.")

STYLE_PURO = ("STYLE: Premium direct-response motion graphics on a deep black void — a matte black stage with soft "
  "volumetric haze and nothing else in frame but typography and one glass panel with thin luminous green edges. "
  "Off-white line graphics only, subtle film grain, shallow depth of field, the restraint of a high-end brand film. Vertical portrait composition: the panel and the stacked typography are centred in the middle of the frame.")

TECHNICAL = ("TECHNICAL: 1080x1920, 9:16 vertical portrait, 10 seconds, single continuous piece, no cuts to black, no letterboxing. The top 15 percent and the bottom 15 percent of the frame will later be cropped away, so every product, every graphic and every letter must sit comfortably inside the central 70 percent of the frame height. Nothing important touches the top or bottom edge.")

PALETTE = ("PALETTE: Background pure black #0B0B0C. Typography and card line-art off-white #F6F3EC. The single "
  "accent is LeafTide green #3FB27A with real bloom — it appears ONLY as the edge light of a glass panel at the "
  "instant it lands, and as the glow on the emphasised line. Jars keep their own deep green #00562E body and "
  "#1B5E36 lid. No gold, no blue, no second accent.")

CAMERA = ("CAMERA: One continuous slow push-in for the whole piece, no cuts. Every element decelerates into place "
  "as if settling under its own weight — nothing moves at a constant speed. Elements that leave shrink and defocus "
  "rather than disappearing.")

AUDIO = ("AUDIO: No speech of any kind. A low cinematic bed with a soft sub pulse, one muted click when a panel "
  "lands, and complete silence for the final beat.")

DONT_BASE = ("DO NOT: never render any word from these instructions as visible text — no technical terms, no \"caption\", no \"safe zone\", no \"frame\", no pixel sizes, no colour codes, no font names, no durations; no burned-in subtitles, no captions, no spoken words, no extra text of any kind beyond the "
  "exact phrase, no invented words, no gibberish lettering, no extra line of text, no headline above the phrase, "
  "no invented label copy, no fictional seals with writing, no gold accent, no lens flare streaks, no rapid "
  "strobing, no zoom punches, no watermark, no logo bug in the corner, no letterbox bars, no split screen")
DONT_AVATAR = DONT_BASE + ", no lip sync, no mouth movement, no second person in frame."
DONT_PROD = DONT_BASE + ", no second product, no competitor packaging."
DONT_PURO = DONT_BASE + ", no people in frame."

NOSPEECH_AVATAR = ("NO SPEECH: the woman never speaks, there is no dialogue, no voice-over, no narrator, no lip "
  "movement, her mouth stays closed and calm. The woman must match the supplied reference image — same face, "
  "same hair, same age, same skin tone.")
NOSPEECH_PROD = ("NO SPEECH: there is no person in frame, no dialogue, no voice-over, no narrator. The product jar "
  "must match the supplied reference image exactly — same deep green jar, same green screw lid, same label artwork "
  "and leaf motif. Do not invent a different label.")
NOSPEECH_PURO = "NO SPEECH: there is no person in frame, no dialogue, no voice-over, no narrator."


def critical(frase, linhas, nospeech):
    n = len(frase.split())
    desc = " ".join(f'Line {i+1} reads "{l}".' for i, l in enumerate(linhas))
    return (f'CRITICAL RULES — ONE TEXT EXCEPTION: The ONLY readable text allowed anywhere in this video is the '
      f'exact phrase "{frase}" — {n} words, nothing else. It must be spelled exactly like that, letter for letter, '
      f'and it appears as exactly {len(linhas)} line(s). {desc} There is no additional line. There is no headline, '
      f'no label, no sub-line, no kicker, no extra word above, below or beside it. Never invent additional words to '
      f'fill space. The phrase appears EXACTLY ONCE in the frame at any moment — never duplicated on a second card, never repeated elsewhere. Absolutely no other readable text, letters, numbers, subtitles, captions, watermarks or UI copy '
      f'may appear anywhere — every other panel and surface stays completely blank. {nospeech} This is an original '
      f'motion graphics composition.')


def typo(linhas, enfase_idx):
    partes = []
    for i, l in enumerate(linhas):
        if i == enfase_idx:
            partes.append(f'Line {i+1}: "{l}" one size larger with a soft green glow.')
        else:
            partes.append(f'Line {i+1}: "{l}" at base size in off-white.')
    return ("TYPOGRAPHY: Bold condensed geometric sans, all caps, off-white, tight tracking, generous line spacing. "
      f"Exactly {len(linhas)} line(s). " + " ".join(partes) + " Nothing else is typeset anywhere in the frame.")


def _p(t):
    t=(t or "").strip()
    return (t if not t or t.endswith(".") else t+".")


def timeline(kind, linhas, enfase_idx, hero, extra_a, extra_b):
    if kind == "produto":
        extra_a = (extra_a or '').strip().rstrip('.')
        extra_b = (extra_b or '').strip().rstrip('.')
    else:
        extra_a, extra_b = _p(extra_a), _p(extra_b)
    l0 = linhas[0]
    lf = linhas[enfase_idx]
    if kind == "avatar":
        abertura = ("0.0-1.5s the woman alone in the black void on the right, breathing, still, camera pushing in "
          "very slowly, the space above her completely empty — no panel, no type.")
        beatA = f"1.5-3.5s a wide glass panel rises into the space above her head and its green edge lights as it lands, the panel is still empty. {extra_a}"
        beatB = f'3.5-5.5s the words "{l0}" resolve on the first line in off-white, and she tilts her head slightly upward toward them as if reading. {extra_b}'
        burst = (f'5.5-7.5s peak density — the words "{lf}" snap into place one size larger with a green bloom, and '
          "she lifts an open hand up toward the type as the block settles.")
        resolve = ("7.5-8.8s the glass panel shrinks, blurs and drifts away, leaving only the phrase and the woman, "
          "and she lowers her hand.")
    elif kind == "produto":
        abertura = f"0.0-1.5s {hero} alone in the black void, camera pushing in very slowly, no graphics at all."
        beatA = f"1.5-3.5s {extra_a} and a glass card rises beneath it, its green edge lighting up as it lands."
        beatB = f'3.5-5.5s {extra_b} and the words "{l0}" resolve in off-white directly beneath the product.'
        burst = (f'5.5-7.5s peak density — the words "{lf}" scale up one size with a green bloom while thin off-white '
          "connector lines trace between the elements.")
        resolve = ("7.5-8.8s the cards shrink, blur and drift out of frame, the connector lines dissolve, the product "
          "remains.")
    else:  # puro
        abertura = "0.0-1.5s the frame is empty black with slow drifting haze, camera pushing in very slowly, no type at all."
        beatA = f"1.5-3.5s a glass panel rises into the centre of the frame and its green edge lights as it lands, still empty. {extra_a}"
        beatB = f'3.5-5.5s the words "{l0}" resolve inside the panel in off-white. {extra_b}'
        burst = f'5.5-7.5s peak density — the words "{lf}" snap into place one size larger with a green bloom and the whole block settles.'
        resolve = "7.5-8.8s the glass panel shrinks, blurs and drifts away, leaving only the phrase on black."
    fim = ("8.8-10.0s everything stops. The frame freezes, desaturates one step, a thin green bar draws itself under "
      "the last line from left to right and halts. Silence.")
    return "TIMELINE: " + " ".join([abertura, beatA, beatB, burst, resolve, fim])


def montar(m):
    kind = m["kind"]
    style = {"avatar": STYLE_AVATAR, "produto": STYLE_PROD, "puro": STYLE_PURO}[kind]
    nosp = {"avatar": NOSPEECH_AVATAR, "produto": NOSPEECH_PROD, "puro": NOSPEECH_PURO}[kind]
    dont = {"avatar": DONT_AVATAR, "produto": DONT_PROD, "puro": DONT_PURO}[kind]
    frase = " ".join(m["linhas"])
    return "\n\n".join([
        critical(frase, m["linhas"], nosp), style, TECHNICAL,
        typo(m["linhas"], m.get("enfase", len(m["linhas"]) - 1)),
        PALETTE, AUDIO,
        timeline(kind, m["linhas"], m.get("enfase", len(m["linhas"]) - 1),
                 m.get("hero", "a single LeafTide jar"), m.get("a", ""), m.get("b", "")),
        CAMERA, dont,
    ])


# ------------------------------------------------------------------- os 24
MOTIONS = [
 # ---------------- VERMELHOS (oferta / CTA) ----------------
 dict(n=1, cor="VERMELHO", kind="produto", linhas=["$1500 A MONTH", "$19.99 A JAR"], enfase=1,
      hero="a single LeafTide jar", ref=[REF_POTE],
      a="a tall thin bar chart in off-white rises on the left representing the injection cost",
      b="a much shorter bar settles beside the jar on the right"),
 dict(n=4, cor="VERMELHO", kind="produto", linhas=["100% MONEY BACK"], enfase=0,
      hero="a single LeafTide jar", ref=[REF_POTE],
      a="a circular seal outline draws itself in off-white over the jar",
      b="the seal completes and stamps down with a small settle"),
 dict(n=10, cor="VERMELHO", kind="puro", linhas=["SECURE CHECKOUT"], enfase=0, ref=[],
      a="an abstract form outline with four blank rounded fields appears inside it",
      b="the four fields fill one by one with off-white bars and a closed padlock icon lights in green"),
 dict(n=12, cor="VERMELHO", kind="produto", linhas=["WHILE STOCK LASTS"], enfase=0,
      hero="a row of three LeafTide jars", ref=[REF_KIT],
      a="a horizontal off-white progress bar appears beneath the jars",
      b="the bar drops in three visible steps and one jar dims out"),
 dict(n=20, cor="VERMELHO", kind="puro", linhas=["20 SPOTS ONLY"], enfase=0, ref=[],
      a="a grid of twenty small off-white squares draws itself inside the panel",
      b="the squares fill in one by one from the left"),
 dict(n=22, cor="VERMELHO", kind="produto", linhas=["CEREMONIAL MATCHA KIT"], enfase=0,
      hero="a single LeafTide jar", ref=[REF_POTE],
      a="a bamboo whisk silhouette in off-white line art rises beside the jar",
      b="a ceramic bowl and a bamboo scoop join it, three objects evenly spaced"),
 dict(n=24, cor="VERMELHO", kind="produto", linhas=["CLICK BELOW NOW"], enfase=0,
      hero="a row of six LeafTide jars", ref=[REF_KIT],
      a="a wide rounded button shape lights in green at the bottom of frame",
      b="a downward arrow in off-white pulses twice above the button"),
 dict(n=41, cor="VERMELHO", kind="produto", linhas=["4 TO 6 MONTHS", "NO REBOUND"], enfase=1,
      hero="a row of six LeafTide jars", ref=[REF_KIT],
      a="a horizontal timeline rule draws itself in off-white beneath the jars",
      b="six evenly spaced ticks fill along the rule from left to right"),
 dict(n=45, cor="VERMELHO", kind="produto", linhas=["3 TO 5 BUSINESS DAYS"], enfase=0,
      hero="a single LeafTide jar", ref=[REF_POTE],
      a="a simple off-white parcel outline forms around the jar",
      b="the parcel outline slides forward and a doorway shape appears behind it"),
 dict(n=47, cor="VERMELHO", kind="produto", linhas=["ORDER NOW"], enfase=0,
      hero="a row of six LeafTide jars", ref=[REF_KIT],
      a="a circular guarantee seal outline lights on the right and a wide green button shape lights at the bottom",
      b="both hold steady and a thin off-white frame draws around the whole composition"),
 # ---------------- ROXOS (frases de impacto / lettering) ----------------
 dict(n=2, cor="ROXO", kind="avatar", linhas=["NO SIDE EFFECTS", "NO REBOUND"], enfase=1, ref=[REF_RHONDA],
      a="", b=""),
 dict(n=6, cor="ROXO", kind="avatar", linhas=["EVEN IF THE JAR", "IS EMPTY"], enfase=1, ref=[REF_RHONDA],
      a="", b=""),
 dict(n=9, cor="ROXO", kind="puro", linhas=["GLP-1 AND GIP", "RESTORED NATURALLY"], enfase=1, ref=[],
      a="two vertical off-white bars begin low inside the panel",
      b="both bars rise smoothly to full height and hold"),
 dict(n=13, cor="ROXO", kind="puro", linhas=["$89", "$19.99"], enfase=1, ref=[],
      a="", b="a single diagonal stroke draws through the first line, striking it out"),
 dict(n=17, cor="ROXO", kind="avatar", linhas=["WATCHING LIFE", "PASS BY"], enfase=1, ref=[REF_RHONDA],
      a="", b=""),
 dict(n=19, cor="ROXO", kind="puro", linhas=["NINE MONTHS AWAY"], enfase=0, ref=[],
      a="a grid of twelve small off-white squares draws itself inside the panel",
      b="nine of the squares darken one by one"),
 dict(n=29, cor="ROXO", kind="puro", linhas=["IT ALWAYS", "COMES BACK"], enfase=1, ref=[],
      a="a jagged off-white line graph begins to draw across the panel",
      b="the line dips and climbs back higher than it started, three times"),
 dict(n=31, cor="ROXO", kind="avatar", linhas=["IT HAPPENS", "WITHOUT YOU"], enfase=1, ref=[REF_RHONDA],
      a="", b=""),
 dict(n=33, cor="ROXO", kind="puro", linhas=["A LEADING PREDICTOR", "OF EARLY DEATH"], enfase=1, ref=[],
      a="", b=""),
 dict(n=35, cor="ROXO", kind="avatar", linhas=["BREAK THE CYCLE", "NOW"], enfase=1, ref=[REF_RHONDA],
      a="", b=""),
 dict(n=37, cor="ROXO", kind="puro", linhas=["WEEK ONE", "THE FOOD NOISE QUIETS"], enfase=1, ref=[],
      a="a jagged dense waveform draws across the panel in off-white",
      b="the waveform flattens progressively into a calm straight line"),
 dict(n=40, cor="ROXO", kind="avatar", linhas=["SAY YES AGAIN"], enfase=0, ref=[REF_RHONDA],
      a="", b=""),
 dict(n=44, cor="ROXO", kind="puro", linhas=["31 POUNDS", "IN 8 WEEKS"], enfase=0, ref=[],
      a="", b=""),
 dict(n=46, cor="ROXO", kind="avatar", linhas=["ALL YOU HAVE TO LOSE", "IS THE WEIGHT"], enfase=1, ref=[REF_RHONDA],
      a="", b=""),
]

MOTIONS += [
 dict(n=7, cor="VERMELHO", kind="produto", linhas=["3 JARS + 3 FREE"], enfase=0,
      hero="a single LeafTide jar", ref=[REF_KIT],
      a="three jars slide in and settle into a front row",
      b="three more jars fade up behind them, dimmer and slightly smaller"),
 dict(n=25, cor="ROXO", kind="avatar", linhas=["IT WILL NOT", "FIX ITSELF"], enfase=1, ref=[REF_RHONDA],
      a="", b=""),
]


def main():
    apenas = sys.argv[1:] or None
    out = {}
    for m in MOTIONS:
        if apenas and str(m["n"]) not in apenas:
            continue
        p = montar(m)
        pf = os.path.join(S, f"promptV_{m['n']:02d}.txt")
        open(pf, "w").write(p)
        cmd = ["higgsfield", "generate", "create", "gemini_omni", "--prompt", p,
               "--duration", "10", "--aspect-ratio", "9:16", "--json"]
        for r in m["ref"]:
            cmd += ["--image", r]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           env={**os.environ, "PATH": os.path.expanduser("~/.npm-global/bin:") + os.environ["PATH"]})
        try:
            jid = json.loads(r.stdout)[0]
        except Exception:
            jid = f"ERRO: {r.stdout.strip()[:120]} {r.stderr.strip()[:120]}"
        out[m["n"]] = dict(cor=m["cor"], kind=m["kind"], frase=" ".join(m["linhas"]), job=jid)
        print(f"{m['n']:02d} {m['cor']:<9} {m['kind']:<8} {jid}")
    prev = {}
    jf = os.path.join(S, "jobs_vertical.json")
    if os.path.exists(jf):
        prev = json.load(open(jf))
    prev.update({str(k): v for k, v in out.items()})
    json.dump(prev, open(jf, "w"), indent=1, ensure_ascii=False)
    print(f"\n{len(out)} jobs submetidos · {len(out)*30} creditos")


if __name__ == "__main__":
    main()
