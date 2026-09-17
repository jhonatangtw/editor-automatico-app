---
name: avatar-vsl-video-prompts
description: Gera prompts de vídeo para avatares falantes (talking-head / UGC / podcast / VSL) a partir de uma copy + imagem de avatar, para Veo 3.1, Kling V3 ou Seedance 2.0. Use SEMPRE que o usuário enviar copy/roteiro de anúncio (direct-response, VSL, saúde/suplementos) com uma imagem de avatar e pedir prompts de vídeo, blocos de fala, "separe em blocos", "talking head", "avatar falando", "image-to-video", ou mencionar Veo, Kling ou Seedance. Acione também para ajustar/regerar um bloco, corrigir pronúncia, ritmo, boca, gestos, legenda na tela, hooks, cenas de reação/idle, blocos que leem perguntas, ou bugs de geração (corte da 1ª palavra, voz extra, fala corrida, repetição/loop). Segmenta a copy em BLOCOS ÚNICOS AUTOCONTIDOS (≤2500 caracteres), consolida falas curtas em blocos de ~8-9s, casa duração com a fala (anti-repetição) e aplica as travas anti-bug (sem legenda, sem voz extra, boca contida, anti-corte da 1ª palavra, pronúncia fonética, números por extenso, gesto no fígado/barriga).
---

# Avatar VSL / UGC Video Prompts

Gera prompts de vídeo para **avatares falantes** a partir de uma **copy** + uma **imagem de avatar**, prontos para colar em **Veo 3.1**, **Kling V3** ou **Seedance 2.0** (image-to-video).

O objetivo é máxima naturalidade (movimento, microexpressões, textura de câmera amadora) e zero retrabalho: cada bloco já nasce com as travas anti-bug que costumam estragar gerações de avatar.

## Idioma e formato

- **Explicações em PT-BR; prompts em inglês** (os modelos respondem melhor em inglês).
- Entrega **inline no chat** (nunca em arquivo, a menos que o usuário peça).
- Formato **BLOCO ÚNICO AUTOCONTIDO (obrigatório):** cada bloco entregue é um prompt completo e independente, com TODAS as seções juntas no mesmo bloco — `[Subject]/[Setting]/[Action timeline]/[Camera]/[Style]/[Audio]/[Negative]` — pronto pra colar sozinho. NUNCA separe um "Bloco Base" das `Action`. As seções fixas ([Subject], [Setting], [Camera], [Style], [Audio voz], [Negative]) se repetem idênticas em todos os blocos; só mudam `[Action timeline]` e a fala dentro de `[Audio]`. Cada bloco ≤2500 caracteres, com cabeçalho `Bloco N — [TAG] — ~Xs` e linha `> Fala:` antes do prompt.

## Fluxo de trabalho

### 1. Antes de gerar, SEMPRE faça estas perguntas

O usuário envia copy + imagem e espera que a skill reconheça o que fazer. Antes de criar, pergunte (use o tool de múltipla escolha quando disponível):

1. **Qual modelo de geração?** → Veo 3.1 / Kling V3 / Seedance 2.0 (a sintaxe muda por modelo — ver `references/models.md`).
2. **Velocidade de fala?** → cadência natural (~2.5 pal/s), **1.1x (~2.75 pal/s)** ou 1.25x (~3.1 pal/s). Isso define quantas palavras cabem por bloco. Se o usuário já travou uma cadência para o AD atual, use-a e não pergunte de novo.
3. **Dinâmica do avatar** (faça em uma rodada):
   - Boca pouco expressiva (contida) ou mais dinâmica?
   - Movimenta-se mais ou menos (cabeça/corpo)?
   - Gestos de mão amplos ou contidos?

Se o usuário já tiver respondido algo disso na conversa, não repita a pergunta — extraia do contexto.

### 2. Analise a IMAGEM e detecte o contexto automaticamente

Olhe a imagem e extraia, sem perguntar:
- **Proporção/aspect ratio** → SEMPRE analise a proporção da imagem enviada e use a mesma (9:16, 16:9, 1:1, etc.). Nunca assuma 9:16 por padrão.
- **Identidade**: idade aparente, cabelo, pele (poros/sardas/textura), olhos, acessórios (brincos, colar, óculos, etc.), roupa.
- **Cenário**: carro / podcast / escritório / casa / espelho, objetos no quadro (volante, microfone, planta, cinto de segurança...).
- **Pose e mãos**: onde as mãos estão, se seguram celular (selfie UGC), se estão cruzadas no colo.
- **Luz**: natural, dappled (folhas), janela, etc.

**Regra de ouro:** nunca acrescente itens que não existem na imagem (cinto, crachá, estetoscópio, acessórios). Só descreva o que está lá. Se o usuário quiser mudar algo, ele pede.

**IDOSOS — detecção automática:** se o avatar aparenta ser idoso (60+), aplique automaticamente:
- **movimento de boca mínimo** (articulação reduzida),
- **expressões e gestos de mão menores e mais lentos**,
- micromovimentos de cabeça mais sutis.
Não pergunte — reconheça pela imagem e aplique.

### 3. Segmente a copy em blocos

- Calcule a duração: **palavras ÷ cadência** (natural ≈ 2.5 pal/s; 1.1x ≈ 2.75 pal/s; 1.25x ≈ 3.1 pal/s).
- Respeite o **teto de duração do modelo** (Veo 3.1 ≈ 8s; Kling V3 ≈ 10s; Seedance 2.0 ≈ 15s — confirme em `references/models.md`).
- **NUNCA corte uma frase no meio.** Sempre termine bloco em fim de frase (ponto). Se uma frase sozinha estourar o teto, aí sim divida em vírgula natural e marque com reticências (`...`) início/fim para emendar.
- **CONSOLIDAÇÃO (preferir blocos cheios):** agrupe frases curtas vizinhas da MESMA ideia até preencher ~8–9s antes de abrir bloco novo. Não deixe dois clipes curtos (3–4s) seguidos quando dá para juntar num único de 8s — menos cortes, menos retrabalho. Só deixe um bloco curto isolado quando for **proposital**: leitura de pergunta, punchline, beat dramático, revelação de uma palavra.
- **TETO RÍGIDO DE 2500 CARACTERES (obrigatório):** todo bloco entregue deve ter ≤2500 caracteres. SEMPRE meça (ex.: `wc -m`) os blocos que tendem a estourar — falas longas, blocos com elemento extra no cenário (gato/objeto/segunda pessoa) ou com travas anti-corte acumuladas. Se passar, compacte [Style]/[Negative] mantendo as travas até caber. Nunca entregue um bloco acima de 2500.
- Numere os blocos sequencialmente.

### 4. Para CADA bloco, informe o tempo

No cabeçalho de cada bloco, escreva o identificador **e a duração estimada da fala**, porque o usuário usa isso para escolher o tempo da geração na plataforma. Exemplo:

```
Bloco 1 — ~6s
Bloco 2 — ~8s
```

Calcule: `nº de palavras da fala ÷ cadência escolhida`, arredondando, e some o buffer de silêncio (ver regra 5).

### 5. Aplique as TRAVAS OBRIGATÓRIAS em todos os blocos

Estas regras vieram de dezenas de bugs reais e devem estar SEMPRE presentes:

1. **Buffer de silêncio + anti-corte da 1ª palavra (anti-bug de início):** todo bloco começa com silêncio antes da fala e termina com ~0,5s depois. O avatar NUNCA começa já falando no primeiro frame.
   - **Padrão:** ~0,5s de lead-in.
   - **Blocos de abertura / leitura de pergunta / 1ª palavra crítica:** use **1,2s** de lead-in. Marque no Action ("longer silent lead-in, mouth fully closed and still, no speech or lip movement yet"), reforce no [Style] ("no lip movement before 1.2s; first word fully voiced and clearly audible") e no [Audio] ("full silence for the first 1.2s, then voice begins cleanly on the first word"). No [Negative] inclua "clipped first word, swallowed first word, inaudible <primeira palavra>, speaking before 1.2s".
   - **Palavra-isca (quando o modelo ainda come a 1ª palavra mesmo com 1,2s):** comece a fala com uma isca curta descartável que o usuário aprovar (ex.: `"Look this. ..."`), que o Kling "engole" no ataque deixando a palavra real limpa. Use só quando o usuário pedir ou quando o bug persistir.
2. **Voz única (anti-voz extra):** JAMAIS adicione segunda voz, mesmo em cenário de podcast. Proíba explicitamente "yeah", "uhum", "mm-hmm", interjeições de host/entrevistador, qualquer voz off. Só a voz do avatar principal.
3. **Anti-legenda/texto:** o vídeo não pode ter texto. Proíba em vários termos (no subtitles, no captions, no on-screen text, no titles, no overlays, no watermark) e afirme "completely clean frame with zero text". No Veo, feche cada fala com `(no subtitles, no captions, no on-screen text)`.
4. **Anti-"hmm"/filler:** proíba sons de preenchimento ("no filler sounds, no hmm, no uh, no um, no humming"). Em blocos que terminam em vírgula (continuação), marque "after the last word she simply stops, mouth settling closed, no filler sound".
5. **Boca/expressão conforme escolha do usuário:** se "boca contida", inclua em todo Action "subtle, controlled mouth movement, minimal jaw, calm restrained delivery, NOT exaggerated, no wide mouth opening". Se idoso, aplique sempre boca mínima.
6. **Pronúncia fonética (sempre):** reescreva termos que os modelos erram, NA PRÓPRIA FALA (entre aspas), não só na descrição. Mantenha e amplie a lista em `references/pronunciation.md`. Exemplos fixos: `silymarin → Silimerin`, `NAC → N-A-C`, `choline → Koh-leen`, `ashwagandha → ash-wa-gan-da`, `milk thistle → Milk Tissel`, `I'll → I will`. Números por extenso (74% → seventy-four percent; 500 → five hundred; 1960s → nine-teen six-tees).
7. **Cenário/carro parado:** se a cena é num carro estacionado, trave "parked, stationary car, completely still, no rolling background, no sliding light, no engine noise".
8. **Mão do celular (UGC selfie):** se for selfie, a mão que segura o celular fica FORA do quadro; só a mão livre aparece. Confirme o lado pela imagem.
   - **Micro-shake de mão (obrigatório em selfie):** sempre que o avatar estiver gravando em formato selfie segurando o celular com uma das mãos, inclua um **shake natural e constante de quem segura o celular na mão** — micro-tremor orgânico, pequeno drift de enquadramento, leve jitter do braço, nunca estabilizado/tripé. Não pode parecer câmera fixa. Ao mesmo tempo, não exagere (não é câmera tremendo): é o balanço sutil e involuntário de uma mão humana. Descreva algo como: "constant subtle natural handheld micro-shake from the hand holding the phone, slight organic drift in framing, never tripod-stable, never perfectly still — but not shaky-cam, just the small involuntary motion of a real hand holding a phone." Importante: o micro-shake é da MÃO/CELULAR; se a cena for num carro estacionado ou cenário que deve ficar parado, o fundo/veículo permanece imóvel — só a câmera (mão) treme.
9. **Ritmo (anti-fala corrida):** se a fala couber justa no tempo, reforce na direção "calm, even, unrushed pace, not rushed". Se não couber, reduza o texto do bloco (volte à regra 3).
10. **Anti-repetição / loop (tempo morto):** se sobrar muito tempo no fim do clipe (fala curta num clipe longo), o modelo preenche repetindo a fala ou o movimento. Regra: **duração ≈ (palavras ÷ cadência) + ~0,9s de buffers**, sem deixar sobra grande. A fala deve preencher quase todo o clipe. Reforce no Action ("delivers the full line once, continuously, at a natural pace that fills the whole window"), no [Audio] ("the line is spoken once only, no repetition, no looping") e no [Negative] ("repeated words, repeating the sentence, looping speech, double speech, echo, stutter"). Se o usuário reportar "está repetindo bases/fala", encurte a duração nesta lógica.
11. **Elemento extra no cenário (pet/objeto/figurante passando):** quando a cena pede movimento de fundo (ex.: o gato do avatar passando), **solte a trava de fundo parado** nesse bloco específico: troque "background completely still" por "warm indoor tone" e **remova "background motion" do [Negative]** — senão o modelo trava o movimento. Descreva a passagem com início/fim no tempo, direção (ex.: left to right), naturalidade ("unhurried, not looking at camera, like his own pet") e que o avatar não reage. Adicione negativos específicos do elemento ("deformed cat, extra cat, cat morphing, cat staring at camera"). Esses blocos tendem a estourar 2500 → meça e compacte. Nos demais blocos, mantenha o fundo parado.

### 6. Gesto no FÍGADO / ESTÔMAGO / BARRIGA (regra de conteúdo)

Sempre que a fala citar **liver, stomach, belly, midsection, abdomen, bloat, gut** (ou equivalente), inclua no Action um **gesto coerente com a cena** apontando/abrindo as mãos em direção à região do corpo correspondente, ancorado na palavra, voltando à pose depois.
- Para **liver**: indicar o lado superior direito do tronco, abaixo das costelas (anatomicamente correto) — ou as duas mãos abrindo em direção ao tronco, conforme a cena.
- Para **belly/midsection/bloat**: gesto em direção ao abdômen/barriga.
- **Adapte à pose da imagem:** se as mãos estão cruzadas no colo, o gesto é contido (uma ou as duas mãos sobem brevemente e voltam). Se for idoso, gesto menor e mais lento.
- **Aviso ao usuário:** mãos saindo e voltando num clipe curto podem deformar no Veo/Kling; ofereça a versão de gesto mínimo como alternativa.

### 7. Estrutura do prompt por modelo

A sintaxe muda por modelo. Leia `references/models.md` para o formato exato de Veo 3.1 (5 partes + `(no subtitles)`), Kling V3 (blocos `[Subject]/[Setting]/[Action timeline]/[Camera]/[Style]/[Audio]/[Negative]`) e Seedance 2.0. Monte CADA bloco já no formato BLOCO ÚNICO AUTOCONTIDO do modelo escolhido (todas as seções juntas, prontas pra colar sozinhas).

### 8. Tipos de bloco especiais

- **[READS] — lendo e respondendo perguntas:** quando o AD é formato "ele lê perguntas e responde", os blocos de pergunta começam com uma olhada breve pra baixo (como quem lê) e sobem o olhar pra câmera ao falar. Tag `[READS Q1]`, `[READS Q2]`. Os blocos de resposta são `[ANSWER]` normais.
- **[REACTION / IDLE] — escuta silenciosa:** cena do avatar parado assistindo algo (como quem vai comentar depois), SEM fala. No [Audio] use "No speech, no voice, the man does not talk" + ambiente; no [Negative] adicione "talking, lip movement, speech, mouthing words". Use micro-reações faciais (sobrancelha, blink, leve nod) e termine com a ponte de quem vai começar a falar (lábios entreabrindo, respiração). Variantes: neutra/curiosa, **cética** (head shake lento, leve franzir), pensativa (nod), surpresa contida. Serve de ponte pro Bloco 1.
- **[HOOK] — abertura:** entra já falando direto na câmera (sem beat morto na frente; se precisar blindar a 1ª palavra, use a palavra-isca). Frase curta e de alto CTR.
- **Continuações:** blocos que terminam em `...` (frase quebrada em vírgula) fecham com "after the last word he simply stops, mouth settling closed, no filler sound" para emendar sem corte no bloco seguinte.

## Ajustes pontuais (regenerações)

O usuário frequentemente volta para corrigir UM bloco. Padrões comuns e correções (detalhe em `references/troubleshooting.md`):
- "fala corrida" → dividir o bloco ou forçar ritmo.
- "começa falando errado / funde sílaba / stutter no nome" → buffer de silêncio + separar palavras + pronúncia fonética.
- "boca muito expressiva" → trava de boca contida.
- "aparece legenda" → reforço anti-texto multitermo.
- "voz extra / yeah / uhum" → trava de voz única.
- "cortou no meio da fala" → o bloco era longo demais para o tempo; resegmente.
- "entonação não fecha / soa aberta" → pedir "downward conclusive falling intonation" + silêncio final.
- "regerar a partir de X" → criar bloco que começa exatamente naquele trecho, e avisar para o bloco anterior terminar antes dele (evitar repetição).
- erro 422 no FAL → problema de payload, não de conteúdo: tirar aspas duplas (usar simples), travessões longos e reticências; conferir duration/aspect/imagem. Ver `references/troubleshooting.md`.

## Lembre-se

- A copy de saúde/suplemento é do anunciante; a skill formata em prompts de vídeo, não valida nem inventa claims médicos.
- Confirme o modelo ANTES de gerar — o formato inteiro depende disso. Se a cadência já estiver travada para o AD, não repergunte.
- Sempre analise a imagem antes de escrever (proporção, identidade, cenário, pose, idade).
- Nunca invente elementos que não estão na imagem.
- **Todo bloco ≤2500 caracteres — meça os que tendem a estourar e compacte antes de entregar.**
- Bloco único autocontido sempre; consolide falas curtas vizinhas em blocos de ~8–9s; duração casada com a fala (anti-repetição); buffer/lead-in anti-corte da 1ª palavra.
