---
name: gemini-omni
description: Gera prompt de motion graphics pro Gemini Omni a partir de um vídeo selfie COM FALA do Marcelo. Se o vídeo passar de 10s, fatia automaticamente em takes ≤10s alinhados em frases inteiras (Omni não aceita mais que isso) e organiza tudo numa pasta com README + take + prompt por clip. Transcreve a fala, analisa o cenário, pergunta o estilo de motion (Apple-clean / CODA Dark / Clone de Cérebro / Híbrido / Linear Vercel / Editorial Magazine / Liquid Organic / Brutalist) e monta um prompt cinematográfico com timecodes precisos, animações sincronizadas com a fala e branding consistente. O áudio original em PT-BR é sempre preservado. Use quando pedirem "prompt pro Gemini Omni", "ilustrar minha fala", "animar esse vídeo", "motion pra esse reel" ou mandarem um path de vídeo selfie com intenção de adicionar overlays. NÃO use quando o vídeo enviado for uma REFERÊNCIA de motion graphics que se quer imitar ("recria esse vídeo", "engenharia reversa desse motion") — isso é a skill omni-flash-reverse.
tags: [skill]
---

Skill que recebe um vídeo selfie (vertical 9:16) do Marcelo e devolve um prompt pronto pra colar no Gemini Omni — com animações que ilustram exatamente o que ele fala, sincronizadas por timecode, no estilo de motion escolhido.

**Limite duro do Omni: 10 segundos por clip.** Se o vídeo for maior, a skill fatia em takes ≤10s cortando só em fim de frase (nunca no meio da palavra) e gera 1 prompt por take.

---

## 🔀 Qual skill usar (roteamento)

Três skills tocam vídeo + Google Flow. O sinal decisivo é **o que o vídeo de entrada é**:

| O vídeo de entrada é… | O que se quer | Skill |
|---|---|---|
| **Selfie com fala** (Marcelo falando) | Overlays animados sincronizados na fala, áudio PT-BR preservado | **esta skill** (`gemini-omni`) |
| **Referência de motion graphics** (animação, product demo, explainer SaaS) | Um prompt que **recrie aquele estilo** do zero no Omni Flash | `omni-flash-reverse` |
| **Vídeo real já gravado** | Mapear B-roll bloco a bloco em cima da fala existente | `video-workflow` |
| **Copy de anúncio + imagem de avatar** | Prompts de talking-head (Veo/Kling/Seedance) | `skill-black-belt` |
| **Vídeos já exportados** | QA por frames (legenda, visual, compliance) | `conferir-ads-por-frame` |

**Regra de bolso:** se o vídeo é o que se quer **enriquecer** → `gemini-omni`. Se é o que se quer **imitar** → `omni-flash-reverse`.

A `omni-flash-reverse` compartilha a mesma filosofia de atenção desta skill (energia cinética, materialidade, tipografia cinética, acento como beat-marker) — se ajustar os princípios aqui, espelhar lá.

---

## 🎯 Engenharia da atenção (the why behind the prompts)

Esta seção é a **filosofia de design** que rege os shots gerados nos prompts. Toda decisão de animação deveria passar por esses princípios — caso contrário vira motion-graphics genérico de Canva. O objetivo não é "ter movimento", é fabricar a sensação de produto Apple/Linear/Vercel: autoridade discreta, materialidade tátil, pacing emocional.

### Os 5 princípios de retenção

1. **Energia cinética calibrada.** Movimento prende; movimento demais cansa. Cada animação tem que *significar* algo — revelar uma feature, demonstrar um conceito, transicionar uma ideia. Nunca movimento por movimento. Se a animação for removida e a mensagem ficar igual, ela tava sobrando.

2. **Pacing como narrativa.** O ritmo é arquitetura emocional, não só velocidade. Padrão Apple replicado nos prompts: respiração longa no início (1 elemento, ~2s contemplando), aceleração no meio (cortes rápidos a cada 0.8–1.2s mostrando features), respiração no final (produto inteiro, silêncio, asterisco fica).

3. **Oscilação calma → intensa → calma.** Não animar em ritmo uniforme o reel inteiro. Mantém pacing simples na maioria dos takes (15–25s entre transições visuais). A cada 2–3 takes, introduz um "burst": 5–10 elementos rápidos. Depois volta ao calmo. O contraste em si retém — é o mesmo princípio que torna Keynotes assistíveis por 2h.

4. **Cor como pacing emocional.** Laranja `#FF5000` não é decoração — é cronômetro. Aparece SÓ no asterisco (`*`) e no underline de palavras-âncora. Cada aparição marca um beat narrativo. Se o laranja virou ruído (>2 asteriscos visíveis simultâneos no mesmo card), tá sendo usado mal.

5. **Áudio como espinha dorsal (silêncio antes do reveal).** Sincronizar entradas visuais nas batidas da fala. **O silêncio visual antes de um reveal-chave vale mais que qualquer trilha** — segredo Apple. Em takes onde o Marcelo faz uma pausa respirando (>0.4s sem fala), deixar a tela quieta nesse intervalo (não enfiar animação preenchendo).

### Os 4 pilares da estética Apple/Linear/Vercel

- **Materialidade.** Não animamos UI chapada, animamos *matéria*. Vidro com refração, frosted glass que parece físico, sombras com peso, hairline edges que sugerem 1px real de borda. O cérebro lê "real" e o real prende mais que o digital chapado. (Por isso o Apple-clean usa frosted glass e não card preto sólido.)

- **Câmera cinemática com escala ativa.** Não é zoom-in chapado, mas TAMBÉM não é só "upward glide e fade" — tem que ter **movimento de câmera real**. Os 3 movimentos básicos a misturar em todo take:
  - **Push-in:** durante hold de um elemento, escala cresce sutilmente (1.0 → 1.04) por 1-2s — como se a câmera estivesse se aproximando. Sustenta interesse sem novo elemento.
  - **Pull-out:** ao sair, elemento encolhe (1.0 → 0.92) + slip out of focus simultâneo. Não é só fade chapado — é a câmera se afastando.
  - **Emphasis hit:** em palavra-âncora (asterisco) ou número-chave, breve scale-up rápido (1.0 → 1.08 → 1.0 em 400ms) — pulse curto que marca o beat.
  - **Parallax drift idle:** todos os elementos parados oscilam levemente (2-3% em X/Y) — câmera nunca trava 100%, sempre uma respiração mínima.
  No prompt descrever assim: "the headline holds in place with a slow gentle push-in, scaling up subtly as if the camera is approaching" / "card exits by slipping backward into soft focus, shrinking slightly as it goes" / "a brief emphasis pulse hits the asterisk as it lands". **Sem esses movimentos, vira motion-graphics chapado de Canva.**

- **Tipografia em movimento como ator + LEGENDA ANIMADA.** Texto não é só label de card — texto também é **kinetic typography da fala do Marcelo**. Princípio crítico: **palavras-âncora da fala dele aparecem como big text gigante no centro**, sincronizadas com a voz, word-by-word. Isso quebra a monotonia "card-ícone-card-ícone" e dá ritmo visual. Os 3 papéis da tipografia:
  - **Headline-âncora:** palavras-chave da fala (números, conceitos, verbos fortes) aparecem GIGANTES, dominando o frame, word-by-word com tracking respirando. Exemplos: "R$ 158.000*", "VENDENDO*", "INFOPRODUTOS", "30 DIAS*", "TEMPO".
  - **Label de card:** texto menor dentro de cards (categorias UPPERCASE como "MARKETING", "FUNIL", "PODCASTS").
  - **Subline contextual:** texto pequeno e dim abaixo dos elementos (ex: "criou esse infoproduto", "como ter acesso?").
  No prompt, **alternar entre estes 3 papéis** em cada take. Nunca um take inteiro só com cards-de-ícone — sempre intercalar com pelo menos UMA aparição de headline-âncora gigante sincronizada com a palavra que o Marcelo enfatiza.

- **Easing customizado, nunca linear.** Linear é morto. Apple usa ease-out longo (entra rápido, desacelera no fim). Linear/Vercel usam *spring physics* com leve overshoot. **Nunca animação linear.** No prompt, descrever como "slow confident glide that decelerates into rest" ou "soft settle with the subtlest overshoot, as if landing under its own weight".

### Visualização do invisível (3 metáforas pra IA/software)

Vídeo de IA tem um problema que vídeo de iPhone não tem: o produto é invisível. Não dá pra girar a IA em 360°. As 3 metáforas que estão funcionando nas referências (Linear, Claude reveals, OpenAI keynotes, Gleb Kuznetsov):

| Metáfora | Quando usar | Como descrever no prompt |
|---|---|---|
| **Partículas / líquido orgânico** | Conceito de "pensar", "processar", "fluido", "vivo" | "soft white particles drifting upward like dust in sunlight, coalescing into a shape" / "liquid metal-like surface settling into a card" |
| **Grids e nós conectando-se** | Estrutura, conhecimento, conexão de fontes | "thin hairline lines drawing themselves between dots one by one, forming a network constellation" |
| **Luz emergindo** | Output, resposta, insight, reveal final | "a soft bloom of warm white light expanding outward from a central point, then settling" |

**Regra:** ao animar conceitos abstratos (IA, clones, dados, inteligência, automação), preferir uma dessas 3 metáforas em vez de ícone hairline genérico. Ícones hairline são pra conceitos concretos (carrossel, site, app); metáforas materiais são pra abstratos.

### Anatomia do reel (mapa pra distribuir os takes)

Quando os takes formam um reel de 30–60s, distribuir a intensidade visual seguindo essa anatomia (não animar cada take com a mesma carga):

| Segmento | % do reel | Carga visual | O que acontece |
|---|---|---|---|
| **Hook** | 0–10% | Alta-densidade, um único elemento dominante | Headline-âncora grande (número, pergunta, frase-bomba) — materialidade no centro. Sem texto explicativo, deixa pergunta no ar. |
| **Contextualização** | 10–25% | Média, com respiração | Título/categoria entra, frosted card sustenta. Espectador "se localiza". |
| **Burst de features** | 25–60% | ALTA — cortes/cards rápidos, oscilação intensa | Sequência de cards/ícones revelando cada conceito. É o "show, don't tell". Pode ter 3-6 elementos por take aqui. |
| **Respiração** | 60–80% | BAIXA — um elemento só, lento | Take inteiro com 1 card, 1 frase. Espectador descansa, absorve. **É aqui que a venda emocional acontece.** |
| **Crescendo + CTA** | 80–100% | Alta novamente, mas com fechamento | Recap rápido (asterisco-âncora aparece de novo) + CTA grande com seta laranja. Última frame: silêncio, só o asterisco no centro. |

**Como aplicar:** ao gerar o prompt take-a-take, perguntar "em que segmento desse reel esse take cai?" e calibrar a carga. Take 1 não pode ter a mesma intensidade que take 4 do meio. Take final tem que ter silêncio visual.

---

## Fluxo

1. **Receber o path do vídeo** (Marcelo passa direto ou já tá no contexto). **Antes de processar**, se o vídeo ainda NÃO foi gravado, recomendar o LAYOUT primeiro (ver Etapa 0 abaixo) — assim Marcelo grava já no formato certo.
2. **Validar o arquivo** existe e é um vídeo válido + medir duração
3. **Criar a pasta de trabalho** `conteudo/YYYY-MM-DD-gemini-omni-{slug}/` com subpastas `source/`, `takes/`, `prompts/`
4. **Extrair áudio + transcrever** com Whisper (modelo `small`, idioma `pt`, output JSON pra ter segmentos com timestamps)
5. **Decidir splits**: se duração ≤10s, take único. Senão, agrupar segmentos do Whisper em chunks ≤10s respeitando fim de frase
6. **Cortar os takes** com ffmpeg (re-encode pra cut frame-accurate) e salvar em `takes/take-NN_Xs-Ys.mp4`
7. **Extrair 3 frames de referência** do vídeo original (início, meio, fim) pra entender o cenário
8. **Perguntar o MODO DE EDIÇÃO** via AskUserQuestion (Manual / Edição Livre) — ver Etapa 7.5 abaixo
9. **Se Manual:** perguntar LAYOUT (Etapa 8) + ESTILO (Etapa 9) como sempre
   **Se Edição Livre:** Claude analisa transcrição + frames + contexto, propõe plano completo customizado, Marcelo aprova/ajusta em texto livre, prompts variam entre takes
10. **Montar 1 prompt por take** seguindo o plano (LAYOUT + ESTILO do Manual OU plano customizado da Edição Livre), com:
   - Timecodes **relativos ao take** (0:00 = início do clip, não do original)
   - **Posição do take na anatomia do reel** (hook / contextualização / burst / respiração / CTA?) → calibrar a carga visual (não animar tudo com a mesma intensidade — ver seção "Anatomia do reel")
   - Animação por conceito consultando "Mapeamento conceito → animação". **Conceito abstrato** (IA, clones, inteligência, processamento) → usar metáfora material (partículas, grids, luz), **nunca ícone hairline genérico**
   - **Pausa do Marcelo no áudio** (>0.4s sem fala dentro do take) → inserir "hold the current card silent and still during this pause" no shot. Silêncio visual antes de reveal vale mais que animação contínua
   - Branding consistente (cores, tipografia, easing — laranja é beat marker, não decoração)
   - Linha CRITICAL preservando o áudio PT-BR
11. **Salvar README + prompts** na pasta, estrutura detalhada na Etapa 11 abaixo
12. **Apendar em `log.md`** entrada de ingest com link pra pasta
13. **(Etapa final — em construção)** Abrir o Gemini Omni via Playwright MCP, fazer upload de cada take, colar o prompt e baixar o resultado. Por enquanto, deixar o Marcelo fazer manualmente

---

## Etapa 1-2: Validar vídeo

```bash
ls -la "$VIDEO_PATH" && ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_PATH"
```

Guardar a duração em segundos (float). Não há limite superior — qualquer vídeo será fatiado em takes ≤10s.

## Etapa 3: Criar pasta de trabalho

```bash
SLUG="{3-5 palavras kebab-case do tema}"
DATE=$(date +%Y-%m-%d)
WORKDIR="~/seu-vault/conteudo/${DATE}-gemini-omni-${SLUG}"
mkdir -p "$WORKDIR/source" "$WORKDIR/takes" "$WORKDIR/prompts" "$WORKDIR/frames"
cp "$VIDEO_PATH" "$WORKDIR/source/original.mp4"
```

A partir daqui, `$WORKDIR/source/original.mp4` é a fonte canônica.

## Etapa 4: Transcrever com timestamps

```bash
ffmpeg -y -i "$WORKDIR/source/original.mp4" -vn -acodec libmp3lame -q:a 4 "$WORKDIR/source/audio.mp3"
whisper "$WORKDIR/source/audio.mp3" --model small --language pt --output_dir "$WORKDIR/source" --output_format json
```

O JSON gerado em `$WORKDIR/source/audio.json` tem `segments[]` com `{start, end, text}` por frase. **Esses segments são a base do split** — corte sempre entre segments, nunca no meio de um.

## Etapa 5: Decidir splits (≤10s por take, cortando em fim de frase)

Algoritmo:
1. Se duração total ≤10s → 1 take só, pula split (copia original pra `takes/take-01_0s-{DUR}s.mp4`)
2. Senão, iterar pelos segments do Whisper agrupando:
   - Acumular segments enquanto `(segment.end - take_start) ≤ 10.0`
   - Quando o próximo segment estouraria 10s, fechar o take atual com `take_end = último_segment.end` e começar novo com `take_start = next_segment.start`
3. Edge case: segment único >10s → forçar cut em 10s exatos (raro, só se Marcelo falar 10s sem respirar)
4. Resultado: lista de tuplas `[(start_0, end_0), (start_1, end_1), ...]` em segundos float

Salvar essa lista em `$WORKDIR/source/splits.json` pra rastreabilidade.

## Etapa 6: Cortar os takes (frame-accurate)

Pra cada `(start, end)` da lista, índice `NN` (zero-padded a 2 dígitos):

```bash
ffmpeg -y -ss "$START" -to "$END" -i "$WORKDIR/source/original.mp4" \
  -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k \
  "$WORKDIR/takes/take-${NN}_${START_INT}s-${END_INT}s.mp4"
```

Naming convention: `take-01_0s-10s.mp4`, `take-02_10s-19s.mp4`, etc. — números inteiros arredondados pra baixo no start e pra cima no end, pra leitura humana. O timestamp exato fica em `splits.json`.

**Por que re-encode em vez de `-c copy`:** `-c copy` só corta em keyframes, então o início do clip pode pular até 2s do que você pediu. Re-encode (CRF 18, fast preset) é frame-accurate e fica visualmente lossless.

## Etapa 7: Extrair frames de referência

```bash
ffmpeg -y -i "$WORKDIR/source/original.mp4" -vf "fps=1" "$WORKDIR/frames/frame_%02d.jpg"
```

Ler frame_01 (início), o do meio (~metade da duração) e o último. Identificar:
- Posição do Marcelo no frame (geralmente direita em vertical)
- Cor da parede / iluminação ambiente
- Elementos visuais que NÃO devem ser cobertos (rosto, monitor com código demonstrativo, etc.)

Essas observações se aplicam a TODOS os takes (mesmo cenário) — descrever uma vez e reutilizar em cada prompt.

## Etapa 7.5: Perguntar o MODO DE EDIÇÃO

**Esta é a PRIMEIRA pergunta** — vem antes de tudo o mais. Define se Marcelo escolhe layout+estilo manualmente OU se a IA propõe o plano completo baseado no conteúdo do vídeo.

Usar AskUserQuestion com 2 opções:

```
{
  "question": "Como você quer editar?",
  "header": "Modo de edição",
  "options": [
    {"label": "Manual (Recomendado pra estilo conhecido)", "description": "Você escolhe LAYOUT (Split-screen / Overlay / Motion-only) e ESTILO (8 opções disponíveis) nas próximas perguntas. Controle granular total, fluxo previsível."},
    {"label": "Edição Livre (IA propõe o plano)", "description": "Claude analisa transcrição + frames + tom + público + tema, propõe LAYOUT + ESTILO + variações por take + paleta + tipografia. Você só aprova ou ajusta em linguagem natural. Pode quebrar padrões do catálogo e variar entre takes (T1 contemplativo, T3 burst denso). Mais lento mas pode surpreender pra cima."}
  ]
}
```

### Se Marcelo escolher MANUAL

Seguir para Etapa 8 (LAYOUT) → Etapa 9 (ESTILO) → Etapa 10 (montar prompts) como sempre.

### Se Marcelo escolher EDIÇÃO LIVRE

Pular Etapas 8 e 9 (não perguntar mais nada). Em vez disso, executar:

#### 7.5.a: Análise do conteúdo

Ler com cuidado:
- **Transcrição completa** (`$WORKDIR/source/audio.json` — segmentos com timestamps)
- **Frames de referência** (`$WORKDIR/frames/frame_*.jpg`) — visualizar pra entender cenário, energia, enquadramento
- **Contexto do vault** (`CLAUDE.md` raiz) — conteúdo atual do Marcelo, deals ativos, brand context se for vídeo de marca específica
- **Características do reel** (duração, número de takes, ritmo da fala)

Identificar 5 dimensões:

| Dimensão | Valores possíveis |
|---|---|
| **Tom** | didático, manifesto, venda, narração, conversa íntima, anúncio institucional, casual/bastidor |
| **Público** | devs (Claude Code), empresários (CODA/MGTInc), audiência geral, comunidade fechada |
| **Tema** | tech/IA, business, conteúdo educacional, lançamento de produto, opinião/pensamento |
| **Energia** | baixa-contemplativa, média-conversacional, alta-burst, oscilante |
| **Gravação** | full-frame Marcelo, top-half preto, áudio-only (regravado), close-up, plano aberto |

#### 7.5.b: Propor plano completo

Montar e mostrar pro Marcelo em formato editorial (NÃO usar AskUserQuestion — usar texto livre + perguntar "OK ou ajustar?" no fim):

```
## Plano de edição — {nome-do-reel}

**O que percebi:**
- Tom: {X}
- Público: {Y}
- Tema central: {Z}
- Energia geral: {W}
- Gravação: {Q}

**Proposta:**

🎬 **LAYOUT:** {Motion-only / Split-screen / Overlay}
  Por quê: {justificativa de 1 linha}

🎨 **ESTILO BASE:** {nome do estilo proposto, pode ser do catálogo ou customizado}
  - Background: {descrição}
  - Tipografia headline: {família + estilo}
  - Tipografia label: {família}
  - Accent color: {hex + nome humano}
  - Sparkle/asterisco: {sim/não + tipo}
  - Materialidade: {flat / frosted glass / paper / dark cards / etc}
  - Densidade visual: {low / medium / high}

🎞 **VARIAÇÕES POR TAKE:**
  - Take 1 ({tempo}): {anatomia + carga visual + observação específica}
  - Take 2 ({tempo}): ...
  - Take N: ...

🎵 **PACING:**
  - Como o áudio guia a animação (pausas, ênfases)
  - Onde o silêncio visual ganha valor

✨ **MOMENTOS-ÂNCORA** identificados na fala:
  - "{palavra-X}" no take {N} → tratamento {Y}
  - "{número Z}" no take {M} → headline gigante com sparkle

OK ou quer ajustar?
```

#### 7.5.c: Aprovar/Ajustar

Marcelo pode:
- Responder "OK" / "vamos" / "topa" → seguir pra Etapa 10 gerando prompts com o plano
- Pedir ajuste em texto livre ("muda a paleta pra mais escura", "deixa T3 mais cinético", "tira o sparkle, prefiro underline")
- Pedir refundição total ("não, esse vídeo é mais manifesto, dá uma vibe CODA Dark seca")

Iterar até aprovação. Cada iteração atualiza o plano e mostra novamente.

#### 7.5.d: Gerar prompts com plano customizado

Na Etapa 10, em vez de seguir um dos templates fixos de estilo, montar bloco STYLE + bloco MOTION em prosa natural usando as decisões do plano. Cada take pode ter densidade/animação ligeiramente diferentes (anatomia do reel real).

Manter SEMPRE:
- CRITICAL RULE 1 (áudio PT-BR sagrado)
- CRITICAL RULE 2 (sem metadata na tela)
- CRITICAL RULE 3 (sem retratos humanos)
- Timecodes relativos ao take
- Textos visuais em PT-BR
- Safe areas (top 12% + bottom 18%)

**Salvar o plano** em `$WORKDIR/source/plano-edicao.md` antes de gerar prompts — pra rastreabilidade e pra Marcelo poder revisar depois.

---

## Etapa 8: Perguntar o LAYOUT (modo Manual)

**Esta etapa SÓ roda se Marcelo escolheu MANUAL na Etapa 7.5.** No modo Edição Livre, o LAYOUT é proposto pela IA dentro do plano.

Layout define o framing do vídeo inteiro e tem implicações na GRAVAÇÃO. Se Marcelo mencionar que ainda não gravou, fazer esta pergunta IMEDIATAMENTE (antes de upload) pra ele já gravar no formato certo.

Usar AskUserQuestion com 3 opções:

```
{
  "question": "Qual o layout do vídeo final?",
  "header": "Layout",
  "options": [
    {"label": "Split-screen (Recomendado)", "description": "Tela dividida: motion graphics na metade superior, creator na inferior. Visualmente equilibrado e prende atenção. RECOMENDAÇÃO PRÉ-GRAVAÇÃO: grave com a câmera enquadrando o creator apenas na metade inferior do frame (top half preto sólido) — assim o Omni anima diretamente na zona vazia sem cobrir nada."},
    {"label": "Overlay sobre o creator", "description": "Motion graphics sobrepostos no frame inteiro com o creator. Mais difícil — exige safe areas em volta do rosto e do que está em foco. Recomendado APENAS pra vídeos curtos (<15s) onde o creator está num canto."},
    {"label": "Motion-only (sem creator)", "description": "Apenas motion graphics no vídeo final. O creator NÃO aparece — só o áudio dele passa como narrator. Estilo apresentação de IA/SaaS/empresa de tech (Apple keynote, OpenAI announcement, Linear launch). Mais trabalho de animação porque o frame inteiro precisa contar a história visual."}
  ]
}
```

### Implicações de cada layout no prompt

**LAYOUT A — Split-screen (motion top, creator bottom):**
- Bloco TASK: "Add motion graphics ONLY to the upper half of the frame. The bottom half contains the speaker and must remain completely untouched."
- LAYOUT block: top half = motion stage, bottom half = pass-through
- Se o vídeo NÃO tem top half preto (ou seja, full-frame com creator no centro), AVISAR Marcelo: oferecer adicionar letterbox preto via ffmpeg ou pedir re-gravação no formato certo
- Comando ffmpeg pra adicionar letterbox preto top (se necessário): `ffmpeg -i input.mp4 -vf "scale=1080:960,pad=1080:1920:0:960:black" output.mp4`

**LAYOUT B — Overlay sobre o creator:**
- Bloco TASK: "Add motion graphics composited OVER the speaker's footage. Maintain safe areas around the speaker's face and any visible gestures."
- LAYOUT block: identificar lado livre do frame (geralmente esquerdo ou superior) via análise dos frames de referência
- Aviso explícito no prompt: "Never cover the speaker's face or hands. The overlays sit primarily in the upper-third or left-third where the background is plainest."
- Safe area: top 12% + bottom 18% obrigatórios livres (zonas de UI do IG/TikTok)

**LAYOUT C — Motion-only (creator some):**
- Bloco TASK: "The speaker does NOT appear visually in the output. Only their audio is preserved (CRITICAL RULE 1). Generate full-frame motion graphics that tell the story visually based on the spoken script, occupying the entire 1080×1920 frame."
- LAYOUT block: full-frame motion stage, sem zonas reservadas
- Estilo tipicamente: Apple Keynote / OpenAI launch / Linear / Vercel announcement — mais espaço pra grandes headlines, hero shots, transições editoriais
- IMPORTANTE: como o creator não aparece, prompts precisam ter densidade visual MAIOR — o frame inteiro precisa contar a história, não só metade
- Pode usar full-frame hero shots, fullscreen headline anchors, transitions cinematográficas
- Quando aplicar bem: lançamentos de produto, anúncios institucionais, vídeos onde a fala é VOICE-OVER (creator não precisa estar no frame)

### Recomendação pré-gravação por layout

Se Marcelo ainda NÃO gravou, lembrar ele:
- **Layout A:** filmar com câmera na metade inferior, top half preto. Pode ser gravado já com letterbox (preset Filmic Pro / app de câmera com guides) ou processado pós com ffmpeg
- **Layout B:** filmar normalmente, ficar num dos lados do frame (não centralizado) pra deixar o outro lado livre pra overlays
- **Layout C:** gravar foco no ÁUDIO. Vídeo do creator nem precisa estar bem enquadrado — só o áudio será usado. Pode até gravar só áudio se preferir

## Etapa 9: Perguntar o estilo (modo Manual)

**Esta etapa SÓ roda se Marcelo escolheu MANUAL na Etapa 7.5.** No modo Edição Livre, o ESTILO foi proposto pela IA dentro do plano.

Usar AskUserQuestion com as 8 opções abaixo — mostrar todas de uma vez, Marcelo escolhe consciente:

```
{
  "question": "Qual estilo de motion quer pra esse vídeo?",
  "header": "Estilo",
  "options": [
    {"label": "Apple-clean", "description": "Frosted glass tátil, tipografia premium branca, câmera cinematic com push-in/pull-out, asterisco laranja como beat marker. Para: credibilidade institucional, lançamentos, conteúdo que precisa de autoridade tranquila."},
    {"label": "CODA Dark", "description": "Cards pretos sólidos com zero arredondamento, UPPERCASE bold, asterisco laranja como carimbo, snap rápido sem curvas. Para: manifestos, punchlines, opinião forte, conteúdo que confronta."},
    {"label": "Clone de Cérebro", "description": "Dark academia digital + Obsidian, serif editorial italic, asterisco roxo lavanda brushy, monospace em labels. Para: conteúdo sobre conhecimento, IA, estudos, pensamento profundo."},
    {"label": "Híbrido", "description": "Glass card (Apple) + UPPERCASE bold (CODA) + asterisco laranja. Meio termo: premium e assertivo ao mesmo tempo. Para: conteúdo de negócios que precisa de presença sem ser frio."},
    {"label": "Linear / Vercel", "description": "Developer-tool aesthetic ultra-minimal, dark desaturated, cards só como hairline border, monospace em labels, acento elétrico (azul ou lime), cursor piscando antes do reveal. Para: tech, IA, produto SaaS, devs."},
    {"label": "Editorial Magazine", "description": "Print animado: tipografia grande como capa de Wired, réguas editoriais, paleta de tinta (uma cor de acento tipo vermelho-profundo ou verde-floresta), reveal por máscara (texto desencobre em vez de aparecer). Para: opinião forte, storytelling, conteúdo que quer parecer longform."},
    {"label": "Liquid Organic", "description": "Formas biomorphicas que respiram, fundo warm charcoal, transições de morph fluido, cores de pigmento orgânico (ocre, âmbar, sienna). Animações crescem como matéria viva. Para: criatividade, flow, conteúdo sobre processo e transformação."},
    {"label": "Brutalist", "description": "Zero polish, raw, tipografia oversized que corta as bordas do frame, hard cuts, flash invertido nos beats fortes, réguas grossas, zero suavidade. Para: manifestos radicais, opinião que choca, conteúdo de alto contraste emocional."}
  ]
}
```

**Importante:** NÃO inferir o estilo baseado no conteúdo do vídeo, nome do produto mencionado, ou contexto da campanha. Sempre perguntar e deixar Marcelo decidir. Estilo é escolha editorial dele, não derivação automática.

## Etapa 10: Montar o prompt (1 por take)

**Crítico:** os timecodes do prompt são **relativos ao take** (0:00 = início daquele clip), não ao vídeo original. Antes de montar cada prompt, subtrair `take_start` dos timestamps do Whisper.

**Importante:** o prompt mistura LAYOUT (Etapa 8) + ESTILO (Etapa 9). O LAYOUT define o bloco TASK + LAYOUT do template. O ESTILO define os blocos VISUAL e MOTION.

Exemplo: se um segment original é `[12.3s → 14.1s]` e o take começa em `10s`, no prompt vira `[2.3s → 4.1s]`.

### ⚠️ REGRAS CRÍTICAS — Bugs e filtros confirmados do Gemini Omni

#### Bug 1: vazamento de metadata como texto na tela (2026-05-27)
Quando o prompt continha specs técnicas como "16px", "88px SF Pro Display", "1.5px stroke", "600ms cubic-bezier", "rgba(255,255,255,0.06)" dentro dos shot-by-shots, o Omni renderizou esses strings COMO TEXTO VISÍVEL na animação (apareceram literais nos cards).

**Solução obrigatória em todo prompt:**

1. **CRITICAL RULE 2** logo no topo do prompt, proibindo render de qualquer metadata técnica (px, ms, hex codes, nomes de fontes, easing names, fps, stroke widths, rgba(...)).
2. **Shots descritos em prosa natural**, sem números. Em vez de "88px SF Pro Display 700", escrever "large white sans-serif text". Em vez de "600ms cubic-bezier(0.22,1,0.36,1)", escrever "slow confident upward glide".
3. **Texto pra renderizar SEMPRE entre aspas** — instrução clara que só o que está em quotes deve aparecer na tela.
4. **Estilo descrito qualitativamente**, não em CSS. "Soft rounded corners" em vez de "border-radius: 16px". "Vivid pure orange accent" em vez de "#FF5000".

#### Bug 2: filtro de políticas dispara com retratos de pessoas públicas (2026-05-27)
Quando o prompt do take 2 mencionou "head silhouette icon" + nomes "HORMOZI / BRUNSON / STEVE JOBS", o Omni recusou com "Esta geração pode violar nossas políticas". Combinação silhueta humana + nome de figura pública real = trigger de policy.

**Solução obrigatória quando o vídeo mencionar nomes de pessoas reais:**

1. **CRITICAL RULE 3 — TEXT ONLY, NO PORTRAITS** no topo do prompt: proibir explicitamente geração de "human silhouettes, portrait outlines, avatar icons, or any depiction of a person".
2. **Nomes viram tipografia pura** — cards com APENAS texto centralizado, sem nenhuma figura humana. Como um directory listing ou credit roll.
3. **Se ainda assim falhar**: usar SÓ sobrenome ("JOBS" em vez de "STEVE JOBS") ou referência indireta ("DESIGN ICON", "MARKETING GURU").
4. A regra ajuda mesmo quando o vídeo NÃO tem nomes — fica como guardrail de segurança barato.

### Template ESQUELETO (todos os estilos compartilham — varia o bloco TASK + LAYOUT por layout escolhido)

```
CRITICAL RULE 1 — AUDIO: Do not transcribe, translate, regenerate, dub, or modify the audio in any way. The original Brazilian Portuguese voiceover must be passed through byte-for-byte to the output. Only the visual layer receives new content.

CRITICAL RULE 2 — NO METADATA ON SCREEN: This prompt contains internal styling notes. Under no circumstances should any of the following appear as visible text in the output video: pixel sizes (e.g. "16px", "88px"), font weights or family names (e.g. "SF Pro Display", "Bold 700"), color codes (e.g. "#FF5000", "rgba(...)"), easing curve names (e.g. "cubic-bezier", "ease-out"), durations (e.g. "600ms", "30fps"), stroke widths (e.g. "1.5px"), or any other technical specification. ONLY render text that is explicitly placed inside quotation marks in the SHOTS section below.

{BLOCO_TASK_LAYOUT_ESPECÍFICO — varia por escolha do LAYOUT na Etapa 8, ver abaixo}

{BLOCO_VISUAL_DO_ESTILO_EM_PROSA}

{BLOCO_MOTION_DO_ESTILO_EM_PROSA}

SHOTS — render only the text shown in quotation marks below. Times are relative to this clip's 0:00.

{PARA_CADA_FRASE: SHOT X — start to end
  Descrição da animação em prosa natural, sem números/specs.
  Texto a renderizar SEMPRE entre aspas duplas.}

GLOBAL RULES:
- {ZONAS_INTOCAVEIS_DO_LAYOUT}
- Text language: Portuguese (PT-BR), exactly as written in quotes.
- Audio: do not modify.
- Output: single MP4, vertical 9:16, original as base layer (or fully replaced for Motion-only), overlays composited per LAYOUT rules.
```

### Bloco TASK + LAYOUT — por layout escolhido

**LAYOUT A — Split-screen (motion top, creator bottom):**
```
TASK: Add motion graphics to the upper half of this {DURATION}-second vertical (9:16) clip. The footage already has a SOLID BLACK upper half (the top portion of the frame is pure black) and the speaker is composited in the lower half. ALL motion graphics live in the upper black half only. The lower half — including the speaker, his clothing, the background, and any visible elements — must remain completely untouched.

LAYOUT:
- Top half of frame: motion stage. All overlays live here.
- Bottom half of frame: speaker untouched. Pass through as-is.

GLOBAL RULES additions:
- Do not place anything in the lower half of the frame. The speaker stays pristine.
```

**LAYOUT B — Overlay sobre o creator:**
```
TASK: Add motion graphics composited OVER this {DURATION}-second vertical (9:16) clip. The speaker is in the frame and visible — motion graphics overlay ON TOP of the footage without covering the speaker's face, hands, or any gestures.

LAYOUT:
- Speaker is positioned at the {LADO_DO_FRAME — to be filled by analyzing frame_01.jpg} of the frame.
- Motion stage: the opposite side and any plain background area. Headlines occupy the upper portion when the speaker is in the lower portion, or the side opposite the speaker.
- Safe area for IG/TikTok UI: keep top 12% and bottom 18% free of critical text.

GLOBAL RULES additions:
- Never cover the speaker's face, hands, or visible gestures.
- Overlays primarily sit in the plainest background areas (e.g. wall, sky, blurred space).
- Use semi-transparent frosted glass cards (slightly more opaque than usual) so backgrounded footage doesn't compete with text.
```

**LAYOUT C — Motion-only (creator some):**
```
TASK: The speaker does NOT appear visually in the output of this {DURATION}-second vertical (9:16) clip. Only the audio (their voice) is preserved per CRITICAL RULE 1. Replace the entire video frame with full-frame motion graphics that tell the story visually based on the spoken script. The output is a pure motion graphics piece narrated by the speaker's voice — like an Apple keynote slide, an OpenAI launch announcement, or a Linear product reveal.

LAYOUT:
- Full frame: motion stage. Use the entire 1080×1920 canvas.
- No speaker, no source footage visible. The original video is discarded as the visual base; only its audio track is retained.
- Hero shots, fullscreen headline anchors, and cinematic editorial transitions are encouraged — the frame inside is fully yours.
- Background: dark near-black with subtle radial gradient or deep solid black, depending on style.

GLOBAL RULES additions:
- The speaker does not appear visually at any point.
- Audio remains byte-for-byte intact (CRITICAL RULE 1) — this is non-negotiable.
- Treat each take as a slide in a premium tech keynote: one dominant element at a time, with cinematic transitions between them.
- Density should be HIGHER than split-screen layout since the entire frame is yours to compose.
```

---

## Blocos de Estilo — VISUAL + MOTION

> **Regra universal:** specs numéricas (px, ms, hex codes, nomes de fonte) ficam APENAS nesta documentação como referência. Nunca entram no prompt enviado ao Omni — causam o Bug 1 de metadata.

---

### Estilo 1 — Apple-clean

#### Bloco VISUAL

```
Style: Apple-keynote minimalism with deep tactile materiality — the goal is not "clean UI", it is the feeling of physical objects existing in a lit space. Cards are dark frosted glass: imagine a thin pane of darkened glass with microscopic surface texture, a hairline white edge that catches light like a real material seam, and a weighted drop shadow that places the card precisely two or three millimeters above whatever is behind it. The glass is not uniformly dark — it has the faintest warm tint at the center and cools very slightly toward the edges, like glass held up to a dim lamp. Very soft rounded corners, never sharp. Text is clean modern white sans-serif throughout: headline anchors are large and dominant in sentence case; category labels are smaller and uppercase; sublines are dim and fine, barely above invisible. Typography behaves as a physical actor: each word carries its own weight and arrives with intention. Letter-tracking on headline reveals breathes — slightly compressed on entry, exhaling outward to final spacing as the word settles, as if the letters need a moment to find their place. The only accent color is vivid pure orange — used SOLELY for the asterisk character (*) that follows key words and for a single thin underline under a single emphasized phrase per take. Orange must not fill words, must not appear on more than one element at a time, must not be used as decoration. It is a narrative beat marker. Icons are pure white hairline outlines — zero fill, zero glow, zero color. Backgrounded elements (cards that were in focus and are now exiting) carry a soft depth-of-field blur, as if a cinematic lens is pulling focus forward to the incoming element. The overall feeling: something real, physical, and expensive, lit by a photographer who understands negative space.
```

#### Bloco MOTION

```
Motion: Slow, confident, deeply cinematic — directed as if a real camera operator is controlling every element. Nothing moves at constant speed; everything has a natural physics that suggests mass. Cards and headlines enter with a soft upward glide that decelerates dramatically into rest — the element rushes in with energy and then settles with the inevitability of something finding its exact gravitational home. NEVER linear motion on any element. While an element holds on screen, it carries a continuous slow push-in: the card scales up by the smallest perceptible amount over one or two seconds, as if the camera is slowly leaning in to read it. This push-in is never obvious — if you can easily see it happening, it is too much. When an element exits, it reverses into a pull-out: it recedes and slips into soft depth-of-field blur simultaneously, shrinking slightly as it goes — the camera moving away, losing interest, refocusing on what comes next. On key beats — when an asterisk lands, when a number is spoken with emphasis, when an anchor word arrives — a brief emphasis pulse hits the element: a quick scale up of a few percent and an immediate, confident settle. It lands like a soft stamp. Idle elements carry a barely-perceptible parallax drift, oscillating a few pixels in X and Y — the camera is never fully locked, always breathing. Word-by-word reveals: each word arrives with a small upward offset and settles with ease-out deceleration, staggered from the previous word by a tight interval. Giant headline-anchor moments — where the speaker's key word dominates the frame in large text — should appear at least once per take, fully synchronized with the spoken word, held for the exact duration of the speaker's emphasis. Critical pacing rule: when the speaker pauses or inhales between sentences, the visual layer STOPS completely — hold the current state without any motion, without parallax, without animation. The silence before the next reveal is more valuable than any animation that could fill it. No bouncy spring physics. No whip pans. No pop-in. Subtle motion blur on all moving elements.
```

> **Specs de referência pra reprodução manual (After Effects):** corner radius 16px, easing cubic-bezier(0.22,1,0.36,1), duração 600ms, accent #FF5000, hairline stroke 1.5px, SF Pro Display 600-700.

---

### Estilo 2 — CODA Dark

#### Bloco VISUAL

```
Style: Confrontational editorial minimalism — the aesthetic of a cult manifesto printed on matte black paper, not a product advertisement. Cards are pure flat black with perfectly sharp corners: zero rounding, zero glass, zero softness, zero gradients. This is intentional — the sharpness is the design. Typography is exclusively heavy bold uppercase sans-serif: wide letter-tracking, tight leading, each word filling the card with the authority of a declaration. Text is white on black. There is one and only one color accent permitted: vivid pure orange. This orange appears as the signature asterisk (*) after every headline keyword — landing like a stamp, a certification mark, the period at the end of a sentence that means it. It may also appear as a thin horizontal rule separating elements. Never more than one orange element visible at once. Never orange filling a word or coloring background — it hits like a single mark, then the frame returns to black and white. Icon strokes are orange, not white — thin, geometric, with sharp terminations and no curves. No transparency anywhere. No frosted glass. No particle effects. No subtle textures. Every element is either completely present or completely absent, with no gradations between. Drop shadows are opaque and deep, not soft — they suggest real physical weight, not digital UI. The aesthetic declares: this is a fact, rendered without apology.
```

#### Bloco MOTION

```
Motion: Decisive, percussive, editorial — every movement is purposeful and stops the instant it arrives. No easing curves that trail off gently. Cards and headlines do not float; they snap into position with controlled velocity and halt immediately, like a stamp meeting a surface. The rhythm is: silence — hit — hold — silence — hit — hold. Think of a physical typewriter carriage snapping to a new position, or a court gavel coming down: fast approach, instant contact, total stillness. Headlines enter word-by-word in rapid tight stagger — each word arrives in a handful of frames and lands, then the complete phrase holds completely still. During hold, a minimal push-in drifts the flat card very slightly toward the viewer — barely perceptible, as if a camera is leaning in to read the text with gravity. On exit: a direct cut to black or a rapid downward slip — no fade, no blur, no softening. The orange asterisk does not fade in; it appears on a single frame, stamped. On major anchor words or peak emphasis moments, the frame flashes to inverted colors for two or three frames — a visual stutter, a photocopier glitch, a moment of intensity. Thick horizontal rules draw themselves across the frame in one fast horizontal stroke, instantly. Transitions between takes: hard cut to black for a brief beat — a breath, a punctuation mark — before the next element arrives. No dissolves. No smooth crossfades. No continuous motion filling dead air. When the speaker pauses, the visual freezes completely: total stillness, no parallax. The silence IS the design. The overall feeling: a poster coming to life, not a film.
```

> **Specs de referência pra reprodução manual (After Effects):** fundo puro preto, zero border-radius, Space Grotesk Bold 700, tracking -0.02em, accent #FF5000, icon stroke 2px orange, shadow 0 12px 32px black opaco.

---

### Estilo 3 — Clone de Cérebro

#### Bloco VISUAL

```
Style: Dark academia digital meeting a living knowledge graph — this is what Obsidian would look like if it were a film studio. Cards are deep near-black surfaces with a cool, almost imperceptible blue undertone — never pure black, never warm, the specific temperature of a library at night. The surface has a barely-visible noise texture, like matte paper or aged vellum, giving the impression of something physical rather than a screen. Card edges are hairline thin, slightly off-white (cooled toward silver), suggesting a physical edge catching a dim desk lamp. Three typographic voices coexist in every take: (1) HEADLINE-ANCHORS use a classical editorial serif — italic-capable, manuscript-weight, the letterforms you would find on the cover of an old Wired issue or a Penguin Classic hardcover; these headlines are large, dominant, and italic when the word carries emotional weight. (2) CARD LABELS and SUBLINES use a clean modern sans-serif at smaller scale. (3) Microcopy, timestamps, and bracket-labels use a monospace typewriter-style typeface — appearing as if typed directly into a terminal or an Obsidian note, sometimes with double-bracket notation like [[ ]] around key terms. The only accent color is soft lavender purple — not neon, not electric, not blue-shifted: a calm, aged purple like a pressed violet or a faded ink stamp. This purple appears solely on the asterisk (*) and occasionally as a thin underline under a single phrase. The asterisks themselves have a hand-drawn, slightly imprecise quality — as if the asterisk were an ink stroke made by a real pen, not a geometric vector. Purple is a thought marker, not decoration. Icons are clean hairline outlines in soft off-white, never pure white, never filled. Background elements blur into soft depth-of-field as new elements come forward. The composition carries generous negative space and editorial hierarchy — it feels like something a thoughtful human laid out by hand, not generated by a template.
```

#### Bloco MOTION

```
Motion: Slow, contemplative, scholarly — like a documentary camera observing someone thinking, not a product demo showing features. Every movement has the quality of consideration: nothing rushes, nothing snaps, nothing demands. Cards and headlines enter with a soft upward glide that decelerates long and gently into rest, as if the element is settling onto a reading surface. During hold, each card carries a slow push-in — the camera drifting closer to examine the text, as if leaning in to read a handwritten note. On exit, elements pull back and slip into soft focus blur, the camera retreating respectfully. The classical serif headline letters reveal with letter tracking that begins slightly compressed and breathes outward to final spacing as the word settles — the letters exhaling, as if the word is being said aloud slowly and considered by the speaker. The brushy lavender asterisk arrives with a soft bloom from its center — not a mechanical appear, but an organic emergence, like ink spreading on paper — and lands distinct from the final word of the phrase, a thought marker punctuating the idea. The monospace bracket labels type themselves in at reading pace, as if being entered live into a terminal. Icon strokes draw themselves via animated path — lines forming like a careful hand drawing with ink, never popping in complete. Kinetic typography mixes with cards throughout each take: anchor words from the speaker's speech appear as giant serif italic headlines dominating the frame, sometimes completely alone — let the word breathe and hold by itself before adding anything else. Never let a take consist only of icon-cards without at least one large headline-anchor moment. Critical pacing rule: when the speaker pauses or inhales, the visual stops entirely — hold perfectly still. The stillness is where thought lives. The overall feeling: studying something important, alone, late at night.
```

> **Specs de referência pra reprodução manual (After Effects):** fundo `#0a0a0b`, surface `#131316`, accent `#a78bfa` (lavanda) / `#7c3aed` (CTAs), display Instrument Serif (regular + italic), body Inter, mono JetBrains Mono. Asterisco brushy stroke (não geometric perfect). Zero neon glow no roxo.

---

### Estilo 4 — Híbrido

#### Bloco VISUAL

```
Style: The institutional middle ground — premium without being cold, assertive without being raw. This style borrows material quality from Apple-clean and typographic directness from CODA Dark, fusing them into something that works for business content that needs both credibility and presence. Cards use subtle dark frosted glass with gentle soft-rounded corners — darker and less transparent than Apple-clean (closer to a tinted window than a clear glass), but not the pure opaque black of CODA. The glass surface carries a hairline white edge and a soft weighted shadow. Typography switches register: headlines and category labels are bold uppercase sans-serif (the CODA voice — assertive, filling the card with intention), while sublines and supporting text are lowercase clean sans-serif (the Apple voice — considered, human). The orange asterisk (*) follows every key headline word, landing like a seal of authority. The asterisk is fully geometric here — no brushy texture, clean and precise. Background uses near-black with the faintest radial glow from the center, suggesting depth without being a gradient. White text throughout. Icons are white hairline outlines, slightly geometric, clean. The composition is grid-aligned and confident — less meditative than Apple-clean, less confrontational than CODA, but equally intentional.
```

#### Bloco MOTION

```
Motion: Sits precisely between Apple-clean's cinematic breathing and CODA Dark's editorial snap — the rhythm of a well-rehearsed keynote speaker who is both premium and efficient. Cards enter with a medium-speed ease-out glide, decelerating into rest with confidence but arriving more briskly than Apple-clean — there is urgency here, not just presence. Headline words reveal with tight stagger, each word arriving with a small upward offset and a clean ease-out that feels decisive. During hold, the push-in is moderate and legible — more pronounced than Apple-clean's whisper of movement, clearly intentional, as if the camera is leaning in with purpose. The orange asterisk lands with a brief clean emphasis pulse: a fast scale-up and immediate settle that functions as a visual beat marker, never lingering. On exit: a clean fade combined with a gentle, slightly quick retraction — faster than Apple-clean, without the abruptness of CODA's hard cut. Transitions carry a consistent editorial cadence: elements arrive in sequence with a steady rhythm, like sentences being read aloud by someone who knows exactly what they are saying. When the speaker pauses, the visual holds — current card locked, no parallax, no motion. The silence reads as confidence, not awkwardness. No spring bounce. No whip transitions. The overall feeling: a founder presenting to investors — prepared, authoritative, human.
```

> **Specs de referência pra reprodução manual (After Effects):** glass surface ~70% opacity (darker than Apple-clean), corner radius 10px, Space Grotesk Bold para headlines, Inter para sublines, accent #FF5000, easing ~500ms (entre Apple 600ms e CODA snap de ~200ms).

---

### Estilo 5 — Linear / Vercel

#### Bloco VISUAL

```
Style: Developer-tool aesthetic at its most refined — the visual language of Linear, Vercel, Arc, and Raycast. The background is a very deep, slightly desaturated dark (not pure black — imagine the darkest possible charcoal with a whisper of cool blue-grey, the color of a monitor room at 3am). It carries an extremely subtle noise texture, like matte paper viewed from a distance — the surface breathes slightly without any visible pattern. Cards in this style are defined NOT by their fill but by their outline: a single hairline border at very low opacity is the entire card. The card interior is nearly fully transparent — you see almost nothing except the thin edge, as if the card were drawn in air. This transparency collapses the hierarchy of "card then text" into just "text, precisely placed". Typography is clean modern sans-serif for headlines, with generous tracking and a light-to-regular weight — never heavy. Category labels and secondary information use a monospace typeface, rendering as if output from a terminal or IDE. Small bracket notation [ ] appears around metadata and category tags. The only accent color is a single cool electric tone — either a sharp electric blue or a bright lime green, chosen once per video and never mixed. This accent appears on: the asterisk (*) or cursor element marking beats; a single underline drawing beneath an anchor phrase; and on icon strokes. White text hierarchy: primary in full white, secondary at sixty or seventy percent opacity, tertiary at thirty percent — creating three legible tonal layers. Icons are surgical hairline outlines, minimal, precise. No frosted glass. No warm tones. No gradients. No decoration. The composition feels like a well-architected dashboard: every element justifies its presence by doing something specific.
```

#### Bloco MOTION

```
Motion: Engineered precision — animations feel built by someone who deeply understands timing, not someone chasing trends. Every movement has a clear job and stops doing that job the instant it is finished. Elements enter with a fast ease-out and settle with the subtlest spring overshoot — the element snaps to its grid position and micro-rebounds by one or two pixels, then locks. This overshoot reads as "found its exact place", not as "bouncing". Text reveals begin with a blinking monospace cursor at the text start position — the cursor pulses once or twice before the text types itself in at reading pace, letter by letter, as if being generated live. On anchor words and key beats, a horizontal accent-color underline draws itself left-to-right beneath the text in a single clean stroke — not a fade-in, a draw. The stroke arrives at the speed of a confident pen. During hold: a barely-perceptible horizontal scan-line drift along the card's hairline border — the edge luminosity pulses very gently, suggesting active state. Push-in exists but is minimal — this aesthetic prizes stillness and precision over cinematic movement. Transitions: horizontal wipe or direct hard cut — never diagonal, never radial, never circular. When the speaker pauses, the visual freezes: cursor stops blinking, all motion ceases. No parallax drift during silence. Crossfades are neutral and quick — one element fading out as the next is already arriving. The overall feeling: a product demo built by engineers who care about craft, not a brand spot.
```

> **Specs de referência pra reprodução manual (After Effects):** fundo `#0d0d10`, card border 1px `rgba(255,255,255,0.12)`, accent azul `#3b82f6` ou lime `#84cc16` (escolher um), headline Inter Light/Regular, mono JetBrains Mono, cursor blink 500ms interval.

---

### Estilo 6 — Editorial Magazine

#### Bloco VISUAL

```
Style: Print editorial translated into motion — the visual sensibility of Wired, NYT Magazine, or Eye magazine, as if a page learned to move. The background alternates between two states depending on the take's role in the reel: a warm off-white (paper tone, not digital white — the specific off-white of a high-quality matte stock) for contextual or contemplative takes, and a deep rich charcoal for high-emphasis or anchor takes. This binary print contrast system is used deliberately, never randomly. Typography is the central design element — everything else serves it. Two voices: (1) a large expressive editorial serif for headline-anchors — the kind of letterform on a magazine cover, italic-capable, with visible optical adjustments at large size, the letters feeling hand-crafted; (2) a tight condensed uppercase sans-serif for category labels, pull-quotes, and secondary information — compressed, newspaper-style, the text equivalent of a caption below a photograph. Accent is used as printer's ink: a single deep spot color per video (deep editorial red, forest green, cobalt, or deep gold — chosen to feel like an ink run, not a UI color). This accent appears on: thick horizontal rules dividing content zones; the initial capital of a section title; a single category label per take. No glass surfaces. No transparency. No particle effects. No gradients. Rules and borders are used as editorial devices: thick horizontal separators, thin vertical margins, framing boxes around pull-quotes. The composition feels typeset by a human editor — not generated, not templated, not algorithmic.
```

#### Bloco MOTION

```
Motion: Editorial pacing — weighted, narrative, deliberate. Elements in this style do not arrive, they are revealed. The central motion technique is mask-based uncovering: a horizontal wipe moves across the frame exposing text that was always present but hidden, as if a sheet of paper is sliding away to reveal what was printed underneath. This uncovering moves at reading pace — not slow, not rushed, the speed at which you would read the revealed text. Thick horizontal accent rules draw themselves left-to-right in a single confident stroke, arriving edge-to-edge as if a ruling pen swept across the page. The initial capital of section headers arrives with a brief ink-drop bloom — a radial expansion from the letter center settling to final size, like ink spreading on absorbent paper. Pull-quotes and supporting text rise into frame with a slow, deliberate upward travel — not a glide, more like a page scrolling up. Editorial serif headlines are uncovered word by word with the mask technique rather than appearing: the reveal speed matches the speaker's natural reading pace of those words. During hold: no push-in, no parallax. This aesthetic values the stillness of a page. The camera does not move — you are reading, not watching a film. Transitions between elements are clean quick cuts or direct fade-outs — like turning a page. When the speaker pauses, all motion stops completely. The feeling: you have been handed something to read, and what it says matters.
```

> **Specs de referência pra reprodução manual (After Effects):** background warm off-white `#f5f0e8` ou charcoal `#1a1a1a`, accent red `#b91c1c` / green `#166534` / cobalt `#1d4ed8`, headline display serif (Playfair Display ou Freight Display), label condensed sans (Barlow Condensed ou Bebas), régua thick `4-6px`.

---

### Estilo 7 — Liquid Organic

#### Bloco VISUAL

```
Style: Living, breathing, biomorphic — the visual sensibility of a creative studio that treats motion as a material substance rather than a graphic tool. This is the aesthetic of Studio Dumbar, Sagmeister & Walsh, and Abstract: The Art of Design. The background is a warm deep tone — a rich dark charcoal with undertones of brown and terracotta, the specific darkness of soil at dusk rather than digital black. Background elements drift continuously: amorphous blobs of barely-visible tonal variation (slightly warmer or cooler than the ground tone) float slowly through the frame over long cycles, never calling attention to themselves, creating the sensation that the background itself is breathing. Card surfaces are fluid and irregular: shapes with softly imperfect edges that suggest they were formed by process rather than drawn by a cursor — never perfectly rectangular, always with the slight imprecision of something that grew into its shape. Typography mixes two voices: a bold expressive display sans-serif for headline-anchors — strong and rooted, with optical weight at large sizes; and a flowing italic for sublines and supporting text — suggesting movement and organic quality. The accent colors are warm organic pigment tones: deep ochre, burnt sienna, warm amber, or terracotta. These are the colors of natural pigments and earthy dyes, never digital primaries. Accent appears on asterisks, on single underline strokes, and on the irregular borders of key cards. No sharp geometric edges anywhere. No grid-alignment as a principle — elements find positions that feel compositionally considered rather than mathematically correct. The composition has the quality of something settling into its most comfortable form.
```

#### Bloco MOTION

```
Motion: Fluid, unhurried, alive — animations feel grown rather than engineered. No snap. No hard edges. No constant velocity. Everything moves as if through a warm, slightly viscous medium. Cards and elements enter by morphing: beginning as an amorphous organic blob of color that slowly resolves and clarifies into its final form — shape, text, and edges emerging from soft undefined matter, like a developing photograph or an image coalescing in water. Typography reveals by opacity rising very slowly from zero — not a position shift, not a wipe, just gradual luminous emergence, as if text is developing in a darkroom under amber light. Letter by letter is permitted here, but the stagger between letters is slow enough to feel organic, not mechanical. Transitions between elements use soft morphing: the outgoing element's border flows outward and dissolves into the space, as if it were absorbed by the background, while the incoming element coalesces from that same space. On key beats and anchor words: instead of a scale pulse, a warm ripple emanates from the word's center — a single slow wave of tonal brightening spreading outward like a drop in still water, fading as it reaches the edges of the frame. The background drifting blobs continue moving throughout: they never stop, even during speaker pauses, but they move so slowly they read as atmosphere rather than animation. During speaker pauses: foreground motion slows even further but does not fully stop — it breathes rather than freezing. The push-in during hold is very slow and continuous, like a calm long inhale. The overall feeling: warm, considered, alive — something that thinks slowly and deeply.
```

> **Specs de referência pra reprodução manual (After Effects):** fundo `#1a1410`, blob tones `#2a1f18`–`#241c15`, accent ocre `#c2852a` / sienna `#a0522d` / âmbar `#d4a017`, headline Canela ou GT Alpina Bold, subline italic correspondente. Background blobs: cycles de 40-60s, opacity máx 15%.

---

### Estilo 8 — Brutalist

#### Bloco VISUAL

```
Style: Raw, confrontational, deliberately anti-polish — the visual language of architecture that leaves concrete unfinished, of punk zines, of websites that refuse to hide their own structure. This is the right aesthetic for content that is an opinion, a provocation, or a manifesto — not a product launch, not a brand spot. Background is pure white OR pure black with zero treatment: no gradient, no noise, no texture, no depth. The choice between white and black is made once per video and held consistently, never alternating. Typography is oversized, sometimes misaligned, and intentionally pushed beyond the comfortable boundaries of the frame. Headlines overflow their implied containers — text that is cut off at frame edges on purpose, as if the idea is too large for the screen to contain it. Type scale is radical: one word enormous (filling sixty or seventy percent of frame width), the next word tiny beside it, the contrast between them IS the design. Mixed case is permitted — all caps, all lowercase, or mixed — chosen to match the emotional register of the word, not for consistency. Color is violent in its simplicity: a single pure primary (construction-zone yellow, emergency red, pure white on black, or pure black on white). Thick horizontal and vertical rules carry real weight — not hairline, not decorative, but heavy editorial marks. Layouts deliberately break the invisible grid: text layers overlap, elements sit at intentional diagonals, some elements are clearly slightly wrong in their placement — the wrongness is considered. Icons, when used, are hand-drawn in quality — rough, slightly imprecise, like a sticker or a rubber stamp rather than a wireframe. The message of every element: this was not made to impress you.
```

#### Bloco MOTION

```
Motion: Abrupt, rhythmic, percussive — built by hand, not by algorithm, and proud of it. No ease-in. No ease-out. No smooth velocity curves. Animations operate on two states: present and absent. Elements arrive on a hard cut — they do not travel, they appear. The one exception is when an oversized text element enters moving at constant speed from off-screen, like someone sliding a banner past the camera — it travels at a steady, relentless pace and STOPS the instant it reaches position, with zero deceleration, as if hitting a wall. On anchor words and peak emphasis moments, the entire frame inverts colors for two to three frames — a visual stutter, a photocopier glitch, a flash of intensity that registers subconsciously even if the viewer cannot name it. Thick rules draw themselves in a single fast horizontal stroke from edge to edge — instantly, in one frame. When a new element replaces another, use a hard cut to black for three to five frames before the incoming element appears — a breath, a pause, a punctuation mark built from darkness. No dissolves. No fades. No morphs. During speaker pauses: the current frame holds completely static with zero motion — but optionally, text may jitter very subtly, shifting by one pixel randomly per frame, as if the frame itself is vibrating from the force of what was just stated. This jitter is optional and used sparingly, only on the most confrontational holds. The overall feeling: a fist hitting a table to make a point.
```

> **Specs de referência pra reprodução manual (After Effects):** background puro `#000000` ou `#ffffff`, regras 4-8px de espessura, tipografia sem easing (linear ou step), accent amarelo `#FFD700` / vermelho `#DC2626`, invert flash em 2-3 frames, jitter ±1-2px random offset. Fontes: Display Gothic, Helvetica Inserat, Impact, ou equivalente condensed ultra-bold.

---

## Mapeamento conceito → animação visual

Dois grupos: **concretos** (objetos do mundo real → ícone hairline minimalista) e **abstratos** (estados/processos → metáfora material). Nunca traduzir conceito abstrato como ícone hairline genérico — fica fraco.

**Concretos (ícone hairline):**
| Conceito mencionado | Ícone sugerido |
|---|---|
| carrossel / slides | 3 retângulos 4:5 staggered diagonal |
| site / página web | janela de browser com 3 dots top-left + linhas horizontais |
| aplicativo / app | outline de phone vertical com notch |
| código / programar | janela com 4-5 linhas de "código" (hairlines com indentação variável) |
| chat / conversa | duas bubbles empilhadas, uma com dots de typing |
| dinheiro / receita / faturamento | cifrão dentro de circle hairline |
| tempo / prazo / rápido | relógio outline com ponteiros |
| dados / métricas / análise | bar chart hairline 3-4 barras crescentes |
| vault / Obsidian / base de conhecimento | safe hexagonal outline com dot central e linhas radiais |
| email / newsletter | envelope outline com linha horizontal cortando |
| podcast / áudio | microfone outline com ondas de som laterais |
| redes sociais / audiência / seguidores | 3 círculos sobrepostos (people) ou grafo de nós simples |
| funil / conversão / vendas | triângulo invertido com 3 linhas horizontais (funil) |
| produto / lançamento / oferta | caixa outline com seta saindo pra cima |
| comunidade / grupo / mastermind | 3 círculos dispostos em triângulo conectados por linhas |
| mentoria / consultoria | dois círculos sobrepostos parcialmente (venn) com raio no maior |
| copy / texto / escrita | folha de papel outline com 3 linhas + caneta hairline |
| tráfego / anúncio / mídia paga | cursor com círculo de seta ao redor (click target) |
| câmera / vídeo / conteúdo | câmera outline com triângulo de play ao lado |
| dashboard / relatório | retângulo com 2 colunas e linha no topo (tabela) |

**Abstratos (metáfora material — preferir essas pra IA/clones/inteligência):**
| Conceito mencionado | Metáfora preferida | Descrição pro prompt |
|---|---|---|
| IA / inteligência / pensar | partículas/líquido | "soft white particles drifting upward, slowly coalescing into the shape of a brain-like silhouette outlined in hairlines, with subtle inner glow" |
| clones / fontes / conhecimento | grids/nós conectando | "thin hairline lines drawing themselves one by one between scattered white dots, forming a network constellation that settles into a stable graph" |
| insight / reveal / resposta | luz emergindo | "a soft warm-white bloom of light expanding outward from a central point, then settling into a clean centered headline as the light fades" |
| agente / automação / sistema | grids + leve loop | "interconnected nodes with one node pulsing softly, suggesting a continuous process — gentle, not mechanical" |
| processamento / análise de dados | partículas + grid | "particles flowing into a structured grid that locks into place line by line, then settles" |
| transformação / mudança / evolução | liquid morph | "an amorphous shape slowly clarifying and resolving into a clean geometric form, as if matter finding its purpose" |
| estratégia / planejamento / visão | grid tático | "a sparse grid of hairline lines drawing themselves to form a field, with one intersection marked by a soft crosshair pulse — like a chess board lighting up a move" |
| crescimento / escala / expansão | curva orgânica | "a single smooth curve line drawing itself from lower-left to upper-right, unhurried, arriving at its peak exactly as the speaker lands the word" |
| autoridade / posição / reputação | pilar/monumento | "a single tall vertical form rising from the bottom center of the frame — not a building, not a column, just a clean rising presence that holds" |
| clareza / foco / simplicidade | luz cortando névoa | "a narrow beam of warm white light cutting through a soft diffuse haze, the haze retreating as the light advances" |
| velocidade / eficiência / resultado | trilha de movimento | "a clean horizontal motion trail — a hairline line moving left to right faster than the eye tracks it, leaving a brief luminous afterimage that fades immediately" |
| sistema / processo / método | engrenagem viva | "two or three hairline gear outlines rotating slowly in mesh — not mechanical-aggressive, but deliberate and considered, like a mechanism designed to last" |

Se aparecer conceito não listado: concreto vira ícone hairline, abstrato vira metáfora material. **Nunca** usar ícone hairline literal pra conceito abstrato (ex: cérebro outline pra "IA" — usar partículas). **Nunca** usar metáfora material pra conceito concreto (ex: "partículas coalescing" pra "carrossel" — usar os 3 retângulos).

## Etapa 11: Salvar a estrutura no Obsidian

Pasta de trabalho (criada na Etapa 3):

```
conteudo/YYYY-MM-DD-gemini-omni-{slug}/
├── README.md                              ← índice + transcrição completa + status de cada take
├── source/
│   ├── original.mp4                       ← cópia do vídeo original
│   ├── audio.mp3                          ← áudio extraído
│   ├── audio.json                         ← saída do Whisper (segments com timestamps)
│   └── splits.json                        ← tuplas (start, end) usadas pra cortar
├── takes/
│   ├── take-01_0s-10s.mp4
│   ├── take-02_10s-19s.mp4
│   └── take-03_19s-27s.mp4
├── prompts/
│   ├── take-01_0s-10s.md                  ← prompt pronto pra colar no Omni
│   ├── take-02_10s-19s.md
│   └── take-03_19s-27s.md
└── frames/
    ├── frame_01.jpg
    └── frame_NN.jpg
```

Slug: 3-5 palavras kebab-case do tema central (ex: `jarvis-claude-code`, `agentes-multi-tasking`, `live-fistcare`).

### README.md (raiz da pasta)

```markdown
# Gemini Omni — {Título descritivo}

**Vídeo fonte:** `source/original.mp4` (origem: `{path original}`)
**Duração total:** {DURATION}s
**Takes:** {N} clips de até 10s
**Estilo:** {Apple-clean / CODA Dark / Híbrido / Linear Vercel / Editorial Magazine / Liquid Organic / Brutalist / Clone de Cérebro}
**Data:** {YYYY-MM-DD}

---

## Takes

| # | Range (original) | Arquivo | Prompt | Tema do take |
|---|---|---|---|---|
| 01 | 0:00 – 0:10 | [`takes/take-01_0s-10s.mp4`](takes/take-01_0s-10s.mp4) | [`prompts/take-01_0s-10s.md`](prompts/take-01_0s-10s.md) | {1-frase resumindo o que ele fala nesse take} |
| 02 | 0:10 – 0:19 | [`takes/take-02_10s-19s.mp4`](takes/take-02_10s-19s.mp4) | [`prompts/take-02_10s-19s.md`](prompts/take-02_10s-19s.md) | ... |

---

## Transcrição completa (PT-BR, timestamps do original)

| Timecode | Fala | Take |
|---|---|---|
| 0:00 – 0:03 | "..." | 01 |
| 0:03 – 0:08 | "..." | 01 |
| 0:10 – 0:14 | "..." | 02 |

---

## Como usar

1. Abrir Gemini Omni
2. Pra cada take: subir o `.mp4` correspondente + colar o conteúdo do `.md` de prompt
3. Baixar o resultado e remontar os clips em sequência (CapCut/Premiere) — eles foram cortados em fim de frase, então emendam limpo

## Notas

- **Idioma do prompt:** inglês (Gemini lê melhor). **Áudio do vídeo:** permanece em PT-BR intacto.
- **Textos visuais nas animações:** em PT-BR.
- Timecodes nos prompts são **relativos a cada take** (0:00 = início do clip).
```

### prompts/take-NN_*.md (um por take)

```markdown
# Take {NN} — {range no original}

**Range no original:** {start}s – {end}s
**Duração do take:** {dur}s
**Arquivo de vídeo:** `../takes/take-NN_*.mp4`

---

​```​
{PROMPT_COMPLETO_COM_TIMECODES_RELATIVOS_AO_TAKE}
​```​
```

> **Importante:** usar **3 backticks** (```) por fora do prompt por padrão. O botão "copy" do Obsidian funciona com 1 clique nessa cerca. Só usar 4 backticks (````) se o prompt interno realmente contiver triple-backticks (raro — só se Marcelo pedir snippet de código dentro do prompt).

## Etapa 12: Log

Apendar em `log.md`:

```
- YYYY-MM-DD — Gemini Omni: vídeo `{nome}` ({DURATION}s) fatiado em {N} takes ≤10s, estilo {estilo}. Pasta: `conteudo/{YYYY-MM-DD}-gemini-omni-{slug}/`.
```

## Etapa 13 — Automação Playwright (pipeline paralelo)

**Status: ATIVA** (validada ao vivo em 2026-05-27 com 5 takes do reel "Claude frentes para dominar"). O fluxo está em uma sub-skill complementar: ao final da Etapa 11 (prompts salvos), oferecer ao Marcelo rodar `/omni-run` que faz o pipeline abaixo. Marcelo NÃO quer download automático (ele baixa manual depois pelo histórico do Flow).

### App alvo: Google Flow (Gemini Omni Flash)

- URL: `https://labs.google/fx/pt/tools/flow`
- Login: Google account (Marcelo tem tier PRO — 1000 credits/mês). Confirmar `PRO` badge no avatar.
- Modelo default: **Omni Flash** (mostrado no painel do editor — `pen_magic` icon)

### Fluxo end-to-end (paralelo)

Ganho: 5 takes em ~3-5min total (vs ~15min sequencial). Cada geração processa no servidor independentemente.

```
1. browser_navigate https://labs.google/fx/pt/tools/flow
2. Click "Create with Google Flow" → cria projeto novo, URL vira /project/{uuid}
   (Ou navega direto pra projeto existente se for retry)

3. UPLOAD EM BATCH (todos os takes de uma vez):
   - Click "Adicionar mídia" (toolbar) → abre menu dropdown
   - Click "Enviar mídia" → abre file chooser
   - browser_file_upload com ARRAY de paths (paths=[take-01, take-02, ...])
   - PRIMEIRA VEZ: modal "Rights to use this video" — click "I agree, Do not show again"
   - Esperar ~30-60s todos processarem (uploads acontecem em paralelo no Flow)

4. CAPTURAR MAPPING UUID ↔ NOME DE ARQUIVO:
   - Após upload, snapshot do projeto mostra cada item com:
     - href="/edit/{media-uuid}"
     - Nome do arquivo (ex: "take-01_0s-8s") visível como label no thumbnail
   - Salvar mapping {take-NN: media-uuid} em splits.json (campo "media_uuid")

5. DISPARAR GERAÇÕES EM SEQUÊNCIA RÁPIDA (sem esperar):
   PARA CADA take em 01..NN:
     a. browser_navigate /project/{uuid}/edit/{media-uuid}
     b. Click div[contenteditable]:has-text("Descreva")
     c. browser_type prompt completo do .md (entre as cercas ```)
     d. Click button[aria-label*="arrow_forward"]  (botão "Criar" verde)
     e. (NÃO esperar terminar — pula pro próximo)

6. FIM. Não baixar. Marcelo abre /project/{uuid} manualmente e baixa
   cada take quando estiver pronto (botão "Baixar" no header da edição).
```

### Seletores cravados (validados 2026-05-27)

| Elemento | Seletor robusto |
|---|---|
| Botão "Create with Google Flow" (landing) | `button:has-text("Create with Google Flow")` |
| Botão "Novo projeto" (dashboard) | `button:has-text("Novo projeto")` |
| Botão "Adicionar mídia" (toolbar projeto) | `button:has-text("Adicionar mídia")` |
| Menuitem "Enviar mídia" | `menuitem:has-text("Enviar mídia")` |
| Modal "I agree, Do not show again" | `button:has-text("I agree, Do not show again")` |
| Textbox prompt | `div[contenteditable]:has-text("Descreva")` |
| Botão "Criar" (submit geração) | `button[aria-label*="arrow_forward"]` ou role=button name "arrow_forward Criar" |
| Botão "Baixar" (download resultado) | `button:has-text("download Baixar")` |
| Botão "Voltar aos projetos" | `button:has-text("arrow_back Voltar aos projetos")` |

### Pegadinhas confirmadas

- **"Falha" warning é VISUAL BUG inicial.** Aparece junto com upload em progresso E com geração iniciando — NÃO interpretar como erro até verificar progresso > 0. Bug visual confirmado, não server error.
- **`page.fill()` colapsa newlines em espaços** ao colar prompt no contenteditable. Visualmente fica um parágrafo só, mas o Omni interpreta as keywords (CRITICAL RULE, TASK, SHOT) corretamente e gera resultado válido. Aceitar essa limitação.
- **Botão "Criar" só habilita depois de prompt + vídeo carregados.** Se tentar clicar antes, fica `[disabled]`.
- **URLs de edit são estáveis.** Pode navegar direto via `browser_navigate` em vez de clicar thumbnail — mais robusto.
- **Modal de rights aparece só na primeira vez** se clicar "Do not show again". Skill deve tentar o click mas tolerar ausência do modal em runs subsequentes.
- **Output do Flow vem em 720x1280** (downsampling de 1080x1920), H.264 + AAC. Resolução adequada pra IG/TikTok.
- **Áudio do output não é byte-for-byte do input.** Flow faz re-encode + processamento sutil que muda timbre. Solução conhecida: `ffmpeg -map 0:v -map 1:a` substituindo áudio do output pelo do take original (Marcelo prefere fazer manualmente no CapCut). Ver `feedback_omni_audio_passthrough.md`.

### Sub-skill: `/omni-run <pasta>`

Quando criar a skill separada (próximo passo), ela recebe um path tipo `conteudo/2026-05-27-gemini-omni-{slug}/` e executa as etapas 1-5 acima usando os `.md` em `prompts/` e os `.mp4` em `takes/`. Salva mapping de UUIDs em `splits.json` pra rastreabilidade.

---

## Princípios de prompt que NÃO mudam (independente do estilo)

1. **Áudio PT-BR é sagrado** — linha CRITICAL sempre no topo
2. **Rosto do Marcelo nunca é coberto** — overlays sempre no lado livre (geralmente esquerda)
3. **Textos visuais em PT-BR** — `Carrossel*`, `Site*`, `Aplicativo*`, etc.
4. **Timecodes precisos** — relativos ao clip enviado, sem offset
5. **Safe area** — top 12% + bottom 18% livres (zonas de UI do IG/TikTok)
6. **9:16 vertical, 1080x1920, 30fps, 8-10 Mbps** — sempre
7. **Asterisco ou beat marker de acento** — presente em todos os estilos (cor e forma variam por estilo)

## Edge cases

- **Vídeo horizontal (16:9):** adaptar safe area (top 8% + bottom 14%) e mudar âncora pra "lower-third" em vez de left/right
- **Vídeo sem fala (só ambiente):** pular transcrição, pedir ao Marcelo um briefing curto do que quer ilustrar
- **Fala muito rápida (>15 palavras/seg):** agrupar 2-3 frases por shot pra não saturar
- **Marcelo no centro do frame (não na lateral):** usar lower-third ao invés de side panels
- **Whisper transcreve "Cloud Code"** (erro comum) → corrigir pra `Claude Code` ao montar a tabela e o prompt
