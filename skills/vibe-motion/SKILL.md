---
name: vibe-motion
description: Gera prompts de motion design prontos pra colar no Higgsfield Vibe Motion — o app que gera motion graphics como código (Remotion), com texto que nunca quebra. Produz clipes STANDALONE, sem VO, a partir de uma ideia ou asset (produto, logo, headline, número). Reaproveita a filosofia de retenção da gemini-omni (energia cinética calibrada, materialidade Apple/Linear, tipografia cinética, asterisco como beat-marker) mas inverte a regra de metadata — aqui specs numéricas (px, ms, hex, easing) são o diferencial. Use SEMPRE que pedirem "prompt pro Vibe Motion", "motion design estilo Higgsfield", "criar clipe de motion graphics", "animar essa headline/número/logo", "kinetic typography", "infográfico animado", "poster animado", "text animation", "hook animado pra Meta/TikTok", "reveal de preço", "CTA animado", ou mandarem um produto/copy pedindo motion graphics puro (sem creator falando). Aciona também pra variantes A/B. Não confundir com gemini-omni, que anima overlays na fala de um vídeo selfie.
---

Skill que recebe uma ideia (ou asset — imagem de produto, logo, headline, número-chave) e devolve um prompt pronto pra colar no **Higgsfield Vibe Motion**, gerando um clipe de motion graphics standalone no estilo das referências premium (Apple/Linear/Vercel), mantendo a assinatura visual da operação.

**O que é o Vibe Motion e por que o prompt é diferente.** O Vibe Motion gera motion graphics como **código (Remotion)**, não por pixel prediction. Consequências práticas que mudam tudo no prompt:
- **O texto nunca quebra.** Kinetic typography é uma força, não um risco. Pode abusar de headlines gigantes word-by-word.
- **Specs numéricas são o diferencial, não bug.** Tem inspector visual com hex/RGB exatos e sliders de easing. `#FF5000`, `y+16px`, `600ms ease-out`, `scale 0.96→1.0` são bem-vindos no prompt. **Isto é o oposto da gemini-omni** (onde metadata vazava como texto na tela — lá era proibido).
- **É iterável.** Você troca um módulo, re-renderiza e aprende o que mudou. Ideal pra parameter sweep / A/B.
- **Sem áudio.** Motion graphics puro. Não existe CRITICAL RULE de passthrough de VO aqui. Se precisar de voz, casa depois no CapCut/Premiere.
- **Entrada:** ideia via chat + assets opcionais (logo, SVG, imagem, footage). O sistema constrói a animação em volta do asset, não sobre placeholder genérico.

---

## 🎯 Filosofia de design (herdada da gemini-omni, sem mudança)

Toda decisão de animação passa por estes princípios — senão vira motion-graphics genérico de Canva. O objetivo é fabricar a sensação de produto Apple/Linear/Vercel: autoridade discreta, materialidade tátil, pacing emocional.

### Os 5 princípios de retenção

1. **Energia cinética calibrada.** Movimento prende; movimento demais cansa. Cada animação tem que *significar* algo — revelar, demonstrar, transicionar. Se remover a animação e a mensagem ficar igual, ela tava sobrando.
2. **Pacing como narrativa.** Ritmo é arquitetura emocional. Respiração longa no início (1 elemento ~2s), aceleração no meio (cortes rápidos mostrando features), respiração no final (1 elemento, silêncio visual).
3. **Oscilação calma → intensa → calma.** Nunca ritmo uniforme o clipe inteiro. Introduz um "burst" (5-10 elementos rápidos), depois volta ao calmo. O contraste em si retém.
4. **Cor como pacing emocional.** O acento (laranja `#FF5000` por padrão, ou a cor de marca) não é decoração — é cronômetro. Aparece SÓ no asterisco (`*`) ou num underline de palavra-âncora. Cada aparição marca um beat. Se virou ruído (>2 acentos visíveis no mesmo frame), tá mal usado.
5. **Silêncio antes do reveal → aqui vira "o end frame é sagrado".** Sem áudio, o beat de descanso não é a pausa da fala — é a **stillness do frame final**. O estado final é o que o espectador julga: perfeitamente alinhado ao grid, totalmente opaco, sem drift, sem bounce. Se o fim tá relaxado, toda a transição parece amadora.

### Os 4 pilares da estética Apple/Linear/Vercel

- **Materialidade.** Não animar UI chapada — animar *matéria*. Frosted glass com refração, sombras com peso, hairline edges de 1px. O cérebro lê "real" e o real prende mais.
- **Câmera cinemática com escala ativa.** Push-in no hold (`scale 1.0→1.04` em 1-2s), pull-out na saída (`scale 1.0→0.92` + slip into focus blur), emphasis hit em palavra-âncora (`scale 1.0→1.08→1.0` em ~400ms), parallax drift idle (2-3% em X/Y — nunca 100% travado). Sem isso, vira Canva chapado.
- **Tipografia em movimento como ator.** Palavras-âncora aparecem GIGANTES no centro, word-by-word, com tracking respirando. 3 papéis: headline-âncora (número/verbo forte gigante), label de card (UPPERCASE categoria), subline contextual (texto pequeno dim). Alternar sempre — nunca só card-ícone-card.
- **Easing customizado, nunca linear.** Linear é morto. Apple = ease-out longo `cubic-bezier(0.22,1,0.36,1)` ~600ms. Linear/Vercel = spring com leve overshoot. **No Vibe Motion pode escrever o easing exato no prompt** — use isso.

### Anatomia do clipe (mapa pra distribuir a carga)

| Segmento | % do clipe | Carga | O que acontece |
|---|---|---|---|
| **Hook** | 0-15% | Alta-densidade, 1 elemento dominante | Headline-âncora gigante (número/pergunta/frase-bomba). Deixa pergunta no ar. |
| **Contexto** | 15-30% | Média, com respiração | Título/categoria entra, frosted card sustenta. |
| **Burst de features** | 30-60% | ALTA — cards rápidos | Sequência revelando cada conceito. "Show, don't tell". 3-6 elementos. |
| **Respiração** | 60-80% | BAIXA — 1 elemento lento | 1 card, 1 frase. Venda emocional acontece aqui. |
| **Crescendo + CTA** | 80-100% | Alta, com fechamento | Recap (asterisco reaparece) + CTA grande. End frame: silêncio, só o asterisco, alinhado ao grid. |

Clipes Vibe Motion costumam ser curtos (3-10s). Num clipe curto, comprimir: hook forte → 1-2 features → CTA/end frame estável. Não tentar encaixar a anatomia inteira num clipe de 4s.

---

## Fluxo

1. **Capturar a intenção**: o que o clipe precisa comunicar? (hook, reveal de feature, reveal de preço, CTA, infográfico, animação de logo). Se o usuário mandou copy/VSL, extrair a headline-âncora e o(s) beat(s).
2. **Definir FORMAT** (Etapa A) — Text Animation / Infographic / Poster / Logo Animation / from scratch.
3. **Definir ASSET** (Etapa B) — tem imagem de produto/logo/SVG? Ou é from-scratch tipográfico? O prompt muda: com asset, o motion se constrói em volta dele.
4. **Definir PALETTE** (Etapa C) — preset (Mosaic / Prism / Candy) OU hex de marca (default: near-black base + off-white text + acento laranja `#FF5000`).
5. **Montar o prompt modular** (Etapa D) seguindo o esqueleto: FORMAT → CANVAS+safe zones → PALETTE → TYPE → LAYERS → INITIAL STATE → FINAL STATE → TRANSFORMATION → PACING → ON-SCREEN TEXT.
6. **Rodar a QA checklist** (Etapa E) antes de entregar.
7. **Entregar** o prompt pra colar no app + oferecer parameter sweep (variantes A/B) se for criativo de performance.

**Perguntar só o essencial.** Se a intenção, o formato e a paleta já dão pra inferir da copy/contexto, não perguntar — montar direto e deixar o usuário corrigir por exemplo. Perguntar apenas quando houver bifurcação real (ex: tem asset de produto ou é tipográfico puro? qual acento de marca?).

---

## Etapa A — FORMAT

O Vibe Motion tem presets de formato que definem a estrutura base. Escolher o mais próximo da intenção:

| FORMAT | Quando usar | Estrutura típica |
|---|---|---|
| **Text Animation** | hook, frase-bomba, headline-âncora, quote | 1-3 blocos de texto gigante, word-by-word, fundo limpo |
| **Infographic** | dado, comparação, "antes/depois", stat de prova | número grande + label + barra/gráfico hairline animando |
| **Poster** | reveal de produto, key visual, capa de oferta | asset central + título + acento, composição estática que respira |
| **Logo Animation** | vinheta de marca, bumper, intro/outro | logo entra por stroke-on/reveal + settle no grid |
| **from scratch** | criativo custom sem molde | você arquiteta os layers do zero |

## Etapa B — ASSET

- **Com asset** (imagem de produto, logo, SVG, footage): declarar no prompt que a animação se constrói EM VOLTA do asset. O asset geralmente é a camada estática (não se move) enquanto texto/acento se movem sobre ele. Exemplo: produto no centro imóvel, headline entra word-by-word na parte superior.
- **From-scratch tipográfico**: sem asset, o texto É o herói. Fundo near-black, headline gigante domina o frame.
- **Assets do usuário**: no fluxo DR, o asset costuma ser um still de produto (foto real ou gerado no Higgsfield/Nano Banana) ou o logo da marca. Se o usuário não anexou, perguntar se quer clipe tipográfico puro ou se vai subir um asset no app.

## Etapa C — PALETTE

- **Presets nativos**: Mosaic, Prism, Candy (coloridos, energéticos — bons pra DTC jovem/vibrante).
- **Brand hex (default premium)**: base near-black `#0A0A0B`, texto off-white `#F6F3EC`, acento único laranja `#FF5000`. Autoridade institucional.
- **Regra do acento**: UMA cor de acento só, usada exclusivamente como beat-marker (asterisco `*`) ou underline. Nunca preencher palavras inteiras com o acento.
- **Marca específica**: se for pra uma marca com guideline (ex: Editor Black Belt = preto `#0B0B0C`, gold `#C9A227`, off-white `#F6F3EC`), trocar o acento pela cor da marca e informar os hex exatos no prompt (o inspector do Vibe Motion respeita hex).

## Etapa D — Montar o prompt modular

O backbone do prompt Vibe Motion é **modular** (validado pela comunidade): escolher a camada que pode se mover, definir o estado inicial com contraste claro, cravar o estado final alinhado, e descrever a transformação com **verbos, não vibes**. Isso dá atribuição: se o motion sair errado, você sabe qual módulo mexer.

### Esqueleto (colar e preencher)

```
FORMAT: {Text Animation | Infographic | Poster | Logo Animation | from scratch}
CANVAS: 1080x1920 vertical (9:16), 30fps. Safe zones: top 12% and bottom 18% free of critical text (IG/TikTok UI).
PALETTE: base {#0A0A0B near-black}, text {#F6F3EC off-white}, single accent {#FF5000 pure orange}. Accent used ONLY as asterisk beat-marker or single-word underline — never fill whole words.
TYPE: anchors in a bold condensed sans display; labels in a clean geometric sans; category labels UPPERCASE.
MATERIALITY: cards are dark frosted glass with a 1px hairline white edge and a soft weighted drop shadow — physical sheets, not flat rectangles. Foreground sharp, backgrounded layers carry subtle depth-of-field blur.

LAYERS (only these move — everything else stays perfectly static):
- {headline anchor}
- {accent asterisk}
- {optional: one card / one icon}

INITIAL STATE:
- headline: y+16px, opacity 0
- asterisk: opacity 0, scale 0.96
- {asset/card, if any}: opacity 0, scale 0.98

FINAL STATE (this is what the viewer judges — make it clean):
- headline: aligned to grid, fully opaque, at rest, zero drift
- asterisk: settled beside the last word, full opacity
- everything locked, no residual bounce

TRANSFORMATION (verbs, not vibes):
- headline reveals word-by-word with an ease-out glide, cubic-bezier(0.22,1,0.36,1), ~600ms, fast in and decelerating to rest; letter tracking slightly tight on entry, breathing outward into final spacing
- during the hold, a slow gentle push-in (scale 1.0→1.04 over ~1.5s), as if a lens approaches
- a brief emphasis pulse hits the asterisk as it lands (scale 1.0→1.08→1.0 in ~400ms)
- idle layers carry a barely-perceptible parallax drift (2-3% X/Y) — camera never fully locked

PACING: {segmento da anatomia — hook / feature-burst / CTA}. One dominant element at a time. End on a full stillness beat: the final frame holds silent, grid-aligned, only the accent asterisk present.

ON-SCREEN TEXT (PT-BR, render exactly as written, in quotes):
- "{HEADLINE}"
- "{subline opcional}"
```

### Regras de preenchimento

- **ON-SCREEN TEXT sempre em PT-BR e sempre entre aspas.** Só o que está em aspas deve ser renderizado como texto. O resto do prompt é instrução de motion, em inglês.
- **Timecodes: opcional.** Diferente do Omni, não há fala pra sincronizar. Se o clipe tem beats sequenciais (ex: 3 features em burst), pode cravar timing por bloco ("first feature at 0.0s, second at 1.2s, third at 2.4s"). Se é 1 headline só, não precisa.
- **Specs numéricas: usar.** É o diferencial do Vibe Motion. Hex, px de offset, ms de duração, curva de easing, valores de scale — todos bem-vindos, o inspector respeita.
- **Animation Speed**: o app tem slider de velocidade global. No prompt, indicar a intenção ("energetic, snappy" ou "smooth, premium, unhurried") e ajustar no slider depois.

---

## Etapa E — QA checklist (rodar ANTES de entregar)

Checklist chata mas decisiva (é o que separa motion pro de motion amador). Antes de entregar o prompt, verificar que ele força:

1. **Legibilidade no mobile** — headline grande o suficiente, contraste alto, dentro das safe zones.
2. **Reading order claro** — o olho sabe pra onde ir primeiro. Um elemento dominante por vez.
3. **End frame estável** — estado final alinhado ao grid, opaco, sem drift/bounce residual. O fim é o que o espectador julga.
4. **Sem camera motion acidental** — parallax drift é intencional e sutil; nada de whip pan ou zoom aleatório não pedido.
5. **Sem type drift** — o texto assenta e trava. Nada de tremor ou reflow depois do settle.
6. **Acento comportado** — no máx 1 asterisco/underline visível por vez. Se tem 2+, o beat-marker virou ruído.
7. **Motion serve à intenção** — se a animação não guia leitura nem marca ênfase, é ruído mesmo que fique bonito. Cortar.

Se algum item falhar, ajustar o módulo correspondente no prompt (não o prompt inteiro — é a vantagem do modular).

---

## Parameter sweep (variantes A/B pra performance)

O Vibe Motion brilha em iteração. Pra DR/performance, gerar um pequeno lote de variantes (6-12, não 100) travando o template e variando UM eixo por lote:

- **Lock**: mesmo asset, mesmo grid de layout, mesmas cores de marca, mesmo end state.
- **Vary um eixo**: timing (velocidade da entrada), order (ordem de revelação das palavras/features), ou transformation (tipo de easing/entrada).
- **QA com a checklist acima** em cada variante.
- **Ship e mede**: thumbstop, hold time, CTR, CPA. Atualiza o default com o que ganhou.

Ao oferecer sweep, gerar as N variações como blocos de prompt separados, cada um com o mesmo esqueleto e só o eixo variado destacado no topo (`// VARIANT 3 — vary: entrance easing = spring with slight overshoot`).

---

## Mapeamento conceito → animação

Dois grupos. **Concretos** (objeto do mundo real → ícone hairline). **Abstratos** (estado/processo → metáfora material). Nunca traduzir abstrato como ícone hairline genérico — fica fraco.

**Concretos (ícone hairline outline, stroke-on draw):** carrossel → 3 retângulos 4:5 staggered; site → janela de browser com 3 dots; app → phone vertical com notch; código → janela com linhas indentadas; dinheiro/receita → cifrão em círculo; tempo → relógio; dados → bar chart 3-4 barras crescentes.

**Abstratos (metáfora material — preferir pra IA/energia/transformação):**
| Conceito | Metáfora | Descrição pro prompt |
|---|---|---|
| energia / vitalidade / "vivo" | partículas/líquido | "soft white particles drifting upward, coalescing into a glowing shape" |
| conexão / rede / fontes | grids/nós | "thin hairline lines drawing themselves between scattered dots, forming a constellation that settles" |
| insight / resultado / reveal | luz emergindo | "a soft warm bloom of light expanding from a central point, settling into a clean headline" |
| processo / sistema | partículas + grid | "particles flowing into a structured grid that locks line by line" |

Como é code-based, kinetic typography é sempre uma opção forte — na dúvida entre ícone e headline gigante, a headline retém mais.

---

## Playbook DR (arquétipos prontos)

Blocos de referência pros criativos mais comuns da operação. Preencher o esqueleto da Etapa D com estes moldes.

**HOOK — número/pergunta bomba (Text Animation, ~3s):**
Headline-âncora gigante entra word-by-word, push-in no hold, asterisco laranja com emphasis pulse, end frame trava a pergunta no ar. ON-SCREEN: `"VOCÊ AINDA TOMA ISSO*"` ou `"R$ 158.000*"`.

**FEATURE BURST — 3 benefícios (Infographic, ~5s):**
3 cards frosted glass entram em sequência rápida (0.0s / 1.2s / 2.4s), cada um com ícone hairline stroke-on + label UPPERCASE. Pacing alto. End: os 3 cards alinhados no grid, quietos. ON-SCREEN: `"ABSORÇÃO 3X"`, `"SEM ESTÍMULO"`, `"30 DIAS*"`.

**REVEAL DE PREÇO (Poster, ~4s):**
Preço "de" riscado entra pequeno, dá pull-out; preço "por" entra gigante com emphasis pulse e asterisco laranja. Push-in sustenta. End frame: preço final travado, asterisco ao lado. ON-SCREEN: `"DE R$ 297"` → `"POR R$ 97*"`.

**CTA (Text Animation, ~3s):**
Verbo de ação gigante word-by-word + seta laranja hairline apontando (draw-on). End frame: CTA + seta travados, silêncio. ON-SCREEN: `"COMEÇA HOJE*"` + seta.

**LOGO / VINHETA (Logo Animation, ~2-3s):**
Logo entra por stroke-on ou fade+scale-settle, leve overshoot, trava no grid central. Asterisco/acento pode pulsar uma vez. End frame: logo estático, limpo.

---

## Princípios que NÃO mudam

1. **9:16 vertical, 1080x1920, 30fps** por padrão (DR Meta/TikTok). Horizontal só se pedido.
2. **Safe zones** top 12% + bottom 18% sempre livres de texto crítico.
3. **ON-SCREEN TEXT em PT-BR, entre aspas.** Instrução de motion em inglês.
4. **Acento único** = beat-marker, nunca decoração. Máx 1 visível por vez.
5. **End frame sagrado** — alinhado ao grid, opaco, sem drift. É o que o espectador julga.
6. **Easing nunca linear.** Sempre ease-out/spring, e no Vibe Motion pode cravar a curva exata.
7. **Motion serve à mensagem.** Se remover e a mensagem ficar igual, cortar.

## Diferenças-chave vs gemini-omni (não confundir os dois)

| | gemini-omni | vibe-motion |
|---|---|---|
| Entrada | vídeo selfie com fala | ideia + asset opcional |
| Saída | overlay sincronizado sobre o vídeo | clipe standalone de motion graphics |
| Áudio | PT-BR sagrado, passthrough | sem áudio (motion puro) |
| Estrutura do prompt | shot-a-shot com timecodes da fala | modular: layer / initial / final / transformation |
| Specs numéricas na tela | PROIBIDAS (vazavam como texto) | PERMITIDAS e recomendadas (Remotion respeita) |
| Sync | por timecode relativo à fala | por beats do próprio clipe (opcional) |
| Alvo | Google Flow (Omni Flash) | app Higgsfield Vibe Motion |

## Edge cases

- **Copy longa / VSL inteira**: um clipe Vibe Motion é curto (3-10s). Não tentar animar a VSL toda num clipe — extrair só a headline-âncora ou 1 beat. Pra sequência longa, gerar vários clipes curtos e montar depois.
- **Sem asset e sem headline clara**: pedir ao usuário a frase-âncora ou o número-chave — é o herói do clipe tipográfico.
- **Marca com guideline específica**: trocar acento/tipografia pelos hex e fontes da marca; informar os valores exatos no prompt.
- **Precisa de VO**: fora do escopo desta skill (motion puro). Gerar o motion aqui e casar a voz depois (ElevenLabs/HeyGen → CapCut/Premiere), ou usar a gemini-omni se a base for um vídeo falado.
- **Horizontal (16:9)**: ajustar safe area (top 8% + bottom 14%) e âncora pra lower-third.
