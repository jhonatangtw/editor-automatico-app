---
name: storyboard-viral-3d
description: Cria um storyboard completo, cena por cena, para criativos virais no estilo "Character VSL / AI Character UGC" do TikTok Shop — aquele formato com personagem 3D antropomórfico (estilo Pixar) que narra uma carta de vendas comprimida, com legenda karaokê, fake UI nativa e disclaimer de compliance. Para CADA cena entrega um prompt de imagem pronto pra gerar (Nano Banana 2 / Seedance / Higgsfield), além da copy/locução, a legenda na tela e a nota de animação. Use SEMPRE que o usuário enviar uma copy de anúncio, uma VSL, um roteiro, ou apenas um produto/nicho e pedir para "criar um storyboard", "montar o criativo cena por cena", "transformar essa copy em vídeo", "fazer um criativo de personagem 3D", "criativo viral do TikTok Shop", "anúncio com personagem animado", "roteiro visual", "storyboard de VSL", ou descrever um produto e dizer que quer um vídeo viral no estilo daqueles esqueletos/personagens 3D. Aciona mesmo quando o usuário só cola a copy e diz "faz o storyboard disso".
---

# Storyboard Viral 3D — Character VSL para TikTok Shop

Transforma uma **copy** (ou apenas um **produto/nicho**) num **storyboard completo cena a cena**, no formato de criativo viral que domina o TikTok Shop: um personagem 3D antropomórfico (estilo Pixar/Disney) que conduz uma VSL comprimida, com troca constante de cenário, legenda karaokê palavra-por-palavra, fake UI nativa e disclaimer de compliance fixo.

O entregável central de cada cena é um **prompt de imagem pronto pra gerar**. Cada cena também traz a locução, a legenda na tela e uma nota de animação (pro `video-prompt-builder` ou geração image-to-video).

## A pegada do formato (o que torna isso viral)

Antes de montar qualquer storyboard, internalize a lógica — ela guia cada decisão:

1. **Hook de roubo de atenção, não de beleza.** Os primeiros 1–2s são um pattern interrupt: close extremo, distorção, movimento exagerado, personagem grotesco-fofo. Não é "bonito", é *scroll-stopping*.
2. **Personagem-mascote como fio condutor.** O MESMO personagem aparece em todas as cenas, costurando cenários completamente diferentes. É isso que dá coesão e torna o formato escalável (troca produto/nicho, mantém personagem).
3. **Churn de cenário.** Cada 3–8s o ambiente muda (academia → quarto → dentro do corpo → praia → escritório → produto). Novidade constante = Hold Rate alto mesmo numa peça longa de 30–60s.
4. **Native disguise.** Fake UI do TikTok (logo + @handle) queimada no vídeo o tempo todo. Faz parecer repost orgânico e marca d'água contra roubo.
5. **Legenda karaokê palavra-por-palavra.** Uma palavra de cada vez, centralizada, com o @handle embaixo. Prende o olho no centro e força a leitura ativa.
6. **Arco de VSL comprimido.** Hook → identificação → problema → mecanismo/ciência → prova/aspiração → produto + CTA. Uma carta de vendas de 30min espremida em 30–60s.
7. **Compliance à vista.** Disclaimer ("results may vary, consult your doctor" / "resultados podem variar, consulte um médico") fixo no rodapé. Separa quem entende de DR de quem toma ban.

## Os dois modos de entrada

### Modo A — Só o produto / nicho
O usuário manda o produto (frasco, link, descrição) ou só o nicho ("suplemento de beterraba pra energia").
1. Primeiro **escreva a copy/roteiro** seguindo o arco de VSL comprimido (use a skill `copywriting` se precisar de mais profundidade de ângulo). Mantenha 30–60s de locução.
2. **Confirme o ângulo com o usuário** em 1–2 linhas antes de gerar o storyboard inteiro ("Vou pela dor de cansaço/baixa energia, com mecanismo de óxido nítrico — fecha?"). Não interrogue; proponha e siga.
3. Depois rode o storyboard normal.

### Modo B — Copy pronta
O usuário cola a copy / VSL / roteiro.
1. **Não reescreva a copy** (a menos que peçam). Respeite as palavras dele.
2. **Segmente a copy em beats** (ver framework abaixo) e mapeie cada segmento numa cena.
3. Rode o storyboard.

## Passo a passo

### 1. Trave o CHARACTER BIBLE (o passo mais importante)
A consistência do personagem entre cenas é o que faz ou quebra o criativo. Antes das cenas, defina um **bloco fixo** descrevendo o mascote — e **embuta esse bloco literalmente no início de TODO prompt de imagem**. Sem isso, cada geração vira um personagem diferente.

- Se o usuário mandou uma **imagem de referência** do personagem → descreva-a fielmente nesse bloco e instrua o uso da imagem como referência na geração.
- Se **não houver** personagem → proponha um que case com o nicho (ex.: esqueleto fitness pra energia/treino; órgão antropomórfico pra saúde intestinal; ver `pixar3d` pra craft de personagem). Trave a faixa/acessório/cor como "assinatura" recorrente.

Formato do bloco (exemplo):
> **CHARACTER BIBLE (copiar em todo prompt):** An anthropomorphic 3D cartoon skeleton, Pixar Disney style, bones inside a glossy translucent rubbery transparent skin, big expressive googly cartoon eyes with bright blue irises, wearing a signature green athletic sweatband headband, photorealistic 3D render with subsurface scattering on the translucent skin.

### 2. Defina o SISTEMA VISUAL PERSISTENTE
Liste uma vez os elementos que se repetem na peça inteira (camada de edição, não vão no prompt de imagem, mas o editor precisa saber):
- **Formato:** vertical 9:16.
- **Render look:** Pixar/Disney 3D fotorrealista, subsurface scattering, global illumination, soft shadows, 4K (consistente em todas as cenas).
- **Legenda karaokê:** palavra-chave por palavra, centralizada, branca com contorno, @handle pequeno embaixo.
- **Fake UI nativa:** logo do TikTok + @handle no canto.
- **Disclaimer fixo:** rodapé, fonte pequena, o tempo todo.

### 3. Mapeie a copy nos beats
Quebre a locução nos beats do framework (próxima seção). Cada beat vira uma ou mais cenas. **A copy manda no ritmo** — não force 7 cenas se a copy só tem 4 beats, nem corte um beat que a copy desenvolve.

Para cada trecho da copy, escolha a **tradução visual** mais forte (a "imagem que ilustra a frase"). Use a biblioteca de metáforas visuais em `references/biblioteca-visual.md`.

### 4. Gere o storyboard — FORMATO DE SAÍDA OBRIGATÓRIO

Comece com o **CHARACTER BIBLE** e o **SISTEMA VISUAL PERSISTENTE**. Depois, cada cena neste formato exato:

```
CENA [N] — [função do beat] (≈[timestamp])
• LOCUÇÃO: "[trecho da copy que toca nessa cena]"
• LEGENDA (karaokê): [palavra(s)-chave destacada(s) na tela]
• TRADUÇÃO VISUAL: [o que aparece — cenário, ação do personagem, enquadramento]
• PROMPT DE IMAGEM:
[prompt completo em inglês, começando com o CHARACTER BIBLE, pronto pra colar no gerador]
• ANIMAÇÃO: [movimento do personagem + câmera; se houver fala, marcar lip-sync em português]
```

Feche com uma linha de **CTA / próximo passo** (ex.: "Cena final emenda com close do produto real + seta vermelha + 'compra no link'").

## Framework de beats (VSL comprimido)

A ordem é flexível e dirigida pela copy, mas esses são os beats canônicos. Cada um tem uma função e um arquétipo visual. Detalhes e variações em `references/beat-framework.md`.

1. **HOOK / Pattern Interrupt** — para o scroll. Close extremo + distorção + movimento. ("what actually happens to your body…")
2. **CALLOUT / Identificação** — quem é o público / estado atual. (personagem relatable no dia a dia)
3. **PROBLEMA / Agitação da dor** — o sofrimento (cansaço, inchaço, baixa libido). Estado-problema visual (personagem exausto, fumaça na cabeça).
4. **MECANISMO / "Aqui está o porquê"** — a ciência. Visual interno (microbioma, células, fluxo sanguíneo) — o "credibility shot".
5. **VILÃO / Choque visceral** — o que tá errado dentro de você (bola de toxina, placa, gordura). Imagem grotesca e memorável.
6. **SOLUÇÃO / Prova / Aspiração** — o "depois" (personagem em forma, casal saudável, energia). Transformação.
7. **PRODUTO + CTA** — quebra do 3D pro real (mão humana segurando o frasco), seta vermelha, "no TikTok Shop / no link".

## Regras do prompt de imagem (cada cena)

- **Sempre começar pelo CHARACTER BIBLE** literal, depois a cena. Isso mantém o personagem idêntico entre gerações.
- **Inglês**, mesmo que a copy/locução seja em português (modelos de imagem performam melhor em inglês). A locução fica em PT no campo LOCUÇÃO.
- **Um beat = uma imagem clara.** Não empilhe duas ideias num frame.
- **Estilo técnico fixo no fim de todo prompt:** `cinematic composition, shallow depth of field, soft lighting with rim light, subsurface scattering, soft shadows, global illumination, highly detailed PBR materials, 50mm lens, f/1.8, Octane render style, ultra detailed, photorealistic lighting, 4K, vertical 9:16 format`.
- Para os beats de **mecanismo** e **vilão**, o personagem pode sair de cena (CGI interno do corpo, macro de bactéria etc.) — aí o CHARACTER BIBLE não entra, mas mantenha o look 3D fotorrealista.
- Para a cena de **produto/CTA**, descreva a **mão humana real** segurando o frasco (quebra proposital do AI pro real) — sem o personagem.
- Para craft mais fino de personagem, ângulo e expressão, puxe da skill `pixar3d`; para realismo de cenário/produto, da `photorealism-prompts`.

## Animação (opcional, mas recomendado)

Cada cena traz uma nota de animação curta (movimento + câmera). Se o usuário quiser os prompts de vídeo completos, encaminhe cada cena pro `video-prompt-builder` (Seedance 2.0) usando a imagem gerada como start frame. Cenas com fala = marcar **lip-sync em português** e sugerir voz via ElevenLabs PT-BR se o timbre nativo não convencer.

## Compliance (saúde / suplemento)

Esse formato vive em nicho de saúde — proteja o criativo:
- Mantenha o **disclaimer** fixo ("Resultados podem variar. Consulte um médico." / versão em inglês).
- Na copy, prefira linguagem de **benefício e sensação** ("mais energia", "leveza") a **claims médicos absolutos** ("cura", "trata", "elimina doença"). Se a copy do usuário tiver claim duro, sinalize o risco de reprovação/ban, mas respeite a decisão dele.
- Não invente ingredientes ou estudos. Se o produto não foi especificado, deixe genérico.

## Referências

- `references/beat-framework.md` — os 7 beats em detalhe, com função, gatilho de copy e arquétipo visual de cada um, além de variações por nicho.
- `references/biblioteca-visual.md` — biblioteca de metáforas visuais (como traduzir frases de copy em imagem) e blocos de prompt reutilizáveis.
- `references/exemplo-storyboard.md` — um storyboard completo de exemplo (do hook ao CTA) pra calibrar o nível de detalhe esperado.
