# Sistema visual CLARO — clean pharma

O segundo DNA da skill. O primeiro (`prompt-template.md`) é o **ESCURO**: vazio preto, haze,
acento único, seis beats. Este é o **CLARO**: estúdio claro de saúde/farma, filamentos de sinapse,
painel de vidro com borda azul, e um ritmo diferente — reveal compacto nos 5s iniciais e hold calmo
no resto.

Derivado do clipe de oferta do MemoFlow (`$19.99 PER BOTTLE` → `FIRST 3 FREE`, três frascos).

**Os dois sistemas não se misturam no mesmo lote.** Escolha um por criativo. Misturar preto profundo
com estúdio claro no mesmo VSL faz o overlay parecer de dois jobs diferentes.

---

## Quando usar o claro em vez do escuro

| Escuro (preto profundo) | Claro (clean pharma) |
|---|---|
| Dor, urgência, escassez, contraste de preço | Oferta, prova, credibilidade, mecanismo |
| Body gravado em ambiente escuro | Body em luz alta / fundo claro / cenário de casa |
| Nicho de emagrecimento, performance, agressivo | Nicho de saúde, cognição, farma, público mais velho |
| Acento quente ou verde | Acento azul / azul-aço |

O motion tem que emendar com o body que está na V1. Overlay preto por cima de body claro faz
o corte piscar.

---

## O DNA do claro

| Camada | O que é |
|---|---|
| Base | Fundo neutro claro, levemente azulado, estúdio arejado — **nunca fundo escuro, nunca vazio preto** |
| Textura | Filamentos finos tipo sinapse, à deriva, **esparsos** — nunca denso, nunca competindo com o produto |
| Produto | Herói, luz de estúdio difusa, brilhos suaves, profundidade de campo sutil |
| Painel | Vidro de cantos arredondados, borda fina luminosa azul, **abaixo** do produto |
| Tipografia base | Neutro escuro (tinta / ardósia). **Off-white não existe aqui** — ver armadilha do contraste abaixo |
| Ênfase | Azul da marca com bloom suave — a **única** cor de texto no quadro |
| Fecho | Não congela nem dessatura: **segura flutuando**. É o hold que dá o ar de premium |

---

## Os quatro beats de 10 segundos

O escuro gasta os 10s inteiros contando uma história em seis beats. O claro **resolve em 5s e
segura os outros 5**:

```
0.0–1.3s   ABERTURA    o produto flutua para o alto-meio, filamentos ao fundo, ZERO texto
1.3–3.0s   PAINEL + L1 o painel de vidro acende embaixo e a linha 1 pousa dentro dele (chime)
3.0–5.0s   PICO        a linha 1 encolhe e sobe, a linha de ênfase entra maior em azul (chime)
5.0–10.0s  HOLD        flutuação final; produto e ênfase seguram centrados até o fim
```

### Isso muda a regra de entrada no clipe

No escuro, o texto resolvido só existe entre 5,5s e 8,8s — daí a fórmula
`entrada = max(0, 8.8 - duracao)` da SKILL.md. **No claro o quadro final vale de 5,0s até 10,0s**,
o que é muito mais folgado para marcação curta:

```
entrada = max(0, min(5.0, 10 - duracao_da_marcacao))
saida   = min(10, entrada + duracao_da_marcacao)
```

Marcação de até 5s cai inteira dentro do hold, começando exatamente no instante em que a
linha de ênfase pousa — você pega o bloom e a calma, nunca a abertura vazia. Marcação maior
que 5s recua e passa a incluir o pico.

---

## Blocos comuns (idênticos em todo o lote CLARO)

### STYLE — arquétipo produto

> STYLE: Premium, clean health motion graphics on a soft neutral background — a light, airy studio
> backdrop with delicate, thin synapse-like filament lines drifting subtly and sparsely in the
> background, never dense, never busy, never competing with the product. The product bottles are lit
> as the hero objects with soft diffused studio lighting and gentle highlights, a floating glass panel
> with rounded corners and thin luminous blue edges sits beneath them, clean line graphics, subtle
> depth of field, restrained and minimal. The product, the offer and the on-screen text are always
> the visual focus — the background never carries information. Vertical portrait composition: the
> bottles sit in the upper middle of the frame, the typography stacks directly beneath, both centred.

### STYLE — arquétipo puro (sem produto)

> STYLE: Premium, clean health motion graphics on a soft neutral background — a light, airy studio
> backdrop with delicate, thin synapse-like filament lines drifting subtly and sparsely, never dense,
> never busy. Nothing in frame but the typography and one floating glass panel with rounded corners
> and thin luminous blue edges. Clean line graphics, subtle depth of field, restrained and minimal.
> Vertical portrait composition: the panel and the stacked typography are centred in the middle
> of the frame.

### TECHNICAL

Igual ao do escuro, **mas sem escrever a resolução em pixels** (ver armadilha 2 — número no prompt
vira número na tela):

> TECHNICAL: Vertical portrait, nine by sixteen, ten seconds, single continuous piece, no cuts to
> black, no letterboxing. The top fifteen percent and the bottom fifteen percent of the frame will
> later be cropped away, so every product, every graphic and every letter must sit comfortably inside
> the central seventy percent of the frame height. Nothing important touches the top or bottom edge.

### PALETTE

> PALETTE: Background is a soft neutral, light and very slightly blue-tinted, close to a warm white —
> never a dark background, never a black void. Typography and line-art render in a deep neutral ink
> tone for full contrast against the light background. The single accent is the brand blue with a
> soft bloom, used ONLY for the emphasised line of text and for the edge light of the glass panel.
> The synapse filament lines render in a faint pale blue at low opacity. No green, no gold, no
> second accent colour.

### AUDIO

> AUDIO: No speech of any kind. A soft, clean ambient bed, one light chime when each line of text
> lands, and brief silence afterwards.

### CAMERA

> CAMERA: One continuous, slow, gentle movement for the whole piece — a soft push-in or delicate
> float, no cuts. Every element decelerates into place as if settling under its own weight — nothing
> snaps in at constant speed, no rapid zoom punches, no strobing. The product never leaves, shrinks
> away or disappears mid-shot.

### DO NOT

O do escuro, com as trocas de cor e as negações novas do claro:

> DO NOT: never render any word from these instructions as visible text — no technical terms, no
> "caption", no "safe zone", no "frame", no pixel sizes, no colour codes, no font names, no
> durations; no burned-in subtitles, no captions, no spoken words, no extra text of any kind beyond
> the exact phrases specified, no invented words, no gibberish lettering, no extra line of text, no
> headline above the phrase, no invented label copy, no fictional seals with writing, no badge with
> writing, no brand-name card, no duplicate copy of any phrase, no text touching the top or bottom
> edge, no dark heavy background, no black void, no cluttered or dense filament pattern, no green
> accent, no gold accent, no circular ring, no curved surface carrying letters, no text following a
> curve, no repeated words, no lens flare streaks, no rapid strobing, no zoom punches, no watermark,
> no logo bug in the corner, no letterbox bars, no split screen, no people in frame.

---

## Trava de produto — múltiplos frascos

Quando o clipe mostra mais de uma unidade, a contagem tem que ser dita e defendida. Reflexo,
refração do vidro e desfoque criam frasco fantasma:

> Exactly three bottles float together side by side, evenly spaced, all matching the reference
> exactly, no variant. Never let reflections, glass refraction, motion blur or depth of field create
> the illusion of an extra or missing bottle beyond the exact three specified.

E a trava de rótulo de sempre:

> Every bottle shown must match the supplied reference images exactly — same bottle shape, same cap
> colour, same label artwork. Never invent a different label. Never place a badge, seal, sticker,
> ribbon or any writing on top of the bottle itself. Never render the brand name as a separate card
> or label anywhere in the frame.

---

## Arquétipo TROCA — duas frases num clipe só

Novo neste sistema. O escuro empilha duas linhas que convivem; o claro **substitui** uma pela outra
(preço → oferta). Isso quebra a trava de frase única da SKILL.md §4, então ela precisa ser reescrita
por frase, com a exclusão mútua declarada:

> CRITICAL RULES — TEXT EXCEPTION: The ONLY readable text allowed anywhere in this video is the two
> exact phrases "$19.99 PER BOTTLE" (3 words) and "FIRST 3 FREE" (3 words) — nothing else. Each
> phrase is spelled exactly like that, letter for letter, appears on exactly ONE unbroken line, and
> appears EXACTLY ONCE in the whole video. The two phrases NEVER appear in the same frame at the same
> time: the first has fully faded before the second is legible. Neither phrase ever wraps onto a
> second line, no word repeats, no extra line or duplicate word ever forms. There is no headline, no
> label, no sub-line, no kicker, no extra word above, below or beside them. Never invent additional
> words to fill space. Absolutely no other readable text, letters, numbers, subtitles, captions,
> watermarks or UI copy may appear anywhere — every other panel and surface stays completely blank.

E o TIMELINE repete as duas strings no beat em que cada uma entra e no beat em que a primeira sai.

### O painel de vidro duplica texto

Superfície de vidro na frente ou atrás da tipografia devolve fantasma espelhado da palavra.
No claro o painel fica **debaixo** do texto, e ainda assim declare:

> The glass panel is clear and non-reflective for text purposes: no ghosted, blurred, mirrored,
> inverted or partial duplicate of any word or phrase ever appears anywhere on the glass surface,
> the glass edge, or beneath the panel — each phrase renders crisply exactly once and nowhere else.

---

## As três correções sobre o prompt de referência

O prompt que gerou a referência funciona, mas carrega três brechas que a skill já sabe fechar.
Elas estão corrigidas nos blocos acima:

**1. Contraste invertido.** O prompt pedia tipografia base **off-white** sobre fundo
**quase branco**. Off-white sobre `#F4F7FA` é texto invisível — o modelo salvou o clipe escurecendo
a fonte por conta própria, e isso não se repete de forma confiável num lote de vinte. No claro a
tipografia base é **neutro escuro**, declarada em TYPOGRAPHY e reforçada em PALETTE. O off-white
pertence ao sistema escuro.

**2. Pixel e hex escritos no prompt.** `1080x1920` e `#F4F7FA` no corpo do texto é exatamente a
armadilha 2 (`Caption safe zone` renderizado dentro do card). O DO NOT proíbe, mas a proibição
disputa com a menção — mais barato não mencionar. Números por extenso, cor por nome.

**3. Contagem de palavras.** A trava da SKILL.md §4 é `— N words, nothing else`. O prompt de
referência tem "single unbroken line" e "exactly once", mas não a contagem. A contagem é a trava
que impede a linha extra alucinada (armadilha 1) — é barata, mantenha.

⚠️ **`$19.99 PER BOTTLE` é o maior risco do lote.** Cifrão com decimal é o campeão de erro de
grafia (ver miscelânea de `armadilhas.md`). Confira esse frame primeiro no QC, sempre.
