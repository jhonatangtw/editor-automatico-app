"""Start frames MarcaD NNN_XX — GPT Image 2.5 via CLI Higgsfield.
Uso: python3 frames.py wave1 | wave2 | status
Estado em JOBS (json fora do scratchpad nao e preciso; ids tambem ficam no `generate list`)."""
import json, os, subprocess, sys, time, urllib.request

PROJ = os.environ.get("HOOKS_JOB") or os.getcwd()   # pasta do job: export HOOKS_JOB="..."
OUT = os.path.join(PROJ, "MEDIA", "IMG", "START FRAMES")
JOBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames_jobs.json")
HF = (__import__("shutil").which("higgsfield") or "higgsfield")

CAM = ("Handheld vertical phone photo, 9:16. Shot on iPhone 13 Pro main camera, 26mm, f/1.5, ISO 500, 1/80s, "
       "faint handheld shake, slight motion softness, flat unedited phone color, mixed daylight and warm tungsten light "
       "fighting on the face.")
ANTI = ("Not a stock image, not a commercial shoot, not an AI render. Lived-in space with small clutter, dust, "
        "slightly crooked objects. Clothing wrinkled with light pilling and a shapeless collar. Asymmetric face: one eye "
        "slightly smaller and lower, uneven eyebrows with stray hairs, broken capillaries on the cheeks and nose, blotchy "
        "skin tone, age spots, ivory not white teeth with uneven edges, dry lips. Hands with raised veins and loose "
        "knuckle skin. Fine 35mm grain, light vignette, Kodak Portra 400 color. No beauty filter, no HDR glow, no digital "
        "sharpening halo, no glossy plastic sheen, no teal-and-orange grade. Any book, sign, calendar or packaging in the "
        "background is out of focus and unreadable.")
FRAME = ("Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, "
         "no subtitles, no watermark, no logo. Looking straight into the lens, mouth open mid-sentence.")
SKIN = ("visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, "
        "no airbushing, no smoothing filters")
RITUAL = ("a small clear glass mason jar of thick translucent golden honey-cinnamon mixture with flecks of cinnamon")
IDENT = ("IDENTITY: the SAME {who} as in the reference image — same face, same hair, same clothing, same room, same "
         "light; same photo session, next frame. ")
def monitor(s, d):
    return (f"a white digital upper-arm blood pressure monitor whose screen clearly reads large black digits "
            f"SYS {s} and DIA {d} (the only readable text in the image)")

# ---------- avatares ----------
A = ("a 63-year-old white American man, short thinning gray hair, gray stubble, slight belly, faded navy-blue henley "
     "shirt with pilling")
A_ROOM = ("in his small suburban living room with wood-paneled walls; a large American flag hangs flat on the wall "
          "directly behind him, slightly out of focus; blurred background: a worn brown recliner, a bookshelf, framed "
          "family photos, a table lamp")
BC = ("his 42-year-old daughter, a white American woman with shoulder-length dark-blonde hair in a loose ponytail, "
      "heather-gray hoodie, and her 74-year-old father, thin white hair, white stubble, rosy broken capillaries, "
      "tan-and-brown plaid flannel shirt")
D = ("a 66-year-old white American Catholic priest, combed gray hair, deep forehead lines, black clerical shirt with "
     "a white collar tab")
E = ("a 54-year-old stocky white American butcher, short salt-and-pepper beard, thick forearms, gray t-shirt under a "
     "white butcher's apron with faint stains")
E_ROOM = ("behind the counter of a small-town butcher shop: stainless steel counter, a worn end-grain wooden butcher "
          "block, knives on a magnetic strip, a walk-in cooler door; a large American flag hangs on the white tile wall "
          "behind him, slightly out of focus")
F = ("a 64-year-old white American farmer, weathered sun-tanned skin, deep crow's feet, faded red-and-black plaid "
     "work shirt with rolled sleeves, a worn tan baseball cap")
F_ROOM = ("on the porch of an old red barn in late afternoon sun; a large American flag is nailed flat to the weathered "
          "barn boards behind him, slightly out of focus; blurred background: hay bales, an old green tractor, fence posts")

def P(*parts):
    return " ".join(parts) + " " + SKIN

S = {}  # nome -> (anchor_key | None, who, prompt)

# ---- wave 1: ancoras ----
S["H01-A_Demonstracao_Cilindro"] = (None, None, P(CAM, f"Selfie-style of {A}, {A_ROOM}.",
    "PROP ON THE LENS: he pushes a clear acrylic medical teaching tube, about two inches wide, right up against the "
    "camera lens so it fills the lower-middle of the frame; the inside is packed almost shut with a thick pale-yellow "
    "waxy lining like old candle wax and hardened cement, lumpy, with only a thin channel left open, sharp focus on the "
    "texture.", "His face behind it, eyebrows raised, serious.", FRAME, ANTI))
S["H05-A_Confissao_Escada"] = (None, None, P(CAM, f"Selfie-style photo filmed by {BC}.",
    "Inside a narrow two-story family house, a carpeted staircase with a wooden handrail; a large American flag hangs "
    "on the stairway wall, slightly out of focus. The daughter holds the phone in the foreground, worried and scared, "
    "brows pulled together, looking into the lens. Behind her, halfway up the stairs, her father climbs very slowly, "
    "bent forward, one hand clutching his chest and the other gripping the handrail, out of breath, face flushed.",
    "Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, no "
    "subtitles, no watermark, no logo. Her mouth open mid-sentence.", ANTI))
S["H07-A_Comando_Padre"] = (None, None, P(CAM, f"Selfie-style of {D},",
    "sitting in his parish office: dark wooden desk, a wall of old books, a small wooden crucifix on the wall softly "
    "blurred; a large American flag on a pole stand directly behind his shoulder, slightly out of focus. He leans "
    "toward the lens, both hands loosely clasped, grave and fatherly expression, kind but worried eyes.", FRAME, ANTI))
S["H09-A_Omissao_Fazenda"] = (None, None, P(CAM, f"Selfie-style of {F}, {F_ROOM}.",
    f"PROP ON THE LENS: he holds {monitor(172, 98)} right up to the camera lens, filling the lower-middle of the frame. "
    "He is out of breath, sweating, face red and strained, his other hand pressed flat on his chest, "
    f"{RITUAL} resting on the porch railing beside him.", FRAME, ANTI))
S["H10-A_Omissao_Acougue"] = (None, None, P(CAM, f"Selfie-style of {E}, {E_ROOM}.",
    "PROP ON THE LENS: with a gloved hand he holds a butcher's cut of beef aorta, a thick pale tube split open "
    "lengthwise, pushed right up to the camera lens; the inner wall is coated with a thick pale-yellow waxy lining like "
    "old candle wax, lumpy and crusted, sharp focus on the texture. Clean butcher-shop look, no blood.", FRAME, ANTI))

# ---- wave 2: derivados (referencia = job da ancora) ----
S["H01-B_Demonstracao_Cilindro"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"Selfie-style of {A}, {A_ROOM}. PROP ON THE LENS: the same clear acrylic tube packed with pale-yellow waxy lining "
    f"is held close to the lens; with his other hand he pours {RITUAL} into the top of the tube in a slow thick golden "
    "stream; where the golden mixture touches, the yellow waxy lining is softening and sliding down in slow drips.",
    "Focused, slight nod.", FRAME, ANTI))
S["H02-A_Confissao_Parque"] = ("H05-A_Confissao_Escada", "daughter and father", P(CAM,
    IDENT.format(who="daughter and father").replace("same room, ", ""),
    f"Outdoors in a suburban park on a sunny morning, a flagpole with a large American flag behind, slightly out of "
    f"focus. Selfie-style: the daughter holds {monitor(172, 98)} up close to the lens in the lower-middle of the frame, "
    "proud and emotional. Far behind her on the park path her 74-year-old father, same flannel shirt, runs fast with a "
    "big happy grin, and two tired young grandchildren trail behind him catching their breath.",
    "Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, no "
    "subtitles, no watermark, no logo. Her mouth open mid-sentence.", ANTI))
S["H03-A_Demonstracao_Pescoco"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"Selfie-style of {A}, {A_ROOM}. He turns his head slightly and points with his index finger at a thick raised "
    f"vein bulging on the side of his neck; with his other hand he holds {monitor(172, 98)} up close to the lens in the "
    "lower-middle of the frame. Worried expression.", FRAME, ANTI))
S["H03-B_Demonstracao_Pescoco"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"Selfie-style of {A}, {A_ROOM}. Close to the lens, he tilts his head and slowly pours {RITUAL} onto the side of "
    "his neck right over the raised vein; a thick golden drip runs down his neck toward the collar.", FRAME, ANTI))
S["H04-A_Demonstracao_Coracao"] = ("H04-B_Demonstracao_Coracao", "man", P(CAM, IDENT.format(who="man"),
    f"Selfie-style of {A}, seated, {A_ROOM}. One second BEFORE the reference image: he holds the same plastic classroom "
    "heart model from the reference right up to the camera lens, the pale-yellow wax on it still intact and untouched; "
    "no jar in his hands.", FRAME, ANTI))
S["H04-B_Demonstracao_Coracao"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"Selfie-style of {A}, seated, {A_ROOM}. He holds the same plastic teaching heart model close to the lens and pours "
    f"{RITUAL} over it in a thick golden stream; the pale-yellow waxy lining is melting and dripping off in soft globs "
    "that fall onto the lap of his blue jeans.", FRAME, ANTI))
S["H05-B_Confissao_Escada"] = ("H05-A_Confissao_Escada", "daughter and father", P(CAM,
    IDENT.format(who="daughter and father"),
    "Same staircase, same flag. The father now climbs the stairs fast, upright and smiling widely, two steps at a time, "
    f"hand lightly on the rail. In the foreground the daughter, amazed, pours {RITUAL} in one continuous golden stream "
    "down onto the wooden floor at the bottom of the stairs while looking into the lens.",
    "Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, no "
    "subtitles, no watermark, no logo. Her mouth open mid-sentence.", ANTI))
S["H06-A_Omissao_Quarto"] = ("H05-A_Confissao_Escada", "daughter and father", P(CAM,
    IDENT.format(who="daughter and father").replace("same room, ", ""),
    "In a modest bedroom with a quilted bedspread; a large American flag hangs on the wall above the headboard, "
    "slightly out of focus. The father sits on the edge of the bed struggling to breathe, mouth open, one hand on his "
    f"chest, pale and sweaty. In the foreground the daughter holds {monitor(192, 118)} up close to the lens in the "
    "lower-middle of the frame.", "Subject in the upper two thirds of the frame, empty lower third for on-screen "
    "caption. No on-screen text, no subtitles, no watermark, no logo. Her mouth open mid-sentence.", ANTI))
S["H06-B_Omissao_Quarto"] = ("H06-A_Omissao_Quarto", "father", P(CAM, IDENT.format(who="father"),
    "Same modest bedroom, same flag above the headboard, filmed by his daughter. The father sits on the edge of the "
    f"bed, flannel shirt fully buttoned, holding {RITUAL} close to the lens and tipping a slow golden stream onto the "
    "front of his shirt over his heart. He looks calmer, breathing easier, eyes on the lens.",
    "Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, no "
    "subtitles, no watermark, no logo.", ANTI))
S["H08-A_Omissao_Tornozelo"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"{A}, seated in the recliner, {A_ROOM}. PROP ON THE LENS: his right foot, in a white cotton sock, rests on a "
    "footstool pushed toward the camera; the sock band is pulled down and the ankle above it is visibly puffy and "
    "swollen with a deep elastic indentation line, filling the lower-middle of the frame; his face behind it, "
    "pointing at the ankle.", FRAME, ANTI))
S["H08-B_Omissao_Tornozelo"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"{A}, seated in the recliner, {A_ROOM}. His swollen bare ankle rests on the footstool close to the lens; he leans "
    f"forward and pours {RITUAL} over the ankle, a thick golden stream coating the skin.", FRAME, ANTI))
S["H09-B_Omissao_Fazenda"] = ("H09-A_Omissao_Fazenda", "farmer", P(CAM, IDENT.format(who="farmer"),
    f"Selfie-style of {F}, {F_ROOM}. Now healthy and relaxed, breathing easy, a small confident smile; he holds "
    f"{RITUAL} up close to the camera lens in the lower-middle of the frame.", FRAME, ANTI))
S["H10-B_Omissao_Acougue"] = ("H10-A_Omissao_Acougue", "butcher", P(CAM, IDENT.format(who="butcher"),
    f"Selfie-style of {E}, {E_ROOM}. The same split beef aorta lies open on the butcher block close to the lens; he "
    f"pours {RITUAL} into it in a slow golden stream, and the pale-yellow waxy lining is softening and sliding off in "
    "slow drips. Clean butcher-shop look, no blood.", FRAME, ANTI))

# ---- rodada 2: refeitos no Nano Banana Pro (GPT Image trocou coracao->tubo e tornozelo->braco) ----
MODEL = {}
HEART = ("PROP ON THE LENS: a plastic anatomical HEART model — unmistakably heart-shaped, glossy painted red chambers, "
         "the aortic arch curving on top, red and blue vessels running over its surface, like a classroom anatomy "
         "model — held up close to the camera lens with both hands. The vessels on its surface are smeared with thick "
         "pale-yellow wax like melted candle wax. It is NOT a tube and NOT a cylinder.")
LEG = ("PROP ON THE LENS: his LOWER LEG and FOOT, not his arm: he sits in the recliner with his right leg stretched out "
       "straight toward the camera on a footstool, jeans rolled up to mid-calf, the foot in a white cotton sock nearest "
       "the lens with the sock band pulled down; the ANKLE just above the sock is visibly puffy and swollen with a deep "
       "elastic indentation line.")
S["H04-A_Demonstracao_Coracao"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"Selfie-style of {A}, seated, {A_ROOM}.", HEART, "No jar in the image. Serious, eyebrows raised.", FRAME, ANTI))
S["H04-B_Demonstracao_Coracao"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"Selfie-style of {A}, seated, {A_ROOM}.", HEART, f"He pours {RITUAL} over the heart model in a thick golden "
    "stream; the pale-yellow wax is melting and dripping off in soft globs that fall onto the lap of his blue jeans.",
    FRAME, ANTI))
S["H08-A_Omissao_Tornozelo"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"{A}, {A_ROOM}.", LEG, "Behind the leg, his face; with one hand he points down at the swollen ankle.", FRAME, ANTI))
S["H08-B_Omissao_Tornozelo"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"{A}, {A_ROOM}.", LEG, f"He leans forward and pours {RITUAL} over the swollen ankle, a thick golden stream "
    "coating it and running onto the sock.", FRAME, ANTI))
S["H03-A_Demonstracao_Pescoco"] = ("H01-A_Demonstracao_Cilindro", "man", P(CAM, IDENT.format(who="man"),
    f"Selfie-style of {A}, {A_ROOM}. He turns his head slightly and points with his index finger at a thick raised "
    "vein bulging on the side of his neck; with his other hand he holds a white digital upper-arm blood pressure "
    "monitor up close to the lens in the lower-middle of the frame. The monitor screen reads EXACTLY 172 on the top "
    "line and 98 on the bottom line (nine-eight, not ninety-three), the only readable text in the image. Worried "
    "expression.", FRAME, ANTI))
for k in ["H04-A_Demonstracao_Coracao","H04-B_Demonstracao_Coracao","H08-A_Omissao_Tornozelo","H08-B_Omissao_Tornozelo","H03-A_Demonstracao_Pescoco"]:
    MODEL[k] = "nano_banana_pro"

# ---- frames C: resultado da demonstracao (sequencia logica prop -> derrama -> gordura derretida) ----
NEXT = "IDENTITY AND CONTINUITY: the SAME man, same clothes, same room, same light and same prop as in the reference image; a few seconds LATER in the same shot. "
S["H01-C_Demonstracao_Cilindro"] = ("H01-B_Demonstracao_Cilindro", "man", P(CAM, NEXT,
    f"Selfie-style of {A}, {A_ROOM}. PROP ON THE LENS: the same clear acrylic tube held up to the lens is now almost "
    "completely clear and open inside, only thin golden streaks left on its walls; the melted pale-yellow wax has slid "
    "out of the bottom and hangs in soft globs dripping onto his jeans and the carpet. He looks amazed.", FRAME, ANTI))
S["H03-C_Demonstracao_Pescoco"] = ("H03-B_Demonstracao_Pescoco", "man", P(CAM, NEXT,
    f"Selfie-style of {A}, {A_ROOM}. The side of his neck is now calm and smooth, the vein no longer bulging, a faint "
    "golden sheen left on the skin. He holds a white digital upper-arm blood pressure monitor up close to the lens; the "
    "screen reads EXACTLY 112 on the top line and 74 on the bottom line, the only readable text in the image. Relieved, "
    "small smile.", FRAME, ANTI))
S["H04-C_Demonstracao_Coracao"] = ("H04-B_Demonstracao_Coracao", "man", P(CAM, NEXT,
    f"Selfie-style of {A}, seated, {A_ROOM}. He holds the same plastic anatomical heart model close to the lens: its red "
    "and blue vessels are now clean and shiny, glazed with golden honey; the melted pale-yellow wax has fallen off in "
    "big soft globs piled on the lap of his blue jeans. No jar in his hands. Amazed expression.", FRAME, ANTI))
S["H08-C_Omissao_Tornozelo"] = ("H08-B_Omissao_Tornozelo", "man", P(CAM, NEXT,
    f"{A}, {A_ROOM}. His lower leg stretched toward the camera on the footstool, white sock nearest the lens: the ankle "
    "is now slim and normal, the swelling gone, the sock band loose, a faint golden sheen on the skin. He points at it, "
    "relieved.", FRAME, ANTI))
S["H10-C_Omissao_Acougue"] = ("H10-B_Omissao_Acougue", "butcher", P(CAM, NEXT,
    f"Selfie-style of {E}, {E_ROOM}. The same split beef aorta lies open on the butcher block close to the lens; its "
    "inner wall is now clean and smooth, glazed golden, and the melted pale-yellow waxy lining has slid out into a soft "
    "pooled puddle on the wood beside it. Clean butcher-shop look, no blood. He looks straight into the lens.",
    FRAME, ANTI))
for k in ["H01-C_Demonstracao_Cilindro","H03-C_Demonstracao_Pescoco","H04-C_Demonstracao_Coracao","H08-C_Omissao_Tornozelo","H10-C_Omissao_Acougue"]:
    MODEL[k] = "nano_banana_pro"

EXTRA_REFS = {"H01-C_Demonstracao_Cilindro": ["H01-A_Demonstracao_Cilindro"]}
S["H01-C_Demonstracao_Cilindro"] = ("H01-B_Demonstracao_Cilindro", "man", P(CAM,
    "IDENTITY IS CRITICAL: the SAME man as in BOTH reference images — same heavy face, same thick gray hair, same gray "
    "stubble, same faded navy henley, same wood-paneled room and same framing; a few seconds after the second reference. ",
    f"Selfie-style of {A}, {A_ROOM}. PROP ON THE LENS: the same short clear acrylic tube from the references, held close "
    "to the lens, is now almost completely clear and open inside, only thin golden streaks on its walls; the melted "
    "pale-yellow wax has slid out of the bottom and drips in soft globs onto his jeans. He looks amazed.", FRAME, ANTI))
S["H10-C_Omissao_Acougue"] = ("H10-B_Omissao_Acougue", "butcher", P(CAM, NEXT,
    f"Selfie-style of {E}, {E_ROOM}. The same split beef aorta lies open on the butcher block close to the lens, and it "
    "is now EMPTY: its inner wall is bare, smooth, clean pinkish-white with a thin golden glaze, NO yellow wax left "
    "inside it at all. All the melted pale-yellow waxy lining has slid out and lies in one soft pooled puddle on the "
    "wood next to it. Clean butcher-shop look, no blood. Amazed, looking straight into the lens.", FRAME, ANTI))

# ---- H04 refeito: medico (pedido do copy/Pedro) ----
DOC = ("a 68-year-old white American male physician, short gray hair, receding hairline, thin wire-rimmed glasses, "
       "clean-shaven with a faint gray shadow, light-blue button-down shirt under a slightly wrinkled white lab coat")
DOC_ROOM = ("sitting in a small doctor's exam room: an exam table with paper cover, a wall-mounted blood pressure cuff "
            "and otoscope, a window with daylight, a framed print on the wall; a large American flag hangs on the wall "
            "directly behind him, slightly out of focus")
DOC_HEART = ("PROP ON THE LENS: a large plastic anatomical HEART model on a small white stand — unmistakably heart-shaped, "
             "red painted chambers, the aortic arch on top, red and blue vessels over its surface, like a classroom "
             "anatomy model — held up close to the camera lens in both hands in the lower-middle of the frame. The "
             "vessels on its surface are smeared with thick pale-yellow wax like melted candle wax.")
S["H04-A_Demonstracao_Coracao"] = (None, None, P(CAM, f"Selfie-style of {DOC}, {DOC_ROOM}.", DOC_HEART,
    "No jar in the image. Serious, eyebrows raised.", FRAME, ANTI))
S["H04-B_Demonstracao_Coracao"] = ("H04-A_Demonstracao_Coracao", "doctor", P(CAM, IDENT.format(who="doctor"),
    f"Selfie-style of {DOC}, {DOC_ROOM}.", DOC_HEART, f"Holding the model's stand with one hand, with the other he "
    f"pours {RITUAL} over the top of the heart in a thick golden stream; where it touches, the pale-yellow wax starts "
    "to soften and slide.", FRAME, ANTI))
S["H04-C_Demonstracao_Coracao"] = ("H04-B_Demonstracao_Coracao", "doctor", P(CAM,
    "IDENTITY IS CRITICAL: the SAME doctor as in BOTH reference images — same face, glasses, lab coat, room and framing; "
    "a few seconds after the first reference. ", f"Selfie-style of {DOC}, {DOC_ROOM}.",
    "He holds the same heart model on its stand close to the lens, still pouring a thin golden stream from the jar: "
    "the melted pale-yellow wax is sliding off the heart in big soft globs, dripping off the stand and falling in "
    "blobs onto the lap of his dark trousers below; parts of the red and blue vessels are now clean and shiny.",
    FRAME, ANTI))
EXTRA_REFS["H04-C_Demonstracao_Coracao"] = ["H04-A_Demonstracao_Coracao"]

# ---- H08 refeito: mulher japonesa (pedido do usuario; casa com "Japanese trick") ----
G = ("a 62-year-old Japanese woman living in the US, straight black hair with gray strands cut in a chin-length bob, "
     "small reading glasses pushed up on her head, soft beige cardigan over a white t-shirt, loose dark-gray cotton "
     "pants rolled up to mid-calf")
G_ROOM = ("seated on a beige fabric sofa in her tidy small American living room; a large American flag hangs flat on "
          "the wall directly behind her, slightly out of focus; blurred background: a potted plant, a low bookshelf, "
          "framed family photos, a floor lamp")
G_LEG = ("PROP ON THE LENS: her LOWER LEG and FOOT, not her arm: her right leg is stretched straight toward the camera "
         "and rests on a small upholstered footstool, the foot in a white cotton sock nearest the lens with the sock "
         "band pulled down; the ANKLE just above the sock is visibly puffy and swollen with a deep elastic "
         "indentation line.")
S["H08-A_Omissao_Tornozelo"] = (None, None, P(CAM, f"Selfie-style of {G}, {G_ROOM}.", G_LEG,
    "Behind the leg, her face; with one hand she points down at the swollen ankle, concerned, confiding expression.",
    FRAME, ANTI))
S["H08-B_Omissao_Tornozelo"] = ("H08-A_Omissao_Tornozelo", "woman", P(CAM, IDENT.format(who="woman"),
    f"Selfie-style of {G}, {G_ROOM}.", G_LEG, f"She leans forward and pours {RITUAL} over the swollen ankle, a thick "
    "golden stream coating it and running onto the sock.", FRAME, ANTI))
S["H08-C_Omissao_Tornozelo"] = ("H08-B_Omissao_Tornozelo", "woman", P(CAM,
    "IDENTITY IS CRITICAL: the SAME woman as in BOTH reference images — same face, hair, cardigan, sofa, room and "
    "framing; a few seconds after the first reference. ", f"Selfie-style of {G}, {G_ROOM}.",
    "Her lower leg stretched toward the camera on the footstool, white sock nearest the lens: the ankle is now slim "
    "and normal, the swelling gone, the sock band loose, a faint golden sheen on the skin. She points at it, relieved, "
    "small smile.", FRAME, ANTI))
EXTRA_REFS["H08-C_Omissao_Tornozelo"] = ["H08-A_Omissao_Tornozelo"]

# ---- H06 refeito: medico + idoso deitado (referencia do copy) ----
DOC2 = ("a 46-year-old American male physician of South Asian descent, short dark wavy hair graying at the temples, "
        "trimmed dark stubble, white lab coat over an olive-green button-down shirt")
PAT = ("an 82-year-old white American man, bald on top with short white hair on the sides, deep wrinkles, thin, wearing "
       "open navy-and-white striped flannel pajamas")
H06_ROOM = ("a modest home bedroom with a wooden headboard, a window with soft daylight, a framed landscape painting; a "
            "large American flag hangs on the wall behind the bed, slightly out of focus")
S["H06-A_Omissao_Quarto"] = (None, None, P(CAM, f"Handheld vertical phone photo of {DOC2} standing at the bedside of "
    f"{PAT}, in {H06_ROOM}. The old man lies in bed under a white quilt, head on the pillow, mouth open, struggling to "
    f"breathe, eyes half closed. The doctor looks into the lens, grave, mouth open mid-sentence, holding {monitor(192, 118)} "
    "up close to the lens in the lower-middle of the frame.", "Subject in the upper two thirds of the frame, empty lower "
    "third for on-screen caption. No on-screen text, no subtitles, no watermark, no logo.", ANTI))
S["H06-B_Omissao_Quarto"] = ("H06-A_Omissao_Quarto", "doctor and patient", P(CAM,
    IDENT.format(who="doctor and old patient"), f"{DOC2} leans over {PAT}, who lies in bed with the pajama top open at "
    f"the chest. The doctor tips {RITUAL} and pours a slow golden stream onto the old man's upper chest, his other palm "
    "gently rubbing it in. The patient's eyes are closed, breathing heavily.", "Subject in the upper two thirds of the "
    "frame, empty lower third for on-screen caption. No on-screen text, no subtitles, no watermark, no logo.", ANTI))
S["H06-C_Omissao_Quarto"] = ("H06-B_Omissao_Quarto", "doctor and patient", P(CAM,
    "IDENTITY IS CRITICAL: the SAME doctor and the SAME old man as in BOTH reference images — same faces, clothes, "
    "bedroom and flag; the next morning. ", f"{PAT} now sits up in bed against the headboard in a buttoned light "
    f"pajama shirt, color back in his face, smiling warmly and talking. {DOC2} stands beside the bed smiling, holding "
    f"{RITUAL} up at chest height toward the lens, his other hand open, explaining.", "Subject in the upper two thirds "
    "of the frame, empty lower third for on-screen caption. No on-screen text, no subtitles, no watermark, no logo.", ANTI))
EXTRA_REFS["H06-C_Omissao_Quarto"] = ["H06-A_Omissao_Quarto"]

# ---- H07 refeito: padre derrama o ritual na arteria em corte ----
ARTERY = ("a large plastic medical teaching model of a blood vessel cut open lengthwise, about sixteen inches long, "
          "glossy dark red outer wall, the inside channel packed with thick pale-yellow waxy lining like old candle wax")
S["H07-B_Comando_Padre"] = ("H07-A_Comando_Padre", "priest", P(CAM, IDENT.format(who="priest"),
    f"Selfie-style of {D}, same parish office, same flag. PROP ON THE LENS: he holds {ARTERY}, tilted toward the camera "
    f"in the lower-middle of the frame, and with his other hand pours {RITUAL} into it in a slow golden stream; where it "
    "touches, the yellow wax begins to soften. Grave, focused expression.", FRAME, ANTI))
S["H07-C_Comando_Padre"] = ("H07-B_Comando_Padre", "priest", P(CAM,
    "IDENTITY IS CRITICAL: the SAME priest as in BOTH reference images — same face, clerical collar, office, flag and "
    "framing; a few seconds after the first reference. ", f"Selfie-style of {D}, same parish office. He holds the same "
    "cut-open blood vessel model close to the lens: the pale-yellow wax inside has dissolved and slid out in soft "
    "melted globs dripping off its end onto the desk, the red channel now mostly clean and glazed golden. No jar in "
    "his hands. He looks into the lens with fatherly, pleading eyes.", FRAME, ANTI))
EXTRA_REFS["H07-C_Comando_Padre"] = ["H07-A_Comando_Padre"]
for k in ["H06-A_Omissao_Quarto","H06-B_Omissao_Quarto","H06-C_Omissao_Quarto","H07-B_Comando_Padre","H07-C_Comando_Padre",
          "H04-A_Demonstracao_Coracao","H04-B_Demonstracao_Coracao","H04-C_Demonstracao_Coracao",
          "H08-A_Omissao_Tornozelo","H08-B_Omissao_Tornozelo","H08-C_Omissao_Tornozelo"]:
    MODEL[k] = "nano_banana_pro"

S["H04-C_Demonstracao_Coracao"] = ("H04-B_Demonstracao_Coracao", "doctor", P(CAM,
    "IDENTITY IS CRITICAL: the SAME doctor as in BOTH reference images — same face, glasses, lab coat, room and framing; "
    "ten seconds after the first reference. ", f"Selfie-style of {DOC}, {DOC_ROOM}.",
    "The jar is gone, he holds only the heart model on its stand close to the lens with one hand: the red and blue "
    "vessels are now CLEAN and shiny with a thin golden glaze, NO yellow wax left on the heart. All the melted "
    "pale-yellow wax has fallen and lies in big soft globs piled on the lap of his khaki trousers below the stand. He "
    "points at the globs on his lap with his free hand, amazed.", FRAME, ANTI))
S["H07-C_Comando_Padre"] = ("H07-B_Comando_Padre", "priest", P(CAM,
    "IDENTITY IS CRITICAL: the SAME priest as in BOTH reference images — same face, clerical collar, office, flag and "
    "framing; ten seconds after the first reference. ", f"Selfie-style of {D}, same parish office. The jar is gone. He "
    "holds the same cut-open red blood vessel model close to the lens and its inner channel is now EMPTY and CLEAN, "
    "smooth red with a thin golden glaze, NO yellow wax left inside. All the dissolved pale-yellow wax has slid out and "
    "lies in a soft melted puddle on the wooden desk below it. He looks into the lens with fatherly, pleading eyes.",
    FRAME, ANTI))

S["H04-C_Demonstracao_Coracao"] = ("H04-B_Demonstracao_Coracao", "doctor", P(CAM,
    "IDENTITY IS CRITICAL: the SAME doctor as in BOTH reference images — same face, glasses, lab coat, exam room, flag "
    "and framing; ten seconds after the first reference. ", f"Selfie-style of {DOC}, seated, {DOC_ROOM}.",
    "The jar is gone. He holds the heart model by its stand out over his own lap, and his THIGH in khaki trousers is "
    "clearly visible in the lower part of the frame directly under the heart. Golden honey mixed with the melted "
    "pale-yellow wax is dripping off the bottom of the heart in long thick strands and FALLING ONTO HIS LEG: big soft "
    "globs of honey and wax have landed on the khaki fabric of his thigh and are soaking into it, with more drips "
    "mid-air between the heart and the leg. The heart's red and blue vessels are now mostly clean and shiny. He "
    "points down at his leg with his free hand, amazed.", FRAME, ANTI))

# ---- H02-A e H05-B refeitos: pai de frente na direcao do movimento ----
S["H02-A_Confissao_Parque"] = ("H05-A_Confissao_Escada", "daughter and father", P(CAM,
    IDENT.format(who="daughter and father").replace("same room, ", ""),
    "Outdoors in a suburban park on a sunny morning, a flagpole with a large American flag behind, slightly out of "
    f"focus. Selfie-style: the daughter holds {monitor(172, 98)} up close to the lens in the lower-middle of the frame, "
    "proud and emotional. FAR in the background, small in the frame at the end of a long straight park path, her "
    "74-year-old father in the same flannel shirt is RUNNING TOWARD THE CAMERA, facing us, mid-stride with one knee "
    "lifted, arms pumping, big happy grin; two young grandchildren run behind him, lagging and tired.",
    "Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, no "
    "subtitles, no watermark, no logo. Her mouth open mid-sentence.", ANTI))
S["H05-B_Confissao_Escada"] = ("H05-A_Confissao_Escada", "daughter and father", P(CAM,
    IDENT.format(who="daughter and father").replace("same room, ", ""),
    "Same house and same carpeted staircase with the wooden handrail and the American flag on the stairway wall, but "
    "now the daughter stands at the TOP of the stairs on the landing, filming a selfie with the staircase going DOWN "
    "behind her. Below her, her father in the same flannel shirt is climbing UP toward her fast and happy, facing the "
    "camera, two steps at a time, big grin, one hand lightly on the rail. In the foreground the daughter, amazed, pours "
    f"{RITUAL} in one continuous golden stream down onto the floor of the landing while looking into the lens.",
    "Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, no "
    "subtitles, no watermark, no logo. Her mouth open mid-sentence.", ANTI))
MODEL["H02-A_Confissao_Parque"] = MODEL["H05-B_Confissao_Escada"] = "nano_banana_pro"

S["H05-A_Confissao_Escada"] = ("H05-B_Confissao_Escada", "daughter and father", P(CAM,
    IDENT.format(who="daughter and father"),
    "Same house, same carpeted staircase with the wooden handrail and the American flag on the stairway wall, same "
    "angle as the reference: the daughter stands at the TOP of the stairs on the landing, filming a selfie with the "
    "staircase going DOWN behind her. Near the BOTTOM of the stairs, far from her, her father in the same flannel shirt "
    "is climbing UP toward her very slowly, facing the camera, bent forward, one hand clutching his chest and the other "
    "gripping the handrail, out of breath, face flushed and pained. In the foreground the daughter looks worried and "
    "scared, brows pulled together, looking into the lens. No jar in her hands.",
    "Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, no "
    "subtitles, no watermark, no logo. Her mouth open mid-sentence.", ANTI))
MODEL["H05-A_Confissao_Escada"] = "nano_banana_pro"

S["H05-A_Confissao_Escada"] = ("H05-A_Confissao_Escada_prev", "daughter and father", P(CAM,
    "IDENTITY: the SAME daughter and the SAME father as in the reference image — same faces, same hair, same house, "
    "same staircase, same flag, same camera angle — but this is a DIFFERENT DAY, so they wear DIFFERENT CLOTHES: the "
    "daughter wears a navy-blue crewneck sweater with a white collar showing and small gold stud earrings, hair down "
    "loose; the father wears a faded burgundy zip-up cardigan over a white undershirt and gray sweatpants, reading "
    "glasses hanging from the collar. ",
    "The daughter stands at the TOP of the stairs on the landing filming a selfie, the staircase going DOWN behind her. "
    "Near the BOTTOM of the stairs, far from her, her father has STOPPED on a step facing the camera, bent forward, "
    "one hand clutching the left side of his chest in pain, the other gripping the handrail hard, grimacing, out of "
    "breath, face flushed. The daughter looks worried and scared, looking into the lens. No jar in her hands.",
    "Subject in the upper two thirds of the frame, empty lower third for on-screen caption. No on-screen text, no "
    "subtitles, no watermark, no logo. Her mouth open mid-sentence.", ANTI))

def load():
    return json.load(open(JOBS)) if os.path.exists(JOBS) else {}

def save(j):
    json.dump(j, open(JOBS, "w"), indent=1)

def submit(name, jobs):
    anchor, _, prompt = S[name]
    if MODEL.get(name) == "nano_banana_pro":
        cmd = [HF, "generate", "create", "nano_banana_pro", "--prompt", prompt, "--aspect_ratio", "9:16",
               "--resolution", "2k", "--json"]
    else:
        cmd = [HF, "generate", "create", "gpt_image_2_5", "--prompt", prompt, "--aspect_ratio", "9:16",
               "--quality", "high", "--resolution", "2k", "--json"]
    if anchor:
        cmd += ["--image-references", jobs[anchor]]
    for extra in EXTRA_REFS.get(name, []):
        cmd += ["--image-references", jobs[extra]]
    out = subprocess.run(cmd, capture_output=True, text=True)
    ids = [t for t in out.stdout.replace('"', " ").replace("[", " ").replace("]", " ").replace(",", " ").split() if len(t) > 20]
    if not ids:
        print("SUBMIT_FAIL", name, out.stdout[-300:], out.stderr[-300:], flush=True)
        return
    jobs[name] = ids[0]; save(jobs)
    print("SUBMIT", name, ids[0], flush=True)

def get(job):
    raw = subprocess.run([HF, "generate", "get", job, "--json"], capture_output=True, text=True).stdout
    return json.JSONDecoder().raw_decode(raw[raw.find("{"):])[0]

def wait_all(names, jobs):
    os.makedirs(OUT, exist_ok=True)
    pending = [n for n in names if n in jobs and not os.path.exists(os.path.join(OUT, n + ".png"))]
    t0 = time.time()
    while pending and time.time() - t0 < 1800:
        for n in list(pending):
            try:
                g = get(jobs[n])
            except Exception as e:
                continue
            st = g.get("status")
            if st == "completed" and g.get("result_url"):
                urllib.request.urlretrieve(g["result_url"], os.path.join(OUT, n + ".png"))
                print("DONE", n, flush=True); pending.remove(n)
            elif st in ("failed", "nsfw", "canceled", "cancelled"):
                print("FAILED", n, st, flush=True); pending.remove(n)
        if pending:
            time.sleep(15)
    for n in pending:
        print("TIMEOUT", n, flush=True)

if __name__ == "__main__":
    mode = sys.argv[1]
    jobs = load()
    wave1 = [n for n in S if S[n][0] is None]
    wave2 = [n for n in S if S[n][0] is not None]
    only = sys.argv[2:] or None
    if mode in ("wave1", "wave2"):
        names = wave1 if mode == "wave1" else wave2
        if only: names = only
        for n in names:
            if n not in jobs:
                submit(n, jobs)
        wait_all(names, jobs)
    elif mode == "status":
        for n, j in jobs.items():
            print(n, j, get(j).get("status"))
