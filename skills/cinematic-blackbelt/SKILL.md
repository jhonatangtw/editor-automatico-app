---
name: cinematic-blackbelt
description: 'Prompts de VÍDEO CINEMATOGRÁFICO FOTORREALISTA (live-action) para Seedance 2.0: 6 blocos + 5 pilares de aterramento (peso corporal, força ambiental, contenção emocional, câmera como observador, âncoras de continuidade). Use SEMPRE que pedirem "prompt cinematográfico", "cena de filme", "shot like a movie", "live-action", "fotorrealismo em movimento", "movimento corporal realista", "close emocional", "performance contida", cena de carro/direção, cena de intimidade, sequência de ação, coreografia de luta, interação com o ambiente (vento, chuva, água, poeira, gravidade), "continuidade entre cenas" ou "match cut" — ou mandarem um beat dramático pra virar vídeo. Acione também pra corrigir falhas típicas: ator flutuando sem peso, cabelo/tecido estático, rosto sobreatuado, câmera drone/voando, cena parecendo estúdio, drift de continuidade. NÃO use pra animação, cartoon/Pixar 3D, motion design, UGC/talking head, avatar falando ou podcast — aí é skill-black-belt, avatar-vsl-video-prompts ou pixar3d.'
---

<!-- editor-automatico:portao-de-credito -->
> **No Editor Automático:** gerar imagem, vídeo, avatar ou voz que gasta crédito é feito **só pelas etapas do pipeline do app** (ferramenta `etapa_rodar` do MCP `editor`), que mostram o preço e esperam a aprovação do aluno. Os comandos de geração citados nesta skill (`higgsfield generate`, `heygen`, `mmx`) ficam bloqueados na Conversa — use-os só como referência de modelo, prompt e parâmetros. Preço e saldo: `motores_listar`.

# Cinematic Blackbelt

Realismo cinematográfico se constrói com **contenção**, não com espetáculo.

Todo prompt gerado por esta skill impõe cinco pilares de aterramento que impedem o Seedance de derivar para os modos de falha que denunciam vídeo de IA: ator flutuando, ambiente morto, rosto sobreatuado, câmera voando.

## Os cinco pilares

1. **Peso corporal e física** — o ator tem massa; movimento tem atrito, inércia e força de contato.
2. **Força ambiental** — vento, água, gravidade, tecido e textura de superfície empurram o ator de volta.
3. **Contenção emocional** — microexpressões, beats sustentados, respiração. Nada de telegrafia facial exagerada.
4. **Câmera como observador** — a lente tem presença física (peso, respiração, drift). Não é drone, não é deus.
5. **Âncoras de continuidade** — direção de luz, figurino, hora do dia e posição de objeto atravessam os planos.

Um prompt que abandona qualquer pilar produz "cinema de IA" — tecnicamente um vídeo, estruturalmente um tell.

## Idioma

Conversa com o usuário em **português**. O prompt em si sai **sempre em inglês**.

## Estrutura do prompt (6 blocos, nesta ordem)

A ordem é estrutural — o Seedance pesa os blocos iniciais para decisões de composição e os finais para movimento e áudio.

```
[STYLE & MOOD]
[SHOT DIRECTION]
[ACTOR BEHAVIOR]
[ENVIRONMENTAL FORCE]
[CAMERA BEHAVIOR]
[AUDIO]
```

### Bloco 1 — Style & Mood (1 linha)

Uma frase, léxico de diretor de fotografia. Use a referência de filme/DP que o usuário deu; sem referência, o default é `35mm anamorphic, naturalistic color, soft contrast`.

- ✓ "35mm anamorphic, naturalistic skin tones, soft window light, muted teal-and-amber palette."
- ✗ "Cinematic, beautiful, dramatic, epic."

Pilhas de adjetivos achatam o output. Especificidade afia.

### Bloco 2 — Shot Direction (1 frase)

A ação destilada: sujeito, verbo, objeto, lugar. Nenhum adjetivo que não esteja fazendo trabalho estrutural.

- ✓ "A woman in her forties leans against a kitchen counter, reading a folded letter."
- ✗ "A beautiful sad woman sadly reads a heartbreaking letter in a sad kitchen."

### Bloco 3 — Actor Behavior (2-3 frases)

É aqui que mora o aterramento. Escreva o corpo do ator como um diretor dá nota: físico, específico, contido.

Sempre inclua os três:

- **Deixa de peso** — onde a massa do corpo está assentada ("weight on her right hip", "shoulders dropped", "hand braced on the counter").
- **Microação** — um movimento pequeno e involuntário ("she swallows", "his jaw tightens once", "her thumb traces the paper's edge").
- **Beat sustentado** — uma parada com intenção ("she pauses for two seconds before reading the next line").

Proibido:

| Não escreva | Escreva |
|---|---|
| "Tears stream down her face" | "her eyes glass over; she does not blink" |
| "He runs furiously" | "he breaks into a run, shoulder leading, arms compact" |
| "Smiles widely" | "the corner of her mouth lifts, then settles" |

### Bloco 4 — Environmental Force (1-2 frases)

O que empurra o ator de volta. Sem isso, o Seedance gera ator no vácuo e o plano lê como estúdio.

Categorias para escolher:

- **Ar** — direção e força do vento em cabelo, tecido, poeira.
- **Água** — peso da chuva nos ombros, água escorrendo de superfícies, trilhas de gota.
- **Gravidade** — como o peso transfere: deslocamento de quadril, flexão de joelho, contato com cadeira/parede/chão.
- **Superfície** — complacência do piso (carpete absorve o passo, madeira transmite som), textura de parede pegando luz.
- **Fonte de luz** — onde está, se está em movimento (faróis passando, vela tremulando, persiana mexendo).

Exemplos:
- "Wind from the open window lifts the left edge of her hair; the curtain breathes inward once."
- "Rain hits his shoulders in irregular bursts; water beads at his collar and falls."

### Bloco 5 — Camera Behavior (1 frase)

A câmera também é um corpo. Dê a ela peso, intenção e limite.

Léxico que o Seedance entende bem:

- "Locked-off static frame, no movement."
- "Slow handheld breathing, micro-drift."
- "Dolly-in at walking pace, ending in medium close-up."
- "Slow push from medium to close-up over 6 seconds."
- "Slow truck right, following the actor's shoulder."
- "Rack focus from foreground hand to background eyes."
- "Anamorphic dolly, slight lens flare from off-screen window."

Proibido:

- "Epic sweeping drone shot" → produz câmera voadora, sem peso, de videogame.
- "Cinematic camera movement" → vago demais; o Seedance cai no floaty.
- "360-degree rotation" → quase sempre quebra continuidade e produz artefato de morph.

### Bloco 6 — Audio (1 linha)

O Seedance gera áudio nativo. Especifique **ambiente primeiro**, depois qualquer fala.

- ✓ "Ambient: distant traffic, refrigerator hum, paper rustling. No dialogue."
- ✓ "Ambient: rain on glass, single car passing. She whispers, 'I'm still here.'"

Se o silêncio é intencional: "Ambient: room tone only. No dialogue, no music."

---

## Padrões por tipo de cena

Templates testados. Use como ponto de partida, não como forma rígida.

### Cena de direção / carro (interior, dia ou noite)

```
35mm anamorphic, naturalistic skin tones, low-key interior with passing exterior light.

A man in his late thirties drives alone on a two-lane highway at dusk.

His hands rest on the wheel at 9 and 3, grip relaxed. He glances at the rearview mirror once, then back to the road. His jaw is set; he has not spoken in some time.

Light from passing streetlamps and oncoming headlights sweeps across his face in slow rhythmic bands. The cabin is enclosed; dust motes catch in the side window light.

Locked-off frame on the driver, slight handheld breathing. Background out-of-focus highway moving at speed.

Ambient: tire hum on asphalt, faint heater fan, occasional passing vehicle. No music, no dialogue.
```

**Crítico:** trave a câmera ou use handheld muito suave. Câmera agressiva em cabine de carro lê como videoclipe, não como filme.

### Close emocional (sustentado, contido)

```
35mm anamorphic, naturalistic skin tones, soft north-facing window light, shallow depth of field.

A woman in her forties stands at a kitchen window, holding a folded letter.

She does not open it. Her thumb traces the fold once. Her shoulders settle, the weight of her body shifting to her left foot. Her eyes glass over but she does not blink; she swallows once.

Daylight from the window catches the side of her face; the curtain behind her stirs faintly. Dust visible in the light beam.

Slow push from medium to tight close-up over the full shot duration, ending at her eyes.

Ambient: distant kitchen radio playing softly under the noise floor, refrigerator hum, paper rustling between her fingers. No dialogue.
```

**Crítico:** sem lágrima, sem luto telegrafado. A performance vive no beat sustentado e na microação.

### Sequência de ação (perseguição a pé, aterrada)

```
35mm anamorphic, naturalistic color, overcast daylight, handheld vérité.

A man in his thirties runs down a narrow alley between brick buildings, pursued from off-screen.

His stride is compact, arms tucked, shoulder leading into each turn. He clips a steel trash can with his hip without slowing. His breathing is audible, irregular. He glances back once, then forward.

Wet pavement catches the gray sky; puddles splash where his feet land. A loose plastic bag tumbles past him in the wind. Brick walls close on both sides.

Handheld camera following at his shoulder height, two paces behind, breathing with his stride. Lens flares briefly when he passes an open doorway.

Ambient: footsteps on wet concrete, his breathing, distant city traffic, the bag scraping against the wall. No music.
```

**Crítico:** mantenha a passada compacta. O Seedance sobre-renderiza "sprinting" como pose de herói de ação, saltitante e sem peso. Escreva "compact, shoulder-leading" para aterrar.

### Cena de intimidade (contida, próxima)

```
35mm, naturalistic skin tones, warm low-key practical light from a bedside lamp, shallow depth of field.

Two people in their thirties sit close on the edge of a bed, neither speaking. One rests their forehead against the other's temple.

They breathe in near-sync. One hand finds the other's, fingers settling without grip. Neither moves to kiss; the stillness holds. A small smile passes between them, then fades.

The bedside lamp throws warm light across one side of both faces; the room behind is in shadow. Bedding compresses where they sit.

Static frame, no camera movement. Shallow focus held on the contact point between their foreheads.

Ambient: room tone, faint clock ticking, soft fabric movement. No dialogue, no music.
```

**Crítico:** intimidade se constrói de não-ação. Resista a acrescentar beijo, lágrima ou fala sussurrada — o Seedance sobre-renderiza os três.

### Interação ambiental (o clima como personagem)

```
35mm anamorphic, naturalistic color, late-afternoon overcast, slight teal cast.

A woman in her fifties walks slowly along a coastal cliff path, hands in her coat pockets.

Her stride is measured, weight settling into each step against the slope. The wind catches her hair from the left; she does not push it back. Her coat collar flutters; she pulls it tighter once.

Strong onshore wind shapes everything in frame — grass laid flat, her coat pressed against her body, salt spray visible in the air. The sea below is gray and churning; gulls hold position against the wind.

Slow truck right, matching her pace, framing her in medium-wide profile with the sea beyond. The horizon line stays level.

Ambient: wind through grass, distant surf, gull calls. Her footsteps soft on the path. No dialogue, no music.
```

**Crítico:** o vento precisa moldar **múltiplos** elementos (cabelo, casaco, grama, gaivotas). Vento em um elemento só lê como ventilador de estúdio.

---

## Continuidade em cenas multi-plano

Quando o pedido é uma sequência (um beat, uma cena, uma troca), continuidade é **imposta por âncoras repetidas em todo prompt** — não por esperança de que o Seedance lembre.

Copie estas cinco âncoras **verbatim** em cada plano:

1. **Âncora de luz** — mesma fonte, mesma direção. "Late-afternoon window light from screen-left."
2. **Âncora de figurino** — descrição completa, mesma redação. "Navy wool coat, gray scarf, no jewelry."
3. **Âncora de hora do dia** — explícita. "Overcast late afternoon, ~4pm light."
4. **Âncora de geografia** — onde o ator estava no fim do plano anterior. "She has just stepped back from the kitchen counter; in this shot she stands at the window."
5. **Âncora de cama de áudio** — mesma assinatura de ambiente em todos os interiores. "Ambient: distant kitchen radio, refrigerator hum."

Para identidade visual (mesmo rosto entre planos), gere **um** retrato-âncora, registre como elemento de personagem e embuta o `<<<element_id>>>` em cada prompt. Não reenvie retrato por plano. Mesmo padrão para locação: registre o plano de estabelecimento como elemento de ambiente.

---

## Execução (Higgsfield MCP)

Entregue o prompt pronto pra colar. Se o usuário pedir pra rodar ("gera aí", "manda no Higgsfield"), submeta pelo MCP com Seedance 2.0 — um plano por chamada `generate_video`, ou `generate_video_batch` para uma sequência inteira.

Parâmetros default para filme:

| Parâmetro | Default |
|---|---|
| `aspect_ratio` | `21:9` (sensação anamórfica) ou `16:9`. `9:16` só se o usuário pedir vertical. |
| `duration` | 6-10s para plano único; 4-5s para corte seco; 12-15s só para cena sustentada (intimidade, ambiental). |
| `generate_audio` | sempre `true` — mesmo em silêncio, escreva "Ambient: room tone only". |

Confirme créditos antes de disparar lote.

---

## Modos de falha e correção

| Sintoma | Causa | Correção |
|---|---|---|
| Ator flutua, sem peso | Falta deixa de peso no Bloco 3 | Adicione "weight settled on her right hip" / "shoulders dropped" / "hand braced on the counter" |
| Cabelo, tecido, ambiente estáticos | Falta força ambiental no Bloco 4 | Adicione linha de vento/gravidade/superfície |
| Rosto sobreatuado, luto/alegria telegrafados | Verbos como "cries", "smiles widely", "rages" | Troque por microação: "swallows once", "corner of mouth lifts then settles" |
| Câmera voa, dá drone, faz swoop | "sweeping" / "epic" / "drone" / "cinematic camera movement" | Troque pelo léxico específico: "locked-off", "slow handheld", "dolly-in at walking pace" |
| Cena lê como estúdio | Sem Bloco 4 **e** sem cama de áudio | Adicione os dois, completos |
| Drift de continuidade entre planos | Âncoras não repetidas | Copie as cinco âncoras verbatim em cada prompt |
| Cena de carro vira videoclipe | Câmera se move demais | Trave o quadro; só respiração de handheld |

Se o usuário reportar falha, **reescreva o bloco culpado — não troque de modelo**. A qualidade mora na estrutura do prompt, não no motor.

---

## Disciplina de saída

Devolva só o que o usuário precisa:

- O prompt de 6 blocos, pronto pra colar (esse é o entregável quando não há execução).
- Se executou: descrição curta em linguagem simples do que foi feito ("Close sustentado na janela da cozinha, 21:9, 8 segundos, ambiente de sala").

Nunca cole: internals de ferramenta, media IDs, element IDs — nem a metodologia ("apliquei os cinco pilares…"). O usuário quer o plano, não o framework.

## Armadilhas

- Não empilhe adjetivos no Bloco 1. "Cinematic, beautiful, dramatic, epic, stunning" produz output mais achatado que uma única referência específica de filme.
- Não escreva a emoção do ator como verbo. Escreva o corpo, escreva a microação — a emoção emerge da contenção, não da declaração.
- Não pule o Bloco 4. Sem força ambiental, todo prompt cinematográfico lê como estúdio por melhor que seja o resto.
- Não dê liberdade ilimitada à câmera. Um quadro travado é mais cinematográfico que um drone em 90% dos casos.
- Não gere plano por beat numa cena multi-plano sem âncoras. Continuidade não é automática.
- Não use esta skill para animação, cartoon, motion design ou UGC.
