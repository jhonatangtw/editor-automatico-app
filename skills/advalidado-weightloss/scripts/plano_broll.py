#!/usr/bin/env python3
"""Plano de b-roll — uma imagem por palavra-chave falada (modelo da skill advalidado-weightloss).

COPIE para <JOB>/broll/plano.py e troque a lista P pelas cenas do SEU AD. A lista abaixo é o
exemplo real do AD de referência (mãe pós-parto, gelatina) — serve de molde de prompt.

Posição = onde o AD validado tinha b-roll; conteúdo = o que é falado naquela palavra.
Toda pessoa em cena é a personagem do H1 (referência: avatar/H1_start.png). Nenhum nome/rosto real.
Gera plano.json; gerar_broll.py lê o plano e chama o Higgsfield.
"""
import json, os

AQUI = os.path.dirname(os.path.abspath(__file__))

ID = ("IDENTITY: the SAME woman as in the reference image — same face, same skin tone, same dark brunette "
      "wavy shoulder-length hair, same small gold hoop earrings. A different moment and a completely different "
      "composition from the reference. The baby is NOT in this shot unless described.")
PESADA = (" In this shot she is about 45 pounds heavier than in the reference: fuller face, soft double chin, "
          "fuller arms and waist — same face otherwise. Non-sexual, everyday, documentary.")
CAM = ("Camera: iPhone 15 Pro rear camera, 24mm equivalent, f/1.8, ISO 500, natural indoor light, Apple color "
       "science, slight wide-angle distortion near the edges.")
ANTI = ("Not a stock image, not a commercial shoot, not an AI render. Imperfect real-home light with two color "
        "temperatures, a little clutter, fine sensor noise, slight vignette, Kodak Portra 400 look. No beauty "
        "filter, no HDR glow, no glossy plastic sheen. Any packaging, sign or paper is plain, unbranded and "
        "unreadable unless the prompt gives exact text. No captions, no logos, no watermark.")
PELE = ("Visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, "
        "no airbrushing, no smoothing filters.")
TRES_D = ("Photoreal 3D medical illustration, cinematic macro shot inside the human body, translucent tissue in warm "
          "pink and amber tones, soft volumetric light, shallow depth of field, tiny floating particles, dark "
          "background. No text, no labels, no arrows, no logos.")

def pessoa(cena, pesada=False):
    return {"ref": True, "prompt": f"{ID}{PESADA if pesada else ''}\nVertical 9:16 photo. {cena}\n{CAM}\n{ANTI}\n{PELE}"}

def objeto(cena):
    return {"ref": False, "prompt": f"Vertical 9:16 photo. {cena}\n{CAM}\n{ANTI}"}

def mecanismo(cena):
    return {"ref": False, "prompt": f"Vertical 9:16 image. {cena}\n{TRES_D}"}

# (id, peça, tempo no original, fala/keyword, cena)
P = [
 ("H1-01", "H1", "0.6–2.6", "My pre-baby jeans sat in my closet for three years",
  objeto("Inside a bedroom closet, a pair of medium-wash women's jeans neatly folded on the top shelf, pushed to the back behind sweaters, a thin layer of dust on them, hangers with loose oversized clothes below, soft window light from the side.")),
 ("H1-02", "H1", "3.8–4.7", "Last week, they zipped",
  pessoa("Close-up from chest to mid-thigh: her own hands pulling up the zipper of the same medium-wash jeans at her waist, standing in her bedroom, the zipper just closing, her sage-green sweatshirt lifted slightly above the waistband.")),
 ("BR01", "corpo", "4.8–10.0", "sacrificed everything… looked in the mirror… the woman staring back at me",
  pessoa("Mirror selfie in a small bathroom, about four months AFTER giving birth (she is NOT pregnant): she holds her phone in front of the mirror with one hand, wearing an oversized faded grey t-shirt and dark leggings, a soft postpartum tummy under the loose shirt, a burp cloth on her shoulder, hair in a messy bun, tired eyes with dark circles, looking at her reflection unhappy. The phone has a plain dark case.", True)),
 ("BR02", "corpo", "18.7–25.6", "I saw the arm, the belly, the double chin… that dress… hiding nothing",
  pessoa("A candid photo taken at her daughter's backyard birthday party: she stands in profile wearing a fitted turquoise sleeveless dress, holding a paper cup, pastel balloons and a bunting banner behind her, kids blurred in the background, harsh afternoon sun.", True)),
 ("BR03", "corpo", "44.2–46.9", "Before she was born, I was a different person, not skinny",
  pessoa("Three years younger, before pregnancy: a normal healthy weight, not skinny, she walks confidently on a sunny city sidewalk wearing high-waisted jeans and a white t-shirt, candid photo taken by a friend, smiling.")),
 ("BR04", "corpo", "55.4–56.0", "low carb",
  objeto("Top-down on a kitchen table: a plate of grilled chicken breast with a small lettuce salad and no bread, a fork, a glass of water.")),
 ("BR05", "corpo", "56.6–57.2", "fasting",
  objeto("A kitchen table at breakfast time with a clean empty plate and an unused fork, only a glass of water and a cup of black coffee, a kitchen timer next to it.")),
 ("BR06", "corpo", "57.5–58.1", "walking",
  pessoa("Low shot from behind of her feet and legs in worn white sneakers and grey sweatpants walking fast on a suburban sidewalk in the early morning, motion in the step.", True)),
 ("BR07", "corpo", "58.3–58.9", "cut out sugar",
  objeto("A woman's hand dropping an open box of glazed donuts into a kitchen trash can, a sugar jar pushed aside on the counter.")),
 ("BR08", "corpo", "59.3–60.0", "cut the carbs",
  objeto("A woman's hand sliding a bowl of pasta and a basket of bread away across a kitchen table, out of frame.")),
 ("BR09", "corpo", "60.6–61.0", "starved myself",
  pessoa("At the kitchen table late at night under a single warm lamp, she sits staring at a tiny plate with three lettuce leaves, hungry and exhausted, chin resting on her hand.", True)),
 ("BR10", "corpo", "61.4–62.3", "and the scale wouldn't budge",
  objeto("Top-down: a woman's bare feet with chipped nail polish standing on a white digital bathroom scale on a tiled floor, the bottoms of grey sweatpants visible, the scale display is blank.")),
 ("BR11", "corpo", "74.2–79.2", "a friend sent me a video of her on TV… stop suffering and watch this",
  pessoa("Over-the-shoulder close-up of her hand holding a smartphone in her kitchen: the screen shows a text message chat with a video thumbnail of a TV studio morning show (the presenter seen from far away and out of focus), and below it a message bubble that reads exactly: \"Stop suffering and watch this\".")),
 ("BR12", "corpo", "81.3–85.6", "After 35, your body stops producing two hormones that control fat burning",
  pessoa("She stands sideways in front of a bedroom mirror in a fitted black tank top and leggings, one hand on her stomach, looking at her side profile with a worried expression, soft morning light.", True)),
 ("BR13", "corpo", "86.4–87.6", "GLP-1 and GIP",
  mecanismo("Two kinds of glowing hormone molecules — one cluster teal, one cluster gold — being released from the cells of the intestinal wall into a nearby blood vessel, the molecules faint and few, as if production is slowing down.")),
 ("BR14", "corpo", "88.5–91.1", "Without them, everything you eat gets stored as fat",
  mecanismo("Food nutrients flowing as tiny glowing particles into a cluster of round yellow fat cells, the fat cells swelling and growing bigger as they absorb the particles.")),
 ("BR15", "corpo", "91.5–92.1", "no matter the diet",
  objeto("A fridge shelf full of identical diet meal-prep containers with portioned steamed broccoli, plain rice and chicken, a measuring tape and a calorie notebook on top.")),
 ("BR16", "corpo", "92.5–93.1", "no matter the exercise",
  pessoa("At a gym, she walks on a treadmill in a pink zip-up hoodie and black leggings, sweating and out of breath, a towel on the handrail, fluorescent gym light.", True)),
 ("BR17", "corpo", "97.6–98.9", "Mounjaro and Ozempic",
  objeto("Two plain white unbranded weekly injection pens with grey caps lying on a bathroom counter next to their plain white boxes, no brand names, no text.")),
 ("BR18", "corpo", "99.2–101.0", "cost $2,000 a month",
  objeto("A pharmacy paper bag on a counter with a long receipt hanging out of it; the receipt's total line reads exactly \"TOTAL $2,000.00\", the rest of the receipt is blurry.")),
 ("BR19", "corpo", "101.6–104.2", "they mimic those hormones with a synthetic injection",
  objeto("Close-up of a woman's hand pressing a plain white injection pen against the side of her belly, the t-shirt lifted only a few centimeters at the side, clinical and non-sexual.")),
 ("BR20", "corpo", "105.4–107.6", "side effects that destroy you from the inside",
  pessoa("In a dim bathroom, she leans over the sink with both hands on the edge, pale and nauseous, eyes closed, a glass of water beside the faucet.", True)),
 ("BR21", "corpo", "108.3–110.6", "when you stop, the weight comes back double",
  pessoa("Seen from behind, she walks slowly away on a grey park path on a cloudy day, wearing a loose black t-shirt, black shorts and white knee socks, shoulders down.", True)),
 ("BR22", "corpo", "111.0–112.1", "But now there's another way",
  objeto("A bright kitchen at sunrise, warm golden light coming through the window onto a clean empty counter, a hopeful fresh-start mood.")),
 ("BR23", "corpo", "113.3–116.6", "The same expert… discovered",
  objeto("Close-up of a researcher's gloved hands in a bright lab holding a glass beaker of clear red liquid up to the light, notes and test tubes on the bench, no face visible.")),
 ("BR24", "corpo", "117.2–117.9", "a gelatin recipe",
  objeto("On a kitchen counter: a glass bowl with a packet of plain unflavored gelatin powder being poured in, a whisk and a measuring cup of warm water next to it.")),
 ("BR25", "corpo", "118.1–119.9", "combined with three natural ingredients",
  objeto("Three natural ingredients lined up on a wooden cutting board: a plain unlabeled glass bottle of apple cider vinegar, two halves of a fresh lime, and a knob of fresh ginger root, a glass bowl of red liquid gelatin behind them.")),
 ("BR26", "corpo", "120.8–122.6", "reactivates those hormones naturally",
  mecanismo("The intestinal wall cells lighting up again and releasing many bright teal and gold hormone molecules into the blood vessel, while nearby round yellow fat cells begin to shrink, a warm healthy glow.")),
 ("BR27", "corpo", "123.8–124.2", "No injection",
  objeto("A single plain white unbranded injection pen lying alone on a white bathroom counter, hard top light, empty space around it.")),
 ("BR28", "corpo", "124.8–126.0", "no diet, no gym",
  objeto("A plate of plain diet food (dry chicken and steamed broccoli) on the floor of a living room next to a pair of dusty dumbbells, both pushed aside and abandoned.")),
 ("BR29", "corpo", "126.5–130.4", "the same trick… to lose 54 pounds after pregnancy",
  objeto("A cardboard donation box on a bedroom floor full of folded maternity clothes and oversized leggings, a handwritten paper label on the box that reads exactly \"TOO BIG\".")),
 ("BR30", "corpo", "131.1–135.4", "the same one used to lose 25 in 21 days",
  objeto("A paper wall calendar on a kitchen wall with 21 consecutive days crossed out in red marker, a red marker hanging on a string next to it.")),
 ("BR31", "corpo", "136.9–140.4", "the gelatin recipes going viral on TikTok and Facebook",
  objeto("A hand holding a smartphone vertically, the screen showing a generic short-video feed with a video of red gelatin being poured and a big heart count, no app logos.")),
 ("BR32", "corpo", "141.5–142.2", "have been altered on purpose",
  objeto("Close-up: a hand pouring a heaping spoon of white flour into a glass bowl of red liquid gelatin, the flour clouding the mixture.")),
 ("BR33", "corpo", "143.1–145.7", "They stripped out the ingredients that actually make it work",
  objeto("A hand taking away the unlabeled apple cider vinegar bottle and the lime halves from a kitchen counter, leaving only a sad bowl of plain gelatin behind.")),
 ("BR34", "corpo", "146.2–148.8", "so they could sell you flour capsules at the end",
  objeto("Opened transparent supplement capsules spilling plain white flour onto a dark table next to a plain unlabeled white supplement bottle.")),
 ("BR35", "corpo", "149.9–150.5", "She's suing those people",
  objeto("A wooden judge's gavel resting on a stack of legal papers on a lawyer's desk, the papers blurry and unreadable.")),
 ("BR36", "corpo", "151.0–153.6", "The original recipe, the one that actually works",
  pessoa("In her bright kitchen, wearing her sage-green sweatshirt and beige cap, she whisks a glass bowl of bright red liquid gelatin, the unlabeled apple cider vinegar bottle and lime halves on the counter, smiling slightly.")),
 ("BR37", "corpo", "154.3–158.2", "is in a video just released for free for a limited time",
  objeto("A smartphone leaning against a jar on a kitchen counter, the screen shows a paused vertical video of red gelatin with a big white play button in the middle, no text on screen.")),
 ("BR38", "corpo", "188.9–206.0", "every woman deserves… the original recipe is on the button below",
  objeto("Kitchen counter close-up: a clear glass container filled with set bright red gelatin cubes, an unlabeled bottle of apple cider vinegar and halved limes beside it, a small potted plant, soft daylight; the top third of the frame is calm empty background.")),
]

plano = [{"id": i, "peca": p, "tempo": t, "fala": f, **c} for i, p, t, f, c in P]
json.dump(plano, open(os.path.join(AQUI, "plano.json"), "w"), ensure_ascii=False, indent=1)
print(len(plano), "planos ·", sum(x["ref"] for x in plano), "com a personagem")

# --- extra (13/10): a mesma foto da festa, agora "vendo a festa" (volta emocional aos 168 s) ---
EXTRA = [("BR39", "corpo", "168.0–174.2", "the same photo. And this time I saw the party. I saw the laughter. I saw the full table",
  pessoa("A candid photo at the same backyard birthday party, same turquoise sleeveless dress, same bunting and pastel balloons: wide shot of a table full of cake and snacks with kids laughing and running around it, and she stands behind the table laughing with her head thrown back, hugging her little daughter (about 3 years old, party hat) on her hip. Warm golden afternoon light, joyful.", True))]
plano += [{"id": i, "peca": p, "tempo": t, "fala": f, **c} for i, p, t, f, c in EXTRA]
json.dump(plano, open(os.path.join(AQUI, "plano.json"), "w"), ensure_ascii=False, indent=1)
print("+ BR39")
