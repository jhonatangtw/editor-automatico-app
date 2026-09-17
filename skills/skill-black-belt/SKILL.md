---
name: skill-black-belt
description: >-
  Pipeline completo de criativos de vídeo IA para direct response (VSL, UGC, TikTok Shop, Meta Ads) — do prompt à execução no Higgsfield. Núcleo: prompts de vídeo para avatares falantes a partir de copy + imagem (Veo 3.1, Kling V3, Seedance 2.0), em blocos autocontidos ≤2500 chars com travas anti-bug. Módulos: storyboard viral 3D Pixar cena a cena pro TikTok Shop; prompts shot-by-shot de efeitos (brand film, B-roll); prompts de imagem ultrarrealista (start frame, produto). Executa manual ou via Higgsfield MCP (Seedance 2.0, Nano Banana Pro). Use SEMPRE que o usuário enviar copy de anúncio com imagem de avatar, pedir "separe em blocos", "talking head", "avatar falando", "image-to-video", mencionar Veo/Kling/Seedance, pedir storyboard, "criativo cena por cena", "personagem 3D", "criativo viral", "prompt de vídeo", "shot list", "gerar imagem", "fotorrealismo", "start frame", corrigir/regerar bloco (fala corrida, legenda, voz extra, loop, erro 422), ou executar no Higgsfield.
---

# Skill Black Belt — Pipeline de Criativos IA (HW Publishing)

Uma skill, quatro modos, do brief à geração. Explicações em **PT-BR; prompts em inglês**. Entrega **inline no chat** (nunca arquivo, salvo pedido).

## ROTEADOR — identifique o modo antes de tudo

| Entrada do usuário | Modo | Onde está |
|---|---|---|
| Copy + imagem de avatar real → vídeo falante (Veo/Kling/Seedance) | **AVATAR** (núcleo) | Este arquivo, abaixo |
| Copy ou produto/nicho → criativo viral com personagem 3D Pixar (TikTok Shop) | **STORYBOARD 3D** | `references/storyboard-3d.md` |
| Brief de vídeo SEM avatar falante (brand film, B-roll, efeitos, product video) | **EFFECTS** | `references/effects-seedance.md` |
| Imagem realista (start frame de avatar, foto de produto, image creative) | **PHOTOREALISM** | `references/photorealism.md` |

**Leia o reference do modo antes de gerar.** Regras de decisão:
- Avatar humano real falando = AVATAR. Personagem 3D/mascote = STORYBOARD.
- Sem imagem de avatar? Ofereça criar o start frame com PHOTOREALISM e depois seguir pro AVATAR.
- Ambíguo entre modos → pergunte em 1 linha, não assuma.

**Pipelines encadeados (a força da skill):**
- PHOTOREALISM → AVATAR: gera o start frame, aprova, segmenta a copy em blocos.
- STORYBOARD → imagem (Nano Banana Pro) → vídeo (Seedance): cena a cena.
- STORYBOARD/AVATAR + EFFECTS: cenas de B-roll/efeitos intercaladas nos blocos falados.

## EXECUÇÃO — Manual (padrão) ou Higgsfield MCP

Padrão: entregar prompts prontos pra colar. Se o usuário pedir pra executar ("gera aí", "roda no Higgsfield") ou aceitar a oferta → leia `references/higgsfield-execution.md` (upload de mídia, Seedance 2.0/Nano Banana Pro, confirmação de créditos, aprovação bloco a bloco).

---

# MODO AVATAR (núcleo)

Gera prompts de vídeo para **avatares falantes** a partir de **copy** + **imagem de avatar**, prontos para **Veo 3.1**, **Kling V3** ou **Seedance 2.0** (image-to-video). Objetivo: máxima naturalidade e zero retrabalho — cada bloco nasce com as travas anti-bug.

**Formato BLOCO ÚNICO AUTOCONTIDO (obrigatório):** cada bloco é um prompt completo e independente, com TODAS as seções juntas — `[Subject]/[Setting]/[Action timeline]/[Camera]/[Style]/[Audio]/[Negative]` — pronto pra colar sozinho. NUNCA separe um "Bloco Base" das Action. As seções fixas se repetem idênticas em todos os blocos; só mudam `[Action timeline]` e a fala no `[Audio]`. Cada bloco ≤2500 caracteres, cabeçalho `Bloco N — [TAG] — ~Xs` e linha `> Fala:` antes do prompt.

## Fluxo de trabalho

### 1. Antes de gerar, SEMPRE pergunte

(use o tool de múltipla escolha quando disponível; se já respondido na conversa, extraia do contexto e não repita)

1. **Modelo de geração?** → Veo 3.1 / Kling V3 / Seedance 2.0 (sintaxe muda — `references/models.md`).
2. **Velocidade de fala?** → natural (~2.5 pal/s), **1.1x (~2.75 pal/s)** ou 1.25x (~3.1 pal/s). Define palavras por bloco. Cadência já travada pro AD atual = não perguntar de novo.
3. **Dinâmica do avatar** (numa rodada só): boca contida ou dinâmica? Movimenta mais ou menos? Gestos amplos ou contidos?

### 2. Analise a IMAGEM e detecte o contexto automaticamente

Extraia sem perguntar:
- **Proporção** → SEMPRE use a da imagem enviada (9:16, 16:9, 1:1...). Nunca assuma 9:16.
- **Identidade**: idade aparente, cabelo, pele (poros/sardas), olhos, acessórios, roupa.
- **Cenário**: carro / podcast / escritório / casa / espelho, objetos no quadro.
- **Pose e mãos**: onde estão, se seguram celular (selfie UGC), se cruzadas no colo.
- **Luz**: natural, dappled, janela, etc.

**Regra de ouro:** nunca acrescente itens que não existem na imagem. Só descreva o que está lá.

**IDOSOS (60+) — aplicar automaticamente, sem perguntar:** movimento de boca mínimo, expressões e gestos menores e mais lentos, micromovimentos de cabeça sutis.

### 3. Segmente a copy em blocos

- Duração: **palavras ÷ cadência** (natural ≈ 2.5; 1.1x ≈ 2.75; 1.25x ≈ 3.1 pal/s).
- Respeite o **teto do modelo** (Veo ≈ 8s; Kling ≈ 10s; Seedance ≈ 15s — confirmar em `references/models.md`).
- **NUNCA corte frase no meio.** Bloco termina em fim de frase (ponto). Frase sozinha estourou o teto → dividir em vírgula natural com reticências (`...`) início/fim.
- **CONSOLIDAÇÃO:** agrupe frases curtas vizinhas da MESMA ideia até ~8–9s antes de abrir bloco novo. Não deixe dois clipes de 3–4s seguidos quando dá pra juntar num de 8s. Bloco curto isolado só quando **proposital**: leitura de pergunta, punchline, beat dramático, revelação.
- **TETO RÍGIDO DE 2500 CARACTERES:** SEMPRE meça (`wc -m`) os blocos que tendem a estourar — falas longas, elemento extra no cenário, travas acumuladas. Passou → compacte [Style]/[Negative] mantendo as travas. Nunca entregue acima de 2500.
- Numere sequencialmente.

### 4. Cabeçalho de CADA bloco com duração estimada

`Bloco 1 — ~6s` etc. Cálculo: `palavras ÷ cadência` arredondado + buffer de silêncio (regra 5.1). O usuário usa isso pra escolher o tempo na plataforma.

### 5. TRAVAS OBRIGATÓRIAS em todos os blocos

1. **Buffer de silêncio + anti-corte da 1ª palavra:** todo bloco começa com silêncio antes da fala e termina com ~0,5s depois. O avatar NUNCA começa já falando no primeiro frame.
   - Padrão: ~0,5s de lead-in.
   - Abertura / leitura de pergunta / 1ª palavra crítica: **1,2s** de lead-in. No Action ("longer silent lead-in, mouth fully closed and still, no speech or lip movement yet"), no [Style] ("no lip movement before 1.2s; first word fully voiced and clearly audible"), no [Audio] ("full silence for the first 1.2s, then voice begins cleanly on the first word"). No [Negative]: "clipped first word, swallowed first word, inaudible <primeira palavra>, speaking before 1.2s".
   - **Palavra-isca** (quando ainda come a 1ª palavra com 1,2s): isca curta descartável aprovada pelo usuário (ex.: `"Look this. ..."`) que o modelo engole no ataque. Só quando o usuário pedir ou o bug persistir.
2. **Voz única:** JAMAIS segunda voz, mesmo em podcast. Proibir "yeah", "uhum", "mm-hmm", interjeições de host, voz off. Só a voz do avatar.
3. **Anti-legenda/texto:** proibir em vários termos (no subtitles, no captions, no on-screen text, no titles, no overlays, no watermark) + "completely clean frame with zero text". No Veo, fechar cada fala com `(no subtitles, no captions, no on-screen text)`.
4. **Anti-"hmm"/filler:** "no filler sounds, no hmm, no uh, no um, no humming". Blocos terminados em vírgula: "after the last word she simply stops, mouth settling closed, no filler sound".
5. **Boca/expressão conforme escolha:** "boca contida" → em todo Action "subtle, controlled mouth movement, minimal jaw, calm restrained delivery, NOT exaggerated, no wide mouth opening". Idoso → boca mínima sempre.
6. **Pronúncia fonética (sempre):** reescrever termos NA PRÓPRIA FALA (entre aspas). Lista em `references/pronunciation.md`. Fixos: `silymarin → Silimerin`, `NAC → N-A-C`, `choline → Koh-leen`, `ashwagandha → ash-wa-gan-da`, `milk thistle → Milk Tissel`, `I'll → I will`. Números por extenso (74% → seventy-four percent; 500 → five hundred; 1960s → nine-teen six-tees).
7. **Carro parado:** "parked, stationary car, completely still, no rolling background, no sliding light, no engine noise".
8. **Mão do celular (UGC selfie):** a mão que segura o celular fica FORA do quadro; só a mão livre aparece. Confirmar o lado pela imagem.
   - **Micro-shake de mão (obrigatório em selfie):** micro-tremor orgânico constante, pequeno drift de enquadramento, nunca tripé — mas sem virar shaky-cam. Descrever: "constant subtle natural handheld micro-shake from the hand holding the phone, slight organic drift in framing, never tripod-stable, never perfectly still — but not shaky-cam, just the small involuntary motion of a real hand holding a phone." O shake é da MÃO/CELULAR; em carro parado, o fundo/veículo fica imóvel — só a câmera treme.
9. **Ritmo (anti-fala corrida):** fala justa no tempo → "calm, even, unrushed pace, not rushed". Não coube → reduzir o texto do bloco (voltar à regra 3).
10. **Anti-repetição/loop:** sobra de tempo no fim = modelo repete fala/movimento. Regra: **duração ≈ (palavras ÷ cadência) + ~0,9s de buffers**, sem sobra grande. Reforçar no Action ("delivers the full line once, continuously, at a natural pace that fills the whole window"), no [Audio] ("the line is spoken once only, no repetition, no looping"), no [Negative] ("repeated words, repeating the sentence, looping speech, double speech, echo, stutter"). Reporte de "repetindo" → encurtar a duração nessa lógica.
11. **Elemento extra no cenário (pet/objeto/figurante):** nesse bloco específico, soltar a trava de fundo parado: trocar "background completely still" por "warm indoor tone" e **remover "background motion" do [Negative]**. Descrever a passagem com início/fim no tempo, direção, naturalidade ("unhurried, not looking at camera, like his own pet") e avatar sem reação. Negativos específicos ("deformed cat, extra cat, cat morphing, cat staring at camera"). Esses blocos estouram 2500 → medir e compactar. Demais blocos: fundo parado.

### 6. Gesto no FÍGADO / ESTÔMAGO / BARRIGA

Fala citou **liver, stomach, belly, midsection, abdomen, bloat, gut** → gesto coerente com a cena apontando/abrindo as mãos pra região correspondente, ancorado na palavra, voltando à pose.
- **Liver**: lado superior direito do tronco, abaixo das costelas — ou as duas mãos abrindo pro tronco.
- **Belly/midsection/bloat**: gesto pro abdômen.
- Mãos cruzadas no colo → gesto contido. Idoso → menor e mais lento.
- **Avisar:** mãos saindo/voltando em clipe curto podem deformar no Veo/Kling; oferecer versão de gesto mínimo.

### 7. Estrutura do prompt por modelo

Ler `references/models.md`: Veo 3.1 (5 partes + `(no subtitles)`), Kling V3 (blocos rotulados com [Negative]), Seedance 2.0. Montar CADA bloco já no formato BLOCO ÚNICO AUTOCONTIDO do modelo escolhido.

### 8. Tipos de bloco especiais

- **[READS]** — lendo perguntas: olhada breve pra baixo, sobe o olhar pra câmera ao falar. Tags `[READS Q1]`, `[READS Q2]`; respostas são `[ANSWER]`.
- **[REACTION / IDLE]** — escuta silenciosa, SEM fala. [Audio]: "No speech, no voice, the man does not talk" + ambiente; [Negative]: "talking, lip movement, speech, mouthing words". Micro-reações (sobrancelha, blink, nod) e ponte pra fala (lábios entreabrindo). Variantes: neutra, cética (head shake lento), pensativa, surpresa contida.
- **[HOOK]** — abertura: entra já falando direto na câmera (blindar 1ª palavra com isca se preciso). Frase curta de alto CTR.
- **Continuações** — blocos em `...` fecham com "after the last word he simply stops, mouth settling closed, no filler sound".

## Ajustes pontuais (regenerações)

Padrões e correções (detalhe em `references/troubleshooting.md`):
- "fala corrida" → dividir o bloco ou forçar ritmo.
- "começa falando errado / funde sílaba" → buffer + separar palavras + pronúncia fonética.
- "boca muito expressiva" → trava de boca contida.
- "aparece legenda" → reforço anti-texto multitermo.
- "voz extra" → trava de voz única.
- "cortou no meio da fala" → resegmentar.
- "entonação não fecha" → "downward conclusive falling intonation" + silêncio final.
- "regerar a partir de X" → bloco começando exatamente no trecho; avisar pro anterior terminar antes.
- erro 422 no FAL → payload, não conteúdo: aspas simples, sem travessão longo/reticências; conferir duration/aspect/imagem.

## Lembre-se

- A copy de saúde/suplemento é do anunciante; a skill formata em prompts, não valida nem inventa claims médicos.
- Confirmar o modelo ANTES de gerar. Cadência travada = não reperguntar.
- Sempre analisar a imagem antes de escrever (proporção, identidade, cenário, pose, idade).
- Nunca inventar elementos que não estão na imagem.
- **Todo bloco ≤2500 caracteres — medir e compactar antes de entregar.**
- Bloco único autocontido sempre; consolidar falas curtas em ~8–9s; duração casada com a fala; buffer anti-corte da 1ª palavra.
- Ao fechar a entrega, oferecer execução via Higgsfield MCP uma vez (`references/higgsfield-execution.md`).

## Mapa de references

| Arquivo | Quando ler |
|---|---|
| `references/models.md` | Sintaxe Veo/Kling/Seedance, tetos de duração, cadência |
| `references/pronunciation.md` | Termo difícil na fala (substância, sigla, marca, número) |
| `references/troubleshooting.md` | Bug de geração reportado, erro 422 |
| `references/storyboard-3d.md` | Modo STORYBOARD (personagem 3D / TikTok Shop) |
| `references/beat-framework.md` | Detalhe dos 7 beats do storyboard |
| `references/biblioteca-visual.md` | Traduzir frase de copy em imagem |
| `references/exemplo-storyboard.md` | Calibrar nível de detalhe do storyboard |
| `references/effects-seedance.md` | Modo EFFECTS (shot-by-shot sem avatar) |
| `references/effects-breakdown-reference.txt` | Calibrar detalhe do modo EFFECTS |
| `references/photorealism.md` | Modo PHOTOREALISM (imagem realista / start frame) |
| `references/higgsfield-execution.md` | Executar via Higgsfield MCP |
