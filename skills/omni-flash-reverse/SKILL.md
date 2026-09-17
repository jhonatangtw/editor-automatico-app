---
name: omni-flash-reverse
description: Engenharia reversa de um vídeo de motion graphics de REFERÊNCIA em um prompt único pronto pra colar no Google Flow (modelo Omni Flash, 10s). Extrai frames de verdade com ffmpeg, faz análise shot-by-shot em 9 dimensões (composição, tipografia, paleta, luz, ícones, motion, transições, áudio), converte tudo num prompt denso de geração e ainda aplica swaps de marca/paleta/copy. Use SEMPRE que o usuário mandar um vídeo de referência (motion graphics, animação, product demo, explainer SaaS, ad de tech) e pedir "recria esse vídeo", "engenharia reversa desse motion", "prompt do Omni Flash", "prompt pro Google Flow", "analisa esse vídeo frame a frame", "quero um vídeo igual a esse", "transforma essa referência em prompt", "clonar esse estilo de motion", ou mandar um link/arquivo dizendo que quer algo no mesmo estilo. NÃO use pra vídeo selfie com fala (isso é gemini-omni) nem pra mapear B-roll em cima de uma fala existente (isso é video-workflow).
tags: [skill]
---

Recebe um **vídeo de referência** (motion graphics / animação / product demo / explainer SaaS) e devolve **um prompt único, copy-paste, pronto pro Google Flow no modelo Omni Flash** — que recria o *look*, o *pacing* e a *estrutura* da referência, com os swaps de marca do usuário já aplicados.

**Configuração alvo no Flow:** `Video | Ingredients | Omni Flash Model | 10s | 1x`

> **Limite duro do Omni Flash: 10 segundos.** Se a referência for mais longa, os beats são **comprimidos proporcionalmente** em 10s (nunca truncados — ver Fase 2, "Compressão de beats").

---

## 🔀 Qual skill usar (roteamento)

| Situação | Skill |
|---|---|
| Vídeo de **referência** de motion graphics → quero um prompt que recrie esse estilo | **esta skill** (`omni-flash-reverse`) |
| Vídeo **selfie falando** → quero overlays animados sincronizados com a fala | `gemini-omni` |
| Vídeo real já gravado → quero mapear B-roll bloco a bloco em cima da fala | `video-workflow` |
| Copy de anúncio + imagem de avatar → prompts de talking-head | `skill-black-belt` / `avatar-vsl-video-prompts` |
| Vídeos já exportados → conferir qualidade/legenda/compliance | `conferir-ads-por-frame` |

**Sinal decisivo:** se o vídeo de entrada é o que se quer **imitar**, é esta skill. Se o vídeo de entrada é o que se quer **enriquecer**, é `gemini-omni` / `video-workflow`.

---

## 🎯 Engenharia da atenção (o *porquê* por trás do prompt)

Esta é a filosofia que separa um prompt que gera "motion graphics de Canva" de um que gera algo com cara de Apple / Linear / Vercel. **Toda decisão da Fase 2 passa por aqui.** Sem isso, a Fase 1 vira só uma lista de fatos.

### Os 5 princípios de retenção

1. **Energia cinética calibrada.** Movimento prende; movimento demais cansa. Cada animação tem que *significar* algo — revelar, demonstrar, transicionar. Se remover a animação e a mensagem ficar igual, ela tava sobrando. Em 10s isso é brutal: não cabe movimento decorativo.

2. **Pacing como narrativa.** Ritmo é arquitetura emocional, não velocidade. Padrão: respiração no início (1 elemento contemplando), aceleração no meio (cortes rápidos), respiração no final (silêncio, hero frame).

3. **Oscilação calma → intensa → calma.** Nunca ritmo uniforme. O contraste é o que retém.

4. **Cor como pacing emocional.** A cor de acento não é decoração — é cronômetro. Cada aparição marca um beat narrativo. Se o acento virou ruído (>2 ocorrências simultâneas no mesmo frame), tá sendo mal usado.

5. **Silêncio antes do reveal.** Um beat de tela quieta antes do momento-chave vale mais que qualquer animação contínua. Em 10s, reserve ~0.6–1.0s de "hold" antes do frame final.

### Os 4 pilares da estética premium

- **Materialidade.** Não animar UI chapada — animar *matéria*. Vidro com refração, frosted glass físico, sombras com peso, hairline edges de 1px real. O cérebro lê "real" e o real prende.

- **Câmera cinemática com escala ativa.** Não é zoom chapado. Os 4 movimentos obrigatórios:
  - **Push-in:** durante hold, escala cresce sutilmente (1.0 → 1.04) — a câmera se aproximando.
  - **Pull-out:** ao sair, encolhe (1.0 → 0.92) + slip out of focus.
  - **Emphasis hit:** em palavra-âncora ou número-chave, pulse rápido (1.0 → 1.08 → 1.0 em ~400ms).
  - **Parallax drift idle:** elementos parados oscilam 2–3% em X/Y — a câmera nunca trava 100%.

  No prompt, escrever em prosa: *"the headline holds with a slow gentle push-in, scaling up subtly as if the camera is approaching"*.

- **Tipografia em movimento como ator.** 3 papéis a alternar: **headline-âncora** (gigante, dominando o frame, word-by-word, tracking respirando), **label** (pequeno, UPPERCASE, dentro de cards), **subline** (dim, contextual). Nunca um prompt inteiro só de card-ícone-card-ícone.

- **Easing customizado, nunca linear.** Linear é morto. Apple = ease-out longo. Linear/Vercel = spring com leve overshoot. No prompt: *"slow confident glide that decelerates into rest"* / *"soft settle with the subtlest overshoot, as if landing under its own weight"*.

### Visualização do invisível (3 metáforas pra IA/software)

Produto de software é invisível — não dá pra girar em 360°. Quando a referência trata de conceito abstrato, usar metáfora material em vez de ícone genérico:

| Metáfora | Quando usar | Como descrever no prompt |
|---|---|---|
| **Partículas / líquido orgânico** | "pensar", "processar", "fluido", "vivo" | "soft white particles drifting upward like dust in sunlight, coalescing into a shape" |
| **Grids e nós conectando-se** | estrutura, conhecimento, conexão de fontes | "thin hairline lines drawing themselves between dots one by one, forming a network constellation" |
| **Luz emergindo** | output, resposta, insight, reveal final | "a soft bloom of warm white light expanding outward from a central point, then settling" |

**Regra:** conceito **concreto** → ícone hairline. Conceito **abstrato** → metáfora material. Nunca inverter.

### Anatomia de um clip de 10s

Como distribuir a carga visual dentro do limite do Omni Flash:

| Segmento | Tempo | Carga | O que acontece |
|---|---|---|---|
| **Hook** | 0.0–1.5s | Alta, 1 elemento dominante | Headline-âncora ou hero shape entra. Sem texto explicativo. |
| **Contexto** | 1.5–3.0s | Média, com respiração | Título/categoria entra, elemento sustenta. |
| **Burst** | 3.0–7.0s | ALTA — cortes rápidos | Sequência de elementos revelando cada conceito. "Show, don't tell". |
| **Respiração** | 7.0–8.5s | BAIXA — 1 elemento, lento | Espectador absorve. |
| **Hero frame** | 8.5–10.0s | Silêncio + fechamento | Frame final segurado. **É o que o espectador lembra.** |

**Orçamento de beats:** máximo **5–7 beats** em 10s. Mais que isso vira picotado e o Omni borra tudo. Se a Fase 1 achou 12 beats, consolidar em 6.

---

## Fluxo

1. **Receber o vídeo de referência** (path local, arquivo anexado, ou o usuário diz que já subiu no Claude).
2. **Validar + medir** duração, resolução, fps, aspect ratio.
3. **Criar pasta de trabalho** e extrair **frames + mosaico** com ffmpeg — a análise da Fase 1 é feita *olhando os frames*, nunca chutada.
4. **FASE 1** — análise shot-by-shot em 9 dimensões + sumário no topo.
5. **Perguntar os swaps da FASE 3** via AskUserQuestion (marca, paleta, copy, duração, tom, add/remove) **antes** de escrever o prompt final.
6. **FASE 2** — montar o prompt de geração, já com os swaps aplicados.
7. **Rodar o checklist de qualidade** (seção própria abaixo) antes de entregar.
8. **Salvar** análise + prompt na pasta e entregar o prompt em bloco copy-paste.
9. *(Opcional)* Oferecer disparar no Google Flow via Playwright/Chrome MCP — seletores na seção "Automação".

---

## Etapa 1-2: Validar e medir

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,nb_frames \
  -show_entries format=duration,size \
  -of default=noprint_wrappers=1 "$VIDEO_PATH"
```

Guardar: `DURATION` (float), `WIDTH×HEIGHT`, `FPS`, aspect ratio derivado. Isso alimenta a linha "Technical specs" da Fase 2.

## Etapa 3: Extrair frames de verdade (não chutar)

```bash
SLUG="{3-5 palavras kebab-case do tema}"
DATE=$(date +%Y-%m-%d)
WORKDIR="$HOME/omni-reverse/${DATE}-${SLUG}"
mkdir -p "$WORKDIR/source" "$WORKDIR/frames"
cp "$VIDEO_PATH" "$WORKDIR/source/reference.mp4"

# 1) Frames densos — 3 por segundo (pega transições rápidas de motion graphics)
ffmpeg -y -i "$WORKDIR/source/reference.mp4" -vf "fps=3,scale=640:-1" \
  "$WORKDIR/frames/f_%04d.jpg"

# 2) Mosaico de contato — visão macro do arco inteiro em 1 imagem
ffmpeg -y -i "$WORKDIR/source/reference.mp4" \
  -vf "fps=2,scale=320:-1,tile=6x6" -frames:v 1 \
  "$WORKDIR/frames/mosaic_%02d.jpg"

# 3) Detecção de cortes — onde estão os beats reais
ffmpeg -i "$WORKDIR/source/reference.mp4" -filter:v \
  "select='gt(scene,0.3)',showinfo" -f null - 2>&1 \
  | grep showinfo | sed -n 's/.*pts_time:\([0-9.]*\).*/\1/p' \
  > "$WORKDIR/source/cuts.txt"
```

**Como usar:**
- Ler o **mosaico primeiro** (macro: arco geral, paleta, quantos beats existem).
- Depois ler frames individuais nos **timestamps de `cuts.txt`** (micro: tipografia exata, geometria dos ícones, direção da luz).
- `fps=3` é o mínimo pra não perder transições de motion graphics. Se a referência for muito rápida (cortes <0.3s), subir pra `fps=6`.

> **Regra dura:** não escrever uma única linha da Fase 1 antes de ter *visto* pelo menos o mosaico + 4 frames individuais. Análise inventada gera prompt genérico.

**Extração de paleta** (opcional mas recomendado — dá hex reais em vez de "azul escuro"):

```bash
ffmpeg -y -i "$WORKDIR/source/reference.mp4" -vf "fps=1,scale=1:1" \
  -f rawvideo -pix_fmt rgb24 - 2>/dev/null | xxd -p -c 3 | sort | uniq -c | sort -rn | head -8
```

---

## FASE 1 — Análise frame-a-frame

Cobrir **a duração inteira**, não só os primeiros segundos.

### Sumário no topo (obrigatório, antes dos beats)

- **Duração total / resolução / aspect ratio / frame rate**
- **Estilo visual em uma linha** — ex: "cinematic B&W kinetic typography com metáfora visual" ou "flat glossy SaaS dashboard UI motion"
- **Pacing** — cortes por segundo, nível de energia, onde acelera/desacelera
- **Motivo recorrente / through-line** — o que costura os beats (uma forma, uma cor, um movimento de câmera, um elemento que reaparece)
- **Contagem de beats** — quantos beats distintos, e quais sobrevivem à compressão em 10s

### Por beat — 9 dimensões

Para cada cena/beat distinto, reportar:

1. **Timestamp range** — ex: `0.0–2.5s`
2. **Composição & câmera** — enquadramento, aspect, movimento (push / pan / orbit / static), profundidade de campo, ponto focal
3. **Sujeito/conteúdo** — cada objeto, ícone, ilustração, foto, elemento 3D: forma exata, estilo (flat / 3D / line / glass), posição e tamanho relativo ao frame
4. **Texto & tipografia** — palavras exatas, família/peso (serif, sans, rounded, condensed), hierarquia de tamanho, cor, letter-spacing, animação cinética (fade, slide, mask-reveal, letter-by-letter, blur-in)
5. **Paleta** — background, foreground, acentos, hex aproximados, gradientes, tratamento monocromático
6. **Luz, sombra & textura** — direção da luz, dureza da sombra, texturas (papel, metal, vidro, matte, glossy), grain/noise, vinheta
7. **Ícones / gráficos / UI** — forma, espessura de linha, fill vs outline, brand marks, botões, cursores, indicadores de progresso, charts
8. **Motion & transições** — como o beat entra e como transiciona pro próximo (cut, morph, wipe, dissolve, liquid, particle dissolve, match-cut)
9. **Áudio** — mood/tempo da trilha, SFX (whoosh, click, chime), presença e tom de voz-over

### Camada extra — leitura editorial (o diferencial)

Depois das 9 dimensões, adicionar por beat **uma linha de intenção**: *por que esse beat existe na narrativa*. Ex: "beat 3 é o burst de features — é aqui que a densidade sobe pra provar capacidade". Sem isso, a Fase 2 recria a forma e perde a função.

E marcar, no conjunto:
- **Qual é o hero frame** (o último frame segurado — o que fica na memória)
- **Onde está o silêncio** (o beat de menor densidade — precisa sobreviver à compressão)
- **Qual é o beat-marker** (a cor/elemento que marca ritmo)

---

## FASE 3 — Perguntar os swaps (roda ANTES da Fase 2)

> A ordem do doc original é 1 → 2 → 3, mas isso obriga a reescrever o prompt depois. **Perguntar os swaps antes de escrever a Fase 2 economiza uma volta inteira.** A numeração é mantida pra compatibilidade com o doc de origem.

Usar **AskUserQuestion** logo depois de apresentar a Fase 1. Se o usuário já tiver dado as informações no pedido inicial, pular a pergunta e só confirmar em uma linha.

```
Pergunta 1 — "Marca e paleta"
  - Manter 100% fiel à referência
  - Trocar só a marca (nome/logo), manter paleta
  - Trocar marca + paleta (pedir hex)
  - Repaginar (paleta e tom novos)

Pergunta 2 — "Copy na tela"
  - Manter as linhas da referência (recriadas, não copiadas)
  - Substituir por copy nova (pedir as linhas)
  - Sem texto — só visual

Pergunta 3 — "Tom / mudança de estilo"
  - Fiel ao original
  - Mais premium/cinematográfico
  - Mais playful, menos corporativo
  - Inverter tratamento (B&W ↔ cor)

Pergunta 4 — "Adicionar ou remover algo?"  (texto livre, opcional)
```

**Campos do formulário original** (usar como checklist mental — qualquer um em branco = fiel ao original):

- Brand name / logo *(pedir brand kit se houver)*
- Color palette override *(hex)*
- Text/copy override
- Duration override *(default 10s)*
- Tone/style shift
- Anything to remove or add

---

## FASE 2 — Converter em prompt de geração Omni Flash

Escrever **um único bloco copy-paste**, em inglês (o Omni lê melhor), como instruções diretas de geração — nunca perguntas, nunca comentário.

### Compressão de beats (quando a referência > 10s)

Não truncar. Comprimir proporcionalmente:

```
novo_start = (start_original / duração_original) × 10
novo_end   = (end_original   / duração_original) × 10
```

Depois **consolidar até caber em 5–7 beats**: beats adjacentes com a mesma função narrativa viram um só. Prioridade de sobrevivência: **hook > hero frame > burst > contexto > respiração**. O beat de respiração pode encolher, mas nunca desaparecer — sem ele o clip fica sufocado.

### Os 6 blocos obrigatórios do prompt

1. **Style line** — uma frase densa cobrindo mood, iluminação, color grading, comportamento de câmera e acabamento (premium / cinematográfico / glossy / matte).
2. **Technical specs** — resolução, aspect ratio, fps, duração (10s nativo do Omni Flash).
3. **Beat-by-beat timeline** — mesma estrutura da Fase 1, reescrita como instrução de geração: o que aparece, como se move, como transiciona. Com **valores de cor exatos, descrição tipográfica exata e geometria exata dos ícones** — nada ambíguo.
4. **Typography spec** — uma linha travando a família/peso pra ficar consistente em todos os beats de texto.
5. **Sound design line** — mood da trilha + SFX ancorados nos beats visuais.
6. **Final frame spec** — descrever exatamente o último frame segurado. **É o que o espectador mais lembra** — nunca deixar genérico.

### Template do prompt final

```
CRITICAL RULE — NO METADATA ON SCREEN: This prompt contains internal styling notes.
Under no circumstances should any of the following appear as visible text in the output:
pixel sizes, font family or weight names, color codes, easing curve names, durations,
frame rates, or stroke widths. ONLY render text that appears inside "double quotes"
in the TIMELINE section below.

CRITICAL RULE — NO HUMAN DEPICTION: Do not generate human silhouettes, portrait
outlines, avatar icons, faces, or any depiction of a real person. Names, if any,
appear as pure typography only.

CRITICAL RULE — ORIGINAL WORK: Recreate the technique and visual language described
below as an original piece. Do not reproduce any specific logo, character, brand mark,
or protected asset from any existing video.

STYLE: {uma frase densa — mood, luz, color grading, comportamento de câmera, acabamento}

TECHNICAL: {WIDTHxHEIGHT}, {aspect ratio}, {fps} fps, 10 seconds, single continuous piece.

TYPOGRAPHY: {uma linha travando a família — ex: "All text uses a clean geometric
sans-serif with tight tracking; headlines in heavy weight uppercase, labels in
medium weight sentence case. Same family throughout, no exceptions."}

PALETTE: {background, foreground, acento — descritos qualitativamente + intenção}
The accent color appears only as a beat marker on emphasis moments, never as decoration.

TIMELINE — render only the text shown in "double quotes".

0.0–1.5s  {HOOK}  {o que aparece, como entra, movimento de câmera, o que NÃO aparece}
1.5–3.0s  {CONTEXTO}  {...}  Transition into next beat: {tipo}
3.0–5.0s  {BURST A}  {...}  Transition: {tipo}
5.0–7.0s  {BURST B}  {...}  Transition: {tipo}
7.0–8.5s  {RESPIRAÇÃO}  {um elemento só, lento, hold silencioso}
8.5–10.0s {HERO FRAME}  {...}

CAMERA: Never fully locked. Elements holding on screen carry a slow gentle push-in
as if the camera is approaching. Exiting elements shrink slightly and slip into soft
focus. Emphasis beats get a brief scale pulse that settles. All idle elements carry a
barely-perceptible parallax drift. Never linear motion — everything decelerates into
rest as if settling under its own weight.

SOUND: {mood da trilha + SFX por timestamp — ex: "Low sustained synth pad throughout,
building subtly. A soft whoosh at each transition. A single crisp click when the final
mark lands at 8.5s. Silence in the last half second."}

FINAL FRAME: {descrição exata do último frame segurado — composição, texto, cor, luz}

DO NOT: no bouncy springs, no whip pans, no pop-in, no lens flares, no stock-footage
look, no motion filling every single second. Silence and stillness are part of the design.
```

### Regras de escrita do prompt (aprendidas na prática)

- **Prosa natural, sem números técnicos dentro dos beats.** Escrever *"large white sans-serif text"*, não *"88px SF Pro 700"*. Escrever *"slow confident upward glide"*, não *"600ms cubic-bezier(0.22,1,0.36,1)"*. Specs numéricas ficam só na documentação/análise, nunca no prompt enviado.
- **Só o que está entre aspas duplas é renderizado como texto.** Deixar isso explícito.
- **Estilo descrito qualitativamente**, não em CSS: *"soft rounded corners"* em vez de `border-radius: 16px`; *"vivid pure orange accent"* em vez de `#FF5000`.
- **Um único bloco.** Sem preâmbulo, sem "aqui está o prompt:" dentro do bloco, sem perguntas.

---

## ✅ Checklist de qualidade (rodar antes de entregar)

Nenhum prompt sai sem passar por aqui:

- [ ] A análise da Fase 1 foi feita **olhando frames reais**, não inferida do título/contexto
- [ ] Todos os beats cobrem a duração inteira da referência (não só o começo)
- [ ] O prompt tem **5–7 beats**, não 12
- [ ] Existe pelo menos **um beat de respiração** (densidade baixa) e ele sobreviveu à compressão
- [ ] O **hero frame** está descrito em detalhe — não é "the logo appears"
- [ ] A tipografia está travada em **uma linha só** e é consistente em todos os beats
- [ ] O acento de cor aparece como **beat marker**, não pintando elementos inteiros
- [ ] Há **movimento de câmera real** (push-in / pull-out / pulse / parallax), não só fade
- [ ] Nenhuma spec numérica (px, ms, hex, nome de fonte) sobrou dentro dos beats
- [ ] As 3 CRITICAL RULES estão no topo
- [ ] Os swaps da Fase 3 foram aplicados (ou confirmado explicitamente que é fiel)
- [ ] O prompt é **um bloco copy-paste**, sem comentário no meio
- [ ] Nenhum logo/personagem/asset protegido da referência foi descrito literalmente

## 🚫 Anti-padrões (se aparecer, refazer)

| Sintoma | Por quê é ruim | Correção |
|---|---|---|
| "Modern, clean, professional motion graphics" | Não diz nada — o Omni gera template genérico | Uma frase densa e específica: material, luz, câmera, acabamento |
| 12 beats em 10s | Vira picotado, o Omni borra as transições | Consolidar em 5–7 |
| Movimento em 100% do tempo | Cansa, mata o reveal | Reservar 0.6–1.0s de hold antes do hero frame |
| Ícone hairline genérico pra conceito abstrato | Fraco, sem materialidade | Metáfora material (partículas / grid / luz) |
| Cor de acento pintando palavras inteiras | Vira decoração, perde o pacing | Acento só em asterisco, underline ou um único mark |
| Final frame descrito como "logo aparece" | Desperdiça o frame mais lembrado | Descrever composição, texto, cor, luz exatos |
| Specs CSS/px dentro dos beats | Bug conhecido: o Omni renderiza como texto na tela | Traduzir tudo pra prosa qualitativa |
| Copiar o texto/logo exato da referência | Risco de IP | Recriar a técnica, não o conteúdo protegido |

---

## ⚠️ Bugs confirmados do Omni Flash

**1. Vazamento de metadata como texto na tela.** Quando o prompt contém specs técnicas (`16px`, `SF Pro Display`, `600ms cubic-bezier`, `rgba(...)`) dentro dos beats, o Omni renderiza esses strings **como texto visível** na animação. → CRITICAL RULE no topo + prosa natural nos beats.

**2. Filtro de política com figuras humanas.** Silhueta/retrato humano + nome de pessoa pública real = recusa por política. → CRITICAL RULE "no human depiction" + nomes como tipografia pura. Se ainda falhar, usar referência indireta.

**3. Newlines colapsam ao colar via automação.** `page.fill()` em contenteditable transforma o prompt num parágrafo só. O Omni ainda interpreta as keywords (`STYLE:`, `TIMELINE`, `FINAL FRAME:`) corretamente — aceitar a limitação.

**4. Output em 720p.** O Flow faz downsample. Adequado pra IG/TikTok; se precisar de mais, upscale depois.

---

## Etapa 8: Salvar a estrutura

```
omni-reverse/YYYY-MM-DD-{slug}/
├── README.md                   ← sumário, decisões, link pro prompt
├── source/
│   ├── reference.mp4
│   ├── cuts.txt                ← timestamps de corte detectados
│   └── probe.txt               ← saída do ffprobe
├── frames/
│   ├── mosaic_01.jpg
│   └── f_0001.jpg …
├── analise-fase1.md            ← análise completa das 9 dimensões
└── prompt-omni-flash.md        ← o prompt final em bloco copy-paste
```

**`prompt-omni-flash.md`** — o prompt vai dentro de uma cerca de 3 backticks pra o botão "copy" funcionar em 1 clique.

---

## Automação — disparar no Google Flow

Se o usuário quiser executar direto, usar Chrome/Playwright MCP.

- **URL:** `https://labs.google/fx/pt/tools/flow`
- **Config alvo:** `Video | Ingredients | Omni Flash | 10s | 1x`

| Elemento | Seletor |
|---|---|
| Criar projeto (landing) | `button:has-text("Create with Google Flow")` |
| Novo projeto (dashboard) | `button:has-text("Novo projeto")` |
| Adicionar mídia | `button:has-text("Adicionar mídia")` |
| Enviar mídia | `menuitem:has-text("Enviar mídia")` |
| Modal de direitos | `button:has-text("I agree, Do not show again")` |
| Campo de prompt | `div[contenteditable]:has-text("Descreva")` |
| Botão Criar | `button[aria-label*="arrow_forward"]` |
| Baixar | `button:has-text("download Baixar")` |

**Pegadinhas:** o aviso "Falha" é bug visual inicial, não erro — verificar progresso antes de reagir. O botão "Criar" só habilita com prompt + mídia carregados. URLs `/edit/{uuid}` são estáveis: navegar direto é mais robusto que clicar thumbnail.

---

## Edge cases

- **Referência sem áudio** → pular dimensão 9, mas **ainda escrever a linha de sound design** (o Omni gera trilha; sem instrução ele improvisa mal).
- **Referência < 10s** → não esticar. Manter o timing original e usar o tempo restante como hold do hero frame.
- **Referência > 60s** → analisar como *ato*, não beat a beat. Escolher o segmento de 10s mais representativo OU comprimir só o arco (hook + 2 provas + fechamento) e avisar explicitamente o que foi cortado.
- **Referência é screen recording de UI real** → não descrever a UI literal (risco de IP + o Omni erra texto pequeno). Abstrair: "a clean dashboard-like panel with hairline dividers and three stat blocks".
- **Referência em 16:9 mas o destino é 9:16** → recompor, não croppar: headline vira full-width, elementos laterais viram empilhados verticalmente. Declarar isso explicitamente no prompt.
- **Referência com pessoas reais em cena** → substituir por tipografia ou metáfora material (bug 2).
- **Usuário só manda um link do vídeo** → tentar baixar; se não der, pedir o arquivo. **Nunca inventar a análise** a partir da descrição.
- **Aspect ratio ambíguo no ffprobe** (SAR ≠ 1) → calcular o DAR real antes de declarar no prompt.

---

## Princípios que não mudam

1. **Frames primeiro, prompt depois.** Análise inventada = prompt genérico.
2. **5–7 beats em 10s.** Sempre.
3. **Recriar a técnica, nunca o conteúdo protegido.**
4. **Prosa qualitativa nos beats, specs numéricas só na documentação.**
5. **O hero frame é o entregável real** — é o que fica na memória do espectador.
6. **Silêncio é design**, não espaço vazio a preencher.
