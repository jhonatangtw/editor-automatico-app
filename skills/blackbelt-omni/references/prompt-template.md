# Esqueleto e exemplos

## Esqueleto preenchível

Substitua o que está entre colchetes. Mantenha a ordem dos blocos.

```
[REGRA DE TEXTO — modo A, B ou C, ver SKILL.md]

CRITICAL RULE — LIKENESS: The only human likeness allowed is the portrait supplied as reference ingredient. Do not invent other faces or silhouettes.

CRITICAL RULE — ORIGINAL WORK: Recreate the technique described below as an original piece. Do not reproduce any existing logo, brand mark, app interface or protected asset. Any interface shown is an abstract generic panel with blank rows.

CRITICAL RULE — CAPTION SAFE ZONE: Keep the horizontal band across the middle of the frame free of graphics. Cards and panels live in the lower third; the subject occupies the upper half. Text will be added over that middle band later in post.

STYLE: Vertical creator-tutorial look — a [pessoa] seated in a dim home studio talking to camera, warm practical lamp glow behind, background thrown into deep blue-charcoal bokeh, subject lit soft from camera left. Over the subject float glass cards outlined in a bright glowing [ACENTO] stroke with real bloom, holding warm off-white graphics inside. Cinematic dark grade, faint film grain, camera always breathing.

TECHNICAL: 1080x1920, vertical 9:16, 25 fps, 10 seconds, single continuous piece.

PALETTE: Deep blue-charcoal background, warm neutral skin tones, glowing [ACENTO] reserved exclusively for card outlines, warm off-white reserved exclusively for the graphics living inside the cards. The [ACENTO] glow ignites as a beat marker on every card entrance and appears nowhere else.

VOICE & DIALOGUE: [bloco de travas de voz do SKILL.md]

DIALOGUE (Brazilian Portuguese, spoken aloud, never shown as subtitles): "[fala, máximo 24 palavras]"

TIMELINE — [declaração de texto].

0.0–1.5s  HOOK. [pessoa falando, sem gráfico, push-in lento]

1.5–3.5s  CARD A. [primeiro card sobe de baixo à esquerda, contorno acende, conteúdo interno se desenha]

3.5–5.5s  CARD B. [segundo card entra pela direita, acende um beat depois, conteúdo chega item a item]

5.5–7.5s  BURST. [pulso nos dois cards, linha conectando, chips ou marcas entrando em sequência]

7.5–8.8s  RESOLVE. [últimas palavras da fala. Cards encolhem, desfocam, saem pela borda inferior]

8.8–10.0s HERO FRAME. [silêncio, congela, dessatura um passo, barra do acento se desenha e para, grain e vinheta]

CAMERA: Never fully locked. The subject frame carries a slow gentle push-in as if the camera is approaching. Cards entering decelerate into rest as if settling under their own weight; cards exiting shrink and slip into soft focus. Emphasis beats pulse once and settle. All idle elements carry a barely-perceptible parallax drift. Nothing moves linearly.

SOUND: [pad e pulso] with a soft airy whoosh as each card slides in, a crisp click when each element lands, and silence in the last half second. Music and effects sit low under the voice, never competing with it.

DO NOT: no subtitles, no burned-in captions, no English, no European Portuguese accent, no second voice, no repeated or looped dialogue, no bouncy springs, no whip pans, no pop-in, no lens flares, no stock-footage look, no recognisable app interface, no motion filling every single second.
```

## Vocabulário por papel de clipe

Cada papel tem um repertório visual próprio. Puxe daqui em vez de inventar do zero.

### HOOK — abre o lote, cria dúvida
- Card com moldura de retrato que se desenha e preenche com silhueta off-white
- Segundo card com grid dois-por-dois chegando painel a painel
- Fio conectando os dois cards, com pontos acendendo em sequência
- Frame final: dessatura + barra do acento

### PROVA — mostra detalhe, valida a promessa
- Retículo fino que trava num ponto e puxa um crop ampliado pro card
- Saltos rápidos do retículo, cada salto empurrando um chip pro card existente
- Textura ou micro-detalhe renderizado em off-white dentro do card
- Frame final: retículo desenha um quadrado ao redor do assunto inteiro

### MECANISMO — explica como funciona
- Pontos espalhados que se ligam por linhas formando uma constelação
- Constelação que contrai e vira grid rígido sobre o assunto
- Coluna de painéis empilhando um a um
- Três chips deslizando pela borda inferior com conector entre eles
- Frame final: grid pisca uma vez sobre o assunto e some

### CTA — fecha, pede a ação
- Painel largo subindo da borda inferior, vazio por dentro
- Forma arredondada tipo campo de input, desenhada em hairline
- Pulso do contorno em anel expandindo devagar
- Frame final: pílula de vidro centralizada no terço inferior, com o CTA dentro (modo B) ou vazia como placeholder (modo A)

## Exemplo real — clipe de CTA, modo B

Trecho de TIMELINE de um CTA com a string `"EU QUERO"` liberada:

```
3.5–5.5s  THE LINE. Centered inside the panel, the two words "EU QUERO" reveal one after the other in heavy uppercase, each snapping in with a tight settle. Spelled exactly as written, large, correctly and legibly, nothing else in the panel.

5.5–7.5s  PULSE. A hairline outline draws itself around the two words and pulses outward once in a slow expanding ring, brightening the panel for a beat before settling back. Two small off-white dots settle beneath the panel, one after another. The text stays perfectly still and unchanged.

7.5–8.8s  RESOLVE. The final words of the spoken line land here. The panel shrinks slightly and slips out of focus toward the bottom edge, carrying the text with it. Only the person remains, a light smile settling in.

8.8–10.0s HERO FRAME. Silence. The image freezes. A rounded glass pill with a bright glowing outline draws itself centered in the lower third, holding "EU QUERO" in heavy uppercase warm off-white, glowing softly against the dark. Held perfectly still with soft bloom and grain to the end.
```

Repare que a string aparece **três vezes** no prompt inteiro (regra, THE LINE, HERO FRAME) e sempre grafada igual. Repetição idêntica reduz erro de renderização.
