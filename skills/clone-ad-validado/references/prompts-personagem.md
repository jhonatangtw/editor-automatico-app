# Prompts da personagem nova (testados em clone real, GPT Image 2.5)

Troque o que está entre colchetes. Mantenha a ordem: **cena e pessoa → câmera →
bloco anti-cara-de-IA → frase final de pele**. Se houver produto na cena, a trava
de produto entra DEPOIS do bloco anti-cara-de-IA e ANTES da frase de pele, aberta
pela escala (ver `boas-praticas-black-belt`).

Parâmetros: `gpt_image_2_5 --aspect_ratio 9:16 --quality high --resolution 2k`.

## 1. Retrato-âncora (selfie UGC)

```
Vertical 9:16 front-facing smartphone selfie video still, UGC style, filmed by the woman herself holding the phone at arm's length slightly above eye level (phone and arm not visible in frame). [ETNIA] woman, [IDADE] years old, [TOM DE PELE], [CABELO: comprimento, textura, penteado, alguns fios soltos], [ACESSÓRIO discreto], no heavy makeup. She wears [ROUPA IGUAL OU EQUIVALENTE À DO ORIGINAL], frame cut at the upper chest. She looks straight into the lens with a friendly, slightly surprised half-smile, mouth gently closed, as if about to tell a friend something important. Her face is centered in the frame, head and shoulders, small headroom. Background: [CÔMODO VIVIDO: parede com marca, cama desarrumada, objeto torto], a window just out of frame on one side blowing out the light on that side of her face.
Camera: iPhone 15 Pro front TrueDepth camera, 23mm equivalent, f/1.9, ISO 400, 1/60s, Apple ProRAW color science, slight wide-angle distortion near the edges, focus on the eyes.
Not a stock image, not a commercial shoot, not an AI render. Light is imperfect: the window side of her face is brighter and slightly overexposed, the other side falls into soft shadow with a faint warm cast from a lamp, two color temperatures on the skin. Face is naturally asymmetric: one eye slightly smaller, uneven eyebrows with a few stray hairs, small dark spots and mild hyperpigmentation on the cheeks, fine lines under the eyes and at the corners of the mouth consistent with her age, slightly dry lips, natural ivory teeth if visible. Fine 35mm-like sensor noise, slight vignette, mild chromatic aberration at the frame edges, Kodak Portra 400 look. No beauty filter, no HDR glow, no digital sharpening halo, no glossy plastic sheen, no teal-and-orange grade. No text, no logos, no watermark.
Visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, no airbrushing, no smoothing filters.
```

Boca fechada e olhar na lente não são detalhe: este quadro é o ponto de partida do lip sync.

## 2. O mesmo rosto em outro cenário

`--image-references <id do job do retrato aprovado>` e:

```
IDENTITY: the SAME woman as in the reference image — same face, same skin, same hair, same earrings, same top. Same day, a different room.
Vertical 9:16 front-facing smartphone selfie video still, UGC style, filmed by herself holding the phone at arm's length at eye level (phone and arm not visible). She stands in her own lived-in [CENÁRIO DO ORIGINAL, com 3–4 objetos concretos e um pouco de bagunça], a bright window on one side. Head and upper chest, face centered and occupying the upper middle of the frame. She looks straight into the lens with a warm, open, mid-sentence expression, lips relaxed and closed.
Camera: [mesma linha de câmera do retrato, ISO ajustado à luz].
[mesmo bloco anti-cara-de-IA] Any packaging, sign or paper in the background is out of focus and unreadable. Face naturally asymmetric with the same fine lines, small dark spots and uneven eyebrows as in the reference.
Visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, no airbrushing, no smoothing filters.
```

## 3. Plano de b-roll que mostrava o corpo da pessoa antiga ("antes")

`--image-references <id do retrato>`; descreva o enquadramento do plano ORIGINAL
(onde o quadro corta, o que fica de fora) e **não descreva o corpo** — descrição de
corpo derruba a geração na moderação (403 no Kling, "nsfw" em outros motores).

```
IDENTITY: the SAME woman as in the reference image — same skin tone, same hair falling onto her shoulders.
Vertical 9:16 casual "before" progress photo taken by a friend with a phone, front view, in a plain [CORREDOR/QUARTO] at home. Frame from her chin (face cropped out at the top edge, only the chin and the ends of her hair visible) down to mid-thigh. She wears [ROUPA DO PLANO ORIGINAL], standing relaxed with arms at her sides, posture slightly slumped and tired. Non-sexual, everyday, documentary.
Camera: iPhone 14 rear camera, 26mm equivalent, f/1.5, ISO 640, 1/50s, flat indoor ceiling light, Apple color science.
[bloco anti-cara-de-IA]
Visible pores, micro-texture, natural skin imperfections, subtle peach fuzz, natural skin sheen, no airbrushing, no smoothing filters.
```

Se mesmo assim a moderação recusar: troque o plano de corpo por um equivalente que
entregue a mesma leitura sem o corpo (roupa larga no cabide, calça que não fecha
sobre a cama, a balança vista de cima).
