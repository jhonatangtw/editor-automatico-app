# -*- coding: utf-8 -*-
# Gerador do sistema visual CLARO (clean pharma). O gemeo escuro e gerar_lote.py.
# Ver ../references/estilo-clean-pharma.md — este script e a implementacao daquele documento.
#
# AJUSTAR ANTES DE REUSAR NOUTRO JOB:
#   REF_*        -> mockups do produto deste job (ver ../assets)
#   MARCA_AZUL   -> nome da cor de acento por EXTENSO (nunca hex dentro do prompt)
#   PRODUTO      -> como o produto e chamado no prompt ("MemoFlow bottle")
#   N_UNIDADES   -> quantos frascos aparecem juntos; a contagem e travada no prompt
#   MOTIONS      -> a lista de motions deste lote
#   --aspect-ratio -> confira getSettings() da sequencia ANTES (SKILL.md secao 0)
"""Monta e submete o lote de motion de overlay no estilo CLARO.

Blocos STYLE / TECHNICAL / PALETTE / CAMERA / AUDIO / DO NOT sao IDENTICOS em todos —
e o que faz o lote emendar como um sistema visual so. Varia apenas: string exata,
tipografia por linha, e TIMELINE.

Arquetipos: "produto" (uma frase sob o produto), "puro" (frase sem produto),
"troca" (frase A e substituida por frase B — preco -> oferta).
"""
import json, os, subprocess, sys

S = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(os.path.dirname(S), "assets")
# ATENCAO: os PNGs em ../assets sao do LeafTide (job original da skill escura).
# Para MemoFlow a ancora que existe hoje e o frasco SOLO abaixo — a pasta com os 7 mockups
# oficiais (1/2/3/4/6/9/12 frascos) citada na memoria memoflow-produto-mockups nao esta mais
# no disco. Enquanto nao aparecer um mockup de 3 frascos, gera-se com o solo + a trava
# "exactly three bottles" do NOSPEECH_PROD, e o QC confere a contagem primeiro.
REF_SOLO = os.path.expanduser("~/Documents/Codex/2026-08-19/ADV-MemoFlow-GIFs/00_ancoras/REF_bottle_memoflow.png")
REF_KIT = REF_SOLO
# close do rotulo — a memoria memoflow-produto-mockups diz que so o frasco inteiro NAO basta
# para o rotulo sair certo; passar os dois sempre.
REF_LABEL = os.path.expanduser("~/Documents/Codex/2026-08-19/ADV-MemoFlow-GIFs/00_ancoras/REF_bottle_label.png")

MARCA = "MemoFlow"
MARCA_AZUL = "MemoFlow blue"
PRODUTO = "MemoFlow bottle"
N_UNIDADES = 3
NUM = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}

# ---------------------------------------------------------------- blocos comuns
STYLE_PROD = ("STYLE: Premium, clean health motion graphics on a soft neutral background — a light, airy studio "
  "backdrop with delicate, thin synapse-like filament lines drifting subtly and sparsely in the background, never "
  "dense, never busy, never competing with the product. The " + PRODUTO + "s are lit as the hero objects with soft "
  "diffused studio lighting and gentle highlights, a floating glass panel with rounded corners and thin luminous "
  "blue edges sits beneath them, clean line graphics, subtle depth of field, restrained and minimal. The product, "
  "the offer and the on-screen text are always the visual focus — the background never carries information. "
  "Vertical portrait composition: the bottles sit in the upper middle of the frame, the typography stacks directly "
  "beneath, both centred.")

STYLE_PURO = ("STYLE: Premium, clean health motion graphics on a soft neutral background — a light, airy studio "
  "backdrop with delicate, thin synapse-like filament lines drifting subtly and sparsely, never dense, never busy. "
  "Nothing in frame but the typography and one floating glass panel with rounded corners and thin luminous blue "
  "edges. Clean line graphics, subtle depth of field, restrained and minimal. Vertical portrait composition: the "
  "panel and the stacked typography are centred in the middle of the frame.")

# sem pixel e sem hex no corpo do prompt — numero escrito vira numero na tela (armadilha 2)
TECHNICAL = ("TECHNICAL: Vertical portrait, nine by sixteen, ten seconds, single continuous piece, no cuts to "
  "black, no letterboxing. The top fifteen percent and the bottom fifteen percent of the frame will later be "
  "cropped away, so every product, every graphic and every letter must sit comfortably inside the central seventy "
  "percent of the frame height. Nothing important touches the top or bottom edge.")

PALETTE = ("PALETTE: Background is a soft neutral, light and very slightly blue-tinted, close to a warm white — "
  "never a dark background, never a black void. Typography and line-art render in a deep neutral ink tone for full "
  "contrast against the light background. The single accent is " + MARCA_AZUL + " with a soft bloom, used ONLY for "
  "the emphasised line of text, which must be blue rather than dark, and for the edge light of the glass panel. "
  "The synapse filament lines render in a faint pale blue at low opacity. No green, no gold, no second accent colour.")

AUDIO = ("AUDIO: No speech of any kind. A soft, clean ambient bed, one light chime when each line of text lands, "
  "and brief silence afterwards.")

CAMERA = ("CAMERA: One continuous, slow, gentle movement for the whole piece — a soft push-in or delicate float, no "
  "cuts. Every element decelerates into place as if settling under its own weight — nothing snaps in at constant "
  "speed, no rapid zoom punches, no strobing. The product never leaves, shrinks away or disappears mid-shot.")

DONT_BASE = ("DO NOT: never render any word from these instructions as visible text — no technical terms, no "
  "\"caption\", no \"safe zone\", no \"frame\", no pixel sizes, no colour codes, no font names, no durations; no "
  "burned-in subtitles, no captions, no spoken words, no extra text of any kind beyond the exact phrases specified, "
  "no invented words, no gibberish lettering, no extra line of text, no headline above the phrase, no invented "
  "label copy, no fictional seals with writing, no badge with writing, no brand-name card, no duplicate copy of any "
  "phrase, no text touching the top or bottom edge, no dark heavy background, no black void, no cluttered or dense "
  "filament pattern, no green accent, no gold accent, no circular ring, no curved surface carrying letters, no text "
  "following a curve, no repeated words, no lens flare streaks, no rapid strobing, no zoom punches, no watermark, "
  "no logo bug in the corner, no letterbox bars, no split screen, no people in frame")
DONT_PROD = DONT_BASE + ", no second product, no competitor packaging."
DONT_PURO = DONT_BASE + "."

TRAVA_VIDRO = ("The glass panel is clear and non-reflective for text purposes: no ghosted, blurred, mirrored, "
  "inverted or partial duplicate of any word or phrase ever appears anywhere on the glass surface, the glass edge, "
  "or beneath the panel — each phrase renders crisply exactly once and nowhere else in the frame.")

NOSPEECH_PURO = "NO SPEECH: there is no person in frame, no dialogue, no voice-over, no narrator."
NOSPEECH_PROD = (NOSPEECH_PURO + " Every " + PRODUTO + " shown must match the supplied reference images exactly — "
  "same bottle shape, same cap colour, same label artwork. Never invent a different label. Never place a badge, "
  "seal, sticker, ribbon or any writing on top of the bottle itself. Never render the brand name as a separate card "
  "or label anywhere in the frame. Exactly " + NUM[N_UNIDADES] + " bottles float together side by side, evenly "
  "spaced, all matching the reference exactly, no variant. Never let reflections, glass refraction, motion blur or "
  "depth of field create the illusion of an extra or missing bottle beyond the exact " + NUM[N_UNIDADES] +
  " specified.")


def critical(frases, nospeech):
    """frases: lista de 1 ou 2 strings. Duas => arquetipo troca, com exclusao mutua declarada."""
    desc = " and ".join('"%s" (%d words)' % (f, len(f.split())) for f in frases)
    plural = "phrases" if len(frases) > 1 else "phrase"
    txt = ('CRITICAL RULES — TEXT EXCEPTION: The ONLY readable text allowed anywhere in this video is the '
      'exact %s %s — nothing else. Each phrase is spelled exactly like that, letter for letter, appears on exactly '
      'ONE unbroken line, and appears EXACTLY ONCE in the whole video. Neither phrase ever wraps onto a second '
      'line, no word repeats, no extra line or duplicate word ever forms. ' % (plural, desc))
    if len(frases) > 1:
        txt += ('The two phrases NEVER appear in the same frame at the same time: the first has fully faded before '
          'the second is legible. ')
    txt += ('There is no headline, no label, no sub-line, no kicker, no extra word above, below or beside them. '
      'Never invent additional words to fill space. Absolutely no other readable text, letters, numbers, subtitles, '
      'captions, watermarks or UI copy may appear anywhere — every other panel and surface stays completely blank. '
      + TRAVA_VIDRO + " " + nospeech + " This is an original motion graphics composition.")
    return txt


def typo(frases):
    """A ultima frase da lista e sempre a de enfase (azul). Reforco triplo: aqui, em PALETTE e no TIMELINE."""
    p = []
    for i, f in enumerate(frases):
        if i == len(frases) - 1:
            p.append('"%s" is the emphasised line: one size larger, dominant, rendered in %s with a soft blue '
                     'bloom — it is the only coloured text in the frame, never dark, never white.' % (f, MARCA_AZUL))
        else:
            p.append('"%s" is set at base size in the deep neutral ink tone.' % f)
    return ("TYPOGRAPHY: Bold clean geometric sans, all caps, tight tracking, generous line spacing, deep neutral "
      "ink as the base colour for full contrast against the light background. Each phrase occupies exactly one "
      "line, centred beneath the product. " + " ".join(p) + " Nothing else is typeset anywhere in the frame.")


def timeline(kind, frases, hero, extra_a, extra_b):
    """Quatro beats: abertura / painel+L1 / pico / hold. Ver estilo-clean-pharma.md."""
    ea = (extra_a or "").strip().rstrip(".")
    eb = (extra_b or "").strip().rstrip(".")
    l1 = frases[0]
    lf = frases[-1]
    if kind == "puro":
        abertura = ("0.0-1.3s a soft push-in begins on an empty light studio background, faint synapse filaments "
          "drifting subtly and sparsely, no type at all.")
    else:
        abertura = ("0.0-1.3s a soft push-in begins. %s float gently into the upper middle of the frame, evenly "
          "spaced, against the soft neutral background; faint synapse filaments drift subtly and sparsely behind "
          "them, and there is no text at all." % (hero[0].upper() + hero[1:]))
    beatA = ('1.3-3.0s below%s a glass panel with rounded corners and thin luminous blue edges fades in, and the '
      'words "%s" settle into place inside it in bold caps in the deep neutral ink tone, decelerating gently as '
      'they land; a soft chime plays on landing%s.' % (" the bottles" if kind != "puro" else "", l1,
                                                       (", " + ea) if ea else ""))
    if len(frases) > 1:
        pico = ('3.0-5.0s the words "%s" fade and shrink slightly upward while the words "%s" emerge centred beneath '
          'the product, rendered in %s with a soft blue bloom, growing larger and becoming the dominant text; a '
          'second soft chime plays as they land and the glass panel edge light intensifies subtly%s.'
          % (l1, lf, MARCA_AZUL, (", " + eb) if eb else ""))
    else:
        pico = ('3.0-5.0s the words "%s" scale up one size and take on a soft bloom, rendered in %s rather than '
          'dark, clearly the only coloured text in the frame; the glass panel edge light intensifies subtly%s.'
          % (lf, MARCA_AZUL, (", " + eb) if eb else ""))
    hold = ('5.0-10.0s the camera settles into a final gentle float, and the %swords "%s" hold steady and centred '
      'for the remainder of the shot, brief silence continuing. Nothing new enters the frame.'
      % ("product and the " if kind != "puro" else "", lf))
    return "TIMELINE: " + " ".join([abertura, beatA, pico, hold])


def montar(m):
    kind = m["kind"]
    prod = kind != "puro"
    frases = m["frases"]
    hero = m.get("hero", "%s %ss" % (NUM[N_UNIDADES], PRODUTO))
    return "\n\n".join([
        critical(frases, NOSPEECH_PROD if prod else NOSPEECH_PURO),
        STYLE_PROD if prod else STYLE_PURO,
        TECHNICAL,
        typo(frases),
        PALETTE, AUDIO,
        timeline(kind, frases, hero, m.get("a", ""), m.get("b", "")),
        CAMERA,
        DONT_PROD if prod else DONT_PURO,
    ])


# ------------------------------------------------------------------- o lote
# kind: "produto" | "puro" | "troca"  ·  frases: 1 string, ou 2 no caso da troca
MOTIONS = [
 dict(n=1, kind="troca", frases=["$19.99 PER BOTTLE", "FIRST 3 FREE"], ref=[REF_SOLO, REF_LABEL]),
]


def main():
    apenas = sys.argv[1:] or None
    seco = os.environ.get("SECO") == "1"
    out = {}
    for m in MOTIONS:
        if apenas and str(m["n"]) not in apenas:
            continue
        p = montar(m)
        pf = os.path.join(S, "promptC_%02d.txt" % m["n"])
        open(pf, "w").write(p)
        if seco:
            print("%02d  %s  -> %s (%d chars)" % (m["n"], " / ".join(m["frases"]), pf, len(p)))
            continue
        cmd = ["higgsfield", "generate", "create", "gemini_omni", "--prompt", p,
               "--duration", "10", "--aspect-ratio", "9:16", "--json"]
        for r in m["ref"]:
            cmd += ["--image", r]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           env={**os.environ, "PATH": os.path.expanduser("~/.npm-global/bin:") + os.environ["PATH"]})
        try:
            jid = json.loads(r.stdout)[0]
        except Exception:
            jid = "ERRO: %s %s" % (r.stdout.strip()[:120], r.stderr.strip()[:120])
        out[m["n"]] = dict(kind=m["kind"], frase=" / ".join(m["frases"]), job=jid)
        print("%02d %-8s %s" % (m["n"], m["kind"], jid))
    if seco:
        return
    prev = {}
    jf = os.path.join(S, "jobs_clean.json")
    if os.path.exists(jf):
        prev = json.load(open(jf))
    prev.update({str(k): v for k, v in out.items()})
    json.dump(prev, open(jf, "w"), indent=1, ensure_ascii=False)
    print("\n%d jobs submetidos · %d creditos" % (len(out), len(out) * 30))


if __name__ == "__main__":
    main()
